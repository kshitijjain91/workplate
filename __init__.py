from flask import Flask, render_template, url_for, session, redirect, request, flash, g
from wtforms import Form, BooleanField, StringField, PasswordField, HiddenField, validators
from .dbconnect import connection
import datetime
import gc
from passlib.hash import sha256_crypt
from flask_mail import Mail, Message
from flask import current_app as app
from threading import Thread
from .auth import OAuthSignIn


# import emails
# from emails import follower_notification


# app.route('/invite/<invitee_email>')
# def invite(invitee_email):
#     user = User.query.filter_by(nickname=nickname).first()
#     # ...
#     follower_notification(user, g.user)
#     return redirect(url_for('user', nickname=nickname))


app = Flask(__name__)
# app.config.from_envvar('YOURAPPLICATION_SETTINGS')
# app.config.from_object(__name__)

# app.config.from_object('config')
app.config.from_pyfile('config.py')

mail = Mail(app)

# threading emails
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()

# flask mail generic function
# def send_email(subject, sender, recipients, text_body, html_body):
#     msg = Message(subject, sender=sender, recipients=recipients)
#     msg.body = text_body
#     msg.html = html_body
#     mail.send(msg)

# function to send mails using rendered templates
def invite_mail(invitee_email, inviter_email, team_name, team_id):
    send_email(subject = "{0} has invited you to join workplate".format(inviter_email),
               sender = app.config['ADMINS'][0],
               recipients = invitee_email,
               text_body = render_template("inviter_email.txt", invitee_email=invitee_email, inviter_email=inviter_email),
               html_body = render_template("inviter_email.html", invitee_email=invitee_email, inviter_email=inviter_email,
                team_name = team_name, team_id = int(team_id), first_name = session.get('first_name')))
                # team_name = team_name, inviter_name = inviter_name))

@app.route('/mail/', methods = ['GET', 'POST'])
def send_mail():
    # msg = Message(subject = 'Hey There!', sender=app.config['ADMINS'][0], recipients=['kshitij.jain@upgrad.com'])
    # send_email(subject = 'Hello from workplate!', sender=app.config['ADMINS'][0],
        # recipients=['kshitij.jain@upgrad.com'], text_body='Hello there!', html_body=None)
    invite_mail('kshitij.jain@upgrad.com', 'kshitijjain91@gmail.com')

    return redirect(url_for('homepage'))



@app.route('/', methods = ['GET', 'POST'])
@app.route('/homepage/', methods = ['GET', 'POST'])
def homepage():
    return render_template("homepage.html")


