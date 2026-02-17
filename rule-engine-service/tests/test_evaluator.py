from datetime import datetime, timedelta
import pytest
from app.services.evaluator import check_schedule, evaluate_condition, evaluate_rule as eval_service_rule

class MockRule:
    def __init__(self, start=None, end=None, active=True, conds=[], op="AND"):
        self.schedule_start = start
        self.schedule_end = end
        self.is_active = active
        self.conditions = conds
        self.condition_operator = op

def test_check_schedule_open():
    rule = MockRule(start=None, end=None)
    assert check_schedule(rule) == True

def test_check_schedule_within():
    now = datetime.utcnow()
    # Check within 10 mins window cleanly
    start = (now - timedelta(minutes=10)).strftime("%H:%M:%S")
    end = (now + timedelta(minutes=10)).strftime("%H:%M:%S")
    rule = MockRule(start=start, end=end)
    assert check_schedule(rule) == True

def test_check_schedule_outside():
    now = datetime.utcnow()
    start = (now + timedelta(minutes=10)).strftime("%H:%M:%S")
    end = (now + timedelta(minutes=20)).strftime("%H:%M:%S")
    rule = MockRule(start=start, end=end)
    assert check_schedule(rule) == False

def test_condition_gt():
    cond = {"property": "temp", "operator": "GT", "threshold": 100}
    assert evaluate_condition(cond, {"temp": 101}) == True
    assert evaluate_condition(cond, {"temp": 100}) == False

def test_condition_missing_prop():
    cond = {"property": "temp", "operator": "GT", "threshold": 100}
    assert evaluate_condition(cond, {"pressure": 50}) == False

def test_evaluate_rule_and():
    # Both true
    conds = [
        {"property": "temp", "operator": "GT", "threshold": 100},
        {"property": "pressure", "operator": "LT", "threshold": 10}
    ]
    rule = MockRule(conds=conds, op="AND")
    assert eval_service_rule(rule, {"temp": 101, "pressure": 5}) == True
    
    # One false
    assert eval_service_rule(rule, {"temp": 101, "pressure": 15}) == False

def test_evaluate_rule_or():
    # One true
    conds = [
        {"property": "temp", "operator": "GT", "threshold": 100},
        {"property": "pressure", "operator": "LT", "threshold": 10}
    ]
    rule = MockRule(conds=conds, op="OR")
    assert eval_service_rule(rule, {"temp": 90, "pressure": 5}) == True
    
    # Both false
    assert eval_service_rule(rule, {"temp": 90, "pressure": 15}) == False
