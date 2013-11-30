#!/usr/local/bin/python

import db
import sys
import BaseHTTPServer

import random
import urlparse
import urllib
import httplib

AUTH_SERVER_HOST = 'localhost'
AUTH_SERVER_PORT = '8080'
SERVER_ID = 8001       #This is set during server initialization


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

class CustomHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        pass

    def do_POST(self):
        content_len = int(self.headers.getheader('content-length'))
        post_body = self.rfile.read(content_len)
        args = urlparse.parse_qs(post_body)

        try:
            username = args.get('username', None)[0]
            submit_type = args.get('submit', None)[0]
            value = int(args.get('value', None)[0])
        except:
            self.send_post_response("Username or Password is incorrect")
            return

        registration_servers = None

        if submit_type == 'Login':  
            difference = handle_login(username, value, SERVER_ID)
            print 'Login ', username, ': Value = ', value, ', Difference = ', difference
            if difference:
                self.send_difference(username, difference)

        elif submit_type == 'Register':
            print 'Registered ', username, ' Value = ', value            
            if handle_registration(username, value, SERVER_ID):
                self.notify_registration(username)
        return

    def notify_registration(self, username):
        params = urllib.urlencode({
            'submit' : 'DBregister',
            'serverID' : SERVER_ID,
            'username' : username,
            })
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}
        conn = httplib.HTTPConnection(AUTH_SERVER_HOST + ':' + AUTH_SERVER_PORT)
        conn.request("POST", "/auth-server",
                     params, headers)

    def send_difference(self, username, difference):
        
        params = urllib.urlencode({
            'submit' : 'DBlogin',
            'serverID' : SERVER_ID,
            'username' : username,
            'difference' : difference,
            })
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}
        conn = httplib.HTTPConnection(AUTH_SERVER_HOST + ':' + AUTH_SERVER_PORT)
        conn.request("POST", "/auth-server",
                     params, headers)



if __name__ == '__main__':
    SERVER_ID = int(sys.argv[1])
    try:
        httpd = BaseHTTPServer.HTTPServer(('localhost', SERVER_ID), CustomHandler)
        print 'Started Database Server ', SERVER_ID
        httpd.serve_forever()
    except:
        httpd.socket.close()