# defining wtforms class for registration form
class RegistrationForm(Form):
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    first_name = StringField('First Name', [validators.Length(min=2, max=80)])
    last_name = StringField('Last Name', [validators.Length(min=0, max=80)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the terms of service.', [validators.DataRequired()])

    # creating two hidden fields for team name and team id
    team_name = HiddenField("Team Name")
    team_id = HiddenField("Team ID")



@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    try:
        form = RegistrationForm(request.form)
        # flash(form.validate())

        if request.method == 'POST' and form.validate():
            email = form.email.data
            username = email.split('@')[0]
            first_name = form.first_name.data
            last_name = form.last_name.data


            # unique username ensure

            if email is None:
                flash("Please enter an email address.")

            password = sha256_crypt.encrypt(str(form.password.data))
            c, conn = connection()

            x = c.execute("select * from users where email = (%s)", (email, ))

            if int(x) > 0:
                flash("Sorry! This email is already taken, please choose another one.")
                return render_template('signup.html', form=form)
            else:
                c.execute('''insert into users (email, username, password, first_name, last_name)
                    values (%s, %s, %s, %s, %s)''', (email, username, password, first_name, last_name))
                conn.commit()
                flash("Thanks for registering.")
                conn.close()
                gc.collect()
                session['logged_in'] = True
                session['username'] = username
                session['email'] = email
                session['first_name'] = first_name
                session['last_name'] = last_name
                session['team_id'] = None
                session['team_name'] = None

                return redirect(url_for('all_project_tasks'))
        elif request.method == 'POST':
            flash("The two passwords should match, please try again.")

        gc.collect()
        return render_template('signup.html', form=form)
    except Exception as e:
        return(str(e))


@app.route('/signup_via_invitation/', methods = ['GET', 'POST'])
@app.route('/signup_via_invitation/<team_name>/<team_id>/', methods = ['GET', 'POST'])
def signup_via_invitation(team_name = None, team_id = None):
    try:
        c, conn = connection()
        form = RegistrationForm(request.form)
        # flash(form.validate())

        if request.method == 'POST' and form.validate():
            email = form.email.data
            username = email.split('@')[0]
            first_name = form.first_name.data
            last_name = form.last_name.data
            # team_name = request.form.get('team_name')
            # team_id = request.form.get('team_id')

            # hidden fields - team name and team ID
            # form = TestForm(request.values, fld1="foo", fld2="bar")
            # team_name = form.team_name.data
            # team_id = form.team_id.data
            flash(team_name)
            flash(team_id)

            # unique username ensure

            if email is None:
                flash("Please enter an email address.")

            password = sha256_crypt.encrypt(str(form.password.data))

            x = c.execute("select * from users where email = (%s)", (email, ))

            if int(x) > 0:
                flash("Sorry! This email is already taken, please login if you already have an account.")
                return render_template('signup_via_invitation.html', form=form)
            else:
                c.execute('''insert into users (email, username, password, first_name, last_name)
                    values (%s, %s, %s, %s, %s);''', (email, username, password, first_name, last_name))
                conn.commit()

                # insert the user into the team
                user_id = c.execute(''' select max(user_id) from users;''')
                user_id = c.fetchone()[0]

                # c.execute(''' insert into users_teams (user_id, team_id)
                    # values (%s, %s);''', (user_id, team_id))
                # conn.commit()

                flash("Thanks for registering.")

                gc.collect()
                session['logged_in'] = True
                session['username'] = username
                session['email'] = email
                session['first_name'] = first_name
                session['last_name'] = last_name
                session['team_id'] = team_id
                session['team_name'] = team_name


                return redirect(url_for('all_project_tasks'))
        elif request.method == 'POST':
            flash("The two passwords should match, please try again.")

        gc.collect()
        return render_template('signup_via_invitation.html', form=form)
    except Exception as e:
        return(str(e))
    finally:
        conn.close()
        # insert_user_into_team(team_id)

def insert_user_into_team(team_id):
    try:
        c, conn = connection()

        # insert the user into the team
        user_id = c.execute(''' select max(user_id) from users;''')
        user_id = c.fetchone()[0]
        c.execute(''' insert into users_teams (user_id, team_id)
                    values (%s, %s);''', (user_id, team_id))
        conn.commit()

    except Exception as e:
        flash(str(e))
    finally:
        conn.close()


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
                    session['email'] = data_row[1]
                    session['first_name'] = data_row[4]
                    session['last_name'] = data_row[5]

                    if len(get_user_teams(username_to_userid(session['username']))) !=0 :
                        session['team_id'] = get_user_teams(username_to_userid(session['username']))[0][0]
                        session['team_name'] = get_user_teams(username_to_userid(session['username']))[0][1]
                    else:
                        session['team_id'] = None
                        session['team_name'] = None

                    # flash('You are now logged in as ' + str(session['username']))
                    return redirect(url_for('all_project_tasks'))
                else:
                    flash('Invalid password, try again.')
        gc.collect()
        return render_template('login.html', error=error)
    except Exception as e:
        flash(str(e))
        return render_template('login.html', error=e)



@app.route('/signup_invite/<team_name>/<team_id>/', methods = ['GET', 'POST'])
def signup_invite(team_name, team_id):
    # if method is post, check if already a member; if no then sign him in
    # if method is not post, return the same page again
    try:
        c, conn = connection()

        if request.method == 'POST':
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            password = request.form.get('password')

            if email is None:
                    flash("Please enter an email address.")

            #check email match
            data = c.execute("select * from users where email = (%s)", (email, ))
            if int(data) > 0:
                flash('''Looks like your account already exists, please try logging in.''')

            else:
                # new user, sign him in: enter fname, lname, username and email into the db,
                # encrypt password and put him in the new team
                password = sha256_crypt.encrypt(str(password))
                username = email.split('@')[0]

                c.execute('''insert into users (email, username, password, first_name, last_name)
                    values (%s, %s, %s, %s, %s)''', (email, username, password, first_name, last_name))
                conn.commit()

                # get the last userid
                userid = c.execute(''' select max(user_id) from users;''')
                user_id = c.fetchone()[0]

                # put him in the new team as well
                c.execute(''' insert into users_teams (user_id, team_id)
                    values (%s, %s);''', (user_id, last_team_id))
                conn.commit()


                flash("Thanks for registering.")
                conn.close()
                gc.collect()
                session['logged_in'] = True
                session['username'] = username
                session['email'] = email
                session['first_name'] = first_name
                session['last_name'] = last_name
                session['team_id'] = team_id
                session['team_name'] = team_name

                # successfully signed in, now log him in
                return redirect(url_for('all_project_tasks'))
        return redirect(url_for('signup_invite', team_name = team_name, team_id = team_id))
    except Exception as e:
        flash(str(e))




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

def get_all_user_emails():
    try:
        c, conn = connection()
        c.execute("select email from users;")
        all_users_email = c.fetchall()
        return all_users_email
    except Exception as e:
        return(str(e))


def get_user_projects(user_id):
    try:
        c, conn = connection()
        c.execute(''' select distinct p.project_id, p.project_name
            from users_projects up, projects p, projects_teams pt
            where up.user_id = (%s) and p.project_id=up.project_id
            and p.project_id = pt.project_id and pt.team_id = (%s);''', (user_id, session['team_id']))
        user_projects = c.fetchall()
        conn.commit()
        return user_projects
    except Exception as e:
        return(str(e))
    finally:
        conn.close()

def get_user_teams(user_id):
    try:
        c, conn = connection()
        c.execute(''' select distinct t.team_id, t.team_name
            from users_teams ut, teams t
            where ut.user_id = (%s) and t.team_id = ut.team_id;''', (user_id, ))
        user_teams = c.fetchall()
        conn.commit()
        return user_teams
    except Exception as e:
        return(str(e))
    finally:
        conn.close()


@app.route('/change_team/<team_id>/', methods = ['GET', 'POST'])
def change_team(team_id):
    session['team_id'] = team_id

    c, conn = connection()
    c.execute(''' select team_name from teams where team_id = (%s);''', (team_id))
    team_name = c.fetchone()
    team_name = team_name[0]
    session['team_name'] = team_name
    return redirect(url_for('all_project_tasks'))

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
    if int(user_data) == 0:
        user_data = c.execute("select user_id from users where email = (%s)", (username, ))

    user_id = c.fetchone()[0]



    conn.close()
    return user_id

def userid_to_username(user_id):
    c, conn = connection()
    user_data = c.execute("select username from users where user_id = (%s)", (user_id, ))
    username = c.fetchone()
    conn.close()
    return username

def email_to_userid(email):
    c, conn = connection()
    user_data = c.execute("select user_id from users where email = (%s)", (email, ))
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
            conn.commit()

            c, conn = connection()
            lastid = c.execute(''' select max(project_id) from projects;''')
            lastid = c.fetchone()[0]
            conn.commit()


            # insert project id into projects_teams
            c, conn = connection()
            c.execute(''' insert into projects_teams (project_id, team_id) values (%s, %s);''',
                (lastid, int(session.get('team_id'))))
            conn.commit()


            for username in users_in_project:
                c, conn = connection()
                user_id = username_to_userid(username)
                c.execute(''' insert into users_projects (user_id, project_id)
                    values (%s, %s);''', (user_id, lastid))
                conn.commit()

            # return redirect(url_for('dashboard', username=session['username']))
            return redirect(url_for('all_project_tasks'))
        return render_template("new_project.html", all_users_list=get_all_users(),
            users_in_team = get_users_in_team(session.get('team_id')))

    except Exception as e:
        flash(str(e))
    finally:
        conn.close()

@app.route('/new_team/', methods = ['GET', 'POST'])
def new_team():
    try:
        c, conn = connection()

        if request.method == 'POST':

            invitee_list = request.form.getlist('invitee_emails')
            invitee_list = invitee_list[0].split(",")
            workplate_invitees = []
            new_invitees = []

            # divide invitees into two lists - 1) already on workplate and 2) new ones

            for email_id in invitee_list:
                c, conn = connection()
                x = c.execute("select * from users where email = (%s)", (email_id, ))

                if int(x) > 0:
                    workplate_invitees.append(email_id)
                else:
                    new_invitees.append(email_id)

            # flash(new_invitees)
            # flash(workplate_invitees)
            # flash(session['first_name'])


            # insert new team into DB
            user_id = username_to_userid(session.get('username'))
            users_in_team = workplate_invitees
            users_in_team.append(session.get('email'))

            # flash(users_in_team)
            if len(new_invitees) != 0:
                flash("{0} have been sent an email invitation".format(', '.join(new_invitees)))

            c.execute(''' insert into teams (team_name, creator_id) values (%s, %s);''',
                (request.form.get('team_name', None), user_id))
            conn.commit()

            # get last team id
            last_team_id = c.execute(''' select max(team_id) from teams;''')
            last_team_id = c.fetchone()[0]
            conn.commit()
            conn.close()

            # send invitation mails to new_invitees
            invite_mail(invitee_email = new_invitees, inviter_email = session['email'],
                team_name = request.form.get('team_name'), team_id = last_team_id)

            # insert users into the team
            c, conn = connection()
            for email in users_in_team:
                user_id = email_to_userid(email)
                c.execute(''' insert into users_teams (user_id, team_id)
                    values (%s, %s);''', (user_id, last_team_id))
                conn.commit()

            session['team_id'] = last_team_id
            session['team_name'] = request.form.get('team_name', None)

            return redirect(url_for('all_project_tasks'))

        return render_template("new_team.html", all_user_emails=get_all_user_emails())
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


def get_users_in_team(team_id):
    try:
        c, conn = connection()
        c.execute('''select username from users u, users_teams ut
            where u.user_id = ut.user_id and
            team_id = (%s);''', (team_id, ))

        users_in_team = c.fetchall()
        return users_in_team
    except Exception as e:
        return(str(e))

@app.route('/new_task/<project_id>/<tab>/', methods = ['GET', 'POST'])
def new_task(project_id, tab = '#secondtab'):
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


            # return redirect(url_for('project_tasks', project_id = project_id))
            return redirect(redirect_url() + tab)

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

        # your completed tasks
        c, conn = connection()
        c.execute(''' select t.task_id, assigned_by, description, date(assigned_at), date(due_at), username,
            date(timepoint)
            from tasks t, task_status ta, users u where u.user_id = assigned_by and
            t.task_id = ta.task_id and assigned_to = (%s)
            and ta.status='done' and project_id = (%s)
            order by date(due_at) asc;''',
            (user_id, project_id))
        tasks_completed_by_you = c.fetchall()
        conn.commit()

        task_list_overdue = [ [ x[0], userid_to_username(x[1])[0], x[2],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5] ] for x in task_list_overdue]

        task_list_due_today = [ [ x[0], userid_to_username(x[1])[0], x[2],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5] ] for x in task_list_due_today]

        task_list_due_later = [ [ x[0], userid_to_username(x[1])[0], x[2],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5] ] for x in task_list_due_later]

        tasks_completed_by_you = [ [ x[0], userid_to_username(x[1])[0], x[2],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5],
        datetime.datetime.strptime(str(x[6]), '%Y-%m-%d').strftime('%B %d')] for x in tasks_completed_by_you]

        return [task_list_due_today, task_list_overdue, task_list_due_later, tasks_completed_by_you]

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

        # all_completed_tasks assigned by you
        c.execute(''' select t.task_id, assigned_to, description, date(assigned_at), date(due_at), username,
            date(ta.timepoint)
            from tasks t, task_status ta, users u where u.user_id = assigned_to and
            t.task_id = ta.task_id and assigned_by = (%s) and assigned_to != (%s)
            and status='done' and project_id = (%s)
            order by date(due_at) asc;''',
            (user_id, user_id, project_id))
        tasks_completed_assigned_by_you = c.fetchall()
        conn.commit()


        tasks_by_you_due_today = [ [ x[0], userid_to_username(x[1])[0], x[2],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5] ] for x in tasks_by_you_due_today]

        tasks_by_you_overdue = [ [ x[0], userid_to_username(x[1])[0], x[2],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5] ] for x in tasks_by_you_overdue]


        tasks_by_you_due_later = [ [ x[0], userid_to_username(x[1])[0], x[2],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5] ] for x in tasks_by_you_due_later]

        tasks_completed_assigned_by_you = [ [ x[0], userid_to_username(x[1])[0], x[2],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5], datetime.datetime.strptime(str(x[6]), '%Y-%m-%d').strftime('%B %d')] for x in tasks_completed_assigned_by_you]






        return [tasks_by_you_due_today, tasks_by_you_overdue, tasks_by_you_due_later, tasks_completed_assigned_by_you]

    except Exception as e:
        return(str(e))
    finally:
        conn.close()


