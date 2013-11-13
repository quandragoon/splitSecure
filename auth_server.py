#!/usr/local/bin/python

import db

import random

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
def register_username(username):
  mappingdb = db.user_server_mapping_setup()
  mapping = mappingdb.query(db.UsernameAggregationServerMapping).get(username)
  if mapping:
    return None
  newuser = db.UsernameAggregationServerMapping()
  newuser.username = username

  aggregation_servers = get_random_aggregation_servers()
  newuser.aggregation_servers = ','.join(aggregation_servers)
  mappingdb.add(newuser)
  mappingdb.commit()
  return aggregation_servers
