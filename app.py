from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dfs_secret_123'

# -------- DATABASE (WORKS LOCALLY + RENDER) ----------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

if os.environ.get("RENDER"):
    db_path = "/tmp/cbt.db"
else:
    db_path = os.path.join(BASE_DIR, "cbt.db")

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -------- LOGIN MANAGER ----------
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# -------- MODELS ----------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, pupil, instructor, parent
    child_id = db.Column(db.Integer, nullable=True)  # for parents


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20))
    question = db.Column(db.String(500))
    option_a = db.Column(db.String(200))
    option_b = db.Column(db.String(200))
    option_c = db.Column(db.String(200))
    option_d = db.Column(db.String(200))
    answer = db.Column(db.String(1))
    instructor_id = db.Column(db.Integer)


class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pupil_id = db.Column(db.Integer)
    score = db.Column(db.Integer)
    total = db.Column(db.Integer)
    comment = db.Column(db.String(200))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -------- ROUTES ----------

@app.route('/')
def index():
    return render_template('index.html')


# SIGNUP
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']

        if User.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for('signup'))

        user = User(username=username, password=password, role=role)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully")
        return redirect(url_for('login'))

    return render_template('signup.html')


# LOGIN
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)

            if user.role == "admin":
                return redirect(url_for('admin_dashboard'))
            elif user.role == "instructor":
                return redirect(url_for('instructor_dashboard'))
            elif user.role == "parent":
                return redirect(url_for('parent_view'))
            else:
                return redirect(url_for('pupil_dashboard'))

        flash("Invalid login details")

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# PUPIL DASHBOARD
@app.route('/pupil')
@login_required
def pupil_dashboard():
    return render_template('pupil_dashboard.html')


# ADMIN DASHBOARD
@app.route('/admin')
@login_required
def admin_dashboard():
    results = Result.query.all()
    return render_template('admin_dashboard.html', results=results)


# INSTRUCTOR DASHBOARD (ADD QUESTIONS)
@app.route('/instructor', methods=['GET','POST'])
@login_required
def instructor_dashboard():

    if request.method == 'POST':
        q = Question(
            level=request.form['level'],
            question=request.form['question'],
            option_a=request.form['option_a'],
            option_b=request.form['option_b'],
            option_c=request.form['option_c'],
            option_d=request.form['option_d'],
            answer=request.form['answer'],
            instructor_id=current_user.id
        )
        db.session.add(q)
        db.session.commit()
        flash("Question added successfully")

    questions = Question.query.filter_by(instructor_id=current_user.id).all()
    return render_template('instructor_dashboard.html', questions=questions)


# EXAM
@app.route('/exam/<level>', methods=['GET','POST'])
@login_required
def exam(level):

    questions = Question.query.filter_by(level=level).all()

    if request.method == 'POST':
        score = 0

        for q in questions:
            selected = request.form.get(str(q.id))
            if selected == q.answer:
                score += 1

        result = Result(pupil_id=current_user.id, score=score, total=len(questions), comment="Well done!")
        db.session.add(result)
        db.session.commit()

        flash(f"You scored {score}/{len(questions)}")
        return redirect(url_for('pupil_dashboard'))

    return render_template('exam.html', questions=questions, level=level)


# PARENT VIEW RESULT
@app.route('/parent')
@login_required
def parent_view():
    results = Result.query.filter_by(pupil_id=current_user.child_id).all()
    return render_template('parent_view.html', results=results)


# -------- CREATE DATABASE TABLES ----------
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