def project_summary(project_id):
    try:
        # 1. Currently open tasks
        # Get all delayed/overdue tasks
        c, conn = connection()
        c.execute(''' select t.task_id, assigned_by, assigned_to, date(assigned_at), date(due_at),
            description, ts.status
            from tasks t, task_status ta, task_status ts
            where t.task_id = ta.task_id and t.task_id = ts.task_id and (ts.status = 'open' or ts.status = 'pending')
            and project_id = (%s) and date(due_at) < curdate() order by date(due_at) asc;;''',
            (project_id))
        open_overdue_tasks = c.fetchall()
        conn.commit()

        open_overdue_tasks = [ [ x[0], userid_to_username(x[1])[0], userid_to_username(x[2])[0],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5][0].upper() + x[5][1:],
        x[6] ] for x in open_overdue_tasks]

        # Get all due today tasks
        c, conn = connection()
        c.execute(''' select t.task_id, assigned_by, assigned_to, date(assigned_at), date(due_at),
            description, ts.status
            from tasks t, task_status ta, task_status ts
            where t.task_id = ta.task_id and t.task_id = ts.task_id and
            (ts.status = 'open' or ts.status = 'pending') and
            project_id = (%s) and date(due_at) = curdate() order by date(due_at) asc;;''',
            (project_id))
        open_duetoday_tasks = c.fetchall()
        conn.commit()

        open_duetoday_tasks = [ [ x[0], userid_to_username(x[1])[0], userid_to_username(x[2])[0],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5][0].upper() + x[5][1:],
        x[6] ] for x in open_duetoday_tasks]

        # Get all due later tasks
        c, conn = connection()
        c.execute(''' select t.task_id, assigned_by, assigned_to, date(assigned_at), date(due_at),
            description, ts.status
            from tasks t, task_status ta, task_status ts
            where t.task_id = ta.task_id and t.task_id = ts.task_id and
            (ts.status = 'open' or ts.status = 'pending') and
            project_id = (%s) and date(due_at) > curdate() order by date(due_at) asc;;''',
            (project_id))
        open_duelater_tasks = c.fetchall()
        conn.commit()

        open_duelater_tasks = [ [ x[0], userid_to_username(x[1])[0], userid_to_username(x[2])[0],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5][0].upper() + x[5][1:],
        x[6] ] for x in open_duelater_tasks]

        all_open_tasks = open_overdue_tasks + open_duetoday_tasks + open_duelater_tasks


        # 2. Done tasks
        # Get all tasks completed (irrespective of whether done in time or delayed)
        c, conn = connection()
        c.execute(''' select t.task_id, assigned_by, assigned_to, date(assigned_at), date(due_at),
            description, ts.status, date(ts.timepoint)
            from tasks t, task_status ta, task_status ts
            where t.task_id = ta.task_id and t.task_id = ts.task_id and ts.status = 'done'
            and project_id = (%s) order by date(due_at) asc;''',
            (project_id))
        all_done_tasks = c.fetchall()
        conn.commit()

        all_done_tasks = [ [ x[0], userid_to_username(x[1])[0], userid_to_username(x[2])[0],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5][0].upper() + x[5][1:],
        x[6][0].upper() + x[6][1:],
        datetime.datetime.strptime(str(x[7]), '%Y-%m-%d').strftime('%B %d')] for x in all_done_tasks]


        # get all done later than due
        # get all done in time

        return [open_overdue_tasks, open_duetoday_tasks,
        open_duelater_tasks, all_open_tasks, all_done_tasks]




    except Exception as e:
        return(e)

    finally:
        conn.close()


