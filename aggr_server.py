#!/usr/local/bin/python

import db


NUM_REPLICAS = 3

def get_database_ids(server_id):
  return ['%s#%s' % (server_id, str(i)) for i in xrange(NUM_REPLICAS)]


def get_password_split(username, database_id):
  splitdb = db.password_split_setup()
  split = splitdb.query(db.PasswordSplit).get(username)
  if split:
    return split.hashed_password_split
  return None


def get_password_splits(username, database_ids):
  """
  Note that with the current implementation, all database replicas must
  agree on the same password split. This can be changed later
  """
  password_split = None
  for database_id in database_ids:
    if not password_split:
      password_split = get_password_split(username, database_id)
    else:
      if (password_split != get_password_split(username, database_id)):
        return None
  return password_split
