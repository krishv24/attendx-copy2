import pymysql

connection = pymysql.connect(host='localhost',
                             user='attendance_user',
                             password='robloxfasds13yr_ver')
try:
    with connection.cursor() as cursor:
        cursor.execute("CREATE DATABASE IF NOT EXISTS attendance_db")
    connection.commit()
finally:
    connection.close()
print("attendance_db created or already exists!")