@app.route('/project_settings/<project_id>/<project_name>/', methods = ['GET', 'POST'])
def project_settings(project_id, project_name):

    # Edit project name, delete project
    # Add users, remove users
    # View info: Created by x on y date

    # Get all users in the project
    users_in_project = get_users_in_project(project_id)

    # Get project info
    try:
        c, conn = connection()
        c.execute('''select creator_id, date(created_at)
            from projects where project_id = (%s);''', (project_id, ))
        conn.commit()
        project_info = c.fetchone()
        project_info = [ userid_to_username(project_info[0]),
        datetime.datetime.strptime(str(project_info[1]), '%Y-%m-%d').strftime('%B %d') ]

    except Exception as e:
        flash(e)
    finally:
        conn.close()

    return render_template("project_settings.html", project_id = project_id,
        project_name = project_name, project_info = project_info,
        users_in_project = users_in_project)



def project_timeline(project_id):
    try:
        c, conn = connection()
        # query list of all task actions in project_id
        c.execute('''select project_id, assigned_by, assigned_to, date(assigned_at),
            date(due_at), description, date(timepoint), status
            from tasks, task_actions where tasks.task_id = task_actions.task_id and project_id = (%s)
            order by date(timepoint) asc;''',
            (project_id, ))
        task_list = c.fetchall()
        conn.commit()
        task_list = [ [ x[0], userid_to_username(x[1])[0], userid_to_username(x[2])[0],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5][0].upper() + x[5][1:],
        datetime.datetime.strptime(str(x[6]), '%Y-%m-%d').strftime('%B %d'),
        x[7] ] for x in task_list]
        return(task_list)


    except Exception as e:
        flash(e)
    finally:
        conn.close()


