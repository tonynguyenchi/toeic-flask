import os
import sys
import shutil
from typing import Optional

try:
    import pandas as pd  # type: ignore
except Exception:
    print("pandas is required. Install with: pip install pandas openpyxl")
    sys.exit(1)

from app import app
from models import db, Question


def normalize_path(p: str) -> str:
    return p.replace("\\", "/").strip()


def relative_image_path_any(abs_path: str, test_set_folder: str) -> Optional[str]:
    """Return path relative to our app's static/images or Content/Images.

    Preference order:
    1) static/images/<...>
    2) Content/Images/<...>
    3) If neither, return <Test n>/<basename>
    """
    norm = normalize_path(abs_path)
    # Prefer app static
    key_static = "/static/images/"
    if key_static in norm:
        return norm.split(key_static, 1)[1]
    key_static2 = "static/images/"
    if key_static2 in norm:
        return norm.split(key_static2, 1)[1]

    # Fallback: original Content folder
    key_content = "/Content/Images/"
    if key_content in norm:
        return norm.split(key_content, 1)[1]
    key_content2 = "Content/Images/"
    if key_content2 in norm:
        return norm.split(key_content2, 1)[1]

    # Last resort: put into the sheet's test folder
    return f"{test_set_folder}/{os.path.basename(norm)}"


def ensure_copied(abs_src: str, rel_dest: str, static_images_root: str) -> None:
    src = abs_src
    dest = os.path.join(static_images_root, rel_dest.replace("/", os.sep))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        shutil.copy2(src, dest)
    except FileNotFoundError:
        print(f"WARN: Source image not found: {src}")
    except Exception as e:
        print(f"WARN: Failed to copy {src} -> {dest}: {e}")


def sync_images(xlsx_path: str, sheets: list[str]) -> None:
    static_images_root = os.path.join(os.path.dirname(__file__), "static", "images")
    content_root = None  # Optional: could compute from paths if needed

    with app.app_context():
        for sheet in sheets:
            try:
                df = pd.read_excel(xlsx_path, sheet_name=sheet, dtype=object)
            except Exception as e:
                print(f"ERROR: Cannot read sheet '{sheet}': {e}")
                continue

            df = df.fillna("")
            headers = [str(h).strip() for h in list(df.columns.astype(str))]
            lower_map = {h.lower(): h for h in headers}

            def col(*aliases: str) -> Optional[str]:
                for a in aliases:
                    key = a.lower().strip()
                    if key in lower_map:
                        return lower_map[key]
                return None

            h_qnum = col("question_number", "qnum", "q", "number", "id", "question no", "question_no")
            h_part = col("part no", "part_no", "part", "partno")
            h_image = col("image", "image_file", "image path", "image_path")

            if not h_qnum or not h_image:
                print(f"WARN: Missing required columns in '{sheet}'. Have: {headers}")
                continue

            # Determine test set from sheet name
            sheet_lower = sheet.lower()
            if "test 1" in sheet_lower:
                test_set = "LC Test 1"
            elif "test 2" in sheet_lower:
                test_set = "LC Test 2"
            else:
                # Default or unknown; allow override via sheet name
                test_set = sheet
            test_folder = test_set.replace('LC ', '')  # e.g., "Test 1"

            updates = 0

            for _, row in df.iterrows():
                qnum_val = row.get(h_qnum)
                qnum_str = str(qnum_val).strip() if qnum_val is not None else ""
                try:
                    qnum = int(float(qnum_str))
                except Exception:
                    continue

                img_abs = str(row.get(h_image) or "").strip()

                rel = None
                if img_abs:
                    rel = relative_image_path_any(img_abs, test_folder)
                    # Ensure file exists under our static/images; do not copy if it already lives there
                    dest_path = os.path.join(static_images_root, rel.replace("/", os.sep))
                    if not os.path.exists(dest_path):
                        ensure_copied(img_abs, rel, static_images_root)
                else:
                    # Fallback to conventional naming in static images
                    # Derive test number (1,2,...) from test_set like 'LC Test 1'
                    test_num = ''.join(c for c in test_set if c.isdigit()) or test_folder.split()[-1]
                    candidate = f"Test {test_num}/Test {test_num} - question {qnum}.png"
                    if os.path.exists(os.path.join(static_images_root, candidate.replace('/', os.sep))):
                        rel = candidate

                # Update DB only if we have a relative path
                if rel:
                    q = Question.query.filter_by(question_number=qnum, test_set=test_set).first()
                    if not q:
                        continue
                    new_val = rel.replace("\\", "/")
                    if q.image_file != new_val:
                        q.image_file = new_val
                        updates += 1

            db.session.commit()
            print(f"Updated {updates} images for {test_set} from sheet '{sheet}'")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sync_images_from_xlsx.py <path_to_xlsx> [sheet1] [sheet2] ...")
        sys.exit(1)
    xlsx = sys.argv[1]
    sheets = sys.argv[2:] or ["Test 1 questions", "Test 2 questions"]
    sync_images(xlsx, sheets)


