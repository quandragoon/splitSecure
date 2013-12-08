#!/usr/local/bin/python

import db
import BaseHTTPServer, SimpleHTTPServer

import random
import urlparse
import encryption
import threading
import urllib
import httplib
import registration
import authentication
import ssl

AES = encryption.AESCipher()
KEY_LIFE = 60

NUM_DATABASE_SERVERS_AUTH = 3
NUM_DATABASE_SERVERS_REG = 5
AUTH_SERVER_PORT = 8080

DATABASE_SERVERS = [
    '8001',
    '8002',
    '8003',
    '8004',
    '8005',
    '8006',
    '8007',
    '8008',
]

LOGIN = 0
REGISTER = 1

FAIL = 0
PASS = 1
PENDING = 2


# map loginID to confirmation
login_confirm = {}

REGISTRATION = registration.Registration(NUM_DATABASE_SERVERS_REG)
AUTHENTICATION = authentication.Authentication(NUM_DATABASE_SERVERS_AUTH)

httpd = None


"""
Returns a list of length NUM_DATABASE_SERVERS_REG
Returned list contains IP addresses of database servers picked
from DATABASE_SERVERS at random
"""


def get_random_database_servers_and_points_registration():
    database_servers = []
    indices = []
    while (len(database_servers) < NUM_DATABASE_SERVERS_REG):
        index = int(random.random() * len(DATABASE_SERVERS))
        if index not in indices:
            indices.append(index)
            database_servers.append((DATABASE_SERVERS[index],
                                    random.randint(0, 10000)))
    return database_servers


def get_random_database_servers_and_points_auth(mapping):
    if not mapping:
        return None
    uncompressed_mapping = mapping.split(',')
    auth_database_servers = []
    indices = []
    while (len(auth_database_servers) < NUM_DATABASE_SERVERS_AUTH):
        index = int(random.random() * len(uncompressed_mapping))
        if index not in indices:
            indices.append(index)
            auth_database_servers.append(uncompressed_mapping[index])
    recompressed_mapping = ','.join(auth_database_servers)
    return recompressed_mapping

"""
Returns a list of database servers, given a username.
Makes a lookup in the username - database servers table
Behavior varies according to whether is_registration is True or not
"""


def get_database_servers(username, is_registration=False):
    mappingdb = db.username_server_mapping_setup()
    mapping = mappingdb.query(
        db.UsernameServerMapping).get(username)

    if (is_registration and not mapping):
        servers = get_random_database_servers_and_points_registration()
        REGISTRATION.insert_pending_registration(username, servers)
        compressed_mapping = ['%s:%s' % (x[0], str(x[1])) for x in servers]
        compressed_mapping = ','.join(compressed_mapping)

        new_mapping = db.UsernameServerMapping()
        new_mapping.username = username
        new_mapping.databases = compressed_mapping

        mappingdb.add(new_mapping)
        mappingdb.commit()
        print compressed_mapping
        return compressed_mapping
    elif (mapping and not is_registration):
        compressed_mapping = mapping.databases
        print get_random_database_servers_and_points_auth(compressed_mapping)
        return get_random_database_servers_and_points_auth(compressed_mapping)

    return None


"""
Registers the provided username.
First makes a lookup in the username - database servers table, if the username
does not exist in the table, create a new entry in the table; otherwise no changes
are made to the DB

Returns:
    None, if the username already exists in the table
    List of database servers if the username does not already exist in the table 
"""


def register(username):
    return get_database_servers(username, is_registration=True)



def login(username):
    compressed_mapping = get_database_servers(username, is_registration=False)
    if not compressed_mapping:
        return None
    AUTHENTICATION.insert_pending_login(username, compressed_mapping)
    return compressed_mapping


def insert_pending_login(username, compressed_mapping):
    mapping = [[[x.split(':')[0], int(x.split(':')[1]), None]
                for x in compressed_mapping.split(',')], NUM_DATABASE_SERVERS_AUTH]
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
    x = float(b1 * c2 - b2 * c1) / (a2 * b1 - b2 * a1)
    y = float(a1 * c2 - a2 * c1) / (a1 * b2 - a2 * b1)
    return (x, y)


def check_pending_login(username):
    if username in pending_login_requests:
        if pending_login_requests[username][1] > 0:
            return True
    return False


class CustomHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

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

        submit_type = args.get('submit', None)[0]

        if submit_type == 'Login':
            username = args.get('username', None)[0]
            self.do_LOGIN(username)
        elif submit_type == 'Register':
            username = args.get('username', None)[0]
            self.do_REGISTER(username)
        elif submit_type == 'Auth':
            username = args.get('username', None)[0]
            loginID = args.get('loginID', None)[0]
            self.do_AUTH(username, loginID)
        elif submit_type == 'DBregister':
            try:
                username = AES.decrypt(args.get('username', None)[0])
                serverID = AES.decrypt(args.get('serverID', None)[0])
                self.verify_registration(serverID, username)
            except:
                pass
        elif submit_type == 'DBlogin':
            try:
                username = AES.decrypt(args.get('username', None)[0])
                serverID = AES.decrypt(args.get('serverID', None)[0])
                difference = int(AES.decrypt(args.get('difference', None)[0]))
                loginID = AES.decrypt(args.get('loginID', None)[0])
                self.verify_login(serverID, username, difference, loginID)
            except:
                pass

        return

    def do_LOGIN(self, username):
        print 'Login Request: ', username
        registration_servers = None
        registration_servers = login(username)
        if not registration_servers:
            return
        AUTHENTICATION.insert_pending_login(username, registration_servers)
        if registration_servers:
            loginID = username + str(random.randint(0, 1000000))
            login_confirm[loginID] = PENDING
            self.send_post_response(loginID + '#' + registration_servers)
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
                # TODO: send cookie to user
            elif login_confirm[key] == PENDING:
                self.send_post_response("L2")
            else:
                self.send_post_response("L0")
                del login_confirm[key]
        else:
            self.send_post_response("Invalid loginID")

    def verify_registration(self, serverID, username):
        print serverID, ': Registered ', username
        if REGISTRATION.check_pending_registration(username):
            REGISTRATION.update_pending_registration(username, serverID)
            if(not REGISTRATION.check_pending_registration(username)):
                print username, ': Registration Successful'
                # TODO: Notify client of successful registration

    def verify_login(self, serverID, username, difference, loginID):
        print serverID, ': Login ', username, ' - Difference = ', difference
        if AUTHENTICATION.check_pending_login(username):
            AUTHENTICATION.update_pending_login(username, serverID, difference)
            if(not AUTHENTICATION.check_pending_login(username)):
                print username, ': Received all responses'
                if AUTHENTICATION.verify_password(username):
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


def renew_key():
    threading.Timer(KEY_LIFE, renew_key).start()
    if httpd is None:
        return

    key = AES.new_key()
    params = urllib.urlencode({
        'key': AES.encrypt(str(key)),
    })
    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"}
    try:
        for x in DATABASE_SERVERS:
            conn = httplib.HTTPSConnection('localhost:' + x)
            conn.request("POST", "/auth-server",
                         params, headers)
    except Exception as e:
        print "Error Distributing Key: ", e
        return

    print "Distributed Key: ", key
    AES.set_key(key)


if __name__ == '__main__':
    try:
        renew_key()
        httpd = BaseHTTPServer.HTTPServer(
            ('localhost', AUTH_SERVER_PORT), CustomHandler)
        httpd.socket = ssl.wrap_socket (httpd.socket, keyfile='server.pem', certfile='server.pem', server_side=True)
        print 'Started Authentication Server'
        httpd.serve_forever()
    except:
        httpd.socket.close()
