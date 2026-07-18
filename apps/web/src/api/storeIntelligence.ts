import type {HumanDecisionEvent,HumanDecisionInput,RecoveryQueueFilters,RecoveryQueueResult,StoreAnalyticsFilters,StoreAnalyticsResult,StoreIntelligenceSummary,StoreOperationalProfile,StoreProfilePage} from '../types/storeIntelligence';
const base='http://localhost:8000/api/store-intelligence';
const query=(filters:Record<string,string|number|boolean|undefined>)=>{const p=new URLSearchParams();Object.entries(filters).forEach(([k,v])=>{if(v!==undefined&&v!=='' )p.set(k,String(v));});return p.toString()?`?${p}`:''};
async function request<T>(path:string,init?:RequestInit):Promise<T>{const r=await fetch(base+path,init);if(!r.ok)throw new Error('Store Intelligence unavailable');return r.json() as Promise<T>}
export const getStoreProfiles=(filters:Record<string,string|number|boolean|undefined>={})=>request<StoreProfilePage>('/profiles'+query(filters));
export const getStoreProfile=(id:string)=>request<StoreOperationalProfile>('/profiles/'+encodeURIComponent(id));
export const getRecoveryQueue=(filters:RecoveryQueueFilters={})=>request<RecoveryQueueResult>('/recovery-queue'+query(filters));
export const getAnalytics=(filters:StoreAnalyticsFilters={})=>request<StoreAnalyticsResult>('/analytics'+query(filters));
export const getStoreSummary=()=>request<StoreIntelligenceSummary>('/summary');
export const createDecision=(input:HumanDecisionInput)=>request<HumanDecisionEvent>('/decisions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(input)});
