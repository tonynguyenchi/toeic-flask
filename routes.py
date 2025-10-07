from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify, session, Blueprint
from flask_login import login_user, logout_user, login_required, current_user, UserMixin, LoginManager
from models import User, Question, ExamAttempt, Answer
from forms import LoginForm, RegistrationForm
from utils import calculate_time_remaining
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from models import db, init_sample_questions

bp = Blueprint('main', __name__)

login_manager = LoginManager()
login_manager.login_view = 'login'  # or your login route name
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return redirect(url_for('home'))  # make sure you have a /home route

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
               
        if user and user.check_password(form.password.data):
            #user.reset_failed_attempts()
            db.session.commit()
            login_user(user, remember=form.remember_me.data)
            
            # Check if user has admin permissions
            from models import has_permission
            if has_permission(user.id, 'system.admin') or has_permission(user.id, 'user.read'):
                # Redirect admin users to admin dashboard
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/') or next_page == '/':
                    next_page = url_for('admin.dashboard')
                return redirect(next_page)
            else:
                # Redirect regular users to home
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('home')
                return redirect(next_page)
        else:
            if user:
                user.failed_login_attempts += 1
                user.last_failed_login = datetime.utcnow()
                db.session.commit()
            flash('Invalid email or password', 'error')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    # Check if user has admin permissions and redirect to admin dashboard
    from models import has_permission
    if has_permission(current_user.id, 'system.admin') or has_permission(current_user.id, 'user.read'):
        return redirect(url_for('admin.dashboard'))
    
    return render_template('home.html')

@app.route('/start_exam', methods=['POST'])
@login_required
def start_exam():
    if request.method == 'GET':
        # Handle GET request - maybe redirect to a different page or show a form
        return redirect(url_for('home'))
    # Handle POST request
    # Randomly assign a test set based on what's available in the DB
    import secrets
    # Collect distinct non-empty test sets from DB
    available_sets = [ (row[0] or '').strip() for row in db.session.query(Question.test_set).distinct().all() ]
    available_sets = [s for s in available_sets if s]

    # Prefer canonical sets if present
    canonical_preferred = ['Test 1', 'Test 2']
    pool = [s for s in available_sets if s in canonical_preferred] or available_sets

    # Avoid repeating the same set back-to-back if there is a choice
    last_set = session.get('test_set')
    if last_set in pool and len(pool) > 1:
        pool_no_repeat = [s for s in pool if s != last_set]
    else:
        pool_no_repeat = pool

    chosen_set = secrets.choice(pool_no_repeat) if pool_no_repeat else 'Test 1'
    session['test_set'] = chosen_set

    attempt = ExamAttempt(
        user_id=current_user.id,
        start_time=datetime.utcnow(),
        total_questions=200,
        correct_answers=0,
        is_completed=False,
        test_set=chosen_set
    )
    db.session.add(attempt)
    db.session.commit()
    return redirect(url_for('exam', attempt_id=attempt.id))

@app.route('/exam/<int:attempt_id>')
@login_required
def exam(attempt_id: int):
    attempt = ExamAttempt.query.get_or_404(attempt_id)
    # Filter questions by selected test set to avoid duplicates across sets
    selected_test_set = session.get('test_set') or 'Test 1'
    questions = Question.query.filter_by(test_set=selected_test_set)\
        .order_by(Question.part, Question.question_number).all()
    
    # Use proper time calculation
    from utils import calculate_time_remaining
    time_remaining = calculate_time_remaining(attempt)
    
    return render_template(
        'exam.html',
        attempt=attempt,
        questions=questions,
        time_remaining=time_remaining,
        current_test_set=selected_test_set
    )

@app.route('/save_answer', methods=['POST'])
@login_required
def save_answer():
    attempt_id = request.form.get('attempt_id')
    question_number = request.form.get('question_number')
    answer = request.form.get('answer')
    
    attempt = ExamAttempt.query.get_or_404(attempt_id)
    
    # Verify user owns this attempt
    if attempt.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Check if exam is still in progress
    if hasattr(attempt, 'status') and attempt.status != 'in_progress':
        return jsonify({'error': 'Exam is no longer active'}), 400
    
    # Resolve question by global question_number
    try:
        qnum = int(question_number)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid question number'}), 400
    question = Question.query.filter_by(question_number=qnum).first()
    if not question:
        return jsonify({'error': 'Question not found'}), 404

    # Upsert Answer
    existing = Answer.query.filter_by(attempt_id=attempt.id, question_id=question.id).first()
    if not existing:
        existing = Answer(attempt_id=attempt.id, question_id=question.id)
        db.session.add(existing)
    existing.selected_answer = (answer or '').strip().upper()[:1]
    db.session.commit()
    
    return jsonify({'success': True, 'question_number': qnum, 'answer': existing.selected_answer})

@app.route('/submit_exam', methods=['POST'])
@login_required
def submit_exam():
    attempt_id = request.form.get('attempt_id')
    attempt = ExamAttempt.query.get_or_404(attempt_id)
    
    # Verify user owns this attempt
    if attempt.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    # Mark as completed and calculate scores
    attempt.status = 'completed'
    attempt.end_time = datetime.utcnow()
    scores = attempt.calculate_scores()
    db.session.commit()
    
    flash('Exam submitted successfully!', 'success')
    return redirect(url_for('results'))

@app.route('/results')
@login_required
def results():
    attempts = ExamAttempt.query.filter_by(user_id=current_user.id)\
                               .filter(ExamAttempt.status.in_(['completed', 'auto_submitted']))\
                               .order_by(ExamAttempt.end_time.desc()).all()
    
    return render_template('results.html', attempts=attempts)

@app.route('/get_exam_state/<int:attempt_id>')
@login_required
def get_exam_state(attempt_id):
    attempt = ExamAttempt.query.get_or_404(attempt_id)
    
    if attempt.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    time_remaining = calculate_time_remaining(attempt)
    
    # Get answers from the relationship
    answers = {}
    for answer in attempt.answers:
        answers[answer.question_id] = answer.selected_answer
    
    # Count answered questions
    answered_count = len([a for a in answers.values() if a])
    
    return jsonify({
        'time_remaining': max(0, time_remaining),
        'answers': answers,
        'answered_count': answered_count,
        'total_questions': 200,
        'progress_percentage': round((answered_count / 200) * 100, 1)
    })
@app.route('/rules_modal')
@login_required
def rules_modal():
    return render_template('partials/rules_modal.html')

@app.route('/test_sets')
@login_required
def test_sets():
    """Display available test sets"""
    test_sets = [
        {
            "id": "Test 1",
            "name": "Test 1",
            "description": "JIM's TOEIC TEST 01",
            "questions_count": Question.query.filter_by(test_set="Test 1").count()
        },
        {
            "id": "Test 2", 
            "name": "Test 2",
            "description": "JIM's TOEIC TEST 02",
            "questions_count": Question.query.filter_by(test_set="Test 2").count()
        }
    ]
    
    return render_template('test_sets.html', test_sets=test_sets)



with app.app_context():
    db.create_all()
    init_sample_questions()

import routes  # keep this as the last line so routes bind to the initialized app
