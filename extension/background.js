importScripts('trust.js');
const BACKEND='http://127.0.0.1:8000';
const stateKey=id=>'tab:'+id;
const tabTransactions=new Map();
function withTab(id,operation){
  const next=(tabTransactions.get(id) || Promise.resolve()).catch(()=>{}).then(operation);
  tabTransactions.set(id,next);
  const cleanup=()=>{if(tabTransactions.get(id)===next)tabTransactions.delete(id);};
  next.then(cleanup,cleanup);return next;
}
chrome.storage.session.setAccessLevel({accessLevel:'TRUSTED_CONTEXTS'}).catch(()=>{});
async function requestBackend(path,body,key,reputation=false) {
  const response=await fetch(BACKEND+path,{method:'POST',headers:{'Content-Type':'application/json','X-TDefense-Key':key,'X-TDefense-Client':chrome.runtime.id,...(reputation?{'X-TDefense-Reputation':'enabled'}:{})},body:JSON.stringify(body),signal:AbortSignal.timeout(6000),cache:'no-store',credentials:'omit',redirect:'error'});
  if (!response.ok) throw new Error(response.status===403?'Pair again with the current backend session.':'The local backend could not complete this check.');
  return response.json();
}
async function tabState(id) {return (await chrome.storage.session.get(stateKey(id)))[stateKey(id)] || {active:false,scanCount:0};}
async function saveState(id,state) {await chrome.storage.session.set({[stateKey(id)]:state});}
async function pair(key) {
  if (typeof key!=='string' || key.length<24 || key.length>100) throw new Error('Paste the current pairing code from local setup.');
  await requestBackend('/api/extension/connect',{},key);
  await chrome.storage.session.set({backendKey:key});
  return {ok:true};
}
async function startMonitoring(id) {
  const intent=crypto.randomUUID();
  await withTab(id,async()=>{const previous=await tabState(id);await saveState(id,{...previous,startIntent:intent});});
  try {
    const {backendKey}=await chrome.storage.session.get('backendKey');
    if (!backendKey) throw new Error('Pair with the local backend first.');
    const tab=await chrome.tabs.get(id);let origin;
    try {const url=new URL(tab.url);if(!['http:','https:'].includes(url.protocol))throw Error();origin=url.origin;}
    catch {throw new Error('Open a regular HTTP or HTTPS website first.');}
    await requestBackend('/api/extension/connect',{},backendKey);
    await withTab(id,async()=>{const previous=await tabState(id);
      if(previous.startIntent!==intent)throw new Error('Monitoring was stopped or a newer action replaced this start.');
      await saveState(id,{active:true,origin,runId:intent,documentId:previous.origin===origin?previous.documentId:null,scanCount:previous.scanCount || 0,reputationEnabled:previous.origin===origin && !!previous.reputationEnabled,lastError:null});});
    await chrome.scripting.executeScript({target:{tabId:id},files:['scanner.js','content.js']});
    await withTab(id,async()=>{const current=await tabState(id);
      if(!current.active || current.runId!==intent)throw new Error('Monitoring was stopped or a newer action replaced this start.');
      await chrome.action.setBadgeBackgroundColor({tabId:id,color:'#c00061'});});
    return {ok:true};
  } catch(error) {
    await withTab(id,async()=>{const current=await tabState(id);
      if(current.startIntent===intent){const retained={...current};delete retained.startIntent;await saveState(id,retained);}
      else if(current.runId===intent && !current.startIntent)await saveState(id,{active:false,scanCount:0});});
    throw error;
  }
}
async function stopMonitoring(id,expected=null) {return withTab(id,async()=>{if(expected && (await tabState(id)).globalGeneration!==expected)return {ok:true};
  await saveState(id,{active:false,scanCount:0});
  await chrome.action.setBadgeText({tabId:id,text:''});
  await chrome.action.setTitle({tabId:id,title:'T-Defense — monitoring paused'});
  try {await chrome.tabs.sendMessage(id,{type:'TDEFENSE_STOP'});} catch { /* Tab may have navigated. */ }
  return {ok:true};
});}
async function assess(snapshot,sender) {
  const id=sender.tab?.id;
  if (sender.frameId!==0) throw new Error('Only the active top-level page is supported.');
  if (!Number.isInteger(id)) throw new Error('No active page session.');
  const senderOrigin=new URL(sender.url).origin;
  const beforeGlobal=await globalSettings();
  const state=await withTab(id,async()=>{const state=await tabState(id);
    if ((state.global && (!beforeGlobal.enabled || state.globalGeneration!==beforeGlobal.generation)) || !state.active || state.origin!==senderOrigin || snapshot?.page_origin!==senderOrigin) throw new Error('Monitoring is not active on this page.');
    if(state.documentId && state.documentId!==sender.documentId)throw new Error('Monitoring was stopped for the previous document.');
    await saveState(id,{...state,documentId:sender.documentId});return state;});
  const runId=state.runId;
  const {backendKey}=await chrome.storage.session.get('backendKey');
  if (!backendKey) throw new Error('Pair with the local backend first.');
  try {
    const result=await requestBackend('/api/page/assess',snapshot,backendKey,!!state.reputationEnabled);
    // A stopped/navigated tab must not be resurrected by a delayed response.
    const completedGlobal=await globalSettings();
    const alive=await chrome.tabs.sendMessage(id,{type:'TDEFENSE_DOCUMENT_CURRENT'},{documentId:sender.documentId}).catch(()=>null);
    await withTab(id,async()=>{const current=await tabState(id);
    if ((current.global && (!completedGlobal.enabled || current.globalGeneration!==completedGlobal.generation)) || !alive?.active || current.documentId!==sender.documentId || !current.active || current.origin!==senderOrigin || current.runId!==runId) throw new Error(alive?.active && current.active && current.origin===senderOrigin && current.documentId===sender.documentId?'Check settings changed. Retry this page check.':'Monitoring was stopped.');
    await saveState(id,{...current,documentId:sender.documentId,scanCount:(current.scanCount || 0)+1,lastScan:result.scanned_at,scanId:result.scan_id,warningCount:result.warning_count,lastError:null});
    await chrome.action.setBadgeText({tabId:id,text:result.warning_count?String(Math.min(99,result.warning_count)):''});
    await chrome.action.setTitle({tabId:id,title:'T-Defense: '+result.warning_count+' warning(s); '+result.status});});
    return {ok:true,result};
  } catch(error) {
    await withTab(id,async()=>{const current=await tabState(id);
    if(current.active && current.origin===senderOrigin && current.runId===runId){await saveState(id,{...current,lastError:error.message});await chrome.action.setBadgeText({tabId:id,text:'?'});}});
    throw error;
  }
}
const WEB_ORIGINS=['http://*/*','https://*/*'];
async function globalSettings(){return (await chrome.storage.local.get('monitoring')).monitoring || {enabled:false,generation:null};}
async function registerPersistent(){
  const registered=await chrome.scripting.getRegisteredContentScripts({ids:['t-defense-always']});
  if(!registered.length)await chrome.scripting.registerContentScripts([{id:'t-defense-always',matches:WEB_ORIGINS,js:['bootstrap.js'],runAt:'document_idle',allFrames:false,persistAcrossSessions:true}]);
}
async function armGlobal(id,origin,documentId=null){
  let generation;
  await withTab('global',async()=>{const settings=await globalSettings();if(!settings.enabled)throw new Error('Monitoring was stopped.');generation=settings.generation;
    await withTab(id,async()=>{const state=await tabState(id);if(state.active && state.origin===origin && state.globalGeneration===generation && (!documentId || state.documentId===documentId))return;
      await saveState(id,{active:true,global:true,globalGeneration:generation,origin,documentId,runId:crypto.randomUUID(),scanCount:state.scanCount || 0,reputationEnabled:state.origin===origin && !!state.reputationEnabled,lastError:null});});});
  const target=documentId?{tabId:id,documentIds:[documentId]}:{tabId:id};
  await chrome.scripting.executeScript({target,files:['scanner.js','content.js']});
  const after=await globalSettings();if(!after.enabled || after.generation!==generation){await stopMonitoring(id,generation);throw new Error('Monitoring was stopped.');}
}
async function armAll(){const tabs=await chrome.tabs.query({});await Promise.allSettled(tabs.filter(tab=>/^https?:/.test(tab.url || '')).map(tab=>armGlobal(tab.id,new URL(tab.url).origin)));}
async function enableEverywhere(){
  if(!await chrome.permissions.contains({origins:WEB_ORIGINS}))throw new Error('Allow website access using Start everywhere in the toolbar popup.');
  const intent=crypto.randomUUID();let already=false;
  await withTab('global',async()=>{const previous=await globalSettings();already=previous.enabled;await chrome.storage.local.set({monitoring:{...previous,startIntent:intent}});});
  if(!already){const {backendKey}=await chrome.storage.session.get('backendKey');if(!backendKey)throw new Error('Pair with the local backend first.');await requestBackend('/api/extension/connect',{},backendKey);}
  await withTab('global',async()=>{const current=await globalSettings();if(current.startIntent!==intent)throw new Error('Monitoring was stopped.');await registerPersistent();await chrome.storage.local.set({monitoring:{enabled:true,generation:already?current.generation:intent}});});
  await armAll();return {ok:true};
}
async function stopEverywhere(){
  await withTab('global',async()=>{await chrome.storage.local.set({monitoring:{enabled:false,generation:crypto.randomUUID()}});await chrome.scripting.unregisterContentScripts({ids:['t-defense-always']}).catch(()=>{});const tabs=await chrome.tabs.query({});await Promise.allSettled(tabs.map(tab=>stopMonitoring(tab.id)));});return {ok:true};
}
async function restoreGlobal(){let enabled=false;await withTab('global',async()=>{const settings=await globalSettings();if(settings.enabled && await chrome.permissions.contains({origins:WEB_ORIGINS})){await registerPersistent();enabled=true;}});if(enabled)await armAll();}
async function broadcast(type){const tabs=await chrome.tabs.query({});await Promise.allSettled(tabs.map(tab=>chrome.tabs.sendMessage(tab.id,{type})));}
async function selection(id){const state=await tabState(id);if(!state.active || !state.documentId)throw new Error('Select a current finding on a monitored page first.');
  const candidate=await chrome.tabs.sendMessage(id,{type:'TDEFENSE_SELECTION'},{documentId:state.documentId});
  if(!candidate?.fingerprint || candidate.origin!==state.origin || !/^[0-9a-f]{64}$/.test(candidate.fingerprint))throw new Error('Choose a smaller current message, link or form. Whole-page findings cannot be permanently trusted.');
  return {...candidate,documentId:state.documentId};}
