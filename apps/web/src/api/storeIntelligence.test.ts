import {beforeEach, describe, expect, it, vi} from 'vitest';
import {createDecision,getAnalytics,getRecoveryQueue,getStoreProfile,getStoreProfiles,getStoreSummary} from './storeIntelligence';

const fetchMock=vi.fn(); global.fetch=fetchMock as unknown as typeof fetch;
const ok=(body:unknown={})=>({ok:true,json:async()=>body});
describe('Store Intelligence API client',()=>{
 beforeEach(()=>fetchMock.mockReset());
 it('requests profiles and preserves false and zero while omitting empty values',async()=>{fetchMock.mockResolvedValue(ok({items:[]}));await getStoreProfiles({pending_action:false,minimum_months_no_use:0,client_id:'',activation_failure:undefined});expect(fetchMock.mock.calls[0][0]).toContain('pending_action=false');expect(fetchMock.mock.calls[0][0]).toContain('minimum_months_no_use=0');expect(fetchMock.mock.calls[0][0]).not.toContain('client_id');expect(fetchMock.mock.calls[0][0]).not.toContain('activation_failure');});
 it('requests exact profile detail',async()=>{fetchMock.mockResolvedValue(ok({}));await getStoreProfile('synthetic/id');expect(fetchMock.mock.calls[0][0]).toContain('/profiles/synthetic%2Fid');});
 it('requests queue, analytics and summary',async()=>{fetchMock.mockResolvedValue(ok({profiles:[]}));await getRecoveryQueue({operational_block:false});fetchMock.mockResolvedValue(ok({findings:[]}));await getAnalytics({attention_level:'low'});fetchMock.mockResolvedValue(ok({}));await getStoreSummary();expect(fetchMock.mock.calls.map(c=>c[0])).toEqual(expect.arrayContaining([expect.stringContaining('/recovery-queue?operational_block=false'),expect.stringContaining('/analytics?attention_level=low'),expect.stringContaining('/summary')]));});
 it('posts append-only decision payload',async()=>{fetchMock.mockResolvedValue(ok({event_id:'synthetic'}));await createDecision({store_id:'synthetic-store',recommendation_at_decision_time:null,decision:'resolved',operational_note:null});const [url,init]=fetchMock.mock.calls[0];expect(url).toContain('/decisions');expect(init.method).toBe('POST');expect(JSON.parse(init.body)).toMatchObject({store_id:'synthetic-store',decision:'resolved'});});
 it('returns a safe error for non-2xx responses',async()=>{fetchMock.mockResolvedValue({ok:false});await expect(getStoreSummary()).rejects.toThrow('Store Intelligence unavailable');});
});
