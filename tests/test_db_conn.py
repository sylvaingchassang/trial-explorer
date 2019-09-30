"""
tests for database connector
"""
import pdaactconn as pconn


def test_remote_conn():
    ac = pconn.AACTConnection()
    ac.connect_to_remote()
    assert ac.active_conn.closed == 0
    ac.close()


def test_local_conn():
    ac = pconn.AACTConnection()
    ac.connect_to_local()
    assert ac.active_conn.closed == 0
    ac.close()


def test_source_setting():
    ac = pconn.AACTConnection()
    ac.set_source(ac.REMOTE)
    assert ac.source == ac.REMOTE

    ac.set_source(ac.LOCAL)
    assert ac.source == ac.LOCAL


def test_remote_query():
    ac = pconn.AACTConnection()
    df = ac.query("SELECT * FROM studies LIMIT 1")
    assert df.shape[0] == 1
    ac.close()


def test_local_query():
    ac = pconn.AACTConnection()
    ac.set_source(ac.LOCAL)
    df = ac.query("SELECT * FROM studies LIMIT 1")
    assert df.shape[0] == 1
    ac.close()


def test_poor_source():
    ac = pconn.AACTConnection()
    ac.source = 'foo'  # bad source
    df = ac.query("SELECT * FROM studies LIMIT 1")
    assert not df
    ac.close()


def test_bad_set_source():
    ac = pconn.AACTConnection()
    ac.set_source('foo')
    assert True
    ac.close()
