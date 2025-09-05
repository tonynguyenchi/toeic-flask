# Overview

This is a TOEIC (Test of English for International Communication) practice test application built with Flask. The system provides a comprehensive online exam platform that simulates the official TOEIC test format with 7 parts, 200 questions, and a 120-minute time limit. Users can register, take practice exams, track their progress, and view detailed results with scoring breakdowns for listening and reading sections.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
- **Flask with SQLAlchemy**: Core web framework using Flask-SQLAlchemy for ORM database interactions
- **Flask-Login**: Handles user authentication and session management
- **Flask-WTF**: Manages form validation and CSRF protection
- **Werkzeug ProxyFix**: Enables proper handling of proxy headers for deployment

## Database Design
- **PostgreSQL**: Primary database configured via DATABASE_URL environment variable
- **User Model**: Stores user credentials, failed login tracking, and relationship to exam attempts
- **Question Model**: Contains TOEIC questions with support for multiple parts, audio files, passages, and answer options
- **ExamAttempt Model**: Tracks user exam sessions with timing and progress data
- **Connection Pooling**: Configured with pool recycling and pre-ping for reliability

## Authentication & Security
- **Password Hashing**: Uses Werkzeug's generate_password_hash for secure password storage
- **Account Lockout**: Implements failed login attempt tracking with temporary lockouts (5 attempts in 15 minutes)
- **Session Management**: Flask-Login provides user session handling with remember-me functionality
- **CSRF Protection**: Flask-WTF forms include CSRF tokens for security

## Frontend Architecture
- **Bootstrap Dark Theme**: Uses Replit's bootstrap-agent-dark-theme for consistent UI
- **Multi-Part Navigation**: Tab-based interface for navigating between TOEIC parts I-VII
- **Real-time Timer**: JavaScript-based countdown timer with visual warnings
- **Audio Integration**: Specialized audio controller for listening comprehension sections
- **Progress Tracking**: Visual progress bars and question navigation bubbles

## Exam Logic
- **Part Structure**: Follows official TOEIC format with specific question ranges per part
- **Time Management**: 120-minute exam duration with server-side time validation
- **Answer Persistence**: Real-time saving of user responses with automatic recovery
- **Scoring System**: TOEIC-standard scoring calculation for listening and reading sections

## File Organization
- **Modular Structure**: Separate files for models, forms, routes, and utilities
- **Template Inheritance**: Base template system with consistent navigation and styling
- **Static Assets**: Organized CSS/JS files for exam functionality, audio control, and timing

# External Dependencies

## Core Framework Dependencies
- **Flask**: Web application framework
- **Flask-SQLAlchemy**: Database ORM and connection management
- **Flask-Login**: User authentication and session management
- **Flask-WTF**: Form handling and CSRF protection
- **WTForms**: Form validation and rendering
- **Werkzeug**: WSGI utilities and security functions

## Frontend Libraries
- **Bootstrap**: UI framework with dark theme from Replit CDN
- **Font Awesome**: Icon library for UI elements
- **Custom JavaScript**: Exam timer, audio control, and navigation logic

## Database
- **PostgreSQL**: Primary database system
- **SQLAlchemy**: Database abstraction layer with connection pooling

## Environment Configuration
- **SESSION_SECRET**: Flask session encryption key
- **DATABASE_URL**: PostgreSQL connection string
- **Development Server**: Configured for host 0.0.0.0:5000 with debug mode