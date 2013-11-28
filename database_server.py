#!/usr/local/bin/python

import db


def get_polynomial_value(username, server_id):
    polynomialdb = db.polynomial_mapping_setup(server_id)
    mapping = polynomialdb.query(
        db.UsernamePolynomialValueMapping).get(username)
    if mapping:
        return mapping.polynomial_value
    return None


def set_polynomial_value(username, polynomial_value, server_id):
    polynomialdb = db.polynomial_mapping_setup(server_id)
    mapping = polynomialdb.query(
        db.UsernamePolynomialValueMapping).get(username)
    if mapping is None:
        new_mapping = db.UsernamePolynomialValueMapping()
        new_mapping.username = username
        new_mapping.polynomial_value = polynomial_value
        return True
    return False

def handle_registration(username, polynomial_value, server_id):
    result = set_polynomial_value(username, polynomial_value, server_id)
    if result:
        # TODO: Return success message back to the auth server
        pass
    else:
        # TODO: Return error message back to the auth server
        pass

def handle_login(username, entered_polynomial_value, server_id):
    stored_polynomial_value = get_polynomial_value(username, server_id)
    if stored_polynomial_value:
        difference = stored_polynomial_value - entered_polynomial_value
        # TODO: Send difference back to the auth server
    # TODO: Return error message back to the auth server


# TODO: Build a HTTP server here that accepts requests from the client, and
# returns appropriate responses to the auth server
