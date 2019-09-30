"""
Interface for specifying how to implement a StudySet

"""
from abc import ABC, abstractmethod


class StudySet(ABC):
    """
    class to define the StudySet Interface
    """
    def __init__(self, **kwargs):
        self.studies = None  # stores the object that represents the flat studies data
        self.required_dims = None  # stores the list of dim_name that represents required dimensions
        self.constraints = None  # constraints in a syntax that is understood by the _load_studies method
        self.study2dim_map = {}  # maps from study's nct_id the dim_name to the dimension object

    @abstractmethod
    def refresh_dim_data(self):
        """ reloads the data that corresponds to the required_dimensisons """

    @abstractmethod
    def drop_studies(self, to_drop):
        """ drops all information related to the studies in the input to_drop """

    @abstractmethod
    def load_studies(self):
        """
        loads into memory the set of studies based on specified constraints, an attribute on self
        """