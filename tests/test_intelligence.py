from backend.app.services.sync_engine import compare_records, fingerprint
from backend.app.services.query_planner import plan

def test_compare_records():
    changes=compare_records('parceria','numero',[{'numero':'1','valor':10}],[{'numero':'1','valor':12}])
    assert len(changes)==1 and changes[0]['field']=='valor'

def test_fingerprint_stable():
    assert fingerprint({'b':2,'a':1})==fingerprint({'a':1,'b':2})

def test_query_planner():
    assert plan('quais vigências vencem?').intent=='list_expiries'
