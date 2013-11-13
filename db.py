from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os
import sys

Base = declarative_base()


class UsernameAggregationServerMapping(Base):
  __tablename__ = 'aggregation_server_mapping'

  username = Column(String, primary_key=True)
  aggregation_servers = Column(String)

  def __repr__(self):
    return "Username=%s, Aggregation servers=%s" \
      % (self.username, self.aggregation_servers)


class PasswordSplit(Base):
  __tablename__ = 'username_password_splits'

  username = Column(String, primary_key=true)
  hashed_password_split = Column(String)

  def __repr__(self):
    return "Username=%s, Password split=%s" \
      % (self.username, self.hashed_password_split)


def dbsetup(name, base):
  thisdir = os.path.dirname(os.path.abspath(__file__))
  dbdir   = os.path.join(thisdir, "db", name)
  if not os.path.exists(dbdir):
    os.makedirs(dbdir)

  dbfile  = os.path.join(dbdir, "%s.db" % name)
  engine  = create_engine('sqlite:///%s' % dbfile)
  Base.metadata.create_all(engine)
  session = sessionmaker(bind=engine)
  return session()


def user_server_mapping_setup():
  return dbsetup('aggregation_server_mapping', UsernameAggregationServerMapping)

def password_split_setup(database_id):
  return dbsetup('username_password_splits_%s' % database_id, PasswordSplit)


if __name__ == '__main__':
  if len(sys.argv) < 2:
    print "Usage: %s [init-server-mapping]" % sys.argv[0]
    exit(1)

  cmd = sys.argv[1]
  if cmd == 'init-server-mapping':
    user_server_mapping_setup()
  else:
    raise Exception("unknown command %s" % cmd)
