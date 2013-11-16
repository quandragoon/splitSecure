#!/usr/local/bin/python

import db
import BaseHTTPServer

import random
import urlparse

NUM_AGGREGATION_SERVERS = 3
POOL_SIZE = 10

AGGREGATION_SERVERS = [
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
def get_random_aggregation_servers():
    aggregation_servers = []
    indices = []
    while (len(aggregation_servers) < NUM_AGGREGATION_SERVERS):
        index = int(random.random() * POOL_SIZE)
        if index not in indices:
            indices.append(index)
            aggregation_servers.append(AGGREGATION_SERVERS[index])
    return aggregation_servers

"""
Returns a list of aggregation servers, given a username.
Makes a lookup in the username - aggregation servers table

Returns:
    None, if the username does not exist in the table
    List of aggregation servers if the username does exist in the table 
"""
def get_aggregation_servers(username):
    mappingdb = db.user_server_mapping_setup()
    mapping = mappingdb.query(db.UsernameAggregationServerMapping).get(username)
    if mapping:
        # Obtain the compressed list of aggregation servers, split the compressed
        # list and return to the user as necessary
        pass
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
    mappingdb = db.user_server_mapping_setup()
    mapping = mappingdb.query(db.UsernameAggregationServerMapping)\
        .get(username)
    if mapping:
        return None
    newuser = db.UsernameAggregationServerMapping()
    newuser.username = username

    aggregation_servers = get_random_aggregation_servers()
    newuser.aggregation_servers = ','.join(aggregation_servers)
    mappingdb.add(newuser)
    mappingdb.commit()
    return aggregation_servers


def login(username):
    mappingdb = db.user_server_mapping_setup()
    mapping = mappingdb.query(db.UsernameAggregationServerMapping)\
        .get(username)
    if not mapping:
        return None

    aggregation_servers = mapping.aggregation_servers.split(',')
    return aggregation_servers


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
            # TODO: Add code to log the user with provided username in
            request_type = LOGIN
            registration_servers = login(username)
        elif submit_type == 'Register':
            # TODO: Add code to register the user with provided username
            request_type = REGISTER
            registration_servers = register(username)

        # TODO: Return appropriate error msg here if registration servers is None
        if not registration_servers:
            # Return error message here
            pass

        # TODO: Write code to issue read and write requests to aggregation servers
        # as required, remember to pass in request_type into the request

if __name__ == '__main__':
    try:
        httpd = BaseHTTPServer.HTTPServer(('', 8000), CustomHandler)
        httpd.serve_forever()
    except:
        httpd.socket.close()
