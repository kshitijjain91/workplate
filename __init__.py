from flask import Flask, render_template, url_for, session, redirect, request, flash, g
from wtforms import Form, BooleanField, StringField, PasswordField, validators
from dbconnect import connection
import datetime
import gc
from passlib.hash import sha256_crypt

app = Flask(__name__)

@app.route('/', methods = ['GET', 'POST'])
@app.route('/homepage/', methods = ['GET', 'POST'])
def homepage():
    return render_template("homepage.html")


# defining wtforms class for registration form
class RegistrationForm(Form):
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the terms of service.', [validators.DataRequired()])


@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    try:
        form = RegistrationForm(request.form)

        if request.method == 'POST' and form.validate():
            email = form.email.data
            username = email.split('@')[0]

            # unique username ensure

            if username is None:
                flash("Please choose a username.")

            password = sha256_crypt.encrypt(str(form.password.data))
            c, conn = connection()

            x = c.execute("select * from users where username = (%s)", (username, ))

            if int(x) > 0:
                flash("Sorry! This username is already taken, please choose another one.")
                return render_template('signup.html', form=form)
            else:
                c.execute('''insert into users (email, username, password)
                    values (%s, %s, %s)''', (email, username, password))
                conn.commit()
                flash("Thanks for registering.")
                conn.close()
                gc.collect()
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('homepage'))
        elif request.method == 'POST':
            flash("The two passwords should match, please try again.")

        gc.collect()
        return render_template('signup.html', form=form)
    except Exception as e:
        return(str(e))


@app.route('/login/', methods = ['GET', 'POST'])
def login():
    try:
        c, conn = connection()
        error = None

        if request.method == 'POST':

            #check email match
            data = c.execute("select * from users where email = (%s)", (request.form['email_username'], ))
            if int(data) <= 0:
                flash('''This email address does not exist, please try again or signup
                    for a new account.''')

            if int(data) > 0:
                data_row = c.fetchone()
                data = data_row[3]

                if sha256_crypt.verify(request.form['password'], data):
                    session['logged_in'] = True
                    session['username'] = data_row[2]
                    flash('You are now logged in as ' + str(session['username']))
                    return redirect(url_for('all_project_tasks'))
                else:
                    flash('Invalid password, try again.')
        gc.collect()
        return render_template('login.html', error=error)
    except Exception as e:
        flash(str(e))
        return render_template('login.html', error=e)


@app.route('/logout/')
def logout():
    session.pop('logged_in', None)
    session.clear()
    flash('You have been logged out.')
    gc.collect()
    return redirect(url_for('homepage'))

def get_all_users():
    try:
        c, conn = connection()
        c.execute("select username from users;")
        all_users_list = c.fetchall()
        return all_users_list
    except Exception as e:
        return(str(e))


def get_user_projects(user_id):
    try:
        c, conn = connection()
        c.execute(''' select distinct p.project_id, p.project_name from users_projects up, projects p
            where up.user_id = (%s) and p.project_id=up.project_id;''', (user_id, ))
        user_projects = c.fetchall()
        conn.commit()
        return user_projects
    except Exception as e:
        return(str(e))
    finally:
        conn.close()

@app.route('/dashboard/<username>/', methods = ['GET', 'POST'])
def dashboard(username='guest'):
    all_users_list = get_all_users()
    user_projects = get_user_projects(username_to_userid(session.get('username')))
    return render_template("dashboard.html", all_users_list=all_users_list, user_projects = user_projects)


def redirect_url():
    return request.referrer


def username_to_userid(username):
    c, conn = connection()
    user_data = c.execute("select user_id from users where username = (%s)", (username, ))

    user_id = c.fetchone()[0]
    conn.close()
    return user_id


@app.route('/new_project/', methods = ['GET', 'POST'])
def new_project():
    try:
        c, conn = connection()

        if request.method == 'POST':
            user_id = username_to_userid(session.get('username'))
            users_in_project = request.form.getlist('users_in_project')
            users_in_project.append(session.get('username'))
            c.execute(''' insert into projects (project_name, creator_id) values (%s, %s);''',
                (request.form.get('project_name', None), user_id))

            lastid = c.execute(''' select max(project_id) from projects;''')
            lastid = c.fetchone()[0]

            for username in users_in_project:
                user_id = username_to_userid(username)
                c.execute(''' insert into users_projects (user_id, project_id)
                    values (%s, %s);''', (user_id, lastid))
                conn.commit()

            return redirect(url_for('dashboard', username=session['username']))
        return render_template("new_project.html", all_users_list=get_all_users())

    except Exception as e:
        flash(str(e))
    finally:
        conn.close()


