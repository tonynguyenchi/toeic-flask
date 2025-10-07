from app import app
from models import db, Question
import os, ntpath

with app.app_context():
    root = os.path.join('static', 'images')
    fixed = 0
    qs = Question.query.filter(Question.image_file.like('output_pngs/%')).all()
    for q in qs:
        folder = 'Test 1' if 'Test 1' in q.test_set else ('Test 2' if 'Test 2' in q.test_set else None)
        if not folder:
            continue
        base = ntpath.basename(q.image_file.replace('\\', '/'))
        candidate = f'{folder}/{base}'
        path = os.path.join(root, candidate.replace('/', os.sep))
        if os.path.exists(path):
            q.image_file = candidate
            fixed += 1
    db.session.commit()
    print('updated', fixed)