"""
Simple class for handling the dimensions that are flat, for example brief_description
"""
from trialexplorer.AACTStudyDimBase import AACTStudyDimBase
from trialexplorer import config
from pdaactconn.Connection import AACTConnection


class AACTStudyDimIntervention(AACTStudyDimBase):
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
        if self.name == 'intervention_other_names':
            
            sql = """
                     SELECT
                     a.id as intervention_id,
                     a.nct_id,
                     a.intervention_type,
                     a.name as intervention_name,
                     a.description as intervention_description,
                     b.id as intervention_other_names_id,
                     b.name as intervention_other_names_name
                     FROM %s a
                     JOIN %s tmp ON tmp.nct_id = a.nct_id
                     JOIN (
		         SELECT b2.*
			 FROM %s b2
			 JOIN %s tmp2 ON tmp2.nct_id = b2.nct_id
                         ) b
                       ON tmp.nct_id = b.nct_id AND a.id = b.intervention_id         
                """ % ('interventions', config.MAIN_TEMP_TABLE, self.name, config.MAIN_TEMP_TABLE)
        else:
            sql = """
                     SELECT
                     a.id as interventions_id,
                     a.nct_id,
                     a.intervention_type,
                     a.name as intervention_name,
                     a.description as intervention_description,
                     b.id as design_group_id,
                     b.group_type as design_group_type,
                     b.title as design_group_title,
                     b.description as design_group_description
                     FROM %s a
                     JOIN %s tmp ON tmp.nct_id = a.nct_id
                     JOIN %s b ON b.nct_id = tmp.nct_id
                     JOIN (
			SELECT c2.*
			FROM %s c2
			JOIN %s tmp2 ON tmp2.nct_id = c2.nct_id
			) c
		        ON c.nct_id = tmp.nct_id AND a.id = c.intervention_id 
                            AND b.id = c.design_group_id
                """ % ('interventions', config.MAIN_TEMP_TABLE, 'design_groups', self.name, config.MAIN_TEMP_TABLE)
        self.raw_data = conn.query(sql, keep_alive=True)

    def allocate_raw_data(self):
        """ split the dataframe into a keyed-by-nct_id dict """
        print(" -- Creating memory pointers for the .data dictionary keyed by nct_id")
        for nct_id, sub_df in self.raw_data.groupby(config.MAIN_ID_COL):
            self.data[nct_id] = sub_df
