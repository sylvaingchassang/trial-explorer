"""
implementation of StudySet that uses the aact database as the datasource
"""
import pandas as pd
import pdaactconn as pc
from trialexplorer.StudySet import StudySet
from trialexplorer import config
from trialexplorer.dim_handlers import DIM_HANDLE_MAP


class DimAutoCompleter:
    def __init__(self):
        for x in DIM_HANDLE_MAP.keys():
            setattr(self, x, x)

        self.list = [x for x in DIM_HANDLE_MAP.keys()]


class AACTStudySet(StudySet):
    def __init__(self, conn=None, tqdm_handler=None):
        """ conn specifies the database connection, if None, attempts to establish a default local connection """
        super().__init__()
        self._constraints = []  # constraints in a syntax that is understood by the _load_studies method
        self.tqdm = tqdm_handler
        self.dimensions = {}  # keyed by dim name, to the dim object with the data
        self.avail_dims = DimAutoCompleter()

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
        print("%s studies loaded!" % self.studies.shape[0])

    def add_dimension(self, dim_name):
        if dim_name in DIM_HANDLE_MAP:
            handler = DIM_HANDLE_MAP[dim_name]
            self.dimensions[dim_name] = handler(dim_name)
            print("added %s to dimensions list, now %s active" % (dim_name, len(self.dimensions.keys())))
        else:
            raise AssertionError("Handler not found for %s, please add it to dim_handlers.py" % dim_name)

    def drop_dimension(self, dim_name):
        if dim_name in self.dimensions:
            self.dimensions[dim_name].dump_data()
            self.dimensions[dim_name] = None
        else:
            print("%s was not an enabled dimension, nothing was done" % dim_name)

    def refresh_dim_data(self):
        self._sync_temp_table()
        for dim_name, dim_obj in self.dimensions.items():
            print(" - Loading dimension %s" % dim_name)
            dim_obj.load_data(self.conn)
        self.conn.close()

    def drop_studies(self, to_drop):
        start_count = self.studies.shape[0]
        print("started with %s studies" % start_count)
        self.studies.drop(to_drop, inplace=True)
        end_count = self.studies.shape[0]
        print("ended with %s studies" % end_count)

        for dim_name, cur_dim in self.dimensions.items():
            print("Dropping records from the %s dimension" % dim_name)
            # dropping from the dim raw data
            cur_dim.raw_data = cur_dim.raw_data[~cur_dim.raw_data[config.MAIN_ID_COL].isin(to_drop)].copy()
            # copy because we set the raw_data and all of the data pointers to another dataframe
            # should let the GC collect the old dataframe - need testing
            # todo: make sure that the dropping studies frees up memory

            # dropping from the dim data
            cur_dim.allocate_raw_data()

    def add_constraint(self, constraint):
        """ adds AND constraints, enforces brackets aroudn the constraint, OR constraints should be added together """
        bracketed_cons = "(" + constraint + ")"
        self._constraints.append(bracketed_cons)

    def remove_constraint(self, constraint_num):
        """ removes the nth constraint """
        del self._constraints[constraint_num]

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
        self.conn.execute(sql_create, keep_alive=True)  # keeps the connection alive to keep the temp table

    def _sync_temp_table(self):
        """ creates the temp table and syncs the records,
        if select_block is specified, then sync with the select block
        otherwise sync with self.studies """

        self._create_temp_table()
        self._reset_temp_table()
        self._chunk_insert(chunksize=config.SQL_CHUNK_SIZE)

    def _reset_temp_table(self):
        """ resets the records in the temp table """
        reset_sql = """
            DELETE FROM %s
        """ % config.MAIN_TEMP_TABLE
        self.conn.execute(reset_sql, keep_alive=True)

    def _chunk_insert(self, chunksize):
        """ inserts the idx in self.studies by chunks (due to max limit on insert and deletes) """
        to_insert = self.studies.index
        num_chunks = len(to_insert) // chunksize + 1

        # progress visuals from tqdm, only if explicitly set in the constructor
        if self.tqdm is None:
            chunk_iter = range(0, num_chunks)
        else:
            chunk_iter = self.tqdm(range(0, num_chunks))

        print("Syncing the temp table %s in %s chunks x %s records each" % (config.MAIN_TEMP_TABLE, num_chunks, chunksize))
        for i in chunk_iter:
            cur_insert = to_insert[chunksize * i: chunksize * (i + 1)]
            cur_insert_template = _generate_chunk_insert_sql(len(cur_insert))
            self.conn.execute(cur_insert_template, *tuple(cur_insert), keep_alive=True)

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

