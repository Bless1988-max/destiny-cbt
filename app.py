from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Question, Result
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'destiny-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_first_request
def create_tables():
    db.create_all()

# HOME
@app.route('/')
def index():
    return render_template("index.html")

# SIGNUP (Pupil only)
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        hashed_password = generate_password_hash(request.form['password'])
        user = User(
            username=request.form['username'],
            role="pupil",
            student_class=request.form['student_class'],
            password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully!")
        return redirect(url_for('login'))
    return render_template("signup.html")

# LOGIN (All Roles)
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            if user.role == "admin":
                return redirect(url_for('admin_dashboard'))
            elif user.role == "instructor":
                return redirect(url_for('instructor_dashboard'))
            else:
                return redirect(url_for('pupil_dashboard'))
        flash("Invalid login details")
    return render_template("login.html")

# DASHBOARDS
@app.route('/admin')
@login_required
def admin_dashboard():
    results = Result.query.all()
    return render_template("admin_dashboard.html", results=results)

@app.route('/instructor')
@login_required
def instructor_dashboard():
    results = Result.query.filter_by(student_class=current_user.student_class).all()
    return render_template("instructor_dashboard.html", results=results)

@app.route('/pupil')
@login_required
def pupil_dashboard():
    return render_template("pupil_dashboard.html")

# ADD QUESTION
@app.route('/add_question', methods=['GET','POST'])
@login_required
def add_question():
    if request.method == 'POST':
        question = Question(
            question_text=request.form['question'],
            option_a=request.form['a'],
            option_b=request.form['b'],
            option_c=request.form['c'],
            option_d=request.form['d'],
            correct_answer=request.form['correct'],
            student_class=request.form['student_class']
        )
        db.session.add(question)
        db.session.commit()
        flash("Question Added Successfully")
    return render_template("add_question.html")

# TAKE EXAM
@app.route('/exam')
@login_required
def take_exam():
    questions = Question.query.filter_by(student_class=current_user.student_class).all()
    return render_template("take_exam.html", questions=questions)

# SUBMIT EXAM
@app.route('/submit_exam', methods=['POST'])
@login_required
def submit_exam():
    questions = Question.query.filter_by(student_class=current_user.student_class).all()
    score = 0
    for q in questions:
        answer = request.form.get(str(q.id))
        if answer == q.correct_answer:
            score += 1

    rating = "Needs Improvement"
    if score >= 18:
        rating = "Excellent"
    elif score >= 15:
        rating = "Very Good"
    elif score >= 10:
        rating = "Good"

    result = Result(
        student_id=current_user.id,
        score=score,
        rating=rating,
        student_class=current_user.student_class
    )
    db.session.add(result)
    db.session.commit()

    return redirect(url_for('result'))

@app.route('/result')
@login_required
def result():
    result = Result.query.filter_by(student_id=current_user.id).order_by(Result.id.desc()).first()
    return render_template("result.html", result=result)

# PARENT SEARCH
@app.route('/parent', methods=['GET','POST'])
def parent():
    result = None
    if request.method == 'POST':
        result = Result.query.filter_by(student_id=request.form['student_id']).first()
    return render_template("parent_result.html", result=result)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
