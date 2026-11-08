let tabId=null,trustToken=null,findingsSignature=null,lastState=null;
const get=id=>document.getElementById(id);
const setText=(id,text)=>{if(get(id).textContent!==text)get(id).textContent=text;};
async function send(type,extra={}){const result=await chrome.runtime.sendMessage({type,tabId,...extra});if(!result?.ok)throw new Error(result?.error || 'Extension command failed.');return result;}
function showStatus(text){get('status').hidden=!text;setText('status',text || '');}
function ago(stamp){if(!stamp)return '';const seconds=Math.max(0,Math.round((Date.now()-new Date(stamp).getTime())/1000));if(seconds<20)return 'Checked just now';if(seconds<90)return 'Checked '+seconds+' seconds ago';const minutes=Math.round(seconds/60);return minutes<90?'Checked '+minutes+' minutes ago':'Checked over an hour ago';}

function pageVerdict(state){
  const findings=(state.findings || []).filter(row=>row.current!==false);
  const count=findings.length;
  const danger=findings.some(row=>row.severity==='high' && row.category!=='possible_spam');
  const spam=count>0 && findings.every(row=>row.category==='possible_spam');
  if(state.lastError && !state.scanId)return {tone:'caution',badge:'UNKNOWN',summary:'Checks unavailable, use caution'};
  if(!state.scanId)return {tone:'',badge:'CHECKING',summary:'Checking this page…'};
  if(!count)return {tone:'',badge:state.coverage?.truncated?'PARTIAL':'CHECKED',summary:'No warnings in checked content'};
  const label=count===1?'1 finding':count+' findings';
  if(danger)return {tone:'danger',badge:'DANGEROUS',summary:'Risky content, '+label};
  if(spam)return {tone:'caution',badge:'CAUTION',summary:'Likely spam, '+label};
  return {tone:'caution',badge:'CAUTION',summary:'Needs a look, '+label};
}

async function refresh(){
  const [tab]=await chrome.tabs.query({active:true,lastFocusedWindow:true});tabId=tab?.id;
  try{setText('page',new URL(tab.url).host || new URL(tab.url).origin);}catch{setText('page','Open a regular website tab');}
  const result=await send('STATE');lastState=result;
  const on=!!result.monitoring?.enabled,state=result.state;
  get('off-card').hidden=on;get('on-card').hidden=!on;get('start').hidden=on;
  get('protection-switch').setAttribute('aria-checked',String(on));
  setText('footnote',on?'Turning the switch off stops monitoring everywhere.':'Start asks for website access once. Monitoring stays on your computer.');
  get('page-card').hidden=!state.active;
  if(state.active){const verdict=pageVerdict(state);get('page-card').className='card page-card '+verdict.tone;setText('page-badge',verdict.badge);setText('page-summary',verdict.summary);setText('page-time',state.lastError && state.scanId?'Last check failed, results may be out of date':ago(state.lastScan));}
  get('scan').disabled=!state.active;
  showStatus(result.backend?(state.lastError && state.lastError!=='Navigation in progress'?state.lastError:''):'Local T-Defense service is not running. Start it on this computer; the extension reconnects by itself.');
  renderFindings(state);
  get('reputation').setAttribute('aria-checked',String(!!state.reputationEnabled));get('reputation').disabled=!state.active;
  setText('trusted-count',(result.trustedCount || 0)+' saved');
  setText('backend-state',result.backend?'Connected automatically':'Not running');
  const id=chrome.runtime.id;setText('installation','ID '+id.slice(0,6)+'…'+id.slice(-7));
}

