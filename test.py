import httplib, urllib
import random, string
import time

def randomword(length):
   return ''.join(random.choice(string.lowercase) for i in range(length))

###########Contact Auth server###########
username = randomword(6)
params = urllib.urlencode({
    'username' : username,
    'submit' : 'Register',
    })
headers = {"Content-type": "application/x-www-form-urlencoded",
           "Accept": "text/plain"}
conn = httplib.HTTPConnection("localhost:8080")
conn.request("POST", "/auth-server",
             params, headers)
print "Sent registration request to authentication sever"
response = conn.getresponse()
data = response.read()
print data
conn.close()

##########parse server addresses############
ports = [x.split(':')[0] for x in data.split(',')]
points = [int(x.split(':')[1]) for x in data.split(',')]
A = random.randint(1, 10000)
B = random.randint(1, 10000)
C = 12345
values = []
for p in points:
	values.append((A*(p**2))+(B*p)+C)

#####Send evaluated values to DB server####
for i in range(0,3):
	params = urllib.urlencode({
	    'username' : username,
	    'value' : values[i],
	    'submit' : 'Register',
	    })
	headers = {"Content-type": "application/x-www-form-urlencoded",
	           "Accept": "text/plain"}
	
	conn = httplib.HTTPConnection("localhost:" + ports[i])
	conn.request("POST", "/",
	             params, headers)
	print 'Sent value ', values[i], ' to database server ', ports[i]
	conn.close()

#########################################################
#########################################################
#######Assume successful registration and login##########

time.sleep(2)

#########################################################
#########################################################
###########Contact Auth server###########

params = urllib.urlencode({
    'username' : username,
    'submit' : 'Login',
    })
headers = {"Content-type": "application/x-www-form-urlencoded",
           "Accept": "text/plain"}
conn = httplib.HTTPConnection("localhost:8080")
conn.request("POST", "/auth-server",
             params, headers)
print "Sent login request to authentication sever"
response = conn.getresponse()
data = response.read()
conn.close()

##########parse server addresses############
ports = [x.split(':')[0] for x in data.split(',')]
points = [int(x.split(':')[1]) for x in data.split(',')]
a = random.randint(1, 10000)
b = random.randint(1, 10000)
c = 12345
values = []
for p in points:
	values.append((a*(p**2))+(b*p)+c)

############################################


#####Send evaluated values to DB server####
for i in range(0,3):
	params = urllib.urlencode({
	    'username' : username,
	    'value' : values[i],
	    'submit' : 'Login',
	    })
	headers = {"Content-type": "application/x-www-form-urlencoded",
	           "Accept": "text/plain"}
	
	conn = httplib.HTTPConnection("localhost:" + ports[i])
	conn.request("POST", "/",
	             params, headers)
	print 'Sent value ', values[i], ' to database server ', ports[i]
	conn.close()

#########################################################


