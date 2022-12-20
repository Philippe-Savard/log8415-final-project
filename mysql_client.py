import mysql.connector
import time


def connect_to_server(ip, request) -> bool:
    try:
        connection = mysql.connector.connect(
            host=ip,
            database='sakila',
            user='labuser',
            password='password'
        )
        print("Waiting for connection with ")
        while not connection.is_connected():
            time.sleep(2)

        if connection.is_connected():
            print("Connection established!")
            cursor = connection.cursor()
            cursor.execute(request)
            record = cursor.fetchall()
            print(record)
            return True
        else:
            return False
    except Exception as e:
        print("ERROR : an error occured while waiting for connection {}".format(e))
        return False


def try_request(ip, request="select * from sakila.country;"):
    stop = False
    while not stop:
        stop = connect_to_server(ip, request)
