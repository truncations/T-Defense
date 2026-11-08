let tabId=null;
const get=id=>document.getElementById(id);
async function send(type,extra={}) {const result=await chrome.runtime.sendMessage({type,tabId,...extra});if(!result?.ok)throw new Error(result?.error || 'Extension command failed.');return result;}
async function refresh() {
  const [tab]=await chrome.tabs.query({active:true,lastFocusedWindow:true});tabId=tab?.id;
  try {get('page').textContent=new URL(tab.url).origin;} catch {get('page').textContent='Open a regular website tab.';}
  const result=await send('STATE');
  get('status').textContent=result.state.lastError || (result.state.active?'Monitoring this page.':result.paired?'Backend code saved. Ready to start.':'Pair with the local backend to begin.');
  get('details').textContent=result.state.scanId?'Completed checks: '+result.state.scanCount+' · latest '+result.state.scanId+' · '+(result.state.warningCount || 0)+' warnings':'No completed check on this tab yet.';
  get('scan').disabled=!result.state.active;get('stop').disabled=!result.state.active;
}
get('pair').onclick=async()=>{try {await send('PAIR',{key:get('key').value.trim()});get('key').value='';await refresh();}catch(error){get('status').textContent=error.message;}};
for(const [id,type] of [['start','START'],['scan','SCAN'],['stop','STOP']])get(id).onclick=async()=>{get(id).disabled=true;try {await send(type);await refresh();}catch(error){get('status').textContent=error.message;}finally{get('start').disabled=false;}};
refresh().catch(error=>{get('status').textContent=error.message;});
