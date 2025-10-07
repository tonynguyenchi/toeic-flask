from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import random
from flask import redirect, url_for, render_template
from flask_login import UserMixin
from sqlalchemy import event
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, plain_password: str) -> None:
        self.password_hash = generate_password_hash(plain_password)

    def check_password(self, plain_password: str) -> bool:
        return check_password_hash(self.password_hash, plain_password)
    # Relationships
    attempts = db.relationship('ExamAttempt', backref='user', lazy=True)

class ExamAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    score = db.Column(db.Integer)
    total_questions = db.Column(db.Integer, default=200)
    correct_answers = db.Column(db.Integer, default=0)
    is_completed = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='in_progress')
    test_set = db.Column(db.String(50))  # Track which test set was used
    
    # Relationships
    answers = db.relationship('Answer', backref='attempt', lazy=True)

    def calculate_scores(self):
        """Calculate and persist the score for this attempt.
        Compares each saved answer against its question's correct answer,
        updates Answer.is_correct, and aggregates totals.
        Returns a small summary dict for convenience.
        """
        correct_count = 0
        answered_count = 0

        for answer in (self.answers or []):
            question = answer.question
            if not question:
                continue

            if answer.selected_answer:
                answered_count += 1
                is_correct = str(answer.selected_answer).strip().upper() == str(question.correct_answer or '').strip().upper()
                # Only update if changed to avoid unnecessary writes
                if answer.is_correct != is_correct:
                    answer.is_correct = is_correct
                if is_correct:
                    correct_count += 1

        self.correct_answers = correct_count
        # Basic scoring: number of correct answers. Adjust if scaled scoring is required.
        self.score = correct_count
        self.is_completed = True
        self.status = 'completed'

        db.session.add(self)

        return {
            'total_answered': answered_count,
            'correct': correct_count,
            'score': self.score,
        }

    # --- Derived scoring fields expected by templates ---
    @property
    def listening_correct(self) -> int:
        """Number of correct answers in listening (parts 1-4)."""
        count = 0
        for ans in (self.answers or []):
            q = ans.question
            if not q:
                continue
            if q.part in (1, 2, 3, 4) and ans.is_correct:
                count += 1
        return count

    @property
    def reading_correct(self) -> int:
        """Number of correct answers in reading (parts 5-7)."""
        count = 0
        for ans in (self.answers or []):
            q = ans.question
            if not q:
                continue
            if q.part in (5, 6, 7) and ans.is_correct:
                count += 1
        return count

    @property
    def listening_score(self) -> int:
        """Scaled listening score out of 495 (simple linear scale)."""
        # Simple scaling: 100 correct -> 495; 0 -> 0
        return int(round(self.listening_correct * 4.95))

    @property
    def reading_score(self) -> int:
        """Scaled reading score out of 495 (simple linear scale)."""
        return int(round(self.reading_correct * 4.95))

    @property
    def total_score(self) -> int:
        """Total scaled score out of 990."""
        return self.listening_score + self.reading_score

    def get_answers(self):
        """Convenience for templates to list answers."""
        return list(self.answers or [])

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    part = db.Column(db.Integer, nullable=False)
    question_number = db.Column(db.Integer, nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(500))
    option_b = db.Column(db.String(500))
    option_c = db.Column(db.String(500))
    option_d = db.Column(db.String(500))
    correct_answer = db.Column(db.String(1), nullable=False)
    audio_file = db.Column(db.String(200))
    image_file = db.Column(db.String(200))
    test_set = db.Column(db.String(50))
    
    # Relationships
    answers = db.relationship('Answer', backref='question', lazy=True)

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('exam_attempt.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    selected_answer = db.Column(db.String(1))
    is_correct = db.Column(db.Boolean, default=False)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)

def init_sample_questions():
    """Initialize the database with sample questions"""
    # This function is now deprecated - questions are imported from Excel files
    # Keeping minimal structure for backward compatibility
    pass

# =============================================================================
# RBAC (Role-Based Access Control) Models
# =============================================================================

