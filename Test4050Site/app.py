from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
import secrets
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generates a random 32-character hex string

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Slidefire556556@localhost/4050_test'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define Task Model
class Task(db.Model):
    __tablename__ = 'tasks'
    task_id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.Integer, nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    priority = db.Column(db.String(10), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    percent_complete = db.Column(db.Numeric(5, 2), nullable=False)
    estimated_days = db.Column(db.Integer)
    actual_days = db.Column(db.Integer)
    next_task_id = db.Column(db.Integer, db.ForeignKey('tasks.task_id'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'))
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.user_id'))

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Keep this as is for plaintext
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

class Project(db.Model):
    __tablename__ = 'projects'
    project_id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100), nullable=False)

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/sysadmin_dashboard')
def sysadmin_dashboard():
    return render_template('sysadmin_dashboard.html')  # Create this template

@app.route('/manager1_dashboard')
def manager1_dashboard():
    # Calculate task metrics
    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(status='Completed').count()
    in_progress_tasks = Task.query.filter_by(status='In Progress').count()
    not_started_tasks = Task.query.filter_by(status='Not Started').count()
    total_projects = Project.query.count()

    if total_tasks > 0:
        average_completion_percentage = Task.query.with_entities(db.func.avg(Task.percent_complete)).scalar() or 0
    else:
        average_completion_percentage = 0

    high_priority = Task.query.filter_by(priority='High').count()
    medium_priority = Task.query.filter_by(priority='Medium').count()
    low_priority = Task.query.filter_by(priority='Low').count()
    today = datetime.today().date()
    upcoming_deadlines = Task.query.filter(Task.due_date >= today).count()

    return render_template('manager1_dashboard.html', 
                           total_tasks=total_tasks,
                           completed_tasks=completed_tasks,
                           in_progress_tasks=in_progress_tasks,
                           not_started_tasks=not_started_tasks,
                           upcoming_deadlines=upcoming_deadlines,
                           total_projects=total_projects,
                           average_completion_percentage=average_completion_percentage,
                           high_priority=high_priority,
                           medium_priority=medium_priority,
                           low_priority=low_priority)

@app.route('/manager2_dashboard')
def manager2_dashboard():
    tasks = Task.query.all()
    average_completion_time = 5  # Placeholder logic
    task_completion_rate = 80  # Placeholder logic
    active_projects = Project.query.count()
    upcoming_tasks = Task.query.filter(Task.due_date >= date.today()).all()
    bottom_employees = [{'name': 'John Doe', 'performance_score': 60}, {'name': 'Jane Smith', 'performance_score': 65}, {'name': 'Alice Johnson', 'performance_score': 70}]
    top_performers = [{'name': 'Michael Brown', 'performance_score': 95}, {'name': 'David Clark', 'performance_score': 90}, {'name': 'Sara White', 'performance_score': 85}]
    
    return render_template('manager2_dashboard.html', 
                           active_projects=active_projects,
                           upcoming_tasks=upcoming_tasks,
                           average_completion_time=average_completion_time,
                           task_completion_rate=task_completion_rate,
                           bottom_employees=bottom_employees,
                           top_performers=top_performers)

@app.route('/user_dashboard/<int:user_id>')
def user_dashboard(user_id):
    user = User.query.get(user_id)
    tasks = Task.query.filter_by(assigned_to=user_id).all()
    
    if user is None:
        flash('User not found!')
        return redirect(url_for('login'))

    return render_template('user_dashboard.html', user=user, tasks=tasks)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user:
            if user.password == password:  # Direct comparison
                session['user_id'] = user.user_id
                session['role'] = user.role_id
                
                if 'sysadmin' in username.lower():
                    return redirect(url_for('sysadmin_dashboard'))
                elif 'manager1' in username.lower():
                    return redirect(url_for('manager1_dashboard'))
                elif 'manager2' in username.lower():
                    return redirect(url_for('manager2_dashboard'))
                else:
                    return redirect(url_for('user_dashboard', user_id=user.user_id))

            else:
                flash('Invalid username or password')
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    role = session.get('role')
    if role == 'user':
        return redirect(url_for('user_dashboard', user_id=session['user_id']))
    elif role == 'Manager1':
        return redirect(url_for('manager1_dashboard'))
    elif role == 'Manager2':
        return redirect(url_for('manager2_dashboard'))
    elif role == 'sysadmin':
        return redirect(url_for('sysadmin_dashboard'))
    else:
        return redirect(url_for('login'))

# Additional routes and error handling remain unchanged...

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)
