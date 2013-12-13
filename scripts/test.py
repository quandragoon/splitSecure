import httplib
import urllib
import random
import string
import time


def randomword(length):
    return ''.join(random.choice(string.lowercase) for i in range(length))


params = urllib.urlencode({
    'submit': 'PublicKey',
})
headers = {"Content-type": "application/x-www-form-urlencoded",
           "Accept": "text/plain"}
conn = httplib.HTTPSConnection("localhost:8080")
conn.request("POST", "/auth-server",
             params, headers)
print "Sent public key request to authentication server"
response = conn.getresponse()
data = response.read()
conn.close()

# Contact Auth server###########
username = randomword(6)
params = urllib.urlencode({
    'username': username,
    'submit': 'Register',
})
headers = {"Content-type": "application/x-www-form-urlencoded",
           "Accept": "text/plain"}
conn = httplib.HTTPSConnection("localhost:8080")
conn.request("POST", "/auth-server",
             params, headers)
print "Sent registration request to authentication sever"
response = conn.getresponse()
data = response.read()
conn.close()

split_data = data.split('#', 1)
servers = split_data[0]
signature = split_data[1]

# parse server addresses############
ports = [x.split(':')[0] for x in servers.split(',')]
points = [int(x.split(':')[1]) for x in servers.split(',')]
A = random.randint(1, 10000)
B = random.randint(1, 10000)
C = 123
values = []
for p in points:
    values.append((A * (p ** 2)) + (B * p) + C)

# Send evaluated values to DB server####
for i in range(0, 5):
    params = urllib.urlencode({
        'username': username,
        'value': values[i],
        'submit': 'Register',
        'signature': signature,
    })
    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"}

    conn = httplib.HTTPSConnection("localhost:" + ports[i])
    conn.request("POST", "/",
                 params, headers)
    print 'Sent value ', values[i], ' to database server ', ports[i]
    conn.close()

#
#
# Assume successful registration and login##########

time.sleep(2)

#
#
# Contact Auth server###########

params = urllib.urlencode({
    'username': username,
    'submit': 'Login',
})
headers = {"Content-type": "application/x-www-form-urlencoded",
           "Accept": "text/plain"}
conn = httplib.HTTPSConnection("localhost:8080")
conn.request("POST", "/auth-server",
             params, headers)
print "Sent login request to authentication sever"
response = conn.getresponse()
data = response.read()
conn.close()

# parse server addresses############
data_split = data.split('#', 2)
loginID = data_split[0]
servers = data_split[1]
signature = data_split[2]

ports = [x.split(':')[0] for x in servers.split(',')]
points = [int(x.split(':')[1]) for x in servers.split(',')]
a = random.randint(1, 10000)
b = random.randint(1, 10000)
c = 123
values = []
for p in points:
    values.append((a * (p ** 2)) + (b * p) + c)

#


# Send evaluated values to DB server####
for i in range(0, 3):
    params = urllib.urlencode({
        'username': username,
        'value': values[i],
        'loginID': loginID,
        'submit': 'Login',
        'signature': signature,
    })
    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain"}

    conn = httplib.HTTPSConnection("localhost:" + ports[i])
    conn.request("POST", "/",
                 params, headers)
    print 'Sent value ', values[i], ' to database server ', ports[i]
    conn.close()

#