def get_users_in_project(project_id):
    try:
        c, conn = connection()
        c.execute('''select username from users u, users_projects up
            where u.user_id = up.user_id and
            project_id = (%s);''', (project_id, ))

        all_users_list = c.fetchall()
        return all_users_list
    except Exception as e:
        return(str(e))

@app.route('/new_task/<project_id>/', methods = ['GET', 'POST'])
def new_task(project_id):
    users_in_project = get_users_in_project(project_id)

    if request.method == "POST":
        try:
            assigned_to = request.form.get('assigned_to')
            task_description = request.form.get('task_description')
            date_str = request.form.get('due_date')
            due_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            due_date = due_date.strftime('%Y-%m-%d %H:%M:%S')

            assigned_by = username_to_userid(session.get('username'))
            assigned_to = username_to_userid(assigned_to)
            priority = 'high'


            c, conn = connection()
            c.execute(''' insert into tasks (project_id, assigned_by, assigned_to,
                due_at, priority, description) values
                (%s, %s, %s, %s, %s, %s); ''',
                (project_id, assigned_by, assigned_to,
                    due_date, priority, task_description))
            conn.commit()

            # insert task action into task_actions
            c, conn = connection()
            c.execute(''' select max(task_id) from tasks;''')
            task_id = int(c.fetchone()[0])
            status = "open"

            c.execute(''' insert into task_actions (task_id, user_id, status)
                values (%s, %s, %s);''', (task_id, assigned_by, status))
            conn.commit()


            return redirect(url_for('project_tasks', project_id = project_id))

        except Exception as e:
            flash(str(e))


    users_in_project = get_users_in_project(project_id)
    all_users_list = get_all_users()
    project_name = projectid_to_projectname(project_id)
    user_projects = get_user_projects(username_to_userid(session.get('username')))

    return render_template("project_tasks.html", users_in_project = users_in_project,
        project_id = project_id, all_users_list = all_users_list,
        user_projects = user_projects, project_name = project_name)

def projectid_to_projectname(project_id):
    c, conn = connection()
    project_data = c.execute("select project_name from projects where project_id = (%s)", (project_id, ))
    project_name = c.fetchone()[0]
    conn.close()
    return project_name

def get_assigned_to_tasks(user_id, project_id):
    try:
        c, conn = connection()

        # due today
        c.execute(''' select t.task_id, assigned_by, description, date(assigned_at), date(due_at), username
            from tasks t, task_status ta, users u where u.user_id = assigned_by and
            t.task_id = ta.task_id and assigned_to = (%s)
            and status='open' and project_id = (%s) and date(t.due_at) = curdate();''',
            (user_id, project_id))
        task_list_due_today = c.fetchall()
        conn.commit()

        # overdue
        c, conn = connection()
        c.execute(''' select t.task_id, assigned_by, description, date(assigned_at), date(due_at), username
            from tasks t, task_status ta, users u where u.user_id = assigned_by and
            t.task_id = ta.task_id and assigned_to = (%s)
            and status='open' and project_id = (%s) and date(t.due_at) < curdate()
            order by date(due_at) asc;''',
            (user_id, project_id))
        task_list_overdue = c.fetchall()
        conn.commit()

        # due later
        c, conn = connection()
        c.execute(''' select t.task_id, assigned_by, description, date(assigned_at), date(due_at), username
            from tasks t, task_status ta, users u where u.user_id = assigned_by and
            t.task_id = ta.task_id and assigned_to = (%s)
            and status='open' and project_id = (%s) and date(t.due_at) > curdate()
            order by date(due_at) asc;''',
            (user_id, project_id))
        task_list_due_later = c.fetchall()
        conn.commit()

        return [task_list_due_today, task_list_overdue, task_list_due_later]

    except Exception as e:
        return(str(e))
    finally:
        conn.close()

