import mysql.connector

db_user = 'root'
db_database = 'sharebox'
language = 'EN'
cnx = mysql.connector.connect(user=db_user, database=db_database)
cursor = cnx.cursor(dictionary=True)

def log_result(log_data):
    columns = ','.join("`" + str(x).replace('/', '_') + "`" for x in log_data.keys())
    values = ','.join("'" + str(x).replace('/', '_') + "'" for x in log_data.values())
    # sql_delete = "delete from result_log where "
    sql = "INSERT INTO %s (test_time, %s) VALUES (NOW(), %s );" % ('result_log', columns, values)

    try:
        cursor.execute(sql)
        cnx.commit()
    except mysql.connector.Error as e:
        print("x Failed inserting data: {}\n".format(e))

def log_result_ev(ev_data):
    for k,v in ev_data.items():
        columns = ','.join("`" + str(x).replace('/', '_') + "`" for x in v.keys())
        values = ','.join("'" + str(x).replace('/', '_') + "'" for x in v.values())
        # sql_delete = "delete from result_log where "
        sql = "INSERT INTO %s (waste_id, %s) VALUES (%s, %s );" % ('result_log_ev',columns,k, values)

        try:
            cursor.execute(sql)
            cnx.commit()
        except mysql.connector.Error as e:
            print("x Failed inserting data: {}\n".format(e))
