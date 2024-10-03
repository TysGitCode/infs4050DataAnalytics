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
    __tablename__ = 'users'  # Ensure this matches the SQL exactly, including case sensitivity
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'))  # Reference should be roles.role_id
    role = db.relationship('Role', backref=db.backref('users', lazy=True))

class Role(db.Model):
    __tablename__ = 'roles'  # Ensure this matches the SQL exactly, including case sensitivity
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)


class Project(db.Model):
    __tablename__ = 'projects'
    project_id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100), nullable=False)

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/sysadmin_dashboard')
def sysadmin_dashboard():
    return render_template('sysadmin_dashboard.html')

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

    return render_template(
        'manager1_dashboard.html',
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        in_progress_tasks=in_progress_tasks,
        not_started_tasks=not_started_tasks,
        upcoming_deadlines=upcoming_deadlines,
        total_projects=total_projects,
        average_completion_percentage=average_completion_percentage,
        high_priority=high_priority,
        medium_priority=medium_priority,
        low_priority=low_priority
    )

@app.route('/manager2_dashboard')
def manager2_dashboard():
    # Fetch all projects and tasks
    projects = Project.query.all()
    
    # Initialize the data we will pass to the template
    project_data = []
    total_completed_tasks = 0
    total_tasks = 0
    total_completion_time = 0
    task_completion_rates = []
    
    # Prepare team performance data (e.g., for bottom and top employees)
    bottom_employees = []
    top_performers = []
    
    for project in projects:
        # Fetch the tasks related to the project
        tasks = Task.query.filter_by(project_id=project.project_id).all()
        completed_tasks = Task.query.filter_by(project_id=project.project_id, status='Completed').count()
        total_project_tasks = len(tasks)
        
        # Calculate progress percentage
        progress = (completed_tasks / total_project_tasks * 100) if total_project_tasks > 0 else 0
        
        # Calculate average completion time for each task
        total_project_completion_time = sum(task.actual_days for task in tasks if task.actual_days is not None)
        average_completion_time = (total_project_completion_time / completed_tasks) if completed_tasks > 0 else 0
        
        # Prepare data for the task completion rate
        task_completion_rate = (completed_tasks / total_project_tasks * 100) if total_project_tasks > 0 else 0
        
        # Calculate global totals for all projects
        total_completed_tasks += completed_tasks
        total_tasks += total_project_tasks
        total_completion_time += total_project_completion_time
        
        # Fetch owner details
        task = tasks[0] if tasks else None
        owner = User.query.filter_by(user_id=task.owner_id).first() if task else None
        team_member = owner.username if owner else 'N/A'
        
        # Append project-specific data
        project_data.append({
            'project_name': project.project_name,
            'status': task.status if task else 'N/A',
            'due_date': task.due_date.strftime('%Y-%m-%d') if task and task.due_date else 'N/A',
            'progress': round(progress, 2),
            'completed_tasks': completed_tasks,
            'total_tasks': total_project_tasks,
            'priority': task.priority if task else 'N/A',
            'team_members': team_member
        })
        
    # Calculate global completion rate
    global_completion_rate = (total_completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    global_average_completion_time = (total_completion_time / total_completed_tasks) if total_completed_tasks > 0 else 0

    # Fetch bottom and top performers for team performance (this is just a placeholder for now)
    bottom_employees = [{'username': 'Employee A', 'performance_score': 50}, {'username': 'Employee B', 'performance_score': 60}, {'username': 'Employee B', 'performance_score': 60}]
    top_performers = [{'username': 'Employee X', 'performance_score': 95}, {'username': 'Employee Y', 'performance_score': 90}]
    
    # Render the dashboard with all the data
    return render_template(
        'manager2_dashboard.html',
        projects=project_data,
        average_completion_time=round(global_average_completion_time, 2),
        task_completion_rate=round(global_completion_rate, 2),
        bottom_employees=bottom_employees,
        top_performers=top_performers
    )



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
            if user.password == password:  # Direct comparison, consider replacing with hashed passwords
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

# Additional routes for new functionalities

# Route for managing users
@app.route('/manage_users')
def manage_users():
    users = User.query.all()  # Fetch all users from the database
    for user in users:
        print(f"User: {user.username}, Email: {user.email}")  # Debug print to ensure emails are being fetched
    return render_template('manage_users.html', users=users)

# Route for managing tasks
@app.route('/manage_tasks')
def manage_tasks():
    tasks = Task.query.all()
    return render_template('manage_tasks.html', tasks=tasks)

# Route for creating a new user
@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])  # Secure password storage
        role_id = request.form['role_id']
        
        # Create and save the new user
        new_user = User(username=username, email=email, password=password, role_id=role_id)
        db.session.add(new_user)
        db.session.commit()
        flash('User created successfully!')
        return redirect(url_for('manage_users'))
    
    return render_template('create_user.html')  # Create this template with the form for adding a user