def get_assigned_by_tasks(user_id, project_id):
    try:
        c, conn = connection()

        # due today
        c.execute(''' select t.task_id, assigned_to, description, date(assigned_at), date(due_at), username
            from tasks t, task_status ta, users u where u.user_id = assigned_to and
            t.task_id = ta.task_id and assigned_by = (%s) and assigned_to != (%s)
            and status='open' and project_id = (%s) and date(t.due_at) = curdate();''',
            (user_id, user_id, project_id))
        tasks_by_you_due_today = c.fetchall()
        conn.commit()

        # overdue
        c.execute(''' select t.task_id, assigned_to, description, date(assigned_at), date(due_at), username
            from tasks t, task_status ta, users u where u.user_id = assigned_to and
            t.task_id = ta.task_id and assigned_by = (%s) and assigned_to != (%s)
            and status='open' and project_id = (%s) and date(t.due_at) < curdate()
            order by date(due_at) asc;''',
            (user_id, user_id, project_id))
        tasks_by_you_overdue = c.fetchall()
        conn.commit()

        # due later
        c.execute(''' select t.task_id, assigned_to, description, date(assigned_at), date(due_at), username
            from tasks t, task_status ta, users u where u.user_id = assigned_to and
            t.task_id = ta.task_id and assigned_by = (%s) and assigned_to != (%s)
            and status='open' and project_id = (%s) and date(t.due_at) > curdate()
            order by date(due_at) asc;''',
            (user_id, user_id, project_id))
        tasks_by_you_due_later = c.fetchall()
        conn.commit()


        return [tasks_by_you_due_today, tasks_by_you_overdue, tasks_by_you_due_later]

    except Exception as e:
        return(str(e))
    finally:
        conn.close()


@app.route('/project_tasks/<project_id>/', methods = ['GET', 'POST'])
def project_tasks(project_id):
    users_in_project = get_users_in_project(project_id)

    all_users_list = get_all_users()
    project_name = projectid_to_projectname(project_id)
    user_projects = get_user_projects(username_to_userid(session.get('username')))
    user_id = username_to_userid(session['username'])

    #assigned to you tasks
    task_list_due_today = get_assigned_to_tasks(user_id=user_id, project_id = project_id)[0]
    task_list_overdue = get_assigned_to_tasks(user_id=user_id, project_id = project_id)[1]
    task_list_due_later= get_assigned_to_tasks(user_id=user_id, project_id = project_id)[2]


    #assigned by you tasks
    tasks_by_you_due_today = get_assigned_by_tasks(user_id=user_id, project_id=project_id)[0]
    tasks_by_you_overdue = get_assigned_by_tasks(user_id=user_id, project_id=project_id)[1]
    tasks_by_you_due_later = get_assigned_by_tasks(user_id=user_id, project_id=project_id)[2]

    due_in = [(x[4]-datetime.date.today()).days for x in task_list_due_later]
    overdue_by = [(datetime.date.today() - x[4]).days for x in task_list_overdue]

    by_you_due_in = [(x[4]-datetime.date.today()).days for x in tasks_by_you_due_later]
    by_you_overdue = [(datetime.date.today() - x[4]).days for x in tasks_by_you_overdue]

    session['back'] = request.base_url


    return render_template("project_tasks.html", users_in_project = users_in_project,
        project_id = project_id, all_users_list = all_users_list,
        user_projects = user_projects, project_name = project_name,
        task_list_due_today = task_list_due_today, task_list_overdue=task_list_overdue,
        task_list_due_later=task_list_due_later,
        tasks_by_you_due_today=tasks_by_you_due_today, tasks_by_you_overdue=tasks_by_you_overdue,
        tasks_by_you_due_later=tasks_by_you_due_later,
        due_in=due_in, overdue_by=overdue_by,
        by_you_due_in = by_you_due_in, by_you_overdue = by_you_overdue)


def all_assigned_to_you(user_id):
    try:
        c, conn = connection()

        # due today
        c.execute(''' select t.task_id, assigned_by, description, date(assigned_at), date(due_at), username
            from tasks t, task_status ta, users u where u.user_id = assigned_by and
            t.task_id = ta.task_id and assigned_to = (%s)
            and status='open' and date(t.due_at) = curdate();''',
            (user_id, ))
        task_list_due_today = c.fetchall()
        conn.commit()

        # overdue
        c, conn = connection()
        c.execute(''' select t.task_id, assigned_by, description, date(assigned_at), date(due_at), username
            from tasks t, task_status ta, users u where u.user_id = assigned_by and
            t.task_id = ta.task_id and assigned_to = (%s)
            and status='open' and date(t.due_at) < curdate()
            order by date(due_at) asc;''',
            (user_id, ))
        task_list_overdue = c.fetchall()
        conn.commit()

        # due later
        c, conn = connection()
        c.execute(''' select t.task_id, assigned_by, description, date(assigned_at), date(due_at), username
            from tasks t, task_status ta, users u where u.user_id = assigned_by and
            t.task_id = ta.task_id and assigned_to = (%s)
            and status='open' and date(t.due_at) > curdate()
            order by date(due_at) asc;''',
            (user_id, ))
        task_list_due_later = c.fetchall()
        conn.commit()

        return [task_list_due_today, task_list_overdue, task_list_due_later]
    except Exception as e:
        flash(str(e))
    finally:
        conn.close()

