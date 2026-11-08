(() => {
  if (globalThis.TDefenseGuard) {globalThis.TDefenseGuard.scan('manual');return;}
  let active=true,inFlight=false,queued=null,timer=null,latest=null,nodes=new Map();
  let expanded=false,selected=null,guarded=null,previewNode=null,previewDomain=null,hoverTimer=null;
  let manualRequested=false,manualGeneration=0,unread=false,unavailableAnnounced=false,frame=null,nextNumber=0;
  let trustGeneration=0,trusted=new Set(),trustedTargets=new Map(),scopeUrl=location.href,drag=null;
  const markerNodes=new Map();
  const findings=new Map(),nodeKeys=new WeakMap(),rows=new Map(),bypass=new WeakMap();
  const host=document.createElement('div');host.id='tdefense-page-guard';
  host.style.cssText='all:initial!important;position:fixed!important;bottom:16px!important;right:16px!important;pointer-events:none!important;z-index:2147483647!important;width:min(410px,calc(100vw - 32px))!important;display:block!important;color-scheme:light!important;';
  const ui=host.attachShadow({mode:'open'});
  ui.innerHTML=`<style>
    *{box-sizing:border-box}.shell{pointer-events:auto;position:relative;z-index:2;font:15px/1.45 "Segoe UI",Arial,sans-serif;color:#331226;background:#fff9fc;border:1px solid #d9acc3;border-radius:15px;box-shadow:0 10px 45px #30001b35;overflow:hidden}.shell.warning{border:2px solid #b00055;background:#fff1f8}.shell:not(.expanded){width:min(280px,calc(100vw - 32px))}.shell:not(.expanded) .meta{display:none}.drag{touch-action:none;cursor:move;border:0;background:transparent;font-size:18px;padding:5px}.risk svg{width:18px;height:18px;display:block}.highlight.spam{outline-color:#005dac;background:rgba(80,175,255,.16)}.finding-row.spam{border-left-color:#005dac}button{font:inherit;cursor:pointer}button:focus-visible{outline:3px solid #005dcb;outline-offset:2px}.header{display:flex;align-items:center;gap:9px;padding:12px}.mark{display:grid;place-items:center;background:#e20074;color:white;font-weight:750;width:28px;height:30px;border-radius:7px}.heading{flex:1;min-width:0}.brand{font-size:14px;font-weight:750;color:#a80051}.count{font-size:13px;display:block}.toggle{border:0;background:transparent;color:#8a2858;padding:9px;font-size:19px}.risk{display:flex;align-items:center;justify-content:center;padding:0;line-height:1;width:29px;height:29px;flex-shrink:0;border:2px solid #181000;border-radius:50%;background:#ffe600;color:#180900;font-size:23px;font-weight:900}.risk[hidden]{display:none}.attention{animation:attention 1.8s ease-in-out infinite}@keyframes attention{50%{background:#ff9c00;box-shadow:0 0 0 5px #ffdd0080}}.body{padding:0 14px 14px;max-height:68vh;overflow:auto}.body[hidden]{display:none}h2{font-size:20px;line-height:1.25;margin:7px 0}h3{font-size:14px;margin:14px 0 8px}p{margin:9px 0}.notice{background:#fff0a0;border-left:4px solid #6c4200;padding:9px;font-size:13px}.finding-list{list-style:none;margin:0;padding:3px;max-height:220px;overflow-y:auto;overscroll-behavior:contain;border:1px solid #cba5b7;border-radius:8px;background:white}.finding-list:empty{display:none}.finding-list li+li{margin-top:5px}.finding-row{display:block;width:100%;text-align:left;border:1px solid #d1a9bc;border-left:5px solid #ad194d;border-radius:6px;background:#fff9cf;padding:9px;color:#271900}.finding-row[aria-pressed=true]{border-color:#161000;box-shadow:inset 0 0 0 2px #161000}.finding-row.previous{background:#fff9ed;border-left-style:dashed}.finding-row strong,.finding-row small{display:block}.finding-row small{font-size:12px;color:#6d4a32;margin-top:3px;overflow-wrap:anywhere}.facts{padding-left:19px;font-size:14px}.facts li{margin:6px 0}.advice{font-weight:650;color:#751443}.actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:12px}.actions button{border:1px solid #ce9db5;border-radius:7px;padding:8px 10px;background:white;color:#8e2058;font-weight:600}.actions .primary{background:#ac0058;color:white}.actions button:disabled{opacity:.5;cursor:wait}.meta{font-size:11px;color:#684658;border-top:1px solid #e1c3d2;padding:8px 13px;background:#fff9fc;overflow-wrap:anywhere}.activity{display:block;margin-bottom:3px}.highlights{position:fixed;inset:0;width:100vw;height:100vh;pointer-events:none;z-index:1;overflow:hidden}.highlight{position:absolute;pointer-events:none;box-sizing:border-box;background:rgba(255,230,0,.22);border:3px solid #171300;outline:2px solid #f00046;border-radius:3px}.highlight.previous{border-style:dashed;background:rgba(255,170,0,.13)}.highlight.selected{outline:4px solid #e20074}.highlight b{position:absolute;top:-18px;left:-3px;background:#171300;color:#fff400;font:800 12px/1.4 "Segoe UI",sans-serif;padding:1px 4px;border-radius:0 0 4px 0;white-space:nowrap}@media(prefers-reduced-motion:reduce){.attention{animation:none}}@media(max-width:450px){.body{max-height:57vh}.finding-list{max-height:175px}}
  </style><div id="highlights" class="highlights" aria-hidden="true"></div><span id="announce" role="alert" aria-atomic="true" style="position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)"></span><section class="shell" aria-label="T-Defense page monitor"><header class="header"><button id="move" class="drag" aria-label="Move panel; use arrow keys" title="Drag to move this panel">⠿</button><span class="mark">T</span><div class="heading"><span class="brand">T-Defense</span><span class="count" id="count">I'm running checks for you periodically</span></div><button type="button" id="risk-indicator" class="risk" hidden title="Open current findings"><svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M11 4h2v11h-2zM11 18h2v2h-2z"/></svg></button><button id="toggle" class="toggle" aria-label="Open all T-Defense findings" aria-expanded="false">⌄</button></header><div id="body" class="body" hidden><h2 id="title">Your page checks</h2><p id="summary">Checks use visible warning signs. An unmarked element is not verified safe.</p><p id="coverage"></p><p id="reputation">Domain reputation checks are off.</p><p id="guard-note" class="notice" hidden>Action paused. Review the findings before continuing.</p><h3 id="list-title">Marked elements</h3><ol id="findings" class="finding-list" aria-label="All marked elements"></ol><p style="font-size:12px">To trust selected exact content, preview it in the extension toolbar popup.</p><p id="finding-status" class="notice" hidden></p><ul id="facts" class="facts"></ul><p id="advice" class="advice"></p><div class="actions"><button id="scan">Check again</button><button id="pause">Pause everywhere</button><button id="continue" class="primary" hidden>Continue once</button></div></div><footer class="meta"><span id="activity" class="activity">Starting a local backend check…</span><details><summary>Check details</summary><span id="meta">No typed values or raw messages sent.</span></details></footer></section>`;
  (document.body || document.documentElement).append(host);
  const get=id=>ui.getElementById(id),shell=ui.querySelector('.shell');
  function ownEvent(event){return event.composedPath().includes(host);}
  const setText=(id,text)=>{if(get(id).textContent!==text)get(id).textContent=text;};
  const attr=(node,name,value)=>{if(node.getAttribute(name)!==value)node.setAttribute(name,value);};
  function details(){host.style.setProperty('width',expanded?'min(410px,calc(100vw - 32px))':'min(280px,calc(100vw - 32px))','important');shell.classList.toggle('expanded',expanded);if(get('body').hidden===expanded)get('body').hidden=!expanded;attr(get('toggle'),'aria-expanded',String(expanded));setText('toggle',expanded?'⌃':'⌄');clampPanel();}
  function header(){
    const connected=[...findings.values()].filter(entry=>entry.node?.isConnected).length;
    host.setAttribute('data-finding-count',String(findings.size));host.setAttribute('data-marked-count',String(connected));
    const headline=manualRequested?"I'm running checks for you periodically":connected?connected+' page element'+(connected===1?'':'s')+' need a second look':findings.size?findings.size+' previous finding'+(findings.size===1?'':'s')+' to review':host.getAttribute('data-status')==='unavailable'?'Checks unavailable — use caution':"I'm running checks for you periodically";
    if(get('count').textContent!==headline)get('count').textContent=headline;
    get('risk-indicator').hidden=!findings.size;get('risk-indicator').classList.toggle('attention',unread && !!findings.size);
    get('risk-indicator').setAttribute('aria-label',findings.size+' possible risks or previous findings. Open T-Defense to review all.');
    shell.classList.toggle('warning',!!findings.size || !!guarded || host.getAttribute('data-status')==='unavailable');
  }
  function queueHighlights(){if(active && frame===null)frame=requestAnimationFrame(drawHighlights);}
  function drawHighlights(){
    frame=null;if(!active)return;const seen=new Set();
    for(const [key,entry] of findings){
      if(!entry.node?.isConnected)continue;
      const style=getComputedStyle(entry.node);if(style.visibility==='hidden'||style.display==='none')continue;
      let rects=Array.from(entry.node.getClientRects());if(rects.length>40)rects=[entry.node.getBoundingClientRect()];
      for(const rect of rects){
        const left=Math.max(0,rect.left),top=Math.max(0,rect.top),right=Math.min(innerWidth,rect.right),bottom=Math.min(innerHeight,rect.bottom);
        if(right<=left || bottom<=top)continue;
        const markerKey=key+':'+rects.indexOf(rect);seen.add(markerKey);let box=markerNodes.get(markerKey);if(!box){box=document.createElement('div');box.append(document.createElement('b'));markerNodes.set(markerKey,box);get('highlights').append(box);}const classes='highlight'+(entry.status==='current'?'':' previous')+(selected===key?' selected':'')+(entry.row.category==='possible_spam'?' spam':'');if(box.className!==classes)box.className=classes;attr(box,'data-finding-key',key);attr(box,'data-element-id',entry.row.element_id);
        const geometry='left:'+left+'px;top:'+top+'px;width:'+(right-left)+'px;height:'+(bottom-top)+'px;';if(box.dataset.geometry!==geometry){box.dataset.geometry=geometry;box.style.cssText=geometry;}
        const badge=box.firstElementChild;if(badge.textContent!=='! '+entry.number)badge.textContent='! '+entry.number;badge.style.top=top<18?'0':'-18px';badge.style.left=top<18?'auto':'-3px';badge.style.right=top<18?'0':'auto';
      }
    }
    for(const [key,box] of markerNodes)if(!seen.has(key)){box.remove();markerNodes.delete(key);}
  }
  function statusText(entry){return entry.status==='current'?'Current finding':entry.status==='pending'?'Rechecking — previous evidence':entry.status==='removed'?'No longer on the page — previous evidence':entry.status==='outside'?'Outside this scan — previous evidence':'Changed or no longer matched — previous evidence';}
  function selectFinding(key,scroll=false){
    if(!findings.has(key))return;selected=key;expanded=true;unread=false;renderList();renderDetails();header();details();queueHighlights();
    const entry=findings.get(key);if(scroll && entry.node?.isConnected){entry.node.scrollIntoView({block:'center',inline:'nearest',behavior:'instant'});if(frame!==null)cancelAnimationFrame(frame);frame=null;drawHighlights();}
  }
  function renderList(){
    for(const [key,item] of rows)if(!findings.has(key)){item.remove();rows.delete(key);}
    for(const [key,entry] of findings){
      let item=rows.get(key);
      if(!item){item=document.createElement('li');const button=document.createElement('button');button.className='finding-row';button.dataset.findingKey=key;button.onclick=()=>selectFinding(key,true);button.append(document.createElement('strong'),document.createElement('small'),document.createElement('small'));item.append(button);rows.set(key,item);get('findings').append(item);}
      const button=item.firstElementChild;button.classList.toggle('previous',entry.status!=='current');button.classList.toggle('spam',entry.row.category==='possible_spam');attr(button,'aria-pressed',String(selected===key));attr(button,'data-element-id',entry.row.element_id);
      const text=['! '+entry.number+' · '+entry.row.title,entry.kind+' · '+entry.label,statusText(entry)];
      Array.from(button.children).forEach((child,index)=>{if(child.textContent!==text[index])child.textContent=text[index];});
    }
    setText('list-title','All findings ('+findings.size+') · click one to locate it');
  }
  function renderDetails(){
    const entry=findings.get(selected);setText('title',guarded?'Pause before you continue':entry?.row.category==='possible_spam'?'Possible promotional spam':findings.size?'Possible security risks':'Your page checks');
    const summary=entry?entry.row.title:latest?.verdict==='inconclusive'?'Some checks are incomplete. The page has not been verified.':'Unmarked elements are not verified safe. These checks can miss threats.';setText('summary',summary);
    get('finding-status').hidden=!entry || entry.status==='current';if(entry)get('finding-status').textContent=statusText(entry)+'. Use Check again for a fresh review.';
    const lines=entry?entry.row.evidence:(latest?.unknowns || []).slice(0,2);
    const factsKey=JSON.stringify(lines);if(get('facts').dataset.contentKey!==factsKey){get('facts').dataset.contentKey=factsKey;get('facts').replaceChildren(...lines.map(text=>{const li=document.createElement('li');li.textContent=text;return li;}));}
    setText('advice',entry?entry.row.next_step:'Verify unusual requests through a separate trusted contact route.');
    get('guard-note').hidden=!guarded;get('continue').hidden=!guarded;
  }
  function reputation(result){
    const rep=result.reputation || {status:'disabled',domains:[]};
    const report=rep.domains?.find(row=>row.domain===previewDomain) || rep.domains?.find(row=>['malicious','suspicious'].includes(row.status)) || rep.domains?.find(row=>row.domain===location.hostname) || rep.domains?.[0];
    const labels={local_findings:'Local checks already found warning signs. No external lookup was needed.',disabled:'VirusTotal checks are off. Enable them in the extension popup.',not_configured:'VirusTotal key is not configured. Domain reputation is unavailable.',no_public_domains:'No eligible public domains to query.',pending:'Domain check pending.',rate_limited:'VirusTotal quota reached. This domain was not checked.',unknown:'VirusTotal has no usable report for this domain.',stale:'VirusTotal report is old. Treat its status as unknown.',unavailable:'VirusTotal check unavailable.',not_checked:'This domain has not been checked.',no_reported_detections:'No reported detections. This does not establish safety.',malicious:'Reported malicious detections. Avoid this destination.',suspicious:'Reported suspicious detections. Verify independently.'};
    const repText=report?report.domain+' · '+(labels[report.status] || report.status)+(report.analyzed_at?' · report '+new Date(report.analyzed_at).toLocaleDateString():''):labels[rep.status] || 'Domain checks are incomplete; some destinations remain unchecked.';setText('reputation',repText);
  }
  function render(result,collected,reset){
    latest=result;nodes=collected.nodes;const metadata=new Map(collected.snapshot.elements.map(row=>[row.element_id,row]));
    if(true){
      const covered=new Set(nodes.values());
      for(const [key,entry] of findings){
        if(!liveNode(entry.node) || collected.ignoredNodes?.has(entry.node)){findings.delete(key);continue;}
        if(!covered.has(entry.node))continue;
        if(result.warnings.some(row=>nodes.get(row.element_id)===entry.node))continue;
        const signal=collected.snapshot.elements.find(row=>nodes.get(row.element_id)===entry.node);
        const domain=signal?.target_origin?new URL(signal.target_origin).hostname:null;
        const report=result.reputation?.domains?.find(row=>row.domain===domain);
        const needsReputation=entry.row.rules.some(rule=>rule.startsWith('virustotal-'));
        if(!needsReputation || report?.status==='no_reported_detections')findings.delete(key);
      }
    }
    const current=new Set();let fresh=0;
    for(const row of result.warnings || []){
      const node=nodes.get(row.element_id);if(!node?.isConnected)continue;
      let key=nodeKeys.get(node);if(!key){key='finding_'+(++nextNumber);nodeKeys.set(node,key);}
      const previous=findings.get(key),signature=row.element_id+':'+row.rules.join(',');
      if(!previous || previous.signature!==signature)fresh++;
      const kind=metadata.get(row.element_id)?.kind || 'element';
      findings.set(key,{row,node,kind,label:globalThis.TDefenseSnapshot.describe(node) || 'Element '+row.element_id,status:'current',number:previous?.number || Number(key.split('_')[1]),signature});current.add(key);
    }
    for(const [key,entry] of findings)if(!current.has(key)){if(!liveNode(entry.node))findings.delete(key);else entry.status=[...nodes.values()].includes(entry.node)?'changed':'outside';}
    if(!findings.has(selected))selected=findings.keys().next().value || null;
    manualRequested=false;unavailableAnnounced=false;host.setAttribute('data-warning-count',String(result.warning_count));host.setAttribute('data-status',result.status);host.setAttribute('data-scan-id',result.scan_id);
    if(fresh){unread=true;get('announce').textContent='T-Defense warning. '+fresh+' new or changed findings. Open T-Defense to review all marked elements.';}
    setText('activity','Monitoring locally · automatic checks');setText('coverage',result.status==='partial'?'Some page content or reputation checks are incomplete.':'Current inspected content checked. This is not a safety guarantee.');
    get('meta').textContent='Latest backend check '+new Date(result.scanned_at).toLocaleTimeString()+' · '+result.scan_id+' · no form values sent';
    get('continue').disabled=false;reputation(result);renderList();renderDetails();header();details();queueHighlights();
  }
  function pending(){
    host.setAttribute('data-status','pending');host.removeAttribute('data-scan-id');
    pruneCurrent();
    if(guarded)get('continue').disabled=true;renderList();renderDetails();header();queueHighlights();
  }
  function unavailable(message){
    manualRequested=false;host.setAttribute('data-status','unavailable');host.removeAttribute('data-scan-id');
    for(const entry of findings.values())if(entry.status==='current')entry.status='pending';
    get('activity').textContent='Checks unavailable — use caution';get('meta').textContent=message;get('continue').disabled=false;
    if(!unavailableAnnounced){get('announce').textContent='T-Defense checks unavailable. Previous findings are retained.';unavailableAnnounced=true;}renderList();renderDetails();header();details();queueHighlights();
  }
  function enqueue(reason,reset=false){queued={reason:reset || queued?.reset?'manual':reason,reset:reset || !!queued?.reset};}
  async function scan(reason='manual',reset=false){
    if(!active)return;
    routeScope();pruneCurrent();
    if(reset){manualRequested=true;manualGeneration++;header();}
    if(inFlight){enqueue(reason,reset);return;}
    inFlight=true;const generation=manualGeneration;const requestScope=scopeUrl;const requestTrust=trustGeneration;
    try{
      const collected=await globalThis.TDefenseSnapshot.filterTrusted(globalThis.TDefenseSnapshot.collect(reason,previewNode?.isConnected?previewNode:null),trusted);if(!active)return;if(requestTrust!==trustGeneration){enqueue('manual');return;}trustedTargets=collected.trustedTargets || new Map();
      const response=await chrome.runtime.sendMessage({type:'TDEFENSE_SNAPSHOT',snapshot:collected.snapshot});if(!active)return;
      if(!response?.ok){if(response?.code==='PAUSED'){stop();return;}if(response?.code==='RETRY'){pending();enqueue('manual',reset || manualRequested);return;}throw new Error(response?.error || 'Local page checks are unavailable.');}
      const current=await globalThis.TDefenseSnapshot.filterTrusted(globalThis.TDefenseSnapshot.collect(reason,previewNode?.isConnected?previewNode:null),trusted);
      if(requestTrust!==trustGeneration || requestScope!==scopeUrl || generation!==manualGeneration || JSON.stringify(current.snapshot)!==JSON.stringify(collected.snapshot)){pending();enqueue('mutation',reset || manualRequested);return;}
      const focused=collected.snapshot.elements.find(row=>collected.nodes.get(row.element_id)===previewNode);previewDomain=focused?.target_origin?new URL(focused.target_origin).hostname:null;
      render(response.result,collected,reset);
    }catch(error){if(active)unavailable(error.message || 'Local page checks are unavailable.');}
    finally{inFlight=false;if(active && queued){const again=queued;queued=null;setTimeout(()=>scan(again.reason,again.reset),250);}}
  }
  function schedule(reason){clearTimeout(timer);timer=setTimeout(()=>scan(reason),800);}
  function warningFor(element){
    const direct=[...findings.values()].find(entry=>entry.node===element);if(direct)return direct;
    return [...findings.values()].find(entry=>entry.node?.isConnected && entry.node.contains(element)) || null;
  }
  function localConcern(element){
    const data=globalThis.TDefenseSnapshot.collect('interaction',element);
    const signal=data.snapshot.elements.find(row=>data.nodes.get(row.element_id)===element) || data.snapshot.elements.find(row=>data.nodes.get(row.element_id)?.contains(element));
    if(!signal)return false;
    return signal.social_signals?.length || signal.download || signal.target_scheme==='data' || signal.gift_code_request || (signal.urgency && signal.sensitive_request) || (signal.email_context && signal.account_action && signal.has_link) || (signal.kind==='form' && signal.sensitive_fields.length && (location.protocol==='http:' || signal.target_origin?.startsWith('http:') || (signal.target_origin && signal.target_origin!==location.origin))) || (signal.displayed_origin && signal.target_origin && new URL(signal.displayed_origin).hostname!==new URL(signal.target_origin).hostname);
  }
  function actionSignature(element,submitter){return JSON.stringify([element.ownerDocument.baseURI,element.href,element.target,element.download,element.action,element.method,element.enctype,submitter?.formAction,submitter?.formMethod,submitter?.formTarget]);}
  function pauseAction(event,element,kind){
    const signature=actionSignature(element,event.submitter);
    if(isLocallyTrusted(element))return;
    if(bypass.has(element)){const approved=bypass.get(element);bypass.delete(element);if(approved===signature)return;}
    if(!warningFor(element) && !localConcern(element))return;
    event.preventDefault();event.stopImmediatePropagation();guarded={element,kind,submitter:event.submitter || null,signature};expanded=true;renderDetails();get('continue').disabled=true;header();details();scan('interaction');
  }
  const click=event=>{if(!active || ownEvent(event) || event.button!==0)return;const link=event.target.closest?.('a[href]');if(link)pauseAction(event,link,'link');};
  const submit=event=>{if(active && !ownEvent(event) && event.target instanceof HTMLFormElement)pauseAction(event,event.target,'form');};
  function preview(element){if(element && element!==previewNode){previewNode=element;clearTimeout(hoverTimer);hoverTimer=setTimeout(()=>scan('interaction'),400);}}
  const hover=event=>{if(!active || ownEvent(event))return;const link=event.target.closest?.('a[href]');if(link)preview(link);const entry=warningFor(event.target);if(entry){selected=nodeKeys.get(entry.node);renderList();renderDetails();queueHighlights();}};
  const focus=event=>{if(!active || ownEvent(event))return;const link=event.target.closest?.('a[href]');if(link)preview(link);const form=event.target.closest?.('form');if(form && (warningFor(form) || localConcern(form)))scan('interaction');};
  const inspect=event=>{if(!active || ownEvent(event))return;const entry=warningFor(event.target);if(entry)selectFinding(nodeKeys.get(entry.node));};
  const visible=()=>{if(!document.hidden)scan('visible');};
  const scroll=event=>{if(!ownEvent(event))queueHighlights();};
  const resize=()=>{clampPanel();queueHighlights();schedule('visible');};
  window.addEventListener('click',click,true);window.addEventListener('submit',submit,true);window.addEventListener('contextmenu',inspect,true);window.addEventListener('scroll',scroll,true);window.addEventListener('resize',resize);
  document.addEventListener('mouseover',hover,true);document.addEventListener('focusin',focus,true);document.addEventListener('visibilitychange',visible);
  const observer=new MutationObserver(changes=>{if(changes.some(change=>change.target!==host && !host.contains(change.target) && !(change.type==='childList' && [...change.addedNodes,...change.removedNodes].every(node=>node===host)))){routeScope();pending();schedule('mutation');}});
  observer.observe(document.documentElement,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['href','action','type','autocomplete','role','download','form','formaction','formmethod','formtarget','method','enctype','target','name','id','placeholder','class','hidden','style','disabled','readonly','required']});
  function liveNode(node){return !!node?.isConnected && !!node.getClientRects().length && getComputedStyle(node).visibility!=='hidden';}
  function pruneCurrent(){let changed=false;for(const [key,entry] of findings)if(!liveNode(entry.node)){findings.delete(key);changed=true;}if(changed){if(!findings.has(selected))selected=findings.keys().next().value || null;renderList();renderDetails();header();queueHighlights();}}
  function routeScope(){if(scopeUrl!==location.href){scopeUrl=location.href;manualGeneration++;findings.clear();rows.forEach(row=>row.remove());rows.clear();nodes.clear();previewNode=null;selected=null;guarded=null;latest=null;renderList();renderDetails();header();queueHighlights();return true;}return false;}
  async function refreshTrust(){const generation=++trustGeneration;trusted=new Set();trustedTargets.clear();const result=await chrome.runtime.sendMessage({type:'TDEFENSE_TRUST_LIST'});if(!result?.ok)throw new Error('Local trust settings could not be read. Elements will be checked.');if(generation===trustGeneration)trusted=new Set(result.entries);}
  function isLocallyTrusted(element){const target=globalThis.TDefenseSnapshot.reviewTarget(element);const expected=trustedTargets.get(target);return !!expected && globalThis.TDefenseSnapshot.identitySource(target)?.source===expected;}
  const hostStyle=(name,value)=>host.style.setProperty(name,value,'important');
  function movePanel(left,top){hostStyle('left',left+'px');hostStyle('top',top+'px');hostStyle('right','auto');hostStyle('bottom','auto');clampPanel();}
  function clampPanel(){if(host.style.top && host.style.top!=='auto'){const bounds=shell.getBoundingClientRect();hostStyle('left',Math.max(8,Math.min(parseFloat(host.style.left)||16,innerWidth-bounds.width-8))+'px');hostStyle('top',Math.max(8,Math.min(parseFloat(host.style.top)||16,innerHeight-bounds.height-8))+'px');}}
  function place(position){if(position)movePanel(position.x*innerWidth,position.y*innerHeight);else{hostStyle('left','auto');hostStyle('top','auto');hostStyle('right','16px');hostStyle('bottom','16px');}}
  async function savePosition(){const rect=shell.getBoundingClientRect();await chrome.runtime.sendMessage({type:'TDEFENSE_POSITION',position:{x:Math.max(0,Math.min(1,rect.left/innerWidth)),y:Math.max(0,Math.min(1,rect.top/innerHeight))}});}
  const routeEvent=()=>{if(routeScope()){pending();schedule('visible');}};
  window.addEventListener('hashchange',routeEvent);window.addEventListener('popstate',routeEvent);
  get('move').onpointerdown=event=>{if(!event.isTrusted)return;const rect=shell.getBoundingClientRect();drag={x:event.clientX,y:event.clientY,left:rect.left,top:rect.top};get('move').setPointerCapture(event.pointerId);event.preventDefault();};
  get('move').onpointermove=event=>{if(!drag)return;movePanel(drag.left+event.clientX-drag.x,drag.top+event.clientY-drag.y);};
  get('move').onpointerup=()=>{if(drag){drag=null;savePosition().catch(()=>{});}};
  get('move').onkeydown=event=>{const delta={ArrowLeft:[-20,0],ArrowRight:[20,0],ArrowUp:[0,-20],ArrowDown:[0,20]}[event.key];if(!delta)return;event.preventDefault();const rect=shell.getBoundingClientRect();movePanel(rect.left+delta[0],rect.top+delta[1]);savePosition().catch(()=>{});};
  const routeInterval=setInterval(routeEvent,1000);
  const interval=setInterval(()=>scan('periodic'),8000);
  function stop(){
    active=false;queued=null;window.removeEventListener('hashchange',routeEvent);window.removeEventListener('popstate',routeEvent);clearTimeout(timer);clearTimeout(hoverTimer);clearInterval(interval);clearInterval(routeInterval);if(frame!==null)cancelAnimationFrame(frame);observer.disconnect();
    window.removeEventListener('click',click,true);window.removeEventListener('submit',submit,true);window.removeEventListener('contextmenu',inspect,true);window.removeEventListener('scroll',scroll,true);window.removeEventListener('resize',resize);
    document.removeEventListener('mouseover',hover,true);document.removeEventListener('focusin',focus,true);document.removeEventListener('visibilitychange',visible);chrome.runtime.onMessage.removeListener(messageHandler);host.remove();markerNodes.clear();trustedTargets.clear();findings.clear();rows.clear();nodes.clear();guarded=null;delete globalThis.TDefenseGuard;
  }
  get('risk-indicator').onclick=()=>{expanded=true;unread=false;details();header();};
  get('toggle').onclick=()=>{expanded=!expanded;if(expanded)unread=false;details();header();};
  get('scan').onclick=()=>scan('manual',true);
  get('pause').onclick=()=>chrome.runtime.sendMessage({type:'TDEFENSE_PAUSE'}).catch(()=>stop());
  get('continue').onclick=()=>{const action=guarded;if(!action || !action.element.isConnected){guarded=null;renderDetails();return;}if(action.signature!==actionSignature(action.element,action.submitter)){action.signature=actionSignature(action.element,action.submitter);pending();scan('interaction');return;}guarded=null;bypass.set(action.element,action.signature);try{if(action.kind==='link')action.element.click();else action.element.requestSubmit(action.submitter?.isConnected?action.submitter:undefined);}finally{bypass.delete(action.element);renderDetails();}};
  function messageHandler(message,sender,reply){if(sender.id!==chrome.runtime.id)return false;if(message.type==='TDEFENSE_SELECTION'){const entry=findings.get(selected);globalThis.TDefenseSnapshot.identity(entry?.node).then(value=>reply(value?{fingerprint:value.fingerprint,origin:value.origin,kind:value.kind,preview:value.preview}:null));return true;}if(message.type==='TDEFENSE_TRUST_CHANGED'){refreshTrust().then(()=>scan('manual')).catch(error=>{unavailable(error.message);scan('manual');});reply({ok:true});return false;}if(message.type==='TDEFENSE_RESET_POSITION'){place(null);reply({ok:true});return false;}if(message.type==='TDEFENSE_DOCUMENT_CURRENT'){reply({active});return false;}if(message.type==='TDEFENSE_STOP'){stop();reply({ok:true});}else if(message.type==='TDEFENSE_RESTART_CHECK'){pending();scan('manual');reply({ok:true});}else if(message.type==='TDEFENSE_SCAN'){scan('manual',true);reply({ok:true});}return false;}
  details();chrome.runtime.onMessage.addListener(messageHandler);globalThis.TDefenseGuard={scan,stop};chrome.runtime.sendMessage({type:'TDEFENSE_GET_POSITION'}).then(result=>{if(active)place(result.position);}).catch(()=>{});refreshTrust().catch(()=>{}).then(()=>{if(active)scan('initial');});
})();
