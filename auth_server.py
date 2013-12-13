#!/usr/local/bin/python

import db
import BaseHTTPServer
import SimpleHTTPServer

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_PSS
from Crypto.Random import random as crypt_random
from Crypto.Hash import SHA

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

DATABASE_PRIORITIES = []

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

public_key = None
private_key = None


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
                                    int(crypt_random.randint(0, 10000))))
    return database_servers


def get_random_database_servers_and_points_auth(mapping):
    if not mapping:
        return None
    uncompressed_mapping = mapping.split(',')
    auth_database_servers = []
    indices = []
    priorities = []
    sum_priorities = 0
    for x in uncompressed_mapping:
        (database_server, _) = x.split(':')
        index = DATABASE_SERVERS.index(database_server)
        priorities.append(DATABASE_PRIORITIES[index])
        sum_priorities += priorities[-1]
    priorities = [priority / sum_priorities for priority in priorities]

    while (len(auth_database_servers) < NUM_DATABASE_SERVERS_AUTH):
        random_server = random.random()
        index = -1
        while (random_server > 0):
            random_server -= priorities[index]
            index += 1
        if index not in indices:
            indices.append(index)
            auth_database_servers.append(uncompressed_mapping[index])
    recompressed_mapping = ','.join(auth_database_servers)
    return recompressed_mapping


def init_priorities():
    n = len(DATABASE_SERVERS)
    print "Initializing priorities..."
    for i in xrange(n):
        DATABASE_PRIORITIES.append(1.0)


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

    AES.set_key(key)


def generate_private_public_key_pair():
    global private_key, public_key
    private_key = RSA.generate(1024)
    public_key = private_key.publickey()
    print "Generated RSA key pair..."


def get_signature(username):
    global private_key
    msg = SHA.new()
    msg.update(username)
    signer = PKCS1_PSS.new(private_key)
    signature = signer.sign(msg)
    return urllib.quote(signature)


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
        return compressed_mapping
    elif (mapping and not is_registration):
        compressed_mapping = mapping.databases
        auth_servers_and_points = get_random_database_servers_and_points_auth(
            compressed_mapping)
        return auth_servers_and_points

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
    return str(compressed_mapping)


class CustomHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        cookies = self.headers.getheader('Cookie')
        distrib_pass_token_cookie = None
        distrib_pass_username = None
        try:
            cookie_index = cookies.index('DistribPasswordToken')
            next_semicolon = cookies.find(';', cookie_index)
            if next_semicolon == -1:
                distrib_pass_token_cookie = cookies[cookie_index + 21:]
            else:
                distrib_pass_token_cookie = cookies[
                    cookie_index + 21: next_semicolon]
            cookie_index = cookies.index('DistribPassword')
            next_semicolon = cookies.find(';', cookie_index)
            if next_semicolon == -1:
                distrib_pass_username = cookies[cookie_index + 16:]
            else:
                distrib_pass_username = cookies[
                    cookie_index + 16: next_semicolon]
            distrib_pass_token_cookie = urllib.unquote(urllib.unquote(distrib_pass_token_cookie))
        except:
            pass

        if distrib_pass_username:
            msg = SHA.new()
            msg.update(distrib_pass_username)
            verifier = PKCS1_PSS.new(public_key)

            if (not verifier.verify(msg, distrib_pass_token_cookie)):
                distrib_pass_token_cookie = None

        # Add code here that checks validity of the token
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        if self.path == '/page_style.css':
            f = open("static/page_style.css", 'r')
        elif self.path == '/welcome.html':
            if distrib_pass_token_cookie is None:
                f = open("static/login.html", 'r')
            else:
                f = open("static/welcome.html", 'r')
        else:
            f = open("static/login.html", 'r')
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
        elif submit_type == 'CheckReg':
            username = args.get('username', None)[0]
            self.do_CHECKREG(username)
        elif submit_type == 'PublicKey':
            global public_key
            public_key_str = public_key.exportKey()
            self.send_post_response(public_key_str)
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
        registration_servers = None
        registration_servers = login(username)
        if not registration_servers:
            return
        AUTHENTICATION.insert_pending_login(username, registration_servers)
        for x in registration_servers.split(','):
            (database_server, _) = x.split(':')
            index = DATABASE_SERVERS.index(database_server)
            DATABASE_PRIORITIES[index] = 1.0 / \
                ((1.0 / DATABASE_PRIORITIES[index]) + 1.0)

        if registration_servers:
            loginID = username + str(crypt_random.randint(0, 1000000))
            login_confirm[loginID] = PENDING
            signature = get_signature(username)
            # TODO: Change the way signature is sent as appropriate
            self.send_post_response(
                loginID + '#' + registration_servers + '#' + signature)
        else:
            self.send_post_response("Username is incorrect")

    def do_REGISTER(self, username):
        registration_servers = None
        registration_servers = register(username)
        if registration_servers:
            signature = get_signature(username)
            self.send_post_response(registration_servers + '#' + signature)
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

    def do_CHECKREG(self, username):
        if(not REGISTRATION.check_pending_registration(username)):
            self.send_post_response("R1")
        else:
            self.send_post_response("R2")

    def verify_registration(self, serverID, username):
        if REGISTRATION.check_pending_registration(username):
            REGISTRATION.update_pending_registration(username, serverID)
            if(not REGISTRATION.check_pending_registration(username)):
                print username, ': Registration Successful'
                pass

    def verify_login(self, serverID, username, difference, loginID):
        if AUTHENTICATION.check_pending_login(username):
            AUTHENTICATION.update_pending_login(username, serverID, difference)
            index = DATABASE_SERVERS.index(serverID)
            DATABASE_PRIORITIES[index] = 1.0 / \
                ((1.0 / DATABASE_PRIORITIES[index]) - 1.0)
            if(not AUTHENTICATION.check_pending_login(username)):
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


if __name__ == '__main__':
    try:
        renew_key()
        init_priorities()
        generate_private_public_key_pair()
        httpd = BaseHTTPServer.HTTPServer(
            ('localhost', AUTH_SERVER_PORT), CustomHandler)
        httpd.socket = ssl.wrap_socket(
            httpd.socket, keyfile='server.pem', certfile='server.pem',
            server_side=True)
        print 'Started Authentication Server'
        httpd.serve_forever()
    except Exception as e:
        print e
        httpd.socket.close()
