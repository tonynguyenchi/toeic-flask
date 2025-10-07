from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from models import (
    db, User, Role, UserRole, Year, Program, Group, UserGroup, 
    AuditLog, NotificationTemplate, Notification, Question, ExamAttempt,
    get_user_permissions, has_permission, log_audit, get_user_roles
)
from datetime import datetime, timedelta
import json
import csv
import io
from werkzeug.utils import secure_filename
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# =============================================================================
# Permission Decorators
# =============================================================================

def require_permission(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if not has_permission(current_user.id, permission):
                flash('You do not have permission to access this resource.', 'error')
                return redirect(url_for('admin.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not has_permission(current_user.id, 'system.admin'):
            flash('Admin access required.', 'error')
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# =============================================================================
# Admin Dashboard
# =============================================================================

@admin_bp.route('/')
@login_required
def dashboard():
    """Admin dashboard with overview statistics"""
    if not any(has_permission(current_user.id, perm) for perm in 
               ['user.read', 'question.read', 'exam.read', 'report.read']):
        flash('You do not have admin access.', 'error')
        return redirect(url_for('home'))
    
    # Get statistics
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'total_questions': Question.query.count(),
        'total_exams': ExamAttempt.query.count(),
        'completed_exams': ExamAttempt.query.filter_by(is_completed=True).count(),
        'total_roles': Role.query.count(),
        'total_audit_logs': AuditLog.query.count()
    }
    
    # Recent activity
    recent_audits = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         recent_audits=recent_audits,
                         recent_users=recent_users)

# =============================================================================
# User Management
# =============================================================================

@admin_bp.route('/users')
@require_permission('user.read')
def users():
    """List all users with search and filters"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            db.or_(
                User.username.contains(search),
                User.email.contains(search),
                User.first_name.contains(search),
                User.last_name.contains(search)
            )
        )
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    
    if role_filter:
        query = query.join(UserRole).join(Role).filter(Role.name == role_filter)
    
    users = query.paginate(page=page, per_page=20, error_out=False)
    roles = Role.query.filter_by(is_active=True).all()
    
    return render_template('admin/users.html', 
                         users=users, 
                         roles=roles,
                         search=search,
                         role_filter=role_filter,
                         status_filter=status_filter)

@admin_bp.route('/users/<int:user_id>')
@require_permission('user.read')
def user_detail(user_id):
    """User detail view with roles and groups"""
    user = User.query.get_or_404(user_id)
    user_roles = get_user_roles(user_id)
    user_groups = UserGroup.query.filter_by(user_id=user_id, is_active=True).all()
    recent_audits = AuditLog.query.filter_by(user_id=user_id).order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    return render_template('admin/user_detail.html',
                         user=user,
                         user_roles=user_roles,
                         user_groups=user_groups,
                         recent_audits=recent_audits)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@require_permission('user.create')
def create_user():
    """Create new user"""
    if request.method == 'POST':
        try:
            user = User(
                username=request.form['username'],
                email=request.form['email'],
                first_name=request.form.get('first_name', ''),
                last_name=request.form.get('last_name', ''),
                phone=request.form.get('phone', ''),
                is_active=bool(request.form.get('is_active'))
            )
            user.set_password(request.form['password'])
            
            db.session.add(user)
            db.session.commit()
            
            # Assign roles
            role_ids = request.form.getlist('roles')
            for role_id in role_ids:
                user_role = UserRole(
                    user_id=user.id,
                    role_id=int(role_id),
                    assigned_by=current_user.id
                )
                db.session.add(user_role)
            
            db.session.commit()
            
            # Log audit
            log_audit(current_user.id, 'CREATE_USER', 'User', user.id, 
                     None, {'username': user.username, 'email': user.email},
                     request.remote_addr, request.headers.get('User-Agent'))
            
            flash('User created successfully.', 'success')
            return redirect(url_for('admin.user_detail', user_id=user.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'error')
    
    roles = Role.query.filter_by(is_active=True).all()
    return render_template('admin/create_user.html', roles=roles)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@require_permission('user.update')
def edit_user(user_id):
    """Edit user"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            old_values = {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'is_active': user.is_active
            }
            
            user.username = request.form['username']
            user.email = request.form['email']
            user.first_name = request.form.get('first_name', '')
            user.last_name = request.form.get('last_name', '')
            user.phone = request.form.get('phone', '')
            user.is_active = bool(request.form.get('is_active'))
            
            if request.form.get('password'):
                user.set_password(request.form['password'])
            
            # Update roles
            UserRole.query.filter_by(user_id=user_id).delete()
            role_ids = request.form.getlist('roles')
            for role_id in role_ids:
                user_role = UserRole(
                    user_id=user.id,
                    role_id=int(role_id),
                    assigned_by=current_user.id
                )
                db.session.add(user_role)
            
            db.session.commit()
            
            # Log audit
            new_values = {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'is_active': user.is_active
            }
            log_audit(current_user.id, 'UPDATE_USER', 'User', user.id,
                     old_values, new_values,
                     request.remote_addr, request.headers.get('User-Agent'))
            
            flash('User updated successfully.', 'success')
            return redirect(url_for('admin.user_detail', user_id=user.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'error')
    
    roles = Role.query.filter_by(is_active=True).all()
    user_roles = [ur.role_id for ur in UserRole.query.filter_by(user_id=user_id).all()]
    
    return render_template('admin/edit_user.html', user=user, roles=roles, user_roles=user_roles)

# =============================================================================
# Question Bank Management
# =============================================================================

@admin_bp.route('/questions')
@require_permission('question.read')
def questions():
    """List all questions with search and filters"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    part_filter = request.args.get('part', '')
    test_set_filter = request.args.get('test_set', '')
    
    query = Question.query
    
    if search:
        query = query.filter(Question.question_text.contains(search))
    
    if part_filter:
        query = query.filter_by(part=int(part_filter))
    
    if test_set_filter:
        query = query.filter_by(test_set=test_set_filter)
    
    questions = query.paginate(page=page, per_page=20, error_out=False)
    
    # Get filter options
    parts = db.session.query(Question.part).distinct().all()
    test_sets = db.session.query(Question.test_set).distinct().all()
    
    return render_template('admin/questions.html',
                         questions=questions,
                         parts=[p[0] for p in parts if p[0]],
                         test_sets=[t[0] for t in test_sets if t[0]],
                         search=search,
                         part_filter=part_filter,
                         test_set_filter=test_set_filter)

@admin_bp.route('/questions/<int:question_id>')
@require_permission('question.read')
def question_detail(question_id):
    """Question detail view"""
    question = Question.query.get_or_404(question_id)
    return render_template('admin/question_detail.html', question=question)

@admin_bp.route('/questions/create', methods=['GET', 'POST'])
@require_permission('question.create')
def create_question():
    """Create new question"""
    if request.method == 'POST':
        try:
            question = Question(
                part=int(request.form['part']),
                question_number=int(request.form['question_number']),
                question_text=request.form['question_text'],
                option_a=request.form.get('option_a', ''),
                option_b=request.form.get('option_b', ''),
                option_c=request.form.get('option_c', ''),
                option_d=request.form.get('option_d', ''),
                correct_answer=request.form['correct_answer'],
                audio_file=request.form.get('audio_file', ''),
                image_file=request.form.get('image_file', ''),
                test_set=request.form.get('test_set', '')
            )
            
            db.session.add(question)
            db.session.commit()
            
            # Log audit
            log_audit(current_user.id, 'CREATE_QUESTION', 'Question', question.id,
                     None, {'part': question.part, 'question_number': question.question_number},
                     request.remote_addr, request.headers.get('User-Agent'))
            
            flash('Question created successfully.', 'success')
            return redirect(url_for('admin.question_detail', question_id=question.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating question: {str(e)}', 'error')
    
    return render_template('admin/create_question.html')

# =============================================================================
# Organization Management
# =============================================================================

@admin_bp.route('/organizations')
@require_permission('org.read')
def organizations():
    """Organization hierarchy view"""
    years = Year.query.filter_by(is_active=True).all()
    
    # Calculate statistics
    total_programs = sum(len(year.programs) for year in years)
    total_groups = sum(len(program.groups) for year in years for program in year.programs)
    active_years = len([year for year in years if year.is_active])
    
    return render_template('admin/organizations.html', 
                         years=years,
                         stats={
                             'total_programs': total_programs,
                             'total_groups': total_groups,
                             'active_years': active_years
                         })

@admin_bp.route('/organizations/years')
@require_permission('org.read')
def years():
    """Manage academic years"""
    years = Year.query.all()
    return render_template('admin/years.html', years=years)

@admin_bp.route('/organizations/years/create', methods=['GET', 'POST'])
@require_permission('org.create')
def create_year():
    """Create new academic year"""
    if request.method == 'POST':
        try:
            year = Year(
                name=request.form['name'],
                start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
                end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            )
            
            db.session.add(year)
            db.session.commit()
            
            log_audit(current_user.id, 'CREATE_YEAR', 'Year', year.id,
                     None, {'name': year.name},
                     request.remote_addr, request.headers.get('User-Agent'))
            
            flash('Academic year created successfully.', 'success')
            return redirect(url_for('admin.years'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating year: {str(e)}', 'error')
    
    return render_template('admin/create_year.html')

# =============================================================================
# Audit Logs
# =============================================================================

@admin_bp.route('/audit-logs')
@require_permission('audit.read')
def audit_logs():
    """View audit logs"""
    page = request.args.get('page', 1, type=int)
    user_filter = request.args.get('user', '')
    action_filter = request.args.get('action', '')
    resource_filter = request.args.get('resource', '')
    
    query = AuditLog.query
    
    if user_filter:
        query = query.filter_by(user_id=int(user_filter))
    
    if action_filter:
        query = query.filter(AuditLog.action.contains(action_filter))
    
    if resource_filter:
        query = query.filter(AuditLog.resource_type.contains(resource_filter))
    
    logs = query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=50, error_out=False)
    
    return render_template('admin/audit_logs.html', logs=logs)

# =============================================================================
# Import/Export
# =============================================================================

@admin_bp.route('/import-export')
@admin_required
def import_export():
    """Import/Export interface"""
    return render_template('admin/import_export.html')

@admin_bp.route('/export/users')
@require_permission('user.read')
def export_users():
    """Export users to CSV"""
    users = User.query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Username', 'Email', 'First Name', 'Last Name', 'Phone', 'Active', 'Created At'])
    
    # Write data
    for user in users:
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.first_name or '',
            user.last_name or '',
            user.phone or '',
            user.is_active,
            user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    output.seek(0)
    
    # Log audit
    log_audit(current_user.id, 'EXPORT_USERS', 'User', None,
             None, {'count': len(users)},
             request.remote_addr, request.headers.get('User-Agent'))
    
    return jsonify({
        'csv_data': output.getvalue(),
        'filename': f'users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    })

@admin_bp.route('/export/questions')
@require_permission('question.read')
def export_questions():
    """Export questions to CSV"""
    questions = Question.query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Part', 'Question Number', 'Question Text', 'Option A', 'Option B', 'Option C', 'Option D', 'Correct Answer', 'Audio File', 'Image File', 'Test Set'])
    
    # Write data
    for question in questions:
        writer.writerow([
            question.id,
            question.part,
            question.question_number,
            question.question_text,
            question.option_a or '',
            question.option_b or '',
            question.option_c or '',
            question.option_d or '',
            question.correct_answer,
            question.audio_file or '',
            question.image_file or '',
            question.test_set or ''
        ])
    
    output.seek(0)
    
    # Log audit
    log_audit(current_user.id, 'EXPORT_QUESTIONS', 'Question', None,
             None, {'count': len(questions)},
             request.remote_addr, request.headers.get('User-Agent'))
    
    return jsonify({
        'csv_data': output.getvalue(),
        'filename': f'questions_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    })

# =============================================================================
# Reports and Analytics
# =============================================================================

@admin_bp.route('/reports')
@require_permission('report.read')
def reports():
    """Reports dashboard"""
    # Basic statistics
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'total_questions': Question.query.count(),
        'total_exams': ExamAttempt.query.count(),
        'completed_exams': ExamAttempt.query.filter_by(is_completed=True).count(),
        'avg_score': db.session.query(db.func.avg(ExamAttempt.score)).filter_by(is_completed=True).scalar() or 0
    }
    
    # Recent exam attempts
    recent_exams = ExamAttempt.query.filter_by(is_completed=True)\
        .order_by(ExamAttempt.end_time.desc()).limit(10).all()
    
    return render_template('admin/reports.html', stats=stats, recent_exams=recent_exams)

@admin_bp.route('/reports/user-performance')
@require_permission('report.read')
def user_performance_report():
    """User performance report"""
    users = User.query.join(ExamAttempt).filter(ExamAttempt.is_completed == True).all()
    
    performance_data = []
    for user in users:
        attempts = ExamAttempt.query.filter_by(user_id=user.id, is_completed=True).all()
        if attempts:
            avg_score = sum(a.score or 0 for a in attempts) / len(attempts)
            best_score = max(a.score or 0 for a in attempts)
            performance_data.append({
                'user': user,
                'attempts_count': len(attempts),
                'avg_score': round(avg_score, 2),
                'best_score': best_score,
                'last_attempt': max(a.end_time for a in attempts if a.end_time)
            })
    
    performance_data.sort(key=lambda x: x['avg_score'], reverse=True)
    
    # Calculate summary statistics
    summary_stats = {
        'total_students': len(performance_data),
        'avg_score': round(sum(p['avg_score'] for p in performance_data) / len(performance_data), 1) if performance_data else 0,
        'best_score': max(p['best_score'] for p in performance_data) if performance_data else 0,
        'total_attempts': sum(p['attempts_count'] for p in performance_data) if performance_data else 0
    }
    
    return render_template('admin/user_performance_report.html', 
                         performance_data=performance_data,
                         summary_stats=summary_stats)
