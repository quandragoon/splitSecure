SplitSecure is a distributed server-side password storage system.

This prototype is developed by Pranav Kaundinya, Deepak Narayanan, Rohan Mahajan and
Quan Nguyen. The system as configured consists of an authentication (auth) server and
8 database servers, with each user's password share on 5 database servers and 3 database
servers involved in every authentication.

In order to setup the databases, run setup.sh.
To demonstrate the prototype run demo.sh, which runs the authentication server on port 8080
and the database servers on ports 8001-8008.

IMPORTANT: Make sure you are running a private session. 
Visit https://localhost:8080 and have fun!
