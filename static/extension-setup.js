const byId=id=>document.getElementById(id);
let pairingCode='';
async function initialize(){
  try{
    const response=await fetch('/api/extension/pairing',{cache:'no-store'});if(!response.ok)throw Error();
    pairingCode=(await response.json()).pairing_code;byId('pair-code').value=pairingCode;byId('health').textContent='Local backend ready';
  }catch{byId('health').textContent='Open setup on localhost:8000';byId('copy-code').disabled=true;}
}
byId('copy-code').onclick=async()=>{try{await navigator.clipboard.writeText(pairingCode);byId('copy-status').textContent='Copied. Paste it into the T-Defense extension popup.';}catch{byId('pair-code').type='text';byId('pair-code').select();byId('copy-status').textContent='Copy the selected code manually, then paste it into the extension.';}};
async function stats(){try{const response=await fetch('/api/extension/stats',{cache:'no-store'});if(!response.ok)throw Error();const data=await response.json();byId('scan-count').textContent=data.processed_scans;byId('scan-time').textContent=data.last_scan_at?'Latest backend check: '+new Date(data.last_scan_at).toLocaleTimeString():'Waiting for the first scan.';}catch{byId('scan-time').textContent='Backend unavailable. Checks cannot complete.';}}
async function configuration(){try{const response=await fetch('/api/extension/config',{cache:'no-store'});if(!response.ok)throw Error();const data=await response.json();byId('vt-config').textContent=data.virustotal_configured?'Backend key configured. Enable domain checks separately in the extension popup.':'No VirusTotal key configured. Structural checks work; domain reputation is unavailable.';}catch{byId('vt-config').textContent='Could not read backend configuration.';}}
initialize();stats();configuration();setInterval(()=>{stats();configuration();},3000);
