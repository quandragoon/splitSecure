from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os
import sys

Base = declarative_base()


class UsernameServerMapping(Base):
    __tablename__ = 'username_server_mapping'

    username = Column(String, primary_key=True)
    databases = Column(String)

    def __repr__(self):
        return "Username=%s, Databases=%s" \
            % (self.username, self.databases)


class UsernamePolynomialValueMapping(Base):
    __tablename__ = 'username_polynomial_mapping'

    username = Column(String, primary_key=True)
    polynomial_value = Column(String)

    def __repr__(self):
        return "Username=%s, Polynomial value=%s" \
            % (self.username, self.polynomial_value)


def dbsetup(name):
    thisdir = os.path.dirname(os.path.abspath(__file__))
    dbdir = os.path.join(thisdir, "db", name)
    if not os.path.exists(dbdir):
        os.makedirs(dbdir)

    dbfile = os.path.join(dbdir, "%s.db" % name)
    engine = create_engine('sqlite:///%s' % dbfile)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    return session()


def username_server_mapping_setup():
    return dbsetup('username_server_mapping')


def polynomial_mapping_setup(database_id):
    return dbsetup('username_polynomial_mapping_%s' % database_id)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: %s [init-server-mapping]|[init-db]" % sys.argv[0]
        exit(1)

    cmd = sys.argv[1]
    if cmd == 'init-server-mapping':
        username_server_mapping_setup()
    elif cmd == 'init-db':
        database_id = sys.argv[2]
        polynomial_mapping_setup(database_id)
    else:
        raise Exception("unknown command %s" % cmd)