class Role(db.Model):
    """User roles with hierarchical permissions"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    permissions = db.Column(db.JSON)  # List of permission strings
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user_roles = db.relationship('UserRole', backref='role', lazy=True)

class UserRole(db.Model):
    """Many-to-many relationship between users and roles"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # Optional role expiration
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='user_roles')
    assigner = db.relationship('User', foreign_keys=[assigned_by])

# =============================================================================
# Organization Hierarchy Models
# =============================================================================

class Year(db.Model):
    """Academic year (e.g., 2024, 2025)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # e.g., "2024-2025"
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    programs = db.relationship('Program', backref='year', lazy=True)

class Program(db.Model):
    """Academic program within a year (e.g., Computer Science, Business)"""
    id = db.Column(db.Integer, primary_key=True)
    year_id = db.Column(db.Integer, db.ForeignKey('year.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)  # e.g., "CS", "BUS"
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    groups = db.relationship('Group', backref='program', lazy=True)
    
    # Unique constraint on year + code
    __table_args__ = (db.UniqueConstraint('year_id', 'code', name='_year_program_code'),)

class Group(db.Model):
    """Student group within a program (e.g., CS-2024-A, CS-2024-B)"""
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)  # e.g., "A", "B"
    max_students = db.Column(db.Integer, default=50)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user_groups = db.relationship('UserGroup', backref='group', lazy=True)
    
    # Unique constraint on program + code
    __table_args__ = (db.UniqueConstraint('program_id', 'code', name='_program_group_code'),)

class UserGroup(db.Model):
    """Many-to-many relationship between users and groups"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    left_at = db.Column(db.DateTime)  # For tracking when user left
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    user = db.relationship('User', backref='user_groups')

# =============================================================================
# Audit Logging Model
# =============================================================================

