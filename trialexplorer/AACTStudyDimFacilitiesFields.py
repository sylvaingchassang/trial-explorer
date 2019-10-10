"""
Simple class for handling the dimensions that are flat, for example brief_description
"""
from trialexplorer.AACTStudyDimBase import AACTStudyDimBase
from trialexplorer import config
from pdaactconn.Connection import AACTConnection


class AACTStudyDimFacilityGroup(AACTStudyDimBase):
    """
    class for flat dimensions that are just 1 table
    """
    def __init__(self, dim_name):
        super().__init__()
        self.name = dim_name
        self.raw_data = None
        self.data = {}

    def load_data(self, conn):
        """ loads the data from the live connection, with temp table as nct_id list """
        # resetting
        self.data = {}
        # reloading
        self.load_raw_data(conn)
        self.allocate_raw_data()

    def dump_data(self):
        self.raw_data = None
        self.data = None

    def load_raw_data(self, conn: AACTConnection):
        """ loads all of the raw data into a dataframe """
        print(" -- Loading raw data")
        sql = """
                SELECT
                    a.*,
                    b.id AS facility_contacts_id,
                    b.contact_type AS facility_contacts_contact_type,
                    b.name AS facility_contacts_name,
                    b.email AS facility_contacts_email,
                    b.phone AS facility_contacts_phone,
                    c.id AS facility_investigators_id,
                    c.role AS facility_investigators_role,
                    c.name AS facility_investigators_name
                FROM %s a
                JOIN %s tmp ON tmp.nct_id = a.nct_id
                JOIN %s b ON a.id = b.facility_id
                JOIN %s c ON a.id = c.facility_id
                """ % (self.name, config.MAIN_TEMP_TABLE, 'facility_contacts', 'facility_investigators')
        self.raw_data = conn.query(sql, keep_alive=True)

    def allocate_raw_data(self):
        """ split the dataframe into a keyed-by-nct_id dict """
        print(" -- Creating memory pointers for the .data dictionary keyed by nct_id")
        for nct_id, sub_df in self.raw_data.groupby([config.MAIN_ID_COL, 'id',
            'facility_contacts_id', 'facility_investigators_id']):
            self.data[nct_id] = sub_df
