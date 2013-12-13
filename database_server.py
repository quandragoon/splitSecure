#!/usr/local/bin/python

import db
import sys
import BaseHTTPServer
import SimpleHTTPServer

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_PSS
from Crypto.Hash import SHA
import urlparse
import urllib
import httplib
import encryption
import ssl

AUTH_SERVER_HOST = 'localhost'
AUTH_SERVER_PORT = '8080'
SERVER_ID = 8001  # This is set during server initialization

AES = encryption.AESCipher()

public_key = None


def get_polynomial_value(username, server_id):
    print username, server_id

    polynomialdb = db.polynomial_mapping_setup(server_id)
    mapping = polynomialdb.query(
        db.UsernamePolynomialValueMapping).get(username)
    if mapping:
        return mapping.polynomial_value
    return None


def set_polynomial_value(username, polynomial_value, server_id):
    print username, polynomial_value, server_id
    polynomialdb = db.polynomial_mapping_setup(server_id)
    mapping = polynomialdb.query(
        db.UsernamePolynomialValueMapping).get(username)
    if mapping is None:
        new_mapping = db.UsernamePolynomialValueMapping()
        new_mapping.username = username
        new_mapping.polynomial_value = polynomial_value
        polynomialdb.add(new_mapping)
        polynomialdb.commit()
        return True
    return False


def handle_registration(username, polynomial_value, server_id):
    result = set_polynomial_value(username, polynomial_value, server_id)
    if result:
        return True
    return False


def handle_login(username, entered_polynomial_value, server_id):
    stored_polynomial_value = int(get_polynomial_value(username, server_id))
    print stored_polynomial_value
    if stored_polynomial_value:
        difference = stored_polynomial_value - entered_polynomial_value
        return difference
    return None


def get_public_key_from_auth_server():
    params = urllib.urlencode({
        'submit': 'PublicKey',
    })
    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"}
    success = False
    while not success:
        try:
            conn = httplib.HTTPSConnection("localhost:8080")
            conn.request("POST", "/auth-server",
                         params, headers)
            print "Sending public key request to authentication server..."
            response = conn.getresponse()
            data = response.read()
            global public_key
            public_key = RSA.importKey(data)
            conn.close()
            success = True
        except:
            pass


class CustomHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        pass

    def do_POST(self):
        global public_key
        content_len = int(self.headers.getheader('content-length'))
        post_body = self.rfile.read(content_len)
        args = urlparse.parse_qs(post_body)

        try:
            key = AES.decrypt(args.get('key', None)[0])
            AES.set_key(key)
            print "Renewed Key: ", key
            return
        except:
            pass

        try:
            username = args.get('username', None)[0]
            submit_type = args.get('submit', None)[0]
            value = int(args.get('value', None)[0])
            signature = args.get('signature', None)[0]
        except:
            return

        msg = SHA.new()
        msg.update(username)
        print public_key
        verifier = PKCS1_PSS.new(public_key)

        if submit_type == 'Login':
            difference = handle_login(username, value, SERVER_ID)
            print 'Login ', username, ': Value = ', value, ', \
                Difference = ', difference
            loginID = args.get('loginID', None)[0]
            if (not verifier.verify(msg, signature)):
                return

            if difference:
                self.send_difference(username, difference, loginID)

        elif submit_type == 'Register':
            if (not verifier.verify(msg, signature)):
                print msg, signature
                print "NOT REGISTERED"
                return
            if handle_registration(username, value, SERVER_ID):
                print 'Registered ', username, ' Value = ', value
                self.notify_registration(username)
        return

    def notify_registration(self, username):
        params = urllib.urlencode({
            'submit': 'DBregister',
            'serverID': AES.encrypt(str(SERVER_ID)),
            'username': AES.encrypt(username),
        })
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}
        conn = httplib.HTTPSConnection(
            AUTH_SERVER_HOST + ':' + AUTH_SERVER_PORT)
        conn.request("POST", "/auth-server",
                     params, headers)

    def send_difference(self, username, difference, loginID):

        params = urllib.urlencode({
            'submit': 'DBlogin',
            'serverID': AES.encrypt(str(SERVER_ID)),
            'username': AES.encrypt(username),
            'difference': AES.encrypt(str(difference)),
            'loginID': AES.encrypt(loginID)
        })
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}
        conn = httplib.HTTPSConnection(
            AUTH_SERVER_HOST + ':' + AUTH_SERVER_PORT)
        conn.request("POST", "/auth-server",
                     params, headers)

    def send_post_response(self, message):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(message)
        print 'Sent Response: ', message

if __name__ == '__main__':
    SERVER_ID = int(sys.argv[1])
    try:
        get_public_key_from_auth_server()
        httpd = BaseHTTPServer.HTTPServer(
            ('localhost', SERVER_ID), CustomHandler)
        httpd.socket = ssl.wrap_socket(
            httpd.socket, keyfile='server.pem', certfile='server.pem',
            server_side=True)
        print 'Started Database Server ', SERVER_ID
        httpd.serve_forever()
    except Exception as e:
        print e
        httpd.socket.close()