async function handle(message,sender) {
  if(sender.id!==chrome.runtime.id)throw new Error('Unsupported sender.');
  if(message.type==='TDEFENSE_HELLO'){
    if(sender.frameId!==0 || !sender.tab || !/^https?:/.test(sender.url || ''))throw new Error('Unsupported page.');
    if((await globalSettings()).enabled)await armGlobal(sender.tab.id,new URL(sender.url).origin,sender.documentId);return {ok:true};}
  if(message.type==='TDEFENSE_TRUST_LIST' && sender.tab){if(sender.frameId!==0)throw new Error('Unsupported frame.');return {ok:true,entries:(await TrustStore.read(new URL(sender.url).origin)).map(row=>row.fingerprint)};}
  if(message.type==='TDEFENSE_POSITION' && sender.tab){const pos=message.position;if(!pos || !Number.isFinite(pos.x) || !Number.isFinite(pos.y) || pos.x<0 || pos.x>1 || pos.y<0 || pos.y>1)throw new Error('Invalid position.');await chrome.storage.local.set({panelPosition:pos});return {ok:true};}
  if(message.type==='TDEFENSE_GET_POSITION' && sender.tab)return {ok:true,position:(await chrome.storage.local.get('panelPosition')).panelPosition || null};
  if(message.type==='TDEFENSE_SNAPSHOT')return assess(message.snapshot,sender);
  if(message.type==='TDEFENSE_PAUSE' && sender.tab){const state=await tabState(sender.tab.id);if(state.origin!==new URL(sender.url).origin)throw new Error('Wrong page session.');return (await globalSettings()).enabled?stopEverywhere():stopMonitoring(sender.tab.id);}
  if(sender.tab || sender.url!==chrome.runtime.getURL('popup.html'))throw new Error('Use the extension popup controls.');
  if(message.type==='PAIR')return pair(message.key);
  if(message.type==='REPUTATION'){await withTab(message.tabId,async()=>{const state=await tabState(message.tabId);if(!state.active)throw new Error('Start monitoring before enabling domain checks.');await saveState(message.tabId,{...state,startIntent:null,reputationEnabled:message.enabled===true,runId:crypto.randomUUID()});});await chrome.tabs.sendMessage(message.tabId,{type:'TDEFENSE_RESTART_CHECK'}).catch(()=>{});return {ok:true};}
  if(message.type==='TRUST_PREVIEW'){const candidate=await selection(message.tabId);const token=crypto.randomUUID();await chrome.storage.session.set({['trustCandidate:'+message.tabId]:{fingerprint:candidate.fingerprint,origin:candidate.origin,kind:candidate.kind,documentId:candidate.documentId,token}});return {ok:true,candidate:{origin:candidate.origin,kind:candidate.kind,preview:candidate.preview,token}};}
  if(message.type==='TRUST_SELECTED'){const saved=(await chrome.storage.session.get('trustCandidate:'+message.tabId))['trustCandidate:'+message.tabId];const current=await selection(message.tabId);if(!saved || saved.token!==message.token || saved.fingerprint!==current.fingerprint || saved.documentId!==current.documentId)throw new Error('The selected content changed. Preview it again before trusting.');await TrustStore.add(current);await chrome.storage.session.remove('trustCandidate:'+message.tabId);await broadcast('TDEFENSE_TRUST_CHANGED');return {ok:true};}
  if(message.type==='TRUST_ENTRIES')return {ok:true,entries:await TrustStore.read()};
  if(message.type==='TRUST_DELETE'){await TrustStore.remove(message.fingerprint);await broadcast('TDEFENSE_TRUST_CHANGED');return {ok:true};}
  if(message.type==='TRUST_CLEAR'){await TrustStore.clear();await broadcast('TDEFENSE_TRUST_CHANGED');return {ok:true};}
  if(message.type==='RESET_POSITION'){await chrome.storage.local.remove('panelPosition');await broadcast('TDEFENSE_RESET_POSITION');return {ok:true};}
  if(message.type==='START')return enableEverywhere();
  if(message.type==='STOP'){await stopEverywhere();return stopMonitoring(message.tabId);}
  if(message.type==='SCAN'){await chrome.tabs.sendMessage(message.tabId,{type:'TDEFENSE_SCAN'});return {ok:true};}
  if(message.type==='STATE'){const data=await tabState(message.tabId);const {backendKey}=await chrome.storage.session.get('backendKey');return {ok:true,state:data,monitoring:await globalSettings(),paired:!!backendKey};}
  throw new Error('Unsupported extension command.');
}
chrome.runtime.onMessage.addListener((message,sender,reply)=>{
  if(!message || typeof message.type!=='string')return false;
  handle(message,sender).then(reply).catch(error=>reply({ok:false,error:error.message || 'Page checks unavailable.',code:/Monitoring (?:is not active|was stopped)/.test(error.message)?'PAUSED':/Check settings changed/.test(error.message)?'RETRY':'CHECK_FAILED'}));
  return true;
});
chrome.tabs.onRemoved.addListener(id=>{withTab(id,()=>chrome.storage.session.remove(stateKey(id))).catch(()=>{});});
chrome.tabs.onUpdated.addListener(async(id,change)=>{
  if(change.status==='loading'){await withTab(id,async()=>{const state=await tabState(id);if(state.active || state.startIntent){await saveState(id,{...state,startIntent:null,runId:crypto.randomUUID(),documentId:null,lastError:'Navigation in progress',scanId:null});await chrome.action.setBadgeText({tabId:id,text:'…'});}});return;}
  if(change.status!=='complete')return;
  if((await globalSettings()).enabled)return;
  const state=await tabState(id);if(!state.active)return;
  try {const tab=await chrome.tabs.get(id);if(new URL(tab.url).origin!==state.origin){await stopMonitoring(id);return;}await chrome.scripting.executeScript({target:{tabId:id},files:['scanner.js','content.js']});}
  catch {await stopMonitoring(id);}
});

chrome.runtime.onStartup.addListener(()=>restoreGlobal().catch(()=>{}));
chrome.runtime.onInstalled.addListener(()=>restoreGlobal().catch(()=>{}));
chrome.permissions.onRemoved.addListener(()=>{chrome.permissions.contains({origins:WEB_ORIGINS}).then(granted=>{if(!granted)return stopEverywhere();}).catch(()=>{});});
restoreGlobal().catch(()=>{});
