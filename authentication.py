#!/usr/local/bin/python


class Authentication:

    def __init__(self, NUM_DATABASE_SERVERS_AUTH):
        self.pending_login_requests = {}
        self.NUM_DATABASE_SERVERS_AUTH = NUM_DATABASE_SERVERS_AUTH

    def insert_pending_login(self, username, compressed_mapping):
        mapping = [[[x.split(':')[0], int(x.split(':')[1]), None]
                    for x in compressed_mapping.split(',')], self.NUM_DATABASE_SERVERS_AUTH]
        self.pending_login_requests[username] = mapping

    def update_pending_login(self, username, serverID, difference):
        for i in range(0, len(self.pending_login_requests[username][0])):
            x = self.pending_login_requests[username][0][i]
            if x[0] == serverID and x[2] is None:
                self.pending_login_requests[username][0][i][2] = difference
                self.pending_login_requests[username][1] -= 1
                break

    def delete_pending_login(self, username):
        self.pending_login_requests.pop(username)

    def verify_password(self, username):
        data = self.pending_login_requests[username][0]
        print data
        a1 = data[0][1] ** 2
        b1 = data[0][1]
        c1 = data[0][2] * -1

        a2 = data[1][1] ** 2
        b2 = data[1][1]
        c2 = data[1][2] * -1

        a3 = data[2][1] ** 2
        b3 = data[2][1]
        c3 = data[2][2] * -1
        self.delete_pending_login(username)
        sol1 = self.solve_linear_equation(a1, b1, c1, a2, b2, c2)
        sol2 = self.solve_linear_equation(a3, b3, c3, a2, b2, c2)
        print sol1, '   ', sol2

        if sol1[0] == sol2[0] and sol1[1] == sol2[1]:
            return True
        return False

    def solve_linear_equation(self, a1, b1, c1, a2, b2, c2):
        x = float(b1 * c2 - b2 * c1) / (a2 * b1 - b2 * a1)
        y = float(a1 * c2 - a2 * c1) / (a1 * b2 - a2 * b1)
        return (x, y)

    def check_pending_login(self, username):
        if username in self.pending_login_requests:
            if self.pending_login_requests[username][1] > 0:
                return True
        return False
