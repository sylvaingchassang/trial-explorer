"""
tests for trial explorer
"""
import pdaactconn as pc
from trialexplorer import AACTStudySet
from trialexplorer.dim_handlers import DIM_HANDLE_MAP
import random
import os
import psutil

NUM_RANDOM_DIMS = 2
MEM_THRESH = 0.5
USED_DB = pc.AACTConnection.LOCAL


def test_load_studies():
    """ loading a set of studies """
    conn = pc.AACTConnection(source=USED_DB)
    ss = AACTStudySet.AACTStudySet(conn=conn)
    ss.load_studies()
    assert ss.studies.shape[0] > 0


def test_constraints():
    """ adding and removing constraints """
    conn = pc.AACTConnection(source=USED_DB)
    ss = AACTStudySet.AACTStudySet(conn=conn)
    ss.add_constraint("start_date >= '2018-06-30'")
    ss.add_constraint("start_date <= '2018-12-31'")
    ss.load_studies()
    assert 0 < ss.studies.shape[0] < 50000


def test_add_dims():
    """ test adding dimensions """
    conn = pc.AACTConnection(source=USED_DB)
    ss = AACTStudySet.AACTStudySet(conn=conn)
    tested_dims = random.sample(list(DIM_HANDLE_MAP.keys()), NUM_RANDOM_DIMS)
    ss.add_dimensions(tested_dims)
    assert len(ss.dimensions.keys()) > 0


def test_refresh_dims():
    """ test adding dimensions """
    conn = pc.AACTConnection(source=USED_DB)
    ss = AACTStudySet.AACTStudySet(conn=conn)
    ss.add_constraint("start_date >= '2016-06-30'")
    ss.add_constraint("start_date <= '2016-12-31'")
    ss.load_studies()
    tested_dims = random.sample(list(DIM_HANDLE_MAP.keys()), NUM_RANDOM_DIMS)
    ss.add_dimensions(tested_dims)
    ss.refresh_dim_data()
    for _, cur_dim in ss.dimensions.items():
        assert cur_dim.data.shape[0] > 0


def test_all_dimensions():
    """ test loading data from all dimensions """
    conn = pc.AACTConnection(source=USED_DB)
    ss = AACTStudySet.AACTStudySet(conn=conn)
    ss.add_constraint("start_date >= '2017-06-30'")
    ss.add_constraint("start_date <= '2017-12-31'")
    ss.load_studies()
    tested_dims = DIM_HANDLE_MAP.keys()
    ss.add_dimensions(tested_dims)
    ss.refresh_dim_data()
    for _, cur_dim in ss.dimensions.items():
        assert cur_dim.data.shape[0] > 0


def test_drop_data():
    """ dropping data from studies """
    conn = pc.AACTConnection(source=USED_DB)
    ss = AACTStudySet.AACTStudySet(conn=conn)
    ss.add_constraint("start_date >= '2017-06-30'")
    ss.add_constraint("start_date <= '2017-12-31'")
    ss.load_studies()
    ss.drop_studies(ss.studies.index)
    assert ss.studies.shape[0] == 0


def test_drop_dims():
    """ dropping data from dimensions """
    conn = pc.AACTConnection(source=USED_DB)
    ss = AACTStudySet.AACTStudySet(conn=conn)
    ss.add_constraint("start_date >= '2017-12-31'")
    ss.add_constraint("start_date <= '2018-12-31'")
    ss.load_studies()
    tested_dims = random.sample(list(DIM_HANDLE_MAP.keys()), NUM_RANDOM_DIMS)
    ss.add_dimensions(tested_dims)
    ss.drop_dimensions(tested_dims)
    assert len(ss.dimensions) == 0


def test_memory_freeing():
    """ test dropping data frees up memory """
    conn = pc.AACTConnection(source=USED_DB)
    ss = AACTStudySet.AACTStudySet(conn=conn)
    ss.load_studies()
    tested_dims = random.sample(list(DIM_HANDLE_MAP.keys()), NUM_RANDOM_DIMS)
    ss.add_dimensions(tested_dims)
    ss.refresh_dim_data()
    process = psutil.Process(os.getpid())
    pre_clear_mem = process.memory_info().rss
    ss.drop_studies(ss.studies.index)
    post_clear_mem = process.memory_info().rss
    assert post_clear_mem < pre_clear_mem * MEM_THRESH
