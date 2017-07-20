import pymysql
import dbconfig


#create users table
conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base
try:
    with conn.cursor() as cursor:
        cursor.execute('''create table if not exists users
                        (user_id int not null auto_increment primary key,
                        email varchar(200), username varchar(200),
                        password varchar(300));''')

        conn.commit()

except Exception as e:
    print ("Exception in creating table:{0}".format(e))
finally:
    conn.close()



# create projects table
conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base
try:
    with conn.cursor() as cursor:
        cursor.execute('''create table if not exists projects
            (project_id int not null auto_increment primary key,
            project_name varchar(100) not null,
            creator_id int,
            foreign key (creator_id) references users(user_id));''')
        conn.commit()
except Exception as e:
    print("Exception in creating table: {0}".format(e))
finally:
    conn.close()

# add timestamp column to projects
conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base

try:
    with conn.cursor() as cursor:
        cursor.execute('''alter table projects
          add created_at timestamp
          on update current_timestamp
          not null default current_timestamp;''')
        conn.commit()
except Exception as e:
    print("Exception in adding created_at column: {0}".format(e))
finally:
    conn.close()

# add first name and last name to users table
conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base

# first name
try:
    with conn.cursor() as cursor:
        cursor.execute('''alter table users
          add first_name varchar(200);''')
        conn.commit()
except Exception as e:
    print("Exception in adding first name column: {0}".format(e))
finally:
    conn.close()

conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base
# last name
try:
    with conn.cursor() as cursor:
        cursor.execute('''alter table users
          add last_name varchar(200);''')
        conn.commit()
except Exception as e:
    print("Exception in adding last name column: {0}".format(e))
finally:
    conn.close()



# create users_projects table
conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base

try:
    with conn.cursor() as cursor:
        cursor.execute('''create table if not exists users_projects
            (usr_proj_id int not null auto_increment primary key,
            user_id int,
            project_id int,
            foreign key (user_id) references users(user_id),
            foreign key (project_id) references projects(project_id)
            );''')
        conn.commit()
except Exception as e:
    print(str(e))
finally:
    conn.close()


# create tasks table
conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base

try:
  with conn.cursor() as cursor:
    cursor.execute(''' create table if not exists tasks
      (task_id int not null auto_increment primary key,
      project_id int,
      assigned_by int,
      assigned_to int,
      assigned_at timestamp not null default current_timestamp,
      due_at datetime,
      priority varchar(20),
      description varchar(2000),
      remark_1 varchar(2000),
      foreign key (project_id) references projects(project_id),
      foreign key (assigned_by) references users(user_id),
      foreign key (assigned_to) references users(user_id)
      );''')

except Exception as e:
  print(str(e))
finally:
    conn.close()


# create task_actions table
conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base

try:
  with conn.cursor() as cursor:
    cursor.execute(''' create table if not exists task_actions
      (task_action_id int not null auto_increment primary key,
      task_id int,
      user_id int,
      timepoint timestamp not null default current_timestamp,
      status varchar(50),
      remark_1 varchar(1000),
      remark_2 varchar(1000),
      foreign key (task_id) references tasks(task_id),
      foreign key (user_id) references users(user_id)
      );''')


except Exception as e:
  print(str(e))
finally:
    conn.close()

# create view latest task status
conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base

try:
  with conn.cursor() as cursor:
    cursor.execute(''' create view task_status as
      select * from task_actions t1 where t1.timepoint =
      (select max(t2.timepoint) from task_actions t2 where t1.task_id=t2.task_id);''')

except Exception as e:
  print(str(e))
finally:
    conn.close()


# create teams table
# create projects table
conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base
try:
    with conn.cursor() as cursor:
        cursor.execute('''create table if not exists teams
            (team_id int not null auto_increment primary key,
            team_name varchar(100) not null,
            creator_id int,
            created_at timestamp on update current_timestamp
            not null default current_timestamp,
            foreign key (creator_id) references users(user_id));''')
        conn.commit()
except Exception as e:
    print("Exception in creating table: {0}".format(e))
finally:
    conn.close()


# create users_teams table
conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base

try:
    with conn.cursor() as cursor:
        cursor.execute('''create table if not exists users_teams
            (usr_team_id int not null auto_increment primary key,
            user_id int,
            team_id int,
            foreign key (user_id) references users(user_id),
            foreign key (team_id) references teams(team_id)
            );''')
        conn.commit()
except Exception as e:
    print(str(e))
finally:
    conn.close()


# create projects_teams table
conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base

try:
    with conn.cursor() as cursor:
        cursor.execute('''create table if not exists projects_teams
            (project_team_id int not null auto_increment primary key,
            project_id int,
            team_id int,
            foreign key (project_id) references projects(project_id),
            foreign key (team_id) references teams(team_id)
            );''')
        conn.commit()
except Exception as e:
    print(str(e))
finally:
    conn.close()



# manually run after creating team tables

# create dummy team
# insert into teams (team_name, creator_id) values ('dummy', 1);

# put all current dummy users into the dummy team
# insert into users_teams (user_id, team_id) values ('%s', 1);
# %s = all users id


# put all current dummy projects into the dummy team
# insert into projects_teams (project_id, team_id) values (%s, 1);























