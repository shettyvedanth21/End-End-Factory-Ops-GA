from datetime import datetime, time
import logging

logger = logging.getLogger("rule-evaluator")

def check_schedule(rule) -> bool:
    if not rule.schedule_start or not rule.schedule_end:
        return True
    
    now = datetime.utcnow().time()
    try:
        start = datetime.strptime(rule.schedule_start, "%H:%M:%S").time()
        end = datetime.strptime(rule.schedule_end, "%H:%M:%S").time()
        if start <= end:
            return start <= now <= end
        else: # Crosses midnight
            return start <= now or now <= end
    except ValueError:
        return True # Default to open on parse error

def evaluate_condition(condition: dict, payload: dict) -> bool:
    prop = condition.get("property")
    op = condition.get("operator")
    threshold = condition.get("threshold")
    
    if prop not in payload:
        return False
    
    val = payload[prop]
    
    if op == "GT": return val > threshold
    if op == "LT": return val < threshold
    if op == "GTE": return val >= threshold
    if op == "LTE": return val <= threshold
    if op == "EQ": return abs(val - threshold) < 0.001
    if op == "NEQ": return abs(val - threshold) >= 0.001
    
    return False

def evaluate_rule(rule, payload: dict) -> bool:
    if not rule.is_active:
        return False
        
    if not check_schedule(rule):
        return False

    results = [evaluate_condition(c, payload) for c in rule.conditions]
    
    if rule.condition_operator == "AND":
        return all(results)
    else:
        return any(results)
