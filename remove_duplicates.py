from app import app, db
from models import Question
from collections import defaultdict

with app.app_context():
    # Get all questions grouped by part and question_number
    questions_by_part_num = defaultdict(list)
    for q in Question.query.all():
        key = (q.part, q.question_number)
        questions_by_part_num[key].append(q)
    
    # Keep only the first question for each (part, question_number) pair
    deleted_count = 0
    for key, questions in questions_by_part_num.items():
        if len(questions) > 1:
            print(f"Found {len(questions)} duplicates for part {key[0]}, question {key[1]}")
            # Keep the first one, delete the rest
            for q in questions[1:]:
                db.session.delete(q)
                deleted_count += 1
    
    db.session.commit()
    print(f"Deleted {deleted_count} duplicate questions")
    print(f"Remaining questions: {Question.query.count()}")