function renderFindings(state){
  const findings=state.findings || [];const signature=JSON.stringify(findings);
  setText('finding-coverage',state.lastError?'Checks unavailable, saved evidence may be out of date.':state.coverage?.truncated?'Partial page coverage. Unchecked content is not verified safe.':state.scanId?'Inspected content only; no safety guarantee.':'No completed check for this page yet.');
  if(signature===findingsSignature)return;findingsSignature=signature;
  get('popup-findings').replaceChildren(...findings.map(entry=>{
    const li=document.createElement('li');const title=document.createElement('strong');title.textContent=entry.title;li.append(title);
    const tag=document.createElement('small');tag.textContent=entry.current?'Latest inspected evidence':'Previous batch evidence, check again';li.append(tag);
    for(const text of [...entry.evidence,entry.next_step]){const p=document.createElement('p');p.textContent=text;li.append(p);}
    const review=document.createElement('button');review.className='secondary';review.textContent='Locate on page';
    review.onclick=async()=>{try{await send('REVIEW',{elementId:entry.element_id});await previewTrust();}catch(error){showStatus(error.message);}};
    li.append(review);return li;}));
}

async function previewTrust(){
  get('trust-card').hidden=false;
  try{const result=await send('TRUST_PREVIEW');trustToken=result.candidate.token;setText('trust-candidate',result.candidate.origin+' · '+result.candidate.kind+' · '+result.candidate.preview);get('trust-save').disabled=false;}
  catch(error){setText('trust-candidate',error.message);get('trust-save').disabled=true;}
}
get('trust-save').onclick=async()=>{try{await send('TRUST_SELECTED',{token:trustToken});trustToken=null;get('trust-save').disabled=true;setText('trust-candidate','Exact content trusted locally. Changed content or destinations will be checked again.');await trustEntries();}catch(error){setText('trust-candidate',error.message);}};
get('trust-cancel').onclick=()=>{trustToken=null;get('trust-card').hidden=true;};

async function trustEntries(){const result=await send('TRUST_ENTRIES');setText('trusted-count',result.entries.length+' saved');get('trusted-entries').replaceChildren(...result.entries.map(entry=>{const row=document.createElement('p');const label=document.createElement('span');label.textContent=entry.origin+' · '+entry.kind+' · '+entry.fingerprint.slice(0,12)+'…';const button=document.createElement('button');button.className='secondary';button.textContent='Revoke';button.onclick=async()=>{await send('TRUST_DELETE',{fingerprint:entry.fingerprint});await trustEntries();};row.append(label,button);return row;}));}
get('trust-manage').onclick=()=>{const panel=get('trust-manager');panel.hidden=!panel.hidden;if(!panel.hidden)trustEntries().catch(error=>showStatus(error.message));};
get('trust-clear').onclick=async()=>{await send('TRUST_CLEAR');await trustEntries();};

get('start').onclick=async()=>{try{const granted=await chrome.permissions.request({origins:['http://*/*','https://*/*']});if(!granted)throw new Error('Website access was not granted. Protection stays off.');await send('START');await refresh();}catch(error){showStatus(error.message);}};
get('protection-switch').onclick=async()=>{get('protection-switch').disabled=true;try{await send('STOP');await refresh();}catch(error){showStatus(error.message);}finally{get('protection-switch').disabled=false;}};
get('scan').onclick=async()=>{get('scan').disabled=true;try{await send('SCAN');await refresh();}catch(error){showStatus(error.message);}};
get('view-details').onclick=()=>{const panel=get('details-panel');panel.hidden=!panel.hidden;setText('view-details',panel.hidden?'View details':'Hide details');};
get('reputation').onclick=async()=>{const enabled=get('reputation').getAttribute('aria-checked')!=='true';try{await send('REPUTATION',{enabled});await refresh();}catch(error){showStatus(error.message);}};
get('reset-position').onclick=()=>send('RESET_POSITION').catch(error=>showStatus(error.message));
get('open-settings').onclick=()=>{get('home-view').hidden=true;get('settings-view').hidden=false;};
get('close-settings').onclick=()=>{get('settings-view').hidden=true;get('home-view').hidden=false;};

async function poll(){try{await refresh();}catch{}setTimeout(poll,1500);}
refresh().then(async()=>{const key='trustRequested:'+tabId;const request=await chrome.storage.session.get(key);if(request[key]){await chrome.storage.session.remove(key);await previewTrust();}}).catch(error=>showStatus(error.message)).finally(()=>setTimeout(poll,1500));
