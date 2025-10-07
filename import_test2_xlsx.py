import sys
from typing import Optional

try:
    import pandas as pd  # type: ignore
except Exception as exc:  # pragma: no cover
    print("pandas is required. Install with: pip install pandas openpyxl")
    raise

from app import app
from models import db, Question


def resolve_header(headers: list[str], *aliases: str) -> Optional[str]:
    lower_map = {h.lower().strip(): h for h in headers}
    for alias in aliases:
        key = alias.lower().strip()
        if key in lower_map:
            return lower_map[key]
    return None


def import_test2_from_xlsx(xlsx_path: str, sheet_name: str = "Test 2 questions", test_set: str = "LC Test 2") -> None:
    """Import Test 2 questions from an Excel sheet into the database.

    Expected columns (aliases supported):
      - question_number: question_number, qnum, number, id
      - question_text: question_text, question, text, prompt
      - option_a..d: option_a..d, a..d, choice a..d
      - correct_answer: correct_answer, answer, key, solution
      - part no: part no, part_no, part, partno
      - image (optional): image, image_file, image_path
    """

    # Load sheet via pandas (requires openpyxl engine installed)
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name, dtype=object)
    # Replace NaN with empty strings and normalize whitespace
    df = df.fillna("")
    df = df.applymap(lambda v: v.strip() if isinstance(v, str) else v)

    headers = list(df.columns.astype(str))

    h_qnum = resolve_header(headers, 'question_number', 'qnum', 'q', 'number', 'id', 'question no', 'question_no')
    h_qtext = resolve_header(headers, 'question_text', 'question', 'text', 'prompt')
    h_a = resolve_header(headers, 'option_a', 'a', 'optiona', 'choice_a', 'choice a')
    h_b = resolve_header(headers, 'option_b', 'b', 'optionb', 'choice_b', 'choice b')
    h_c = resolve_header(headers, 'option_c', 'c', 'optionc', 'choice_c', 'choice c')
    h_d = resolve_header(headers, 'option_d', 'd', 'optiond', 'choice_d', 'choice d')
    h_ans = resolve_header(headers, 'correct_answer', 'answer', 'correct', 'key', 'solution')
    h_part = resolve_header(headers, 'part no', 'part_no', 'part', 'partno')
    h_image = resolve_header(headers, 'image', 'image_file', 'image path', 'image_path')

    required = [h_qnum, h_a, h_b, h_c, h_d, h_ans, h_part]
    if any(h is None for h in required):
        print("Missing required columns. Found headers:")
        print(headers)
        print({
            'question_number': h_qnum, 'A': h_a, 'B': h_b, 'C': h_c, 'D': h_d,
            'correct_answer': h_ans, 'part no': h_part
        })
        sys.exit(1)

    created = 0
    updated = 0

    with app.app_context():
        for _, row in df.iterrows():
            # Parse question number
            qnum_val = row.get(h_qnum)
            qnum_raw = str(qnum_val).strip() if qnum_val is not None else ''
            try:
                qnum = int(float(qnum_raw))  # handle numbers like 153.0
            except Exception:
                continue

            # Parse part
            part_val = row.get(h_part)
            part_raw = str(part_val).strip() if part_val is not None else ''
            try:
                part_num = int(float(part_raw))
            except Exception:
                # If part missing, infer from qnum ranges for TOEIC
                if 1 <= qnum <= 10:
                    part_num = 1
                elif 11 <= qnum <= 40:
                    part_num = 2
                elif 41 <= qnum <= 70:
                    part_num = 3
                elif 71 <= qnum <= 100:
                    part_num = 4
                elif 101 <= qnum <= 140:
                    part_num = 5
                elif 141 <= qnum <= 152:
                    part_num = 6
                else:
                    part_num = 7

            q = Question.query.filter_by(question_number=qnum, test_set=test_set).first()
            if not q:
                q = Question(question_number=qnum, test_set=test_set)
                db.session.add(q)
                created += 1
            else:
                updated += 1

            q.part = part_num
            q.question_text = str(row.get(h_qtext) or '')
            q.option_a = str(row.get(h_a) or '')
            q.option_b = str(row.get(h_b) or '')
            q.option_c = str(row.get(h_c) or '')
            q.option_d = str(row.get(h_d) or '')
            ans = (row.get(h_ans) or '').strip().upper()[:1]
            q.correct_answer = ans
            if h_image:
                img = str(row.get(h_image) or '').strip()
                if img:
                    # Normalize to relative path under images/ if it's an absolute content path
                    norm = img.replace('\\', '/')
                    key = '/Content/Images/'
                    if key in norm:
                        rel = norm.split(key, 1)[1]
                        q.image_file = rel
                    else:
                        q.image_file = norm

        db.session.commit()
        print(f"Upsert complete for {test_set}. Created: {created}, Updated: {updated}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python import_test2_xlsx.py <path_to_xlsx> [sheet_name]')
        sys.exit(1)

    path = sys.argv[1]
    sheet = sys.argv[2] if len(sys.argv) > 2 else 'Test 2 questions'
    import_test2_from_xlsx(path, sheet_name=sheet, test_set='LC Test 2')


