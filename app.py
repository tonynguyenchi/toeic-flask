from flask import Flask
from flask_login import LoginManager
from models import db, User, init_sample_questions

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-me'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///toeic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))

# Import admin blueprint
from admin_routes import admin_bp

# Register admin blueprint
app.register_blueprint(admin_bp)

# Make has_permission available in templates
@app.context_processor
def inject_permissions():
    from models import has_permission
    return dict(has_permission=has_permission)

with app.app_context():
    db.create_all()
    init_sample_questions()

import routes  # keep this as the last line