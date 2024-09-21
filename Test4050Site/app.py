from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import date

app = Flask(__name__)
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

# Define User Model
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

# User Dashboard Route
@app.route('/user_dashboard')
def user_dashboard():
    current_user_id = 1  # Replace with actual user ID logic
    tasks = Task.query.filter_by(assigned_to=current_user_id).all()
    return render_template('user_dashboard.html', tasks=tasks)

# Manager 1 Dashboard Route
@app.route('/manager1_dashboard')
def manager1_dashboard():
    tasks = Task.query.all()
    return render_template('manager1_dashboard.html', tasks=tasks)

# Manager 2 Dashboard Route
@app.route('/manager2_dashboard')
def manager2_dashboard():
    tasks = Task.query.all()
    today = date.today()
    
    # Example metrics
    average_completion_time = 5  # Placeholder, replace with actual logic
    task_completion_rate = 80  # Placeholder, replace with actual logic

    return render_template('manager2_dashboard.html', tasks=tasks, today=today,
                           average_completion_time=average_completion_time,
                           task_completion_rate=task_completion_rate)

# Error handling for 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Error handling for 500
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)

