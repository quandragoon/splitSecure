#!/usr/local/bin/python


class Registration:

    def __init__(self, NUM_DATABASE_SERVERS_REG):
        self.pending_registration_requests = {}
        self.NUM_DATABASE_SERVERS_REG = NUM_DATABASE_SERVERS_REG

    def insert_pending_registration(self, username, servers):
        self.pending_registration_requests[username] = []
        for x in servers:
            self.pending_registration_requests[username].append(x[0])

    def update_pending_registration(self, username, serverID):
        try:
            self.pending_registration_requests[username].remove(serverID)
        except:
            pass
        if len(self.pending_registration_requests[username]) == 0:
            self.pending_registration_requests.pop(username)

    def check_pending_registration(self, username):
        if username in self.pending_registration_requests:
            return True
        return False