@app.route('/project_tasks/<project_id>/', methods = ['GET', 'POST'])
def project_tasks(project_id):
    users_in_project = get_users_in_project(project_id)

    all_users_list = get_all_users()
    project_name = projectid_to_projectname(project_id)
    user_projects = get_user_projects(username_to_userid(session.get('username')))
    user_teams  = get_user_teams(username_to_userid(session.get('username')))
    user_id = username_to_userid(session['username'])

    #assigned to you tasks
    task_list_due_today = get_assigned_to_tasks(user_id=user_id, project_id = project_id)[0]
    task_list_overdue = get_assigned_to_tasks(user_id=user_id, project_id = project_id)[1]
    task_list_due_later= get_assigned_to_tasks(user_id=user_id, project_id = project_id)[2]
    tasks_completed_by_you = get_assigned_to_tasks(user_id=user_id, project_id = project_id)[3]
    # all_assigned_to_you = task_list_overdue + task_list_due_today + task_list_due_later


    #assigned by you tasks
    tasks_by_you_due_today = get_assigned_by_tasks(user_id=user_id, project_id=project_id)[0]
    tasks_by_you_overdue = get_assigned_by_tasks(user_id=user_id, project_id=project_id)[1]
    tasks_by_you_due_later = get_assigned_by_tasks(user_id=user_id, project_id=project_id)[2]
    tasks_completed_assigned_by_you = get_assigned_by_tasks(user_id=user_id, project_id=project_id)[3]

    # due_in = [(x[4]-datetime.date.today()).days for x in task_list_due_later]
    # overdue_by = [(datetime.date.today() - x[4]).days for x in task_list_overdue]

    # by_you_due_in = [(x[4]-datetime.date.today()).days for x in tasks_by_you_due_later]
    # by_you_overdue = [(datetime.date.today() - x[4]).days for x in tasks_by_you_overdue]

    timeline = project_timeline(project_id)

    session['back'] = request.base_url



    return render_template("project_tasks.html", users_in_project = users_in_project,
        project_id = project_id, all_users_list = all_users_list,
        user_projects = user_projects, user_teams = user_teams, project_name = project_name,
        task_list_due_today = task_list_due_today, task_list_overdue=task_list_overdue,
        task_list_due_later=task_list_due_later, all_assigned_to_you = all_assigned_to_you,
        tasks_by_you_due_today=tasks_by_you_due_today, tasks_by_you_overdue=tasks_by_you_overdue,
        tasks_by_you_due_later=tasks_by_you_due_later,
        tasks_completed_by_you = tasks_completed_by_you,
        tasks_completed_assigned_by_you = tasks_completed_assigned_by_you,
        # due_in=due_in, overdue_by=overdue_by,
        # by_you_due_in = by_you_due_in, by_you_overdue = by_you_overdue,
        timeline = timeline, open_overdue_tasks = project_summary(project_id)[0],
        open_duetoday_tasks = project_summary(project_id)[1],
        open_duelater_tasks = project_summary(project_id)[2],
        all_open_tasks = project_summary(project_id)[3],
        all_done_tasks = project_summary(project_id)[4])


