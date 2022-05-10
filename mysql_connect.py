from contextlib import closing
import pymysql
from pymysql.cursors import DictCursor
import re
import os


# Попытка подключения к БД
def connection():
    try:
        cursor = pymysql.cursors.DictCursor
        connection = pymysql.connect(
            host='192.168.129.58',
            user='asterisk',
            password='c9eec2B4f3',
            db='asterisk',
            charset='utf8mb4',
            cursorclass=cursor
        )
        return connection
    except:
        return 0


# Запрос файла записи разговора из БД и возврат пути к этому файлу
def call_record(connection, id):
    if connection == 0:
        return 'error'
    else:
        with closing(connection) as connection:
            with connection.cursor() as cursor:
                query = "SELECT recordingfile FROM cdr WHERE uniqueid = %s" %id
                cursor.execute(query)
                if cursor == 0:
                    return 'not found'
                else:
                    for row in cursor:
                        file_name = row['recordingfile']
                        result = re.split('-', file_name)
                        if result == ['']:
                            continue
                        else:
                            date = result[3]
                            year = date[0:4]
                            month = date[4:6]
                            day = date[6:8]
                            file = '/var/spool/asterisk/monitor/%s/%s/%s/%s' % (year, month, day, file_name)
                            if file_size(file) == 1:
                                path = "http://192.168.119.250/monitor/%s/%s/%s/%s" % (year, month, day, file_name)
                                return path


def file_size(file):
    try:
        if os.path.getsize(file) < 1000:
            return 0
        else:
            return 1
    except:
        print("No such file")


'''def main():
    print("start")
    call_record(connection(), id)


if __name__ == '__main__':
    main()'''