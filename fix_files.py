from app import app, db
from models import Question

with app.app_context():
    # Fix audio file names for Part 1 questions
    part1_questions = Question.query.filter_by(part=1).all()
    for q in part1_questions:
        if q.audio_file and 'Part 1' in q.audio_file:
            # Fix the space after hyphen
            q.audio_file = q.audio_file.replace('01-Part', '01- Part')
            print(f'Updated audio for question {q.question_number}: {q.audio_file}')
    
    # Fix image file names for Part 1 questions
    for q in part1_questions:
        if q.image_file and 'part1_photo_' in q.image_file:
            # Update to match actual file names
            q.image_file = f'output_pngs/LC Test 1/JIM_s TOEIC LC TEST 01- Part 1_{q.question_number:02d}.png'
            print(f'Updated image for question {q.question_number}: {q.image_file}')
    
    # Commit changes
    db.session.commit()
    print('Database updated successfully!')