def all_assigned_to_you(user_id):
    try:
        c, conn = connection()

        # due today open
        c.execute(''' select t.task_id, assigned_by, description, date(assigned_at), date(due_at),
            username, project_name, p.project_id
            from tasks t, task_status ta, users u, projects p, projects_teams pt
            where u.user_id = assigned_by and
            t.task_id = ta.task_id and t.project_id = p.project_id and assigned_to = (%s)
            and status='open' and date(t.due_at) = curdate() and
            pt.project_id = p.project_id and pt.team_id = (%s);''',
            (user_id, session.get('team_id')))
        task_list_due_today = c.fetchall()
        conn.commit()

        task_list_due_today = [ [ x[0], userid_to_username(x[1])[0],
        x[2][0].upper() + x[2][1:],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5], x[6], x[7]] for x in task_list_due_today]


        # flash(session['team_id'])
        # overdue open
        c, conn = connection()
        c.execute(''' select t.task_id, assigned_by, description, date(assigned_at), date(due_at),
            username, project_name, p.project_id
            from tasks t, task_status ta, users u, projects p, projects_teams pt
            where u.user_id = assigned_by and
            t.task_id = ta.task_id and assigned_to = (%s) and t.project_id = p.project_id
            and status='open' and date(t.due_at) < curdate() and pt.project_id = p.project_id and pt.team_id = (%s)
            order by date(due_at) asc;''',
            (user_id, session.get('team_id')))
        task_list_overdue = c.fetchall()
        conn.commit()

        task_list_overdue = [ [ x[0], userid_to_username(x[1])[0],
        x[2][0].upper() + x[2][1:],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5], x[6], x[7] ] for x in task_list_overdue]

        # due later open
        c, conn = connection()
        c.execute(''' select t.task_id, assigned_by, description, date(assigned_at), date(due_at),
            username, project_name, p.project_id
            from tasks t, task_status ta, users u, projects p, projects_teams pt
            where u.user_id = assigned_by and t.task_id = ta.task_id and assigned_to = (%s)
            and t.project_id = p.project_id and status='open' and date(t.due_at) > curdate()
            and pt.project_id = p.project_id and pt.team_id = (%s)
            order by date(due_at) asc;''',
            (user_id, session.get('team_id')))
        task_list_due_later = c.fetchall()
        conn.commit()


        task_list_due_later = [ [ x[0], userid_to_username(x[1])[0],
        x[2][0].upper() + x[2][1:],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5], x[6], x[7]] for x in task_list_due_later]

        # all assigned to you completed
        c, conn = connection()
        c.execute(''' select t.task_id, assigned_by, description, date(assigned_at),
            date(due_at), username, date(ta.timepoint), project_name, p.project_id
            from tasks t, task_status ta, users u, projects p, projects_teams pt
            where u.user_id = assigned_by and
            t.task_id = ta.task_id and assigned_to = (%s) and t.project_id = p.project_id
            and pt.project_id = p.project_id and pt.team_id = (%s)
            and status='done'
            order by date(due_at) asc;''',
            (user_id, session.get('team_id')))
        all_completed_tasks = c.fetchall()
        conn.commit()

        all_completed_tasks = [ [ x[0], userid_to_username(x[1])[0],
        x[2][0].upper() + x[2][1:],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5],
        datetime.datetime.strptime(str(x[6]), '%Y-%m-%d').strftime('%B %d'),
        x[7], x[8] ] for x in all_completed_tasks]

        return [task_list_due_today, task_list_overdue, task_list_due_later, all_completed_tasks]
    except Exception as e:
        flash(str(e))
    finally:
        conn.close()

