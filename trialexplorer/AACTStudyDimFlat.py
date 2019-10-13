"""
Simple class for handling the dimensions that are flat, for example brief_description
"""
from trialexplorer.AACTStudyDimBase import AACTStudyDimBase
from trialexplorer import config
from pdaactconn.Connection import AACTConnection


class AACTStudyDimFlat(AACTStudyDimBase):
    """
    class for flat dimensions that are just 1 table
    """
    def __init__(self, dim_name):
        super().__init__()
        self.name = dim_name
        self.data = None

    def load_data(self, conn):
        """ loads the data from the live connection, with temp table as nct_id list """
        self.data = None  # resetting
        self.load_data_from_db(conn)  # reloading

    def dump_data(self):
        self.data = None

    def load_data_from_db(self, conn: AACTConnection):
        """ loads all of the raw data into a dataframe """
        print(" -- Loading raw data")
        sql = self._generate_load_query()
        self.data = conn.query(sql,
                               index_col=[config.MAIN_ID_COL],
                               keep_alive=True)
        print(" -- Sorting index")
        self.data.sort_index(inplace=True)

    def _generate_load_query(self):
        """ generates the query used to load data """
        sql = """
                SELECT 
                    a.* 
                FROM %s a
                JOIN %s tmp ON tmp.nct_id = a.nct_id 
                """ % (self.name, config.MAIN_TEMP_TABLE)
        return sql
