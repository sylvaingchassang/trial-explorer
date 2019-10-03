"""
Interface for specifying how to implement a AACTStudyDim,
which represents an 1-n relationship to nct_id in the studies table
"""
from abc import ABC, abstractmethod


class AACTStudyDimBase(ABC):
    """
    class to define the AACTStudyDimBase Interface
    """
    def __init__(self):
        pass

    @abstractmethod
    def load_data(self, conn):
        """ loads data from the database """

    @abstractmethod
    def dump_data(self):
        """ clears the memory of data """