def all_assigned_by_you(user_id):
    try:
        c, conn = connection()

        # due today
        c.execute(''' select t.task_id, assigned_to, description, date(assigned_at), date(due_at),
            username, project_name, p.project_id
            from tasks t, task_status ta, users u, projects p, projects_teams pt
            where u.user_id = assigned_to and
            t.task_id = ta.task_id and assigned_by = (%s) and assigned_to != (%s) and
            t.project_id = p.project_id and status='open' and date(t.due_at) = curdate()
            and pt.project_id = p.project_id and pt.team_id = (%s);''',
            (user_id, user_id, session.get('team_id')))
        task_list_due_today = c.fetchall()
        conn.commit()

        task_list_due_today = [ [ x[0], userid_to_username(x[1])[0],
        x[2][0].upper() + x[2][1:],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5], x[6], x[7] ] for x in task_list_due_today]

        # overdue
        c, conn = connection()
        c.execute(''' select t.task_id, assigned_to, description, date(assigned_at), date(due_at),
            username, project_name, p.project_id
            from tasks t, task_status ta, users u, projects p, projects_teams pt
            where u.user_id = assigned_to and
            t.task_id = ta.task_id and assigned_by = (%s) and assigned_to != (%s) and t.project_id = p.project_id
            and status='open' and date(t.due_at) < curdate()
            and pt.project_id = p.project_id and pt.team_id = (%s)
            order by date(due_at) asc;''',
            (user_id, user_id, session.get('team_id')))
        task_list_overdue = c.fetchall()
        conn.commit()

        task_list_overdue = [ [ x[0], userid_to_username(x[1])[0],
        x[2][0].upper() + x[2][1:],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5], x[6], x[7] ] for x in task_list_overdue]


        # due later
        c, conn = connection()
        c.execute(''' select t.task_id, assigned_to, description, date(assigned_at), date(due_at),
            username, project_name, p.project_id
            from tasks t, task_status ta, users u, projects p, projects_teams pt
            where u.user_id = assigned_to and
            t.task_id = ta.task_id and assigned_by = (%s) and assigned_to != (%s)
            and t.project_id = p.project_id and status='open' and date(t.due_at) > curdate()
            and pt.project_id = p.project_id and pt.team_id = (%s)
            order by date(due_at) asc;''',
            (user_id, user_id, session.get('team_id')))
        task_list_due_later = c.fetchall()
        conn.commit()

        task_list_due_later = [ [ x[0], userid_to_username(x[1])[0],
        x[2][0].upper() + x[2][1:],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5], x[6], x[7]] for x in task_list_due_later]


        # all assigned by you completed
        c, conn = connection()
        c.execute(''' select t.task_id, assigned_to, description, date(assigned_at),
            date(due_at), username, date(ta.timepoint), project_name, p.project_id
            from tasks t, task_status ta, users u, projects p, projects_teams pt
            where u.user_id = assigned_to and
            t.task_id = ta.task_id and assigned_by = (%s) and t.project_id = p.project_id
            and status='done'
            and pt.project_id = p.project_id and pt.team_id = (%s)
            order by date(due_at) asc;''',
            (user_id, session.get('team_id')))
        all_tasks_by_you_completed = c.fetchall()
        conn.commit()

        all_tasks_by_you_completed = [ [ x[0], userid_to_username(x[1])[0],
        x[2][0].upper() + x[2][1:],
        datetime.datetime.strptime(str(x[3]), '%Y-%m-%d').strftime('%B %d'),
        datetime.datetime.strptime(str(x[4]), '%Y-%m-%d').strftime('%B %d'),
        x[5],
        datetime.datetime.strptime(str(x[6]), '%Y-%m-%d').strftime('%B %d'),
        x[7], x[8]] for x in all_tasks_by_you_completed]

        return [task_list_due_today, task_list_overdue, task_list_due_later, all_tasks_by_you_completed]
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
    user_teams = get_user_teams(username_to_userid(session.get('username')))
    project_name = 'All Projects'

    # tasks assigned by the user
    task_list_due_today = all_assigned_to_you(user_id=user_id)[0]
    task_list_overdue = all_assigned_to_you(user_id=user_id)[1]
    task_list_due_later = all_assigned_to_you(user_id=user_id)[2]
    all_completed_tasks = all_assigned_to_you(user_id=user_id)[3]

    # tasks assigned by the user
    tasks_by_you_due_today = all_assigned_by_you(user_id=user_id)[0]
    tasks_by_you_overdue = all_assigned_by_you(user_id=user_id)[1]
    tasks_by_you_due_later = all_assigned_by_you(user_id=user_id)[2]
    all_tasks_by_you_completed = all_assigned_by_you(user_id=user_id)[3]

    # due_in = [(x[4]-datetime.date.today()).days for x in task_list_due_later]
    # overdue_by = [(datetime.date.today() - x[4]).days for x in task_list_overdue]

    # by_you_due_in = [(x[4]-datetime.date.today()).days for x in tasks_by_you_due_later]
    # by_you_overdue = [(datetime.date.today() - x[4]).days for x in tasks_by_you_overdue]

    session['back'] = request.base_url

    # Get the aggregated numbers of all tasks in each project
    # for each project, get:
    # 1. Open tasks - Overdue, due today, due later
    # 2. Postpone completed tasks for now
    open_tasks_list = []

    all_tasks_all_projects = 0

    if len(user_projects) != 0:
        for project in user_projects:
            p_id = project[0]
            p_name = project[1]
            open_overdue_tasks = len(project_summary(p_id)[0])
            open_duetoday_tasks = len(project_summary(p_id)[1])
            open_duelater_tasks = len(project_summary(p_id)[2])
            all_done_tasks = len(project_summary(p_id)[4])

            open_tasks_list.append({
                'project_id': p_id,
                'project_name': p_name,
                'open_overdue_tasks': open_overdue_tasks,
                'open_duetoday_tasks': open_duetoday_tasks,
                'open_duelater_tasks': open_duelater_tasks,
                'all_open_tasks': open_overdue_tasks + open_duetoday_tasks + open_duelater_tasks,
                'all_done_tasks': all_done_tasks,
                'all_tasks': open_overdue_tasks + open_duetoday_tasks + open_duelater_tasks + all_done_tasks
                })


        for dict1 in open_tasks_list:
            all_tasks_all_projects += dict1['all_tasks']


    return render_template("project_tasks.html", users_in_project = all_users_list,
        project_id = None, all_users_list = all_users_list,
        user_projects = user_projects, user_teams = user_teams,
        users_in_team = get_users_in_team(session['team_id']),
        project_name = project_name,
        task_list_due_today = task_list_due_today, task_list_overdue=task_list_overdue,
        task_list_due_later=task_list_due_later,
        tasks_completed_by_you = all_completed_tasks,
        tasks_by_you_due_today=tasks_by_you_due_today, tasks_by_you_overdue=tasks_by_you_overdue,
        tasks_by_you_due_later=tasks_by_you_due_later,
        tasks_completed_assigned_by_you = all_tasks_by_you_completed,
        open_tasks_list = open_tasks_list,
        all_tasks_all_projects = all_tasks_all_projects)
        # due_in=due_in, overdue_by=overdue_by,
        # by_you_due_in = by_you_due_in, by_you_overdue = by_you_overdue)



