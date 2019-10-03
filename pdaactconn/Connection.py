"""
Connection manager, used to send queries either to aact's hosted postgres db or the localhost

query only supports SELECT queries, returns pandas dataframes
exec supports other queries, autocommits
"""
import sys
import os
import pandas as pd
import psycopg2
import configparser
from pdaactconn import config


class AACTConnection:
    REMOTE = 'remote'
    LOCAL = 'local'
    VALID_SOURCES = [REMOTE, LOCAL]

    def __init__(self, ini_path_ovrd=None, source=REMOTE):
        self.ini_path = ini_path_ovrd
        self._init_config()
        self.source = source
        self.active_conn = None

    def set_source(self, source):
        """
        set the source of the current object to either remote or local
        :param source: string, either 'remote' or 'local'
        :return: None
        """
        if source in self.VALID_SOURCES:
            self.source = source
            print(source)
        else:
            print("Cannot set source to %s, only valid sources are %s" % (source, str(self.VALID_SOURCES)),
                  file=sys.stderr)

    def query(self, sql, index_col=None, parse_dates=None, keep_alive=False):
        """
        queries the current connection's set database
        :param sql: string query
        :param index_col: passed to the pd.read_sql function
        :param parse_dates: passed to the pd.read_sql function
        :param keep_alive: if true, keeps the connection alive (preserves temp tables)
        :return: dataframe with results
        """
        if self.active_conn is None:
            if self.source == self.REMOTE:
                self.connect_to_remote()
            elif self.source == self.LOCAL:
                self.connect_to_local()
            else:
                print("Data source set incorrectly to %s, only valid sources are %s. Try running .set_source()"
                      % (self.source,
                         str(self.VALID_SOURCES)))
                return False  # returns False to indicate failed execution

        df = pd.read_sql(sql, self.active_conn, index_col=index_col, parse_dates=parse_dates)

        if not keep_alive:
            self.close()

        return df

    def execute(self, sql_template, *args, keep_alive=False):
        """
        executes sql on connected database
        :param sql_template: sql or the sql template with ? characters if need to substitute with args
        :param args: list of arguments to use in the sql template
        :param keep_alive: if true, keeps the connection alive (preserves temp tables)
        :return:
        """
        if self.active_conn is None:
            if self.source == self.REMOTE:
                self.connect_to_remote()
            elif self.source == self.LOCAL:
                self.connect_to_local()
            else:
                print("Data source set incorrectly to %s, only valid sources are %s. Try running .set_source()"
                      % (self.source,
                         str(self.VALID_SOURCES)))
                return False  # returns False to indicate failed execution

        self.active_conn.cursor().execute(sql_template, args)
        self.active_conn.commit()

        if not keep_alive:
            self.close()

        return True

    def close(self):
        if self.active_conn:
            self.active_conn.close()
            self.active_conn = None

    def connect_to_remote(self):
        """ connect to the preset remote connection string """
        try:
            conn = psycopg2.connect(host=config.AACT_HOST,
                                    database=config.AACT_DB,
                                    user=self.config['Remote']['User'],
                                    password=self.config['Remote']['Password'])
            self.active_conn = conn
        except Exception:
            raise ConnectionError("Unable to connect to remote server: %s, db: %s. "
                                  "Try signing up for a login at "
                                  "https://aact.ctti-clinicaltrials.org/users/sign_up" % (config.AACT_HOST,
                                                                                          config.AACT_DB))

    def connect_to_local(self):
        """ connect to the preset local connection string """
        try:
            conn = psycopg2.connect(host=config.LOCAL_HOST,
                                    database=config.LOCAL_DB,
                                    user=self.config['Local']['User'],
                                    password=self.config['Local']['Password'])
            self.active_conn = conn
        except Exception:
            raise ConnectionError("Unable to connect to local server %s, db: %s "
                                  "Please ensure that you have a local instance of "
                                  "postgres running " % (config.LOCAL_HOST, config.LOCAL_DB))

    def _init_config(self):
        """ reads the private ini file located as specified by the config """
        if self.ini_path is None or self.ini_path == '':
            used_path = config.PRIVATE_CONFIG_LOC
        else:
            used_path = self.ini_path

        if os.path.exists(used_path):
            cur_config = configparser.ConfigParser()
            cur_config.read(used_path)
        else:
            raise FileNotFoundError("Could not find private credentials from %s" % used_path)
        self.config = cur_config
