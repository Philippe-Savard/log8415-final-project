import pymysql
from sshtunnel import SSHTunnelForwarder
import random
from pythonping import ping
import paramiko

from flask import Flask, jsonify

app = Flask(__name__)


class Proxy:

    def __init__(self) -> None:
        # List of common write operations in SQL
        self.w_queries = ["insert", "delete", "update", "create", "grant", "revoke"]

        # Current mode of the proxy server.
        # 0: direct
        # 1: random
        # 2: custom
        self.mode = 0

        # Read the public ips of the MySQL cluster.
        with open('/home/ubuntu/flaskapp/public_ips.txt', 'r') as file:
            self.public_ips = file.readlines()

        # Extract the ips
        self.ndb_mgmd_ip = self.public_ips[0]
        self.ndbd_ips = self.public_ips[1:]

        # Read the private key for sshtunnel
        self.ssh_key = paramiko.RSAKey.from_private_key_file("/home/ubuntu/flaskapp/pkey.pem")

    def contains_write_operation(self, request):
        """
        Check if there is a write operation in the request string.
        :param request: A SQL query in the form of a string compatible with 
        the MySQL framework. e.g. "SELECT * FROM sakila.actors;"
        """
        is_write = False
        for substring in self.w_queries:
            if substring in request:
                is_write = True
                break

        return is_write

    def execute(self, ip, request):
        """
        This method is used to forward requests through the sshtunnel.
        PyMySQL is used to convert string request into actual SQL requests.
        :param ip: public ip address of the target machine.
        :param request: string containing the SQL query to be executed.
        """
        with SSHTunnelForwarder(
            ip,
            ssh_username='ubuntu',
            ssh_pkey=self.ssh_key,
            remote_bind_address=(self.ndb_mgmd_ip, 3306),
            ssh_config_file=None
        ) as _:

            # Connect to the database using dummy labuser
            connection = pymysql.connect(
                host=self.ndb_mgmd_ip,
                user='labuser',
                password='password',
                db='sakila',
                port=3306,
                autocommit=True
            )

            try:
                with connection.cursor() as cursor:
                    cursor.execute(request)

                    # Fetch the results of the query
                    # and convert them to json format
                    return jsonify(cursor.fetchall())
            finally:
                connection.close()

    def direct(self, request):
        """
        Simple direct forward of incoming requests to MySQL master node with
        logic to distribute data.
        :param request: A SQL query in the form of a string compatible with 
        the MySQL framework. e.g. "SELECT * FROM sakila.actors;"
        :return: a json body response of the SQL results
        """
        return self.execute(self.ndb_mgmd_ip, request)

    def random(self, request):
        """
        Randomly choose a slave node on MySQL cluster and forward the request 
        to it.
        :param request: A SQL query in the form of a string compatible with 
        the MySQL framework. e.g. "SELECT * FROM sakila.actors;"
        :return: a json body response of the SQL results
        """
        public_ip = self.ndb_mgmd_ip
        if not self.contains_write_operation(request):
            public_ip = random.choice(self.public_ips)

        return self.execute(public_ip, request)

    def customized(self, request):
        """
        Measure the ping time of all the servers and forward the message to one 
        with less response time.
        :param request: A SQL query in the form of a string compatible with 
        the MySQL framework. e.g. "SELECT * FROM sakila.actors;"
        :return: a json body response of the SQL results
        """
        public_ip = self.ndb_mgmd_ip
        if not self.contains_write_operation(request):
            time_to_beat = 3000  # In ms, starts equal to the timeout period
            for ip in self.public_ips:
                ping_result = ping(ip, timeout=3)
                if time_to_beat > ping_result.rtt_avg_ms and ping_result.packet_loss != 1:
                    public_ip = ip
                    time_to_beat = ping_result.rtt_avg_ms

        return self.execute(public_ip, request)


# Create the proxy instance when lunching the flaskapp
# service.
proxy = Proxy()


@app.route('/<request>')
def mysql(request):
    """
    Execute the request inserted in the url. 
    :param request: the string type request.
    :return: a json body response of the SQL results
    """
    response = '''<h1>Please select a mode by going to /direct, /random or /custom </h1>'''
    if proxy.mode == 0:
        response = proxy.direct(request)
    elif proxy.mode == 1:
        response = proxy.random(request)
    elif proxy.mode == 2:
        response = proxy.customized(request)

    return response


@app.route('/direct')
def direct():
    """
    Change the proxy to direct forwarding mode.
    """
    proxy.mode = 0
    return '''<h1>Successfully changed forwarding mode to Direct</h1>'''


@app.route('/random')
def randomhit():
    """
    Change the proxy to random forwarding mode.
    """
    proxy.mode = 1
    return '''<h1>Successfully changed forwarding mode to Random</h1>'''


@app.route('/custom')
def custom():
    """
    Change the proxy to custom forwarding mode.
    """
    proxy.mode = 2
    return '''<h1>Successfully changed forwarding mode to Custom</h1>'''


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
