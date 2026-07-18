from fastapi.testclient import TestClient
from yarvis_api.main import app

client=TestClient(app)
def test_store_intelligence_routes_are_registered_and_empty_safe():
    response=client.get('/api/store-intelligence/profiles?limit=10&offset=0')
    assert response.status_code==200
    body=response.json(); assert set(body)=={'items','total','limit','offset'} and body['limit']==10
    assert client.get('/api/store-intelligence/profiles/no-such-store').status_code==404
    analytics=client.get('/api/store-intelligence/analytics').json()
    assert {'findings','portfolio_metrics','applied_filters','total_findings'} <= set(analytics)
    summary=client.get('/api/store-intelligence/summary').json()
    assert 'pending_profiles' in summary
def test_decisions_reject_unknown_store_and_filters_are_typed():
    assert client.post('/api/store-intelligence/decisions',json={'store_id':'missing','recommendation_at_decision_time':None,'decision':'resolved'}).status_code==404
    assert client.get('/api/store-intelligence/recovery-queue?pending_action=true').status_code==200
