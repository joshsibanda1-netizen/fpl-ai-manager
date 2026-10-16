from engine import best_lineup, recommend_transfers
from safety import Policy, evaluate

def squad():
    positions = [1,1,2,2,2,2,2,3,3,3,3,3,4,4,4]
    return [{'id':i+1,'name':str(i),'team':(i%5)+1,'position':pos,
             'price':50,'selling_price':50,'next':3+i/10,'total':15+i/2,
             'status':'a'} for i,pos in enumerate(positions)]

def test_lineup_legal():
    out=best_lineup(squad())
    assert len(out['xi'])==11 and len(out['bench'])==4
    assert sum(p['position']==1 for p in out['xi'])==1

def test_safety_fail_closed():
    out=evaluate(policy=Policy(),points_hit=0,chip=None,budget_valid=True,
        rules_valid=True,minutes_to_deadline=120,data_fresh=True,
        action_id='a',processed_ids=set())
    assert not out['eligible_for_manual_review']
    assert not out['execution_available']

def test_no_duplicate():
    policy=Policy(emergency_stop=False)
    out=evaluate(policy=policy,points_hit=0,chip=None,budget_valid=True,
        rules_valid=True,minutes_to_deadline=120,data_fresh=True,
        action_id='a',processed_ids={'a'})
    assert 'Duplicate action' in out['reasons']
