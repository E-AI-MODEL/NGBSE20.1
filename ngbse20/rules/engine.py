"""Simple rules engine."""
from typing import List, Dict, Any

OPS = {
    '>':  lambda a,b: a >  b,
    '<':  lambda a,b: a <  b,
    '>=': lambda a,b: a >= b,
    '<=': lambda a,b: a <= b,
    '==': lambda a,b: a == b,
    '!=': lambda a,b: a != b,
}

def parse_condition(cond: str):
    for op in ('>=','<=','>','<','==','!='):
        if op in cond:
            val = cond.split(op,1)[1].strip()
            try:
                v = float(val)
            except Exception:
                v = val
            return op, v
    try:
        v = float(cond)
    except Exception:
        v = cond
    return '==', v

def trigger_matches(trigger: Dict[str, str], metrics: Dict[str, Any]) -> bool:
    for k, cond in trigger.items():
        if k not in metrics:
            return False
        op, v = parse_condition(str(cond))
        x = metrics.get(k)
        if isinstance(v, (int,float)):
            try:
                x = float(x)
            except Exception:
                return False
        try:
            if not OPS[op](x, v):
                return False
        except Exception:
            return False
    return True

def evaluate_rules(rules: List[Dict[str, Any]], metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    actions = []
    for r in rules:
        if trigger_matches(r.get('trigger',{}), metrics):
            act = dict(r.get('action',{}))
            act['rule_id'] = r.get('id')
            actions.append(act)
    return actions
