#!/usr/local/bin/python

import db
import sys
import BaseHTTPServer, SimpleHTTPServer

import urlparse
import urllib
import httplib
import encryption
import ssl

AUTH_SERVER_HOST = 'localhost'
AUTH_SERVER_PORT = '8080'
SERVER_ID = 8001  # This is set during server initialization

AES = encryption.AESCipher()


def get_polynomial_value(username, server_id):
    polynomialdb = db.polynomial_mapping_setup(server_id)
    mapping = polynomialdb.query(
        db.UsernamePolynomialValueMapping).get(username)
    if mapping:
        return mapping.polynomial_value
    return None


def set_polynomial_value(username, polynomial_value, server_id):
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


class CustomHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        pass

    def do_POST(self):
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
        except:
            return

        if submit_type == 'Login':
            difference = handle_login(username, value, SERVER_ID)
            print 'Login ', username, ': Value = ', value, ', Difference = ', difference
            loginID = args.get('loginID', None)[0]
            if difference:
                self.send_difference(username, difference, loginID)

        elif submit_type == 'Register':
            print 'Registered ', username, ' Value = ', value
            if handle_registration(username, value, SERVER_ID):
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
        httpd = BaseHTTPServer.HTTPServer(
            ('localhost', SERVER_ID), CustomHandler)
        httpd.socket = ssl.wrap_socket (httpd.socket, keyfile='server.pem', certfile='server.pem', server_side=True)
        print 'Started Database Server ', SERVER_ID
        httpd.serve_forever()
    except:
        httpd.socket.close()
