#!/usr/local/bin/python

import db
import BaseHTTPServer

import random
import urlparse

NUM_DATABASE_SERVERS = 3
POOL_SIZE = 10

DATABASE_SERVERS = [
    'ip1',
    'ip2',
    'ip3',
    'ip4',
    'ip5',
    'ip6',
    'ip7',
    'ip8',
    'ip9',
    'ip10',
]

LOGIN = 0
REGISTER = 1

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
Returns a list of aggregation servers, given a username.
Makes a lookup in the username - aggregation servers table

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


def login(username):
    return get_database_servers(username, is_registration=False)


class CustomHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        # Do nothing
        # TODO: Change this behavior
        pass

    def do_POST(self):
        content_len = int(self.headers.getheader('content-length'))
        post_body = self.rfile.read(content_len)
        args = urlparse.parse_qs(post_body)

        username = args.get('username', None)[0]
        password = args.get('password', None)[0]
        submit_type = args.get('submit', None)[0]
        # TODO: Check if username, password or submit_type is None
        # TODO: Insert assert to make sure returned lists have length 1

        registration_servers = None
        request_type = None
        if submit_type == 'Login':
            # TODO: Add code to return registration_servers in the form of HTTP response
            request_type = LOGIN
            registration_servers = login(username)
        elif submit_type == 'Register':
            # TODO: Add code to return registration_servers in the form of HTTP response
            request_type = REGISTER
            registration_servers = register(username)

        # TODO: Return appropriate error msg here if registration servers is
        # None
        if not registration_servers:
            # Return error message here
            pass


if __name__ == '__main__':
    try:
        httpd = BaseHTTPServer.HTTPServer(('', 8000), CustomHandler)
        httpd.serve_forever()
    except:
        httpd.socket.close()
