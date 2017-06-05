import pymysql
import dbconfig as dbconfig

# mysql --user=root -p
def connection():
    conn = pymysql.connect(host="localhost", # your host, usually localhost
                     user=dbconfig.USER, # your username
                      passwd=dbconfig.PASSWORD, # your password
                      db=dbconfig.DATABASE) # name of the data base
    c = conn.cursor()

    return c, conn
