from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Question, ExamAttempt
from forms import LoginForm, RegistrationForm
from utils import calculate_time_remaining

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        # Check for account lockout (5 failed attempts in 15 minutes)
        if user and user.failed_login_attempts >= 5:
            if user.last_failed_login and datetime.utcnow() - user.last_failed_login < timedelta(minutes=15):
                flash('Account temporarily locked due to too many failed attempts. Try again in 15 minutes.', 'error')
                return render_template('login.html', form=form)
            else:
                user.reset_failed_attempts()
                db.session.commit()
        
        if user and user.check_password(form.password.data):
            user.reset_failed_attempts()
            db.session.commit()
            login_user(user, remember=form.remember_me.data)
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
    # Check for in-progress attempt
    in_progress = ExamAttempt.query.filter_by(
        user_id=current_user.id,
        status='in_progress'
    ).first()
    
    return render_template('home.html', in_progress=in_progress)

@app.route('/start_exam', methods=['POST'])
@login_required
def start_exam():
    # Check if user already has an in-progress exam
    existing = ExamAttempt.query.filter_by(
        user_id=current_user.id,
        status='in_progress'
    ).first()
    
    if existing:
        return redirect(url_for('exam', attempt_id=existing.id))
    
    # Create new exam attempt
    attempt = ExamAttempt()
    attempt.user_id = current_user.id
    db.session.add(attempt)
    db.session.commit()
    
    return redirect(url_for('exam', attempt_id=attempt.id))

@app.route('/exam/<int:attempt_id>')
@login_required
def exam(attempt_id):
    attempt = ExamAttempt.query.get_or_404(attempt_id)
    
    # Verify user owns this attempt
    if attempt.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('home'))
    
    # Check if exam is already completed
    if attempt.status in ['completed', 'auto_submitted']:
        flash('This exam has already been completed', 'info')
        return redirect(url_for('results'))
    
    # Calculate remaining time
    time_remaining = calculate_time_remaining(attempt)
    if time_remaining <= 0:
        # Auto-submit if time expired
        attempt.status = 'auto_submitted'
        attempt.end_time = datetime.utcnow()
        attempt.time_remaining = 0
        attempt.calculate_scores()
        db.session.commit()
        flash('Time expired! Exam auto-submitted.', 'warning')
        return redirect(url_for('results'))
    
    # Update remaining time
    attempt.time_remaining = time_remaining
    db.session.commit()
    
    # Get questions
    questions = Question.query.order_by(Question.question_number).all()
    
    return render_template('exam.html', 
                         attempt=attempt, 
                         questions=questions,
                         time_remaining=time_remaining)

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
    if attempt.status != 'in_progress':
        return jsonify({'error': 'Exam is no longer active'}), 400
    
    # Update answer
    attempt.update_answer(question_number, answer)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Answer saved'})

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
    answers = attempt.get_answers()
    
    # Count answered questions
    answered_count = len([a for a in answers.values() if a])
    
    return jsonify({
        'time_remaining': max(0, time_remaining),
        'answers': answers,
        'answered_count': answered_count,
        'total_questions': 200,
        'status': attempt.status
    })

@app.route('/rules_modal')
@login_required
def rules_modal():
    return render_template('partials/rules_modal.html')
