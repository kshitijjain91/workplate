import pymysql
import dbconfig


#create users table
conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base

try:
    with conn.cursor() as cursor:
        cursor.execute(''' select project_id from projects;''')
        projects = cursor.fetchall()
        conn.commit()

        with conn.cursor() as cursor:
            for project in projects:
                cursor.execute(''' insert into projects_teams (project_id, team_id)
                    values (%s, 1);''', (project))
                conn.commit()


except Exception as e:
    print ("Exception occured:{0}".format(e))
finally:
    conn.close()
