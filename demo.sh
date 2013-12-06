#!/bin/sh
#launch the authserver
python auth_server.py &
#launch the various database servers
python database_server.py 8001 &
python database_server.py 8002 &
python database_server.py 8003 &
python database_server.py 8004 &
python database_server.py 8005 &



