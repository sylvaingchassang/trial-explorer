"""
implementation of StudySet that uses the aact database as the datasource
"""
from ctypes import cdll, CDLL
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

    def add_dimensions(self, dim_names):
        # handling single string input to make it a list
        if isinstance(dim_names, str):
            dim_names = [dim_names]

        success_list = []
        fail_list = []
        for dim_name in dim_names:
            if dim_name in DIM_HANDLE_MAP:
                handler = DIM_HANDLE_MAP[dim_name]
                self.dimensions[dim_name] = handler(dim_name)
                success_list.append(dim_name)
            else:
                fail_list.append(dim_name)

        print("Successfuly added these %s dimensions: %s" % (len(success_list), str(success_list)))
        print("Failed to add these %s dimensions: %s" % (len(fail_list), str(fail_list)))

    def drop_dimensions(self, dim_names):
        # handling single string input to make it a list
        if isinstance(dim_names, str):
            dim_names = [dim_names]

        dim_names = list(dim_names)
        cur_dims = list(self.dimensions)

        for dim_name in dim_names:
            if dim_name in cur_dims:
                self.dimensions[dim_name].dump_data()
                del self.dimensions[dim_name]
                print("%s successfully dumped" % dim_name)
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
            if cur_dim.data.index.nlevels == 1:
                cur_dim.data.drop(to_drop, inplace=True, errors='ignore')
            else:
                cur_dim.data.drop(to_drop, level=config.MAIN_ID_COL, inplace=True, errors='ignore')
            libc.malloc_trim(0)

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
        self._create_index()

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

        print("Syncing the temp table %s in %s chunks x %s records each" % (config.MAIN_TEMP_TABLE,
                                                                            num_chunks,
                                                                            chunksize))
        for i in chunk_iter:
            cur_insert = to_insert[chunksize * i: chunksize * (i + 1)]
            cur_insert_template = _generate_chunk_insert_sql(len(cur_insert))
            self.conn.execute(cur_insert_template, *tuple(cur_insert), keep_alive=True)

    def _create_index(self):
        print("Creating index on the temp table")
        sql = """
        CREATE INDEX IDX_tmp_nct_id ON %s(%s)
        """ % (config.MAIN_TEMP_TABLE, config.MAIN_ID_COL)
        self.conn.execute(sql, keep_alive=True)

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

