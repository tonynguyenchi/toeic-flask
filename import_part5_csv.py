import csv
import sys
import os

from app import app
from models import db, Question


def upsert_part5(csv_path: str, test_set: str = 'LC Test 1') -> None:
    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}")
        sys.exit(1)

    with app.app_context():
        created = 0
        updated = 0

        # Try UTF-8 with BOM tolerant reading
        with open(csv_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            # Normalize header names
            headers = [h.strip() for h in (reader.fieldnames or [])]
            lower_headers = {h.lower(): h for h in headers}

            # Map possible aliases
            def resolve(*aliases: str) -> str | None:
                for alias in aliases:
                    key = alias.lower().strip()
                    if key in lower_headers:
                        return lower_headers[key]
                return None

            h_qnum = resolve('question_number', 'qnum', 'q', 'number', 'question no', 'question_no', 'question id', 'id')
            h_qtext = resolve('question_text', 'question', 'text', 'prompt')
            h_a = resolve('option_a', 'a', 'optiona', 'choice_a', 'choice a')
            h_b = resolve('option_b', 'b', 'optionb', 'choice_b', 'choice b')
            h_c = resolve('option_c', 'c', 'optionc', 'choice_c', 'choice c')
            h_d = resolve('option_d', 'd', 'optiond', 'choice_d', 'choice d')
            h_ans = resolve('correct_answer', 'answer', 'correct', 'key', 'solution')
            h_part = resolve('part no', 'part_no', 'part', 'partno')

            required_mapped = [h_qnum, h_qtext, h_a, h_b, h_c, h_d, h_ans]
            if any(h is None for h in required_mapped):
                print("CSV missing required columns. Expected aliases for:")
                print("- question_number: question_number/qnum/number/Question No")
                print("- question_text: question_text/question")
                print("- option_a..d: A/B/C/D or option_a..option_d")
                print("- correct_answer: answer/correct")
                print(f"Found headers: {headers}")
                sys.exit(1)

            for row in reader:
                try:
                    qnum_raw = str(row.get(h_qnum, '')).strip()
                    qnum = int(qnum_raw)
                except Exception:
                    print(f"Skip invalid question_number: {row.get(h_qnum)}")
                    continue

                # Check if this is Part 5 using the Part No column
                part_no = str(row.get(h_part, '')).strip()
                if part_no != '5':
                    continue

                if qnum < 101 or qnum > 140:
                    # only import part 5 range per requirement
                    continue

                q = Question.query.filter_by(question_number=qnum, test_set=test_set).first()
                if not q:
                    q = Question()
                    q.part = 5
                    q.question_number = qnum
                    q.test_set = test_set
                    created += 1
                else:
                    updated += 1

                q.question_text = str(row.get(h_qtext, '')).strip()
                q.option_a = str(row.get(h_a, '')).strip()
                q.option_b = str(row.get(h_b, '')).strip()
                q.option_c = str(row.get(h_c, '')).strip()
                q.option_d = str(row.get(h_d, '')).strip()
                q.correct_answer = (str(row.get(h_ans, '')).strip().upper()[:1] or 'A')

                db.session.add(q)

        db.session.commit()
        print(f"Upsert complete. Created: {created}, Updated: {updated}")


if __name__ == '__main__':
    path = r"E:\TOEIC Coach\Content\Jim TOEIC questions.csv"
    if len(sys.argv) > 1:
        path = sys.argv[1]
    upsert_part5(path)