@app.route('/update_task/<task_id>/<status>/<tab>/', methods = ['GET', 'POST'])
def update_task(task_id, status, tab=''):
    user_id = username_to_userid(session.get('username'))
    try:
        c, conn = connection()
        c.execute(''' insert into task_actions (task_id, user_id, status)
            values (%s, %s, %s);''', (task_id, user_id, status))
        conn.commit()

        return redirect(redirect_url() + tab)
    except Exception as e:
        flash(str(e))
    finally:
        conn.close()


# oauth
@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    # Flask-Login function
    # if not current_user.is_anonymous():
    #     return redirect(url_for('browsebooks'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

# defining an oauth view for logging in through an invitation (so that
# the user can be inserted into the team he/she's invited to)
# @app.route('/authorize/<provider>/<team_id>/')
# def authorize_and_add_to_team(provider, team_id):


@app.route('/callback/<provider>')
def oauth_callback(provider):
    # if not current_user.is_anonymous():
    #     return redirect(url_for('browsebooks'))
    oauth = OAuthSignIn.get_provider(provider)
    name, email = oauth.callback()

    if email is None:
        flash('Authentication failed. Can you try using another account?')
        return(url_for('homepage'))

    # Look if the user already exists, if no then sign him up
    try:
        c, conn = connection()
        emails = c.execute(''' select email from users where email = (%s);''', (email, ))

        # because I've alread used session['username'] several times :/
        username = email.split('@')[0]

        # new user
        if int(emails) <= 0:
            c.execute(''' insert into users (email, username) value (%s, %s);''', (email, username))
            conn.commit()

        # Old user - log him in directly using the email and username
        session['logged_in'] = True
        session['username'] = username
        session['email'] = email
        session['first_name'] = name
        session['last_name'] = None

        if len(get_user_teams(username_to_userid(session['username']))) !=0 :
            session['team_id'] = get_user_teams(username_to_userid(session['username']))[0][0]
            session['team_name'] = get_user_teams(username_to_userid(session['username']))[0][1]
        else:
            session['team_id'] = None
            session['team_name'] = None



    except Exception as e:
        flash(str(e))
    finally:
        conn.close()

    # if email is None:
    #     # I need a valid email address for my user identification
    #     flash('Authentication failed.')
    #     return redirect(url_for('browsebooks'))
    # # Look if the user already exists
    # # user=User.query.filter_by(email=email).first()
    # if not user:
    #     # Create the user. Try and use their name returned by Google,
    #     # but if it is not set, split the email address at the @.
    #     nickname = username
    #     if nickname is None or nickname == "":
    #         nickname = email.split('@')[0]

    #     # We can do more work here to ensure a unique nickname, if you
    #     # require that.
    #     user=User(nickname=nickname, email=email)
    #     db.session.add(user)
    #     db.session.commit()
    # Log in the user, by default remembering them for their next visit
    # unless they log out.
    # login_user(user, remember=True)
    flash("You are logged in as {0}".format(email))
    return redirect(url_for('all_project_tasks'))






















if __name__ == '__main__':
    app.secret_key = 'super_secret_key_1231wqdn'
    app.run(debug=True)
