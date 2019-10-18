"""
Simple class for handling the dimensions that are flat, for example brief_description
"""
from trialexplorer.AACTStudyDimBase import AACTStudyDimBase
from trialexplorer import config
from pdaactconn.Connection import AACTConnection


def generate_2d_dim_constructor(second_table, second_ident):
    """ generates the class for a Dimension handler that is 2 levels down """
    class AACTStudyDim2d(AACTStudyDimBase):
        """
        class for flat dimensions that are just 1 table
        """
        def __init__(self, dim_name):
            super().__init__()
            self.name = dim_name
            self.data = {}
            self.second_table = second_table
            self.second_ident = second_ident

        def load_data(self, conn):
            """ loads the data from the live connection, with temp table as nct_id list """
            self.data = {}  # resetting
            self.load_data_from_db(conn)  # reloading

        def dump_data(self):
            self.data = None

        def load_data_from_db(self, conn: AACTConnection):
            """ loads all of the raw data into a dataframe """
            print(" -- Loading raw data")
            sql = self._generate_load_query()
            self.data = conn.query(sql,
                                   index_col=[config.MAIN_ID_COL, self.second_ident],
                                   keep_alive=True)
            print(" -- Sorting index")
            self.data.sort_index(inplace=True)

        def _generate_load_query(self):
            sql = """
                SELECT 
                    a.* 
                FROM %s b
                JOIN %s tmp ON tmp.nct_id = b.nct_id
                JOIN %s a on a.nct_id=tmp.nct_id and b.id = a.%s
                """ % (self.second_table, config.MAIN_TEMP_TABLE, self.name, self.second_ident)
            return sql

    return AACTStudyDim2d
