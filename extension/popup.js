let tabId=null,trustToken=null,findingsSignature=null,pairingNotice=null;
const setText=(id,text)=>{if(document.getElementById(id).textContent!==text)document.getElementById(id).textContent=text;};
const get=id=>document.getElementById(id);
async function send(type,extra={}) {const result=await chrome.runtime.sendMessage({type,tabId,...extra});if(!result?.ok)throw new Error(result?.error || 'Extension command failed.');return result;}
async function refresh() {
  const [tab]=await chrome.tabs.query({active:true,lastFocusedWindow:true});tabId=tab?.id;
  try {get('page').textContent=new URL(tab.url).origin;} catch {get('page').textContent='Open a regular website tab.';}
  const result=await send('STATE');
  if(result.paired)pairingNotice=null;
  get('status').textContent=pairingNotice || result.state.lastError || (result.monitoring?.enabled?'Continuous monitoring is on.':result.state.active?'Monitoring this page.':result.paired?'Backend code saved. Ready to start.':'Pair with the local backend to begin.');
  get('details').textContent=result.state.scanId?'Completed checks: '+result.state.scanCount+' · latest '+result.state.scanId+' · '+(result.state.warningCount || 0)+' warnings':'No completed check on this tab yet.';
  renderFindings(result.state);
  get('installation').textContent='Installation: '+chrome.runtime.id;
  get('reputation').checked=!!result.state.reputationEnabled;get('reputation').disabled=!result.state.active;
  get('scan').disabled=!result.state.active;get('stop').disabled=!result.state.active && !result.monitoring?.enabled;
}
get('pair').onclick=async()=>{try {await send('PAIR',{key:get('key').value.trim()});get('key').value='';await refresh();}catch(error){get('status').textContent=error.message;}};
for(const [id,type] of [['scan','SCAN'],['stop','STOP']])get(id).onclick=async()=>{get(id).disabled=true;try {await send(type);await refresh();}catch(error){get('status').textContent=error.message;}finally{get('start').disabled=false;}};
get('reputation').onchange=async()=>{try{await send('REPUTATION',{enabled:get('reputation').checked});await refresh();}catch(error){get('status').textContent=error.message;}};
setInterval(()=>refresh().catch(()=>{}),1500);
refresh().then(async()=>{const key='trustRequested:'+tabId;const request=await chrome.storage.session.get(key);if(request[key]){await chrome.storage.session.remove(key);get('trust-preview').click();}}).catch(error=>{get('status').textContent=error.message;});

get('start').onclick=async()=>{try{const granted=await chrome.permissions.request({origins:['http://*/*','https://*/*']});if(!granted)throw new Error('Website access was not granted. Continuous monitoring remains off.');await send('START');await refresh();}catch(error){setText('status',error.message);}};
get('trust-preview').onclick=async()=>{try{const result=await send('TRUST_PREVIEW');trustToken=result.candidate.token;setText('trust-candidate',result.candidate.origin+' · '+result.candidate.kind+' · '+result.candidate.preview);get('trust-save').disabled=false;}catch(error){setText('trust-candidate',error.message);get('trust-save').disabled=true;}};
get('trust-save').onclick=async()=>{try{await send('TRUST_SELECTED',{token:trustToken});trustToken=null;get('trust-save').disabled=true;setText('trust-candidate','Exact content trusted locally. Changed content or destinations will be checked again.');await trustEntries();}catch(error){setText('trust-candidate',error.message);}};
async function trustEntries(){const result=await send('TRUST_ENTRIES');get('trusted-entries').replaceChildren(...result.entries.map(entry=>{const row=document.createElement('p');row.textContent=entry.origin+' · '+entry.kind+' · '+entry.fingerprint.slice(0,12)+'… ';const button=document.createElement('button');button.textContent='Revoke';button.onclick=async()=>{await send('TRUST_DELETE',{fingerprint:entry.fingerprint});await trustEntries();};row.append(button);return row;}));}
get('trust-manager').ontoggle=()=>{if(get('trust-manager').open)trustEntries().catch(error=>setText('trust-candidate',error.message));};
get('trust-clear').onclick=async()=>{await send('TRUST_CLEAR');await trustEntries();setText('trust-candidate','Local trust decisions cleared. Content will be checked again.');};
get('reset-position').onclick=()=>send('RESET_POSITION').catch(error=>setText('status',error.message));

get('auto-pair').onclick=async()=>{try{const result=await send('AUTO_PAIR');pairingNotice=result.approvalRequired?'Local setup opened. Match and approve installation '+result.installationId+'. Then click Connect automatically again; monitoring stays off until Start.':null;await refresh();}catch(error){setText('status',error.message);}};
function renderFindings(state){
  const findings=state.findings || [];const signature=JSON.stringify(findings);
  setText('finding-coverage',state.lastError?'Checks unavailable — retained evidence may be out of date.':state.coverage?.truncated?'Partial page coverage. Unchecked content is not verified safe.':state.scanId?'Inspected content only; no safety guarantee.':'No completed check for this document.');
  if(signature===findingsSignature)return;findingsSignature=signature;
  get('popup-findings').replaceChildren(...findings.map(entry=>{const li=document.createElement('li');const title=document.createElement('strong');title.textContent=entry.title;li.append(title);const state=document.createElement('small');state.textContent=entry.current?'Latest inspected evidence':'Previous batch evidence — recheck';li.append(state);for(const text of [...entry.evidence,entry.next_step]){const p=document.createElement('p');p.textContent=text;li.append(p);}const review=document.createElement('button');review.textContent='Locate / select for trust';review.onclick=async()=>{try{await send('REVIEW',{elementId:entry.element_id});get('trust-preview').click();}catch(error){setText('status',error.message);}};li.append(review);return li;}));
}
