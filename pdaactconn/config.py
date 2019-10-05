"""
Connection configurations
"""
from os import path

PRIVATE_CONFIG_LOC = path.join(path.dirname(__file__), '..', 'config',
                               'private', 'credentials.private.ini')

AACT_HOST = 'aact-db.ctti-clinicaltrials.org'
AACT_DB = 'aact'

LOCAL_HOST = 'localhost'
LOCAL_DB = 'aact'