class AuditLog(db.Model):
    """Audit trail for all significant actions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action = db.Column(db.String(100), nullable=False)  # e.g., "CREATE_USER", "DELETE_QUESTION"
    resource_type = db.Column(db.String(50), nullable=False)  # e.g., "User", "Question"
    resource_id = db.Column(db.String(50))  # ID of the affected resource
    old_values = db.Column(db.JSON)  # Previous values
    new_values = db.Column(db.JSON)  # New values
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')

# =============================================================================
# Notification Models
# =============================================================================

class NotificationTemplate(db.Model):
    """Email/SMS notification templates"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # "email" or "sms"
    subject = db.Column(db.String(200))  # For email
    body = db.Column(db.Text, nullable=False)
    variables = db.Column(db.JSON)  # Available template variables
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    """Individual notifications sent to users"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('notification_template.id'))
    type = db.Column(db.String(20), nullable=False)  # "email" or "sms"
    subject = db.Column(db.String(200))
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed
    sent_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    template = db.relationship('NotificationTemplate', backref='notifications')

# =============================================================================
# Enhanced User Model with RBAC
# =============================================================================

# Add RBAC fields to existing User model
User.first_name = db.Column(db.String(50))
User.last_name = db.Column(db.String(50))
User.phone = db.Column(db.String(20))
User.is_active = db.Column(db.Boolean, default=True)
User.last_login = db.Column(db.DateTime)
User.failed_login_attempts = db.Column(db.Integer, default=0)
User.last_failed_login = db.Column(db.DateTime)
User.password_reset_token = db.Column(db.String(100))
User.password_reset_expires = db.Column(db.DateTime)

# =============================================================================
# RBAC Helper Functions
# =============================================================================

def get_user_roles(user_id):
    """Get all active roles for a user"""
    return db.session.query(Role).join(UserRole).filter(
        UserRole.user_id == user_id,
        UserRole.is_active == True,
        Role.is_active == True,
        db.or_(UserRole.expires_at.is_(None), UserRole.expires_at > datetime.utcnow())
    ).all()

def get_user_permissions(user_id):
    """Get all permissions for a user across all their roles"""
    roles = get_user_roles(user_id)
    permissions = set()
    for role in roles:
        if role.permissions:
            permissions.update(role.permissions)
    return list(permissions)

def has_permission(user_id, permission):
    """Check if user has a specific permission"""
    permissions = get_user_permissions(user_id)
    return permission in permissions

def log_audit(user_id, action, resource_type, resource_id=None, old_values=None, new_values=None, ip_address=None, user_agent=None):
    """Log an audit event"""
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.session.add(audit)
    db.session.commit()

# =============================================================================
# Initialize RBAC Data
# =============================================================================

def init_rbac_data():
    """Initialize RBAC roles and permissions"""
    roles_data = [
        {
            'name': 'super_admin',
            'display_name': 'Super Administrator',
            'description': 'Full system access with all permissions',
            'permissions': [
                'user.create', 'user.read', 'user.update', 'user.delete',
                'role.create', 'role.read', 'role.update', 'role.delete',
                'org.create', 'org.read', 'org.update', 'org.delete',
                'question.create', 'question.read', 'question.update', 'question.delete',
                'exam.create', 'exam.read', 'exam.update', 'exam.delete',
                'session.create', 'session.read', 'session.update', 'session.delete',
                'report.read', 'audit.read', 'system.admin'
            ]
        },
        {
            'name': 'exam_admin',
            'display_name': 'Exam Administrator',
            'description': 'Manage exams, sessions, and reports',
            'permissions': [
                'user.read', 'user.update',
                'question.create', 'question.read', 'question.update', 'question.delete',
                'exam.create', 'exam.read', 'exam.update', 'exam.delete',
                'session.create', 'session.read', 'session.update', 'session.delete',
                'report.read'
            ]
        },
        {
            'name': 'proctor',
            'display_name': 'Proctor/Instructor',
            'description': 'Monitor exam sessions and view student progress',
            'permissions': [
                'user.read',
                'question.read',
                'exam.read',
                'session.read', 'session.update',
                'report.read'
            ]
        },
        {
            'name': 'content_editor',
            'display_name': 'Content Editor',
            'description': 'Manage question bank and content',
            'permissions': [
                'question.create', 'question.read', 'question.update', 'question.delete',
                'exam.read'
            ]
        },
        {
            'name': 'viewer',
            'display_name': 'Viewer',
            'description': 'Read-only access to reports and basic data',
            'permissions': [
                'user.read',
                'question.read',
                'exam.read',
                'report.read'
            ]
        }
    ]
    
    for role_data in roles_data:
        existing_role = Role.query.filter_by(name=role_data['name']).first()
        if not existing_role:
            role = Role(**role_data)
            db.session.add(role)
    
    db.session.commit()

def init_org_data():
    """Initialize sample organization data"""
    # Create current year
    current_year = Year.query.filter_by(name='2024-2025').first()
    if not current_year:
        current_year = Year(
            name='2024-2025',
            start_date=datetime(2024, 9, 1).date(),
            end_date=datetime(2025, 8, 31).date()
        )
        db.session.add(current_year)
    
    # Create sample programs
    programs_data = [
        {'name': 'Computer Science', 'code': 'CS'},
        {'name': 'Business Administration', 'code': 'BUS'},
        {'name': 'English Language', 'code': 'ENG'},
        {'name': 'Engineering', 'code': 'ENG'}
    ]
    
    for prog_data in programs_data:
        existing_program = Program.query.filter_by(
            year_id=current_year.id, 
            code=prog_data['code']
        ).first()
        if not existing_program:
            program = Program(
                year_id=current_year.id,
                **prog_data
            )
            db.session.add(program)
    
    db.session.commit()

def init_admin_user():
    """Create a super admin user if none exists"""
    admin_user = User.query.filter_by(email='admin@toeic.com').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@toeic.com',
            first_name='System',
            last_name='Administrator'
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        
        # Assign super admin role
        super_admin_role = Role.query.filter_by(name='super_admin').first()
        if super_admin_role:
            user_role = UserRole(
                user_id=admin_user.id,
                role_id=super_admin_role.id,
                assigned_by=admin_user.id
            )
            db.session.add(user_role)
    db.session.commit()