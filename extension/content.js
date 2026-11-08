(() => {
  if (globalThis.TDefenseGuard) {globalThis.TDefenseGuard.scan('manual');return;}
  let active=true,inFlight=false,queued=null,timer=null,latest=null,nodes=new Map(),expanded=false,selected=0,guarded=null;
  let reviewed=null,previewNode=null,previewDomain=null,hoverTimer=null;
  let previousKeys=new Set();const bypass=new WeakMap();
  const host=document.createElement('div');host.id='tdefense-page-guard';
  host.style.cssText='all:initial!important;position:fixed!important;top:16px!important;right:16px!important;z-index:2147483647!important;width:min(390px,calc(100vw - 32px))!important;display:block!important;color-scheme:light!important;';
  const ui=host.attachShadow({mode:'open'});
  ui.innerHTML=`<style>
    *{box-sizing:border-box} :host{font:15px/1.45 "Segoe UI",Arial,sans-serif;color:#331226}button{font:inherit;cursor:pointer}button:focus-visible{outline:3px solid #e20074;outline-offset:3px}.shell{font:15px/1.45 "Segoe UI",Arial,sans-serif;color:#331226;background:#fff9fc;border:1px solid #e7bfd3;border-radius:15px;box-shadow:0 10px 45px #30001b35;overflow:hidden}.shell.warning{border:2px solid #c00061;background:#fff1f8}.header{display:flex;align-items:center;gap:9px;padding:13px 15px}.mark{display:grid;place-items:center;background:#e20074;color:white;font-weight:750;width:28px;height:30px;border-radius:7px}.heading{flex:1;min-width:0}.brand{font-size:14px;font-weight:750;color:#b00057}.count{font-size:13px;display:block;color:#6a4c5d}.toggle{border:0;background:transparent;color:#8a2858;padding:8px;font-size:17px}.body{padding:0 16px 16px;max-height:65vh;overflow:auto}.body[hidden]{display:none}h2{font-size:21px;line-height:1.25;margin:4px 0 12px}p{margin:9px 0}ul{padding-left:20px;margin:10px 0}li{margin:7px 0}.advice{font-weight:650;color:#7c1647}.meta{font-size:11px;color:#74576a;border-top:1px solid #ead7e1;padding:9px 15px;background:#fff9fc;overflow-wrap:anywhere}.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:13px}.actions button{border:1px solid #d6a7be;border-radius:7px;padding:8px 11px;background:white;color:#8e2058;font-weight:600}.actions .primary{background:#b9005e;color:white;border-color:#b9005e}.actions button:disabled{opacity:.5;cursor:wait}.notice{background:#ffe0ee;padding:10px;border-radius:7px;font-weight:650}.pulse{animation:pulse 1.2s ease-out 2}@keyframes pulse{from{box-shadow:0 0 0 0 #e2007466}to{box-shadow:0 0 0 11px #e2007400}}@media(prefers-reduced-motion:reduce){.pulse{animation:none}}@media(max-width:450px){.body{max-height:52vh}h2{font-size:19px}}
  </style><span id="announce" role="alert" aria-atomic="true" style="position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)"></span><section class="shell" aria-label="T-Defense page monitor"><header class="header"><span class="mark">T</span><div class="heading"><span class="brand">T-Defense</span><span class="count" id="count">Checking this page…</span></div><button class="toggle" id="toggle" aria-label="Expand T-Defense details" aria-expanded="false">⌄</button></header><div class="body" id="body" hidden><h2 id="title">A second look before you trust it</h2><p id="summary"></p><p id="reputation">Domain reputation checks are off.</p><p id="review-note" class="notice" hidden></p><button id="clear-review" hidden>Close reviewed finding</button><p id="guard-note" class="notice" hidden>Action paused. Review this warning before continuing.</p><ul id="facts"></ul><p class="advice" id="advice"></p><div class="actions"><button id="locate">Show element</button><button id="next">Next finding</button><button id="scan">Check now</button><button id="pause">Pause monitoring</button><button id="continue" class="primary" hidden>Continue once</button></div></div><footer class="meta" id="meta">Connecting to your local backend. No form values collected.</footer></section>`;
  (document.body || document.documentElement).append(host);
  const get=id=>ui.getElementById(id);
  function ownEvent(event){return event.composedPath().includes(host);}
  function details(){get('body').hidden=!expanded;get('toggle').setAttribute('aria-expanded',String(expanded));get('toggle').textContent=expanded?'⌃':'⌄';}
  function facts(lines){get('facts').replaceChildren(...lines.map(text=>{const li=document.createElement('li');li.textContent=text;return li;}));}
  function render(result,reason,newNodes=null) {
    const pendingReview=reason==='review' && host.getAttribute('data-status')==='pending';
    const oldNode=reviewed?.node || (latest?.warnings[selected] && nodes.get(latest.warnings[selected].element_id));
    if(newNodes)nodes=newNodes;
    latest=result;const warnings=result.warnings || [];
    selected=Math.min(selected,Math.max(0,warnings.length-1));
    const keys=new Set(warnings.map(row=>row.element_id+':'+row.rules.join(',')));
    const freshIndex=warnings.findIndex(row=>!previousKeys.has(row.element_id+':'+row.rules.join(',')));
    const fresh=freshIndex>=0;const retainedIndex=warnings.findIndex(row=>nodes.get(row.element_id)===oldNode);
    if(reviewed && retainedIndex>=0){selected=retainedIndex;reviewed.row=warnings[retainedIndex];}else if(fresh && !reviewed)selected=freshIndex;previousKeys=keys;
    if(fresh){get('announce').textContent='T-Defense warning. '+warnings.length+' page elements need a second look. '+warnings[freshIndex].title;expanded=true;get('body').parentElement.classList.remove('pulse');void host.offsetWidth;get('body').parentElement.classList.add('pulse');}
    if(!warnings.length && !guarded && !reviewed)expanded=false;
    host.setAttribute('data-warning-count',String(warnings.length));host.setAttribute('data-scan-id',result.scan_id);host.setAttribute('data-status',result.status);
    ui.querySelector('.shell').classList.toggle('warning',warnings.length>0 || !!guarded || !!reviewed);
    get('count').textContent=warnings.length?warnings.length+' page element'+(warnings.length===1?'':'s')+' need a second look':result.verdict==='inconclusive' || result.status==='partial'?'Limited checks · some risks remain unchecked':'Watching · no matched warning rules';
    const finding=reviewed && retainedIndex<0?reviewed.row:warnings[selected];
    get('review-note').hidden=!reviewed;get('clear-review').hidden=!reviewed;
    if(reviewed)get('review-note').textContent=!reviewed.node.isConnected?'Previously observed finding. This element is no longer on the page.':retainedIndex<0?'Previously observed finding. The latest check did not reproduce it.':'Reviewing this finding. It remains available during rechecks.';
    const rep=result.reputation || {status:'disabled',domains:[]};
    const report=rep.domains?.find(row=>row.domain===previewDomain) || rep.domains?.find(row=>['malicious','suspicious'].includes(row.status)) || rep.domains?.find(row=>row.domain===location.hostname) || rep.domains?.[0];
    const labels={disabled:'VirusTotal checks are off. Enable them in the extension popup.',not_configured:'VirusTotal key is not configured. Domain reputation is unavailable.',no_public_domains:'No eligible public domains to query.',pending:'Domain check pending.',rate_limited:'VirusTotal quota reached. This domain was not checked.',unknown:'VirusTotal has no usable report for this domain.',stale:'VirusTotal report is old. Treat its status as unknown.',unavailable:'VirusTotal check unavailable.',not_checked:'This domain has not been checked.',no_reported_detections:'No reported detections. This does not establish safety.',malicious:'Reported malicious detections. Avoid this destination.',suspicious:'Reported suspicious detections. Verify independently.'};
    get('reputation').textContent=report?report.domain+' · '+(labels[report.status] || report.status)+(report.analyzed_at?' · report '+new Date(report.analyzed_at).toLocaleDateString():''):labels[rep.status] || 'Domain checks are incomplete; some destinations remain unchecked.';
    get('title').textContent=guarded?'Pause before you continue':reviewed && retainedIndex<0?'Previously observed warning':warnings.length?'T-Defense warning':'What this check can tell you';
    get('summary').textContent=finding?finding.title:result.verdict==='inconclusive'?'Some checks are incomplete. The page has not been verified.':'No rule matched the inspected elements. This is not a guarantee that the page is trustworthy.';
    facts(finding?finding.evidence:result.unknowns.slice(0,2));
    get('advice').textContent=finding?finding.next_step:'Use an official app or a trusted contact route if a request seems unusual.';
    get('guard-note').hidden=!guarded;get('continue').hidden=!guarded;get('continue').disabled=false;
    get('locate').hidden=!finding;get('locate').disabled=!!reviewed && !reviewed.node.isConnected;get('next').hidden=warnings.length<2;
    get('meta').textContent='Live backend check '+new Date(result.scanned_at).toLocaleTimeString()+' · '+result.scan_id+' · '+(reason==='mutation'?'page changed':'structural rules')+' · no form values sent · '+(rep.status==='disabled'?'domain checks off':rep.status==='not_configured'?'domain key missing':'domain '+rep.status);
    details();if(pendingReview)pending();
  }
  function unavailable(message) {
    latest=null;nodes.clear();if(host.getAttribute('data-status')!=='unavailable')get('announce').textContent='T-Defense checks unavailable. Use caution.';
    expanded=true;ui.querySelector('.shell').classList.add('warning');host.setAttribute('data-status','unavailable');host.removeAttribute('data-scan-id');
    get('count').textContent='Checks unavailable — use caution';get('title').textContent='We could not check this page';get('summary').textContent=message;
    facts(['Check that the local backend is running and the extension is paired.','This failure is not a clean result.']);get('advice').textContent='Avoid attachments and sensitive information until you verify the request independently.';
    get('guard-note').hidden=!guarded;get('continue').hidden=!guarded;get('continue').disabled=false;get('locate').hidden=true;get('next').hidden=true;
    get('meta').textContent='No completed backend check. Nothing typed into forms was collected.';details();
  }
  async function scan(reason='manual') {
    if(!active)return;
    if(document.hidden && !['interaction','manual'].includes(reason)){queued='visible';return;}
    if(inFlight){queued=reason;return;}
    inFlight=true;
    try {
      const collected=globalThis.TDefenseSnapshot.collect(reason,previewNode?.isConnected?previewNode:null);
      const response=await chrome.runtime.sendMessage({type:'TDEFENSE_SNAPSHOT',snapshot:collected.snapshot});
      if(!active)return;
      if(!response?.ok){if(response?.code==='RETRY'){pending();queued='manual';return;}if(response?.code==='PAUSED'){stop();return;}throw new Error(response?.error || 'Local page checks are unavailable.');}
      const current=globalThis.TDefenseSnapshot.collect(reason,previewNode?.isConnected?previewNode:null);
      if(JSON.stringify(current.snapshot)!==JSON.stringify(collected.snapshot)){pending();queued='mutation';return;}
      const focused=collected.snapshot.elements.find(row=>collected.nodes.get(row.element_id)===previewNode);previewDomain=focused?.target_origin?new URL(focused.target_origin).hostname:null;
      render(response.result,reason,collected.nodes);
    } catch(error) {if(active)unavailable(error.message || 'Local page checks are unavailable.');}
    finally {inFlight=false;if(active && queued){const again=queued;queued=null;setTimeout(()=>scan(again),250);}}
  }
  function pending(){host.setAttribute('data-status','pending');host.removeAttribute('data-scan-id');get('count').textContent='Page changed · checking again…';get('meta').textContent='Rechecking page changes. Previous findings remain available; current status is unconfirmed.';if(guarded)get('continue').disabled=true;}
  function schedule(reason) {clearTimeout(timer);timer=setTimeout(()=>scan(reason),800);}
  function warningFor(element) {
    if(!latest)return null;
    return latest.warnings.find(row=>{const node=nodes.get(row.element_id);return node && (node===element || node.contains(element));}) || null;
  }
  function localConcern(element) {
    const data=globalThis.TDefenseSnapshot.collect('interaction',element);
    const signal=data.snapshot.elements.find(row=>{const node=data.nodes.get(row.element_id);return node===element || node?.contains(element);});
    if(!signal)return false;
    return signal.download || signal.target_scheme==='data' || signal.gift_code_request || (signal.urgency && signal.sensitive_request) || (signal.kind==='form' && signal.sensitive_fields.length && (location.protocol==='http:' || signal.target_origin?.startsWith('http:') || (signal.target_origin && signal.target_origin!==location.origin))) || (signal.displayed_origin && signal.target_origin && new URL(signal.displayed_origin).hostname!==new URL(signal.target_origin).hostname);
  }
  function actionSignature(element,submitter){return JSON.stringify([element.ownerDocument.baseURI,element.href,element.target,element.download,element.action,element.method,element.enctype,submitter?.formAction,submitter?.formMethod,submitter?.formTarget]);}
  function pauseAction(event,element,kind) {
    const signature=actionSignature(element,event.submitter);
    if(bypass.has(element)){const approved=bypass.get(element);bypass.delete(element);if(approved===signature)return;}
    if(!warningFor(element) && !localConcern(element))return;
    event.preventDefault();event.stopImmediatePropagation();guarded={element,kind,submitter:event.submitter || null,signature};
    expanded=true;get('title').textContent='Checking before you continue';get('summary').textContent='This request needs a second look. The original action has been paused.';get('guard-note').hidden=false;get('continue').hidden=false;get('continue').disabled=true;details();scan('interaction');
  }
  const click=event=>{if(!active || ownEvent(event) || event.button!==0)return;const link=event.target.closest?.('a[href]');if(link)pauseAction(event,link,'link');};
  const submit=event=>{if(active && !ownEvent(event) && event.target instanceof HTMLFormElement)pauseAction(event,event.target,'form');};
  function preview(element){if(element && element!==previewNode){previewNode=element;clearTimeout(hoverTimer);hoverTimer=setTimeout(()=>scan('interaction'),400);}}
  const hover=event=>{if(!active || ownEvent(event))return;const link=event.target.closest?.('a[href]');if(link)preview(link);const finding=warningFor(event.target);if(finding){selected=latest.warnings.indexOf(finding);expanded=true;render(latest,'review');expanded=true;details();}};
  const focus=event=>{if(!active || ownEvent(event))return;const link=event.target.closest?.('a[href]');if(link)preview(link);const form=event.target.closest?.('form');if(form && (warningFor(form) || localConcern(form))){expanded=true;scan('interaction');}};
  const inspect=event=>{if(!active || ownEvent(event))return;const row=warningFor(event.target);if(row){reviewed={row,node:nodes.get(row.element_id)};expanded=true;render(latest,'review');}};
  const visible=()=>{if(!document.hidden)scan('visible');};
  window.addEventListener('contextmenu',inspect,true);window.addEventListener('click',click,true);window.addEventListener('submit',submit,true);document.addEventListener('mouseover',hover,true);document.addEventListener('focusin',focus,true);document.addEventListener('visibilitychange',visible);
  const observer=new MutationObserver(changes=>{
    const meaningful=changes.some(change=>change.target!==host && !host.contains(change.target) && !(change.type==='childList' && [...change.addedNodes,...change.removedNodes].every(node=>node===host)));
    if(meaningful){pending();schedule('mutation');}
  });
  observer.observe(document.documentElement,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['href','action','type','autocomplete','role','download','form','formaction','formmethod','formtarget','method','enctype','target','name','id','placeholder']});
  const interval=setInterval(()=>scan('periodic'),8000);
  function stop() {active=false;queued=null;clearTimeout(timer);clearTimeout(hoverTimer);clearInterval(interval);observer.disconnect();window.removeEventListener('contextmenu',inspect,true);window.removeEventListener('click',click,true);window.removeEventListener('submit',submit,true);document.removeEventListener('mouseover',hover,true);document.removeEventListener('focusin',focus,true);document.removeEventListener('visibilitychange',visible);chrome.runtime.onMessage.removeListener(messageHandler);host.remove();guarded=null;nodes.clear();delete globalThis.TDefenseGuard;}
  get('toggle').onclick=()=>{expanded=!expanded;details();};get('scan').onclick=()=>scan('manual');
  get('pause').onclick=()=>chrome.runtime.sendMessage({type:'TDEFENSE_PAUSE'}).catch(()=>stop());
  get('next').onclick=()=>{if(latest?.warnings.length){selected=(selected+1)%latest.warnings.length;expanded=true;reviewed=null;render(latest,'review');}};
  get('clear-review').onclick=()=>{reviewed=null;if(latest)render(latest,'review');else{get('review-note').hidden=true;get('clear-review').hidden=true;}};
  get('locate').onclick=()=>{const row=reviewed?.row || latest?.warnings[selected];const node=reviewed?.node || (row && nodes.get(row.element_id));if(node?.isConnected){reviewed={row,node};expanded=true;render(latest,'review');node.scrollIntoView({block:'center',behavior:'instant'});if(!matchMedia('(prefers-reduced-motion: reduce)').matches)node.animate([{outline:'3px solid #e20074'},{outline:'3px solid transparent'}],{duration:1800});}};
  get('continue').onclick=()=>{const action=guarded;if(!action || !action.element.isConnected){guarded=null;return;}if(action.signature!==actionSignature(action.element,action.submitter)){action.signature=actionSignature(action.element,action.submitter);pending();scan('interaction');return;}guarded=null;bypass.set(action.element,action.signature);if(action.kind==='link')action.element.click();else action.element.requestSubmit(action.submitter?.isConnected?action.submitter:undefined);if(latest)render(latest,'manual');};
  function messageHandler(message,sender,reply){if(sender.id!==chrome.runtime.id)return false;if(message.type==='TDEFENSE_DOCUMENT_CURRENT'){reply({active});return false;}if(message.type==='TDEFENSE_STOP'){stop();reply({ok:true});}else if(message.type==='TDEFENSE_RESTART_CHECK'){pending();scan('manual');reply({ok:true});}else if(message.type==='TDEFENSE_SCAN'){scan('manual');reply({ok:true});}return false;}
  chrome.runtime.onMessage.addListener(messageHandler);
  globalThis.TDefenseGuard={scan,stop};scan('initial');
})();