# Route for editing a user
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        if request.form['password']:
            user.password = generate_password_hash(request.form['password'])  # Update the password only if provided
        user.role_id = request.form['role_id']
        
        db.session.commit()
        flash('User updated successfully!')
        return redirect(url_for('manage_users'))
    
    return render_template('edit_user.html', user=user)  # Create this template with a pre-filled form for editing a user

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    # Fetch the user from the database
    user = User.query.get_or_404(user_id)
    
    # Ensure all required fields are stored in the session before deletion
    session['deleted_user'] = {
        'user_id': user.user_id,
        'username': user.username,
        'email': user.email,  # Ensure email is correctly stored
        'password': user.password,
        'role_id': user.role_id
    }
    
@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully!')
    return redirect(url_for('manage_tasks'))
    # Perform the deletion
    db.session.delete(user)
    db.session.commit()
    
    # Flash message with undo option
    flash(f"User '{user.username}' deleted. <a href='{url_for('undo_delete_user')}'>Undo</a>", 'info')
    return redirect(url_for('manage_users'))


@app.route('/undo_delete_user', methods=['GET', 'POST'])
def undo_delete_user():
    # Check if a user was deleted and stored in the session
    deleted_user = session.pop('deleted_user', None)
    
    if deleted_user:
        # Recreate the user from the session data
        user = User(
            user_id=deleted_user['user_id'],
            username=deleted_user['username'],
            email=deleted_user['email'],
            password=deleted_user['password'],
            role_id=deleted_user['role_id']
        )
        db.session.add(user)
        db.session.commit()
        flash(f"User '{user.username}' restored successfully!", 'success')
    else:
        flash("No recent deletion to undo.", 'warning')
    
    return redirect(url_for('manage_users'))


# Route for viewing system reports
@app.route('/system_reports')
def system_reports():
    return render_template('system_reports.html')

# Route for settings page
@app.route('/settings')
def settings():
    return render_template('settings.html')

# Example route for creating tasks
@app.route('/create_task', methods=['GET', 'POST'])
def create_task():
    if request.method == 'POST':
        task_name = request.form['task_name']
        description = request.form['description']
        # Additional task fields processing
        new_task = Task(task_name=task_name, description=description, owner_id=1, rank=1, priority='Medium', 
                        start_date=date.today(), end_date=date.today(), due_date=date.today(), status='Not Started', 
                        percent_complete=0.0)
        db.session.add(new_task)
        db.session.commit()
        flash('Task created successfully!')
        return redirect(url_for('manage_tasks'))
    return render_template('create_task.html')

# Route for editing a task
@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    if request.method == 'POST':
        # Update task details based on form inputs
        task.task_name = request.form['task_name']
        task.description = request.form['description']
        task.status = request.form['status']
        task.priority = request.form['priority']
        task.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        task.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        task.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')
        task.percent_complete = float(request.form['percent_complete'])

        db.session.commit()
        flash('Task updated successfully!')
        return redirect(url_for('manage_tasks'))
    
    return render_template('edit_task.html', task=task)

@app.route('/Manager2landing')  # This is the route that triggers the HTML file rendering
def manager_dashboard():
    return render_template('Manager2landing.html')  # Make sure the filename is correct

@app.route('/managerlanding')  # The route to serve the manager landing page
def manager_landing():
    return render_template('managerlanding.html')  # Renders the managerlanding.html template

@app.route('/projectviewmanager1')  # Define the route for the project view page
def project_view_manager1():
    return render_template('projectviewmanager1.html')  # Render the corresponding HTML file

@app.route('/userlanding')  # Define the route for the user landing page
def user_landing():
    return render_template('userlanding.html')  # Render the user landing HTML page

@app.route('/userprojectview')  # Define the route for the user project view page
def user_project_view():
    return render_template('userprojectview.html')  # Render the user project view HTML page

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)
