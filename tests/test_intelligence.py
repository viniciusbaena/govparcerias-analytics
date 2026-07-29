from datetime import date
from backend.app.services.alert_engine import build_expiry_alerts
from backend.app.services.query_planner import plan
from backend.app.services.sync_engine import compare_records, fingerprint

def test_snapshot_diff():
    before=[{"id":"1","status":"A","value":10}]
    after=[{"id":"1","status":"B","value":10},{"id":"2","status":"A"}]
    changes=compare_records("x","id",before,after)
    assert any(x["field"]=="status" for x in changes)
    assert any(x["key"]=="2" for x in changes)
    assert fingerprint(before[0])==fingerprint(dict(before[0]))

def test_alert_rules():
    items=[{"numero":"1","municipio":"X","fim":"2026-02-15"}]
    alerts=build_expiry_alerts(items,date(2026,1,1))
    assert alerts[0]["level"]=="alto"

def test_query_planner():
    assert plan("Quais vigências vencem?").intent=="list_expiries"
    assert plan("Compare A e B").intent=="compare_municipalities"
