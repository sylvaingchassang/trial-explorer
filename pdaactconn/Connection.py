"""
Connection manager, used to send queries either to aact's hosted postgres db or the localhost

Only supports SELECT queries, returns pandas dataframes
"""
import sys
import pandas as pd
import psycopg2
import configparser
from pdaactconn import config


class AACTConnection:
    REMOTE = 'remote'
    LOCAL = 'local'
    VALID_SOURCES = [REMOTE, LOCAL]

    def __init__(self, source=REMOTE):
        self._init_config()
        self.source = source

    def set_source(self, source):
        """
        set the source of the current object to either remote or local
        :param source: string, either 'remote' or 'local'
        :return: None
        """
        if source in self.VALID_SOURCES:
            self.source = source
        else:
            print("Cannot set source to %s, only valid sources are %s" % (source, str(self.VALID_SOURCES)),
                  file=sys.stderr)

    def query(self, sql, index_col=None, parse_dates=None):
        """
        queries the current connection's set database
        :param sql: string query
        :param index_col: passed to the pd.read_sql function
        :param parse_dates: passed to the pd.read_sql function
        :return: dataframe with results
        """
        if self.source == self.REMOTE:
            conn = self.connect_to_remote()
        elif self.source == self.LOCAL:
            conn = self.connect_to_local()
        else:
            print("Data source set incorrectly to %s, only valid sources are %s. Try running .set_source()"
                  % (self.source,
                     str(self.VALID_SOURCES)))
            return False  # returns False to indicate failed execution

        df = pd.read_sql(sql, conn, index_col=index_col, parse_dates=parse_dates)
        conn.close()
        return df

    def connect_to_remote(self):
        """ connect to the preset remote connection string """
        try:
            return psycopg2.connect(host=config.AACT_HOST,
                                    database=config.AACT_DB,
                                    user=self.config['Remote']['User'],
                                    password=self.config['Remote']['Password'])
        except ConnectionError:
            print("Unable to connect to remote server: %s, db: %s. "
                  "Try signing up for a login at "
                  "https://aact.ctti-clinicaltrials.org/users/sign_up" % (config.AACT_HOST,
                                                                          config.AACT_DB),
                  file=sys.stderr)

    def connect_to_local(self):
        """ connect to the preset local connection string """
        try:
            return psycopg2.connect(host=config.LOCAL_HOST,
                                    database=config.LOCAL_DB,
                                    user=self.config['Local']['User'],
                                    password=self.config['Local']['Password'])
        except ConnectionError:
            print("Unable to connect to local server %s, db: %s "
                  "Please ensure that you have a local instance of postgres running " % (config.LOCAL_HOST,
                                                                                         config.LOCAL_DB),
                  file=sys.stderr)

    def _init_config(self):
        """ reads the private ini file located as specified by the config """
        try:
            cur_config = configparser.ConfigParser()
            cur_config.read(config.PRIVATE_CONFIG_LOC)
            self.config = cur_config
        except FileNotFoundError:
            print("Could not load private credentials from %s" % config.PRIVATE_CONFIG_LOC)
