#!/usr/local/bin/python

import db
import BaseHTTPServer

import random
import urlparse

NUM_DATABASE_SERVERS = 3
POOL_SIZE = 5
AUTH_SERVER_PORT = 8080

DATABASE_SERVERS = [
    '8001',
    '8002',
    '8003',
    '8004',
    '8005'
]

LOGIN = 0
REGISTER = 1

FAIL = 0
PASS = 1
PENDING = 2


# map loginID to confirmation 
login_confirm = {}

# Mapping from username to db servers from which the auth server is
# awaiting a response
pending_registration_requests = {}
pending_login_requests = {}


"""
Returns a list of length NUM_AGGREGATION_SERVERS
Returned list contains IP addresses of aggregation servers picked
from AGGREGATION_SERVERS at random
"""


def get_random_database_servers_and_points():
    database_servers = []
    indices = []
    while (len(database_servers) < NUM_DATABASE_SERVERS):
        index = int(random.random() * POOL_SIZE)
        if index not in indices:
            indices.append(index)
            database_servers.append((DATABASE_SERVERS[index],
                                    random.randint(0, 10000)))
    return database_servers

"""
Returns a list of database servers, given a username.
Makes a lookup in the username - database servers table

Returns:
    None, if the username does not exist in the table
    List of aggregation servers if the username does exist in the table 
"""


def get_database_servers(username, is_registration=False):
    mappingdb = db.username_server_mapping_setup()
    mapping = mappingdb.query(
        db.UsernameServerMapping).get(username)
    if mapping:
        if is_registration:
            return None
        compressed_mapping = mapping.databases

        return compressed_mapping
    if is_registration:
        servers = get_random_database_servers_and_points()
        insert_pending_registration(username, servers)
        compressed_mapping = ['%s:%s' % (x[0], str(x[1])) for x in servers]
        compressed_mapping = ','.join(compressed_mapping)

        new_mapping = db.UsernameServerMapping()
        new_mapping.username = username
        new_mapping.databases = compressed_mapping

        mappingdb.add(new_mapping)
        mappingdb.commit()

        return compressed_mapping
    return None


"""
Registers the provided username.
First makes a lookup in the username - aggregation servers table, if the username
does not exist in the table, create a new entry in the table; otherwise no changes
are made to the DB

Returns:
    None, if the username already exists in the table
    List of aggregation servers if the username does not already exist in the table 
"""


def register(username):
    return get_database_servers(username, is_registration=True)


def insert_pending_registration(username, servers):
    pending_registration_requests[username] = []
    for x in servers:
        pending_registration_requests[username].append(x[0])


def update_pending_registration(username, serverID):
    try:
        pending_registration_requests[username].remove(serverID)
    except:
        pass
    if len(pending_registration_requests[username]) == 0:
        pending_registration_requests.pop(username)


def check_pending_registration(username):
    if username in pending_registration_requests:
        return True
    return False


def login(username):
    compressed_mapping = get_database_servers(username, is_registration=False)
    insert_pending_login(username, compressed_mapping)
    return compressed_mapping


def insert_pending_login(username, compressed_mapping):
    mapping = [[[x.split(':')[0], int(x.split(':')[1]), None]
                for x in compressed_mapping.split(',')], NUM_DATABASE_SERVERS]
    pending_login_requests[username] = mapping


def update_pending_login(username, serverID, difference):
    for i in range(0, len(pending_login_requests[username][0])):
        x = pending_login_requests[username][0][i]
        if x[0] == serverID and x[2] is None:
            pending_login_requests[username][0][i][2] = difference
            pending_login_requests[username][1] -= 1
            break


def delete_pending_login(username):
    pending_login_requests.pop(username)


def verify_password(username):
    data = pending_login_requests[username][0]
    print data
    a1 = data[0][1] ** 2
    b1 = data[0][1]
    c1 = data[0][2] * -1

    a2 = data[1][1] ** 2
    b2 = data[1][1]
    c2 = data[1][2] * -1

    a3 = data[2][1] ** 2
    b3 = data[2][1]
    c3 = data[2][2] * -1
    delete_pending_login(username)
    sol1 = solve_linear_equation(a1, b1, c1, a2, b2, c2)
    sol2 = solve_linear_equation(a3, b3, c3, a2, b2, c2)
    print sol1, '   ', sol2

    if sol1[0] == sol2[0] and sol1[1] == sol2[1]:
        return True
    return False


