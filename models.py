from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime)
    
    # Relationships
    attempts = db.relationship('ExamAttempt', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def reset_failed_attempts(self):
        self.failed_login_attempts = 0
        self.last_failed_login = None

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    part = db.Column(db.Integer, nullable=False)  # 1-7 for TOEIC parts I-VII
    question_number = db.Column(db.Integer, nullable=False)  # 1-200
    question_text = db.Column(db.Text)
    option_a = db.Column(db.String(500))
    option_b = db.Column(db.String(500))
    option_c = db.Column(db.String(500))
    option_d = db.Column(db.String(500))
    correct_answer = db.Column(db.String(1), nullable=False)  # A, B, C, or D
    explanation = db.Column(db.Text)
    audio_file = db.Column(db.String(255))  # For listening parts
    passage_text = db.Column(db.Text)  # For reading comprehension
    passage_id = db.Column(db.String(50))  # Group questions by passage
    
    def __repr__(self):
        return f'<Question {self.question_number}: Part {self.part}>'

class ExamAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    time_remaining = db.Column(db.Integer, default=7200)  # 120 minutes in seconds
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed, auto_submitted
    answers = db.Column(db.Text)  # JSON string of answers
    listening_score = db.Column(db.Integer)
    reading_score = db.Column(db.Integer)
    total_score = db.Column(db.Integer)
    listening_correct = db.Column(db.Integer, default=0)
    reading_correct = db.Column(db.Integer, default=0)
    
    def set_answers(self, answers_dict):
        self.answers = json.dumps(answers_dict)
    
    def get_answers(self):
        if self.answers:
            return json.loads(self.answers)
        return {}
    
    def update_answer(self, question_number, answer):
        answers = self.get_answers()
        answers[str(question_number)] = answer
        self.set_answers(answers)
    
    def calculate_scores(self):
        """Calculate TOEIC scores based on correct answers"""
        answers = self.get_answers()
        listening_correct = 0
        reading_correct = 0
        
        # Get all questions
        questions = Question.query.order_by(Question.question_number).all()
        
        for question in questions:
            user_answer = answers.get(str(question.question_number))
            if user_answer == question.correct_answer:
                if question.part <= 4:  # Listening parts
                    listening_correct += 1
                else:  # Reading parts
                    reading_correct += 1
        
        self.listening_correct = listening_correct
        self.reading_correct = reading_correct
        
        # Convert to TOEIC scale (simplified conversion)
        # Listening: 100 questions, scale 5-495
        self.listening_score = min(495, max(5, int(listening_correct * 4.9 + 5)))
        
        # Reading: 100 questions, scale 5-495  
        self.reading_score = min(495, max(5, int(reading_correct * 4.9 + 5)))
        
        self.total_score = self.listening_score + self.reading_score
        
        return {
            'listening_correct': listening_correct,
            'reading_correct': reading_correct,
            'listening_score': self.listening_score,
            'reading_score': self.reading_score,
            'total_score': self.total_score
        }

# Initialize sample questions
def init_sample_questions():
    if Question.query.count() == 0:
        # Create sample questions for all 7 parts
        sample_questions = []
        
        # Part I - Photographs (6 questions)
        for i in range(1, 7):
            question = Question()
            question.part = 1
            question.question_number = i
            question.question_text = f"Look at the picture. Choose the statement that best describes what you see."
            question.option_a = "(A) Audio option A"
            question.option_b = "(B) Audio option B"
            question.option_c = "(C) Audio option C"
            question.option_d = "(D) Audio option D"
            question.correct_answer = "A"
            question.audio_file = "sample.mp3"
            sample_questions.append(question)
        
        # Part II - Question-Response (25 questions)
        for i in range(7, 32):
            question = Question()
            question.part = 2
            question.question_number = i
            question.question_text = "You will hear a question or statement and three responses. Choose the best response."
            question.option_a = "(A) Audio response A"
            question.option_b = "(B) Audio response B"
            question.option_c = "(C) Audio response C"
            question.option_d = ""
            question.correct_answer = "B"
            question.audio_file = "sample.mp3"
            sample_questions.append(question)
        
        # Part III - Conversations (39 questions)
        for i in range(32, 71):
            question = Question()
            question.part = 3
            question.question_number = i
            question.question_text = f"What is the main topic of the conversation?"
            question.option_a = "(A) A business meeting"
            question.option_b = "(B) A job interview"
            question.option_c = "(C) A phone call"
            question.option_d = "(D) A presentation"
            question.correct_answer = "C"
            question.audio_file = "sample.mp3"
            sample_questions.append(question)
        
        # Part IV - Talks (30 questions) 
        for i in range(71, 101):
            question = Question()
            question.part = 4
            question.question_number = i
            question.question_text = "What is the speaker mainly talking about?"
            question.option_a = "(A) Company policies"
            question.option_b = "(B) Product features"
            question.option_c = "(C) Meeting agenda"
            question.option_d = "(D) Travel arrangements"
            question.correct_answer = "B"
            question.audio_file = "sample.mp3"
            sample_questions.append(question)
        
        # Part V - Incomplete Sentences (30 questions)
        for i in range(101, 131):
            question = Question()
            question.part = 5
            question.question_number = i
            question.question_text = f"The company will _______ its new product line next month."
            question.option_a = "(A) launch"
            question.option_b = "(B) launching"
            question.option_c = "(C) launched"
            question.option_d = "(D) to launch"
            question.correct_answer = "A"
            sample_questions.append(question)
        
        # Part VI - Text Completion (16 questions)
        for i in range(131, 147):
            question = Question()
            question.part = 6
            question.question_number = i
            question.question_text = "Choose the best word or phrase to complete the text."
            question.option_a = "(A) However"
            question.option_b = "(B) Therefore"
            question.option_c = "(C) Moreover"
            question.option_d = "(D) Nevertheless"
            question.correct_answer = "B"
            question.passage_text = "Our sales team has been working hard this quarter. _______, we have exceeded our targets."
            question.passage_id = "passage_1"
            sample_questions.append(question)
        
        # Part VII - Reading Comprehension (54 questions)
        for i in range(147, 201):
            question = Question()
            question.part = 7
            question.question_number = i
            question.question_text = "According to the passage, what is the main benefit of the new system?"
            question.option_a = "(A) Cost reduction"
            question.option_b = "(B) Time savings"
            question.option_c = "(C) Better quality"
            question.option_d = "(D) Increased efficiency"
            question.correct_answer = "D"
            question.passage_text = "The new automated system has revolutionized our manufacturing process. It has significantly increased efficiency while maintaining high quality standards. The system reduces manual labor and minimizes errors, leading to better overall productivity."
            question.passage_id = "passage_2"
            sample_questions.append(question)
        
        # Add all questions to database
        for question in sample_questions:
            db.session.add(question)
        
        db.session.commit()
        print("Sample questions initialized successfully!")

# Note: init_sample_questions() will be called from app.py after app context is established