def all_assigned_by_you(user_id):
    try:
        c, conn = connection()

        # due today
        c.execute(''' select t.task_id, assigned_to, description, date(assigned_at), date(due_at), username
            from tasks t, task_status ta, users u where u.user_id = assigned_to and
            t.task_id = ta.task_id and assigned_by = (%s) and assigned_to != (%s)
            and status='open' and date(t.due_at) = curdate();''',
            (user_id, user_id))
        task_list_due_today = c.fetchall()
        conn.commit()

        # overdue
        c, conn = connection()
        c.execute(''' select t.task_id, assigned_to, description, date(assigned_at), date(due_at), username
            from tasks t, task_status ta, users u where u.user_id = assigned_to and
            t.task_id = ta.task_id and assigned_by = (%s) and assigned_to != (%s)
            and status='open' and date(t.due_at) < curdate()
            order by date(due_at) asc;''',
            (user_id, user_id))
        task_list_overdue = c.fetchall()
        conn.commit()

        # due later
        c, conn = connection()
        c.execute(''' select t.task_id, assigned_to, description, date(assigned_at), date(due_at), username
            from tasks t, task_status ta, users u where u.user_id = assigned_to and
            t.task_id = ta.task_id and assigned_by = (%s) and assigned_to != (%s)
            and status='open' and date(t.due_at) > curdate()
            order by date(due_at) asc;''',
            (user_id, user_id))
        task_list_due_later = c.fetchall()
        conn.commit()

        return [task_list_due_today, task_list_overdue, task_list_due_later]
    except Exception as e:
        flash(str(e))
    finally:
        conn.close()

@app.route('/all_project_tasks/', methods = ['GET', 'POST'])
def all_project_tasks():
    user_id = username_to_userid(session['username'])

    # get all users
    all_users_list = get_all_users()
    user_projects = get_user_projects(username_to_userid(session.get('username')))
    project_name = 'All open tasks'

    # tasks assigned by the user
    task_list_due_today = all_assigned_to_you(user_id=user_id)[0]
    task_list_overdue = all_assigned_to_you(user_id=user_id)[1]
    task_list_due_later = all_assigned_to_you(user_id=user_id)[2]

    # tasks assigned by the user
    tasks_by_you_due_today = all_assigned_by_you(user_id=user_id)[0]
    tasks_by_you_overdue = all_assigned_by_you(user_id=user_id)[1]
    tasks_by_you_due_later = all_assigned_by_you(user_id=user_id)[2]

    due_in = [(x[4]-datetime.date.today()).days for x in task_list_due_later]
    overdue_by = [(datetime.date.today() - x[4]).days for x in task_list_overdue]

    by_you_due_in = [(x[4]-datetime.date.today()).days for x in tasks_by_you_due_later]
    by_you_overdue = [(datetime.date.today() - x[4]).days for x in tasks_by_you_overdue]

    session['back'] = request.base_url

    return render_template("project_tasks.html", users_in_project = all_users_list,
        project_id = None, all_users_list = all_users_list,
        user_projects = user_projects, project_name = project_name,
        task_list_due_today = task_list_due_today, task_list_overdue=task_list_overdue,
        task_list_due_later=task_list_due_later,
        tasks_by_you_due_today=tasks_by_you_due_today, tasks_by_you_overdue=tasks_by_you_overdue,
        tasks_by_you_due_later=tasks_by_you_due_later,
        due_in=due_in, overdue_by=overdue_by,
        by_you_due_in = by_you_due_in, by_you_overdue = by_you_overdue)



@app.route('/update_task/<task_id>/<status>/', methods = ['GET', 'POST'])
def update_task(task_id, status):
    user_id = username_to_userid(session.get('username'))
    try:
        c, conn = connection()
        c.execute(''' insert into task_actions (task_id, user_id, status)
            values (%s, %s, %s);''', (task_id, user_id, status))
        conn.commit()
        return redirect(redirect_url())
    except Exception as e:
        flash(str(e))
    finally:
        conn.close()


















if __name__ == '__main__':
    app.secret_key = 'super_secret_key_1231wqdn'
    app.run(debug=True)