def solve_linear_equation(a1, b1, c1, a2, b2, c2):
    x = (b1 * c2 - b2 * c1) / (a2 * b1 - b2 * a1)
    y = (a1 * c2 - a2 * c1) / (a1 * b2 - a2 * b1)
    return (x, y)


def check_pending_login(username):
    if username in pending_login_requests:
        if pending_login_requests[username][1] > 0:
            return True
    return False


class CustomHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers() 
        f = open("login.html", "r")
        content = f.read()
        self.wfile.write(content)
        f.close()	

    def do_POST(self):
        content_len = int(self.headers.getheader('content-length'))
        post_body = self.rfile.read(content_len)
        args = urlparse.parse_qs(post_body)

        try:
            username = args.get('username', None)[0]
            submit_type = args.get('submit', None)[0]
        except Exception as e:
	    print e
            self.send_post_response("Username is incorrect")
            return

        if submit_type == 'Login':
            self.do_LOGIN(username)
        elif submit_type == 'Register':
            self.do_REGISTER(username)
        elif submit_type == 'Auth':
            loginID = args.get('loginID', None)[0]
            self.do_AUTH(username, loginID)
        elif submit_type == 'DBregister':
            try:
                serverID = args.get('serverID', None)[0]
                self.verify_registration(serverID, username)
            except:
                pass
        elif submit_type == 'DBlogin':
            try:
                serverID = args.get('serverID', None)[0]
                difference = int(args.get('difference', None)[0])
                loginID = args.get('loginID', None)[0]
                self.verify_login(serverID, username, difference, loginID)
            except:
                pass

        return

    def do_LOGIN(self, username):
        print 'Login Request: ', username
        registration_servers = None
        registration_servers = login(username)
        insert_pending_login(username, registration_servers)
        if registration_servers:
	    loginID = username + str(random.randint(0, 1000000))
            login_confirm[loginID] = PENDING
            self.send_post_response(loginID+'#'+registration_servers)
        else:
            self.send_post_response("Username is incorrect")

    def do_REGISTER(self, username):
        print 'Registration Request: ', username
        registration_servers = None
        registration_servers = register(username)
        if registration_servers:
            self.send_post_response(registration_servers)
        else:
            self.send_post_response("Username is incorrect")

    def do_AUTH(self, username, loginID):
        key = loginID
        if key in login_confirm.keys():
            if login_confirm[key] == PASS:
                self.send_post_response("L1")
                del login_confirm[key]
                #TODO: send cookie to user
            elif login_confirm[key] == PENDING:
                self.send_post_response("L2")
            else:
                self.send_post_response("L0")
                del login_confirm[key]
        else:
            self.send_post_response("Invalid loginID") 

    def verify_registration(self, serverID, username):
        print serverID, ': Registered ', username
        if check_pending_registration(username):
            update_pending_registration(username, serverID)
            if(not check_pending_registration(username)):
                print username, ': Registration Successful'
                # TODO: Notify client of successful registration

    def verify_login(self, serverID, username, difference, loginID):
        print serverID, ': Login ', username, ' - Difference = ', difference
        if check_pending_login(username):
            update_pending_login(username, serverID, difference)
            if(not check_pending_login(username)):
                print username, ': Received all responses'
                if verify_password(username):
                    print username, ': Login Successful'
                    login_confirm[loginID] = PASS
                else:
                    print username, ': Login Failed'
                    login_confirm[loginID] = FAIL

    def send_post_response(self, message):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(message)
        print 'Sent Response: ', message


if __name__ == '__main__':
    try:
        httpd = BaseHTTPServer.HTTPServer(
            ('localhost', AUTH_SERVER_PORT), CustomHandler)
        print 'Started Authentication Server'
        httpd.serve_forever()
    except:
        httpd.socket.close()
