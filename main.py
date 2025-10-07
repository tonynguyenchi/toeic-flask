from flask import Flask
from flask_login import LoginManager
from models import db, User, init_sample_questions
from app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)

