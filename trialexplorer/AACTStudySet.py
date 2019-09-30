"""
implementation of StudySet that uses the aact database as the datasource
"""
import pandas as pd
from trialexplorer.StudySet import StudySet
from trialexplorer import config
import pdaactconn as pc


class AACTStudySet(StudySet):
    def __init__(self, conn=None, tqdm_handler=None):
        """ conn specifies the database connection, if None, attempts to establish a default local connection """
        super().__init__()
        self._constraints = []  # constraints in a syntax that is understood by the _load_studies method
        self.tqdm = tqdm_handler

        # other attrs avail on the super:
        # self.studies = None  # stores the object that represents the flat studies data
        # self.required_dims = None  # stores the list of dim_name that represents required dimensions
        # self.study2dim_map = {}  # maps from study's nct_id the dim_name to the dimension object

        if conn:
            self.conn = conn
        else:
            self.conn = pc.AACTConnection(source=pc.AACTConnection.LOCAL)

    def load_studies(self):
        """ main load method, hydrates self.studies and initiates the db temp table """
        constr_block = self._generate_constr_block()
        sql = """
        SELECT * FROM %s
        """ % config.MAIN_TABLE_NAME
        sql += constr_block
        self.studies = self.conn.query(sql, index_col=[config.MAIN_ID_COL])

        # db temp table
        sql_template = """
        SELECT nct_id FROM %s
        """ % config.MAIN_TABLE_NAME
        sql_template += constr_block

        self._sync_temp_table(select_block=sql_template)
        print("%s studies loaded!" % self.studies.shape[0])

    def refresh_dim_data(self):
        pass

    def drop_studies(self, to_drop):
        start_count = self.studies.shape[0]
        print("started with %s studies" % start_count)
        self.studies.drop(to_drop, inplace=True)
        end_count = self.studies.shape[0]
        print("ended with %s studies" % end_count)

    def add_constraint(self, constraint):
        """ adds AND constraints, enforces brackets aroudn the constraint, OR constraints should be added together """
        bracketed_cons = "(" + constraint + ")"
        self._constraints.append(bracketed_cons)

    def remove_constraint(self, constraint_num):
        """ removes the nth constraint """
        del self._constraints[constraint_num - 1]

    def show_constraints(self):
        """ generates and shows the constraint string block """
        print(self._generate_constr_block())

    def list_columns(self):
        """ loads all of the columns of 'studies' as attributes of self.avail_columns """
        sql = """
        SELECT 
            COLUMN_NAME as c 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = '%s'
        """ % config.MAIN_TABLE_NAME
        df = self.conn.query(sql)
        return list(df['c'])

    def _create_temp_table(self):
        """ syncs what is in self.studies with the temp table in the database """
        sql_create = """ CREATE TEMPORARY TABLE IF NOT EXISTS %s (nct_id varchar)""" % config.MAIN_TEMP_TABLE
        self.conn.execute(sql_create)

    def _sync_temp_table(self, select_block=None):
        """ creates the temp table and syncs the records,
        if select_block is specified, then sync with the select block
        otherwise sync with self.studies """

        self._create_temp_table()
        self._reset_temp_table()
        if select_block:
            insert_template = """
            INSERT INTO %s
            """ % config.MAIN_TEMP_TABLE + select_block
            self.conn.execute(insert_template)
        else:
            self._chunk_insert(chunksize=config.SQL_CHUNK_SIZE)

    def _reset_temp_table(self):
        """ resets the records in the temp table """
        reset_sql = """
            DELETE FROM %s
        """ % config.MAIN_TEMP_TABLE
        self.conn.execute(reset_sql)

    def _chunk_insert(self, chunksize):
        """ inserts the idx in self.studies by chunks (due to max limit on insert and deletes) """
        to_insert = self.studies.index
        num_chunks = len(to_insert) // chunksize + 1

        # progress visuals from tqdm, only if explicitly set in the constructor
        if self.tqdm is None:
            chunk_iter = range(0, num_chunks)
        else:
            chunk_iter = self.tqdm(range(0, num_chunks))

        for i in chunk_iter:
            cur_insert = to_insert[chunksize * i: chunksize * (i + 1)]
            cur_insert_template = _generate_chunk_insert_sql(len(cur_insert))
            self.conn.execute(cur_insert_template, *tuple(cur_insert))

    def _generate_constr_block(self):
        """ generates and shows the constraint string block """
        if len(self._constraints) > 0:
            const_block = "WHERE 1=1 \n"
            for constr in self._constraints:
                const_block += "    AND " + constr + "\n"
            return const_block
        else:
            return ''  # no constraints


def _generate_chunk_insert_sql(num_to_insert):
    """ generate the insertion template for this chunk of text"""
    insert_template = """
    INSERT INTO %s VALUES
    """ % config.MAIN_TEMP_TABLE
    insert_template += ",".join(['(%s)'] * num_to_insert)
    return insert_template


# todo: since the chunk inserts are so fast, we should just initialize the temp table as needed instead of maintaining
# todo: an open connection
