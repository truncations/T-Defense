(() => {
  const version=chrome.runtime.getManifest().version;
  if(globalThis.TDefenseGuard?.version===version){globalThis.TDefenseGuard.scan('manual');return;}
  try{globalThis.TDefenseGuard?.stop();}catch{/* Old extension context may be detached. */}
  document.querySelectorAll('#tdefense-page-guard').forEach(node=>node.remove());
  let active=true,inFlight=false,queued=null,timer=null,latest=null,nodes=new Map();
  let expanded=false,selected=null,guarded=null,previewNode=null,previewDomain=null,hoverTimer=null;
  let manualRequested=false,manualGeneration=0,unread=false,unavailableAnnounced=false,frame=null,nextNumber=0;
  let pendingFrame=null,scheduleStarted=0;
  let trustGeneration=0,trusted=new Set(),trustedTargets=new Map(),scopeUrl=location.href,scopeToken=crypto.randomUUID(),drag=null;
  const markerNodes=new Map();
  const findings=new Map(),nodeKeys=new WeakMap(),rows=new Map(),bypass=new WeakMap();
  const host=document.createElement('div');host.id='tdefense-page-guard';host.dataset.version=version;
  host.style.cssText='all:initial!important;position:fixed!important;bottom:16px!important;right:16px!important;pointer-events:none!important;z-index:2147483647!important;width:104px!important;display:block!important;color-scheme:light!important;';
  const ui=host.attachShadow({mode:'open'});
  ui.innerHTML=`<style>
    *{box-sizing:border-box}.shell{pointer-events:auto;position:relative;z-index:2;font:15px/1.45 "Segoe UI",Arial,sans-serif;color:#331226;background:#fff9fc;border:1px solid #d9acc3;border-radius:15px;box-shadow:0 10px 45px #30001b35;overflow:hidden}.shell.warning{border:2px solid #b00055;background:#fff1f8}.shell:not(.expanded){width:min(280px,calc(100vw - 32px))}.shell:not(.expanded) .meta{display:none}.drag{touch-action:none;cursor:move;border:0;background:transparent;font-size:18px;padding:5px}.risk svg{width:18px;height:18px;display:block}.highlight.spam{outline-color:#005dac;background:rgba(80,175,255,.16)}.finding-row.spam{border-left-color:#005dac}button{font:inherit;cursor:pointer}button:focus-visible{outline:3px solid #005dcb;outline-offset:2px}.header{display:flex;align-items:center;gap:9px;padding:12px}.mark{display:grid;place-items:center;background:#e20074;color:white;font-weight:750;width:28px;height:30px;border-radius:7px}.heading{flex:1;min-width:0}.brand{font-size:14px;font-weight:750;color:#a80051}.count{font-size:13px;display:block}.toggle{border:0;background:transparent;color:#8a2858;padding:9px;font-size:19px}.risk{display:flex;align-items:center;justify-content:center;padding:0;line-height:1;width:29px;height:29px;flex-shrink:0;border:2px solid #181000;border-radius:50%;background:#ffe600;color:#180900;font-size:23px;font-weight:900}.risk[hidden]{display:none}.attention{animation:attention 1.8s ease-in-out infinite}@keyframes attention{50%{background:#ff9c00;box-shadow:0 0 0 5px #ffdd0080}}.body{padding:0 14px 14px;max-height:68vh;overflow:auto}.body[hidden]{display:none}h2{font-size:20px;line-height:1.25;margin:7px 0}h3{font-size:14px;margin:14px 0 8px}p{margin:9px 0}.notice{background:#fff0a0;border-left:4px solid #6c4200;padding:9px;font-size:13px}.finding-list{list-style:none;margin:0;padding:3px;max-height:220px;overflow-y:auto;overscroll-behavior:contain;border:1px solid #cba5b7;border-radius:8px;background:white}.finding-list:empty{display:none}.finding-list li+li{margin-top:5px}.finding-row{display:block;width:100%;text-align:left;border:1px solid #d1a9bc;border-left:5px solid #ad194d;border-radius:6px;background:#fff9cf;padding:9px;color:#271900}.finding-row[aria-pressed=true]{border-color:#161000;box-shadow:inset 0 0 0 2px #161000}.finding-row.previous{background:#fff9ed;border-left-style:dashed}.finding-row strong,.finding-row small{display:block}.finding-row small{font-size:12px;color:#6d4a32;margin-top:3px;overflow-wrap:anywhere}.facts{padding-left:19px;font-size:14px}.facts li{margin:6px 0}.advice{font-weight:650;color:#751443}.actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:12px}.actions button{border:1px solid #ce9db5;border-radius:7px;padding:8px 10px;background:white;color:#8e2058;font-weight:600}.actions .primary{background:#ac0058;color:white}.actions button:disabled{opacity:.5;cursor:wait}.meta{font-size:11px;color:#684658;border-top:1px solid #e1c3d2;padding:8px 13px;background:#fff9fc;overflow-wrap:anywhere}.activity{display:block;margin-bottom:3px}.highlights{position:fixed;inset:0;width:100vw;height:100vh;pointer-events:none;z-index:1;overflow:hidden}.highlight{position:absolute;pointer-events:none;box-sizing:border-box;background:rgba(255,230,0,.22);border:3px solid #171300;outline:2px solid #f00046;border-radius:3px}.highlight.previous{border-style:dashed;background:rgba(255,170,0,.13)}.highlight.selected{outline:4px solid #e20074}.highlight b{position:absolute;top:-18px;left:-3px;background:#171300;color:#fff400;font:800 12px/1.4 "Segoe UI",sans-serif;padding:1px 4px;border-radius:0 0 4px 0;white-space:nowrap}@media(prefers-reduced-motion:reduce){.attention{animation:none}}@media(max-width:450px){.body{max-height:57vh}.finding-list{max-height:175px}}
  
    :host{--td-paper:#fff9fc;--td-ink:#331226;--td-accent:#b00055;--td-line:#d9acc3;--td-shadow:#30001b35;--td-white:#fff;--td-alert:#fff1f8;--td-warning:#ffe600;--td-warning-ink:#181000;--td-flash:#ffb800;--td-alert-ring:#e20074}
    .rail{display:flex;align-items:center;width:104px;height:42px;pointer-events:auto;background:var(--td-paper);color:var(--td-ink);border:1px solid var(--td-line);border-radius:8px;box-shadow:0 3px 14px var(--td-shadow);font:15px/1 "Segoe UI",Arial,sans-serif}.rail .risk{border:0;border-radius:0;background:transparent;color:var(--td-accent);width:48px;height:40px;font-size:15px}.rail .drag{width:26px;padding:0;height:40px;color:var(--td-ink)}.rail .toggle{width:28px;padding:0;height:40px}.count{font-size:15px;white-space:nowrap}.shell,.shell:not(.expanded){position:fixed;right:0;bottom:16px;width:min(410px,calc(100vw - 16px));max-height:calc(100vh - 32px);border-radius:8px 0 0 8px;transform:translateX(110%);visibility:hidden;pointer-events:none;transition:transform .2s ease,visibility .2s}.shell.expanded{transform:translateX(0);visibility:visible;pointer-events:auto}.header{padding:10px}.shell .meta{display:block}.body{max-height:calc(100vh - 155px)}.rail.has-risks{background:var(--td-warning);border:2px solid var(--td-accent);box-shadow:0 0 0 3px var(--td-alert-ring)}.rail.has-risks .risk{color:var(--td-warning-ink);font-size:19px;font-weight:900}.rail .attention{animation:risk-pulse 1.5s ease-in-out infinite;font-weight:900}@keyframes risk-pulse{50%{background:var(--td-flash);box-shadow:inset 0 0 0 2px var(--td-warning-ink)}}#close{display:grid;place-items:center;flex:0 0 44px;width:44px;height:44px;padding:0;border:2px solid var(--td-line);border-radius:8px;background:var(--td-white);color:var(--td-accent);font-size:32px;line-height:1;font-weight:700}#close:hover{background:var(--td-alert)}.shell.warning{border-color:var(--td-accent)}.finding-trust{margin:3px 0 6px;border:1px solid var(--td-line);background:var(--td-white);color:var(--td-accent);border-radius:6px;font-size:12px;padding:6px}.highlights{pointer-events:none}@media(prefers-reduced-motion:reduce){.shell{transition:none}.rail .attention{animation:none}}@media(max-width:450px){.body{max-height:57vh}}
    .shell,.shell:not(.expanded){background:#fdeef3;border:0;font-family:"Segoe UI",Arial,sans-serif;color:#2a0f1c}.shell.warning{border:0;background:#fdeef3}
    .shell .header{padding:16px 16px 10px;display:flex;align-items:center;gap:10px}.shell .mark{width:40px;height:40px;border-radius:10px;background:#c92c56;color:#fff;font-size:22px;font-weight:800}.shell .brand{font-size:24px;font-weight:800;color:#6e1430}
    #close{margin-left:auto;width:44px;height:44px;border:2px solid #c92c56;border-radius:12px;background:#fff;color:#c92c56;font-size:22px;font-weight:700}
    .body{padding:0 16px 16px;display:flex;flex-direction:column;gap:12px;overflow:auto}.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}
    .banner{display:flex;gap:14px;align-items:center;padding:16px;border-radius:18px;background:#fdebc0;color:#3d2400}.banner h2{margin:0;font-size:20px;font-weight:800}.banner p{margin:2px 0 0;font-size:14px}
    .banner-icon{flex:none;display:grid;place-items:center;width:46px;height:46px;border-radius:50%;background:#7a4a00;color:#fff;font-size:26px;font-weight:800}
    .banner.danger{background:#f9d3d8;color:#4a0a10}.banner.danger .banner-icon{background:#8b1010}.banner.clear{background:#d9f0e1;color:#0d3b22}.banner.clear .banner-icon{background:#1b6b3c}
    .tabs{display:grid;grid-template-columns:1fr 1fr;gap:4px;padding:4px;background:#fff;border:1px solid #f3cad6;border-radius:14px}.tab{border:0;border-radius:10px;padding:10px;background:transparent;color:#2a0f1c;font-weight:700}.tab.on{background:#c92c56;color:#fff}
    .finding-list{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px;max-height:46vh;overflow:auto}.finding-list li{display:flex;flex-direction:column;gap:6px}
    .finding-row{display:grid!important;grid-template-columns:22px auto 1fr auto;align-items:center;gap:8px;width:100%;text-align:left;padding:12px!important;background:#fff!important;border:1px solid #f3cad6!important;border-left:1px solid #f3cad6!important;border-radius:12px!important;color:#2a0f1c}
    .finding-row[aria-pressed=true]{border:2px solid #c92c56!important}.finding-row .num{font-weight:800;color:#7a4a00}.finding-row.danger .num{color:#8b1010}.finding-row .type{font-weight:700}.finding-row .text{color:#5a3a48;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .pill{font-size:11px;font-weight:800;letter-spacing:.04em;padding:3px 9px;border-radius:999px;background:#7a4a00;color:#fff}.pill.danger{background:#8b1010}.pill.old{background:#7b6a72}
    .detail{padding:14px;border-radius:14px;background:#fdebc0;color:#3d2400}.detail.danger{background:#f9d3d8;color:#4a0a10}.detail h4{margin:0 0 6px;font-size:16px;font-weight:800}.detail .facts{margin:0 0 6px;padding-left:18px}.detail .advice,.hint{margin:4px 0;font-size:13px}
    .pair{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:6px}.solid,.ghost{min-height:44px;border-radius:12px;font-weight:700;padding:8px}.solid{border:0;background:#c92c56;color:#fff}.ghost{border:2px solid #c92c56;background:#fff;color:#c92c56}
    .detail.danger .solid{background:#8b1010}.detail.danger .ghost{border-color:#8b1010;color:#8b1010}.ghost:disabled{opacity:.5}
    .info dl{display:grid;grid-template-columns:auto 1fr;margin:0;background:#fff;border-radius:12px;overflow:hidden}.info dt,.info dd{margin:0;padding:9px 12px;border-bottom:1px solid #f3cad6;font-size:13px}.info dt{font-weight:700}
    .partial{margin:0;padding:10px 12px;border:2px dashed #e7a3b7;border-radius:12px;font-size:13px}.turn-on{color:#c92c56;font-weight:700}.empty{margin:0;font-size:13px}.notice{margin:0}
    .shell .meta{padding:0 16px 12px;font-size:12px}
    .shell .pair button.solid{border:0;background:#c92c56;color:#fff;font-size:15px}.shell .pair button.ghost{border:2px solid #c92c56;background:#fff;color:#c92c56;font-size:15px}
    .shell .detail.danger .pair button.solid{background:#8b1010}.shell .detail.danger .pair button.ghost{border-color:#8b1010;color:#8b1010}.shell .detail ul.facts{list-style:disc;padding-left:20px}.shell .detail ul.facts li{display:list-item;margin:2px 0}
</style><div id="highlights" class="highlights" aria-hidden="true"></div><span id="announce" role="alert" aria-atomic="true" style="position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)"></span><div id="rail" class="rail"><button id="move" class="drag" aria-label="Move risk tab up or down" title="Drag up or down">⠿</button><button id="risk-indicator" class="risk" title="Open detected elements"><span id="count">! 0</span></button><button id="toggle" class="toggle" aria-label="Open all T-Defense findings" aria-expanded="false">‹</button></div><section class="shell" aria-label="T-Defense page monitor"><header class="header"><span class="mark">T</span><div class="heading"><span class="brand">T-Defense</span></div><button id="close" class="toggle" aria-label="Close findings">×</button></header><div id="body" class="body" hidden><div id="banner" class="banner caution"><span id="banner-icon" class="banner-icon" aria-hidden="true">!</span><div><h2 id="title">Your page checks</h2><p id="summary">Checks use visible warning signs. An unmarked element is not verified safe.</p></div></div><p id="guard-note" class="notice" hidden>Action paused. Review the findings before continuing.</p><div class="tabs" role="tablist"><button id="tab-findings" class="tab on" role="tab" aria-selected="true">Findings <span id="list-count">0</span></button><button id="tab-info" class="tab" role="tab" aria-selected="false">Scan info</button></div><div id="pane-findings" class="pane"><h3 id="list-title" class="sr">Marked elements</h3><ol id="findings" class="finding-list" aria-label="All marked elements"></ol><p id="empty" class="empty">No findings on this page yet. Unmarked elements are not verified safe.</p></div><div id="detail" class="detail caution" hidden><h4 id="detail-title">Treat with care</h4><ul id="facts" class="facts"></ul><p id="advice" class="advice"></p><p class="hint">Check it yourself: hover the link to read its real address.</p><p id="finding-status" class="notice" hidden></p><div class="pair"><button id="locate-finding" class="solid">Locate</button><button id="trust-action" class="ghost finding-trust" disabled>Trust</button></div></div><div id="pane-info" class="pane info" hidden><dl><dt>Scan result</dt><dd id="info-result">Waiting for a check</dd><dt>Scope</dt><dd>This page only</dd><dt>Page content</dt><dd id="coverage">Checked</dd><dt>Reputation checks</dt><dd id="reputation">Domain reputation checks are off.</dd><dt>Monitoring</dt><dd>Local, automatic</dd></dl><p class="hint">Tap Check again for a fresh review. Turn on VirusTotal in the extension popup for a deeper check.</p></div><p id="partial" class="partial"><b>Partial scan:</b> <span id="partial-text">VirusTotal is off.</span> <span class="turn-on">Turn on in the toolbar popup</span></p><div class="pair actions"><button id="scan" class="solid">Check again</button><button id="pause" class="ghost">Pause everywhere</button><button id="continue" class="solid" hidden>Continue once</button></div></div><footer class="meta"><span id="activity" class="activity">Starting a local backend check…</span><details><summary>Check details</summary><span id="meta">No typed values or raw messages sent.</span></details></footer></section>`;
  (document.body || document.documentElement).append(host);
  const get=id=>ui.getElementById(id),shell=ui.querySelector('.shell');
  function ownEvent(event){return event.composedPath().includes(host);}
  const setText=(id,text)=>{if(get(id).textContent!==text)get(id).textContent=text;};
  const attr=(node,name,value)=>{if(node.getAttribute(name)!==value)node.setAttribute(name,value);};
  function details(){shell.classList.toggle('expanded',expanded);if(get('body').hidden===expanded)get('body').hidden=!expanded;attr(get('toggle'),'aria-expanded',String(expanded));setText('toggle',expanded?'›':'‹');clampPanel();}
  function header(){
    const connected=[...findings.values()].filter(entry=>entry.node?.isConnected).length;
    host.setAttribute('data-finding-count',String(findings.size));host.setAttribute('data-marked-count',String(connected));
    setText('count','! '+findings.size);
    attr(get('count'),'title',host.getAttribute('data-status')==='unavailable'?'Checks unavailable — use the extension toolbar':'Detected elements to review');
    get('risk-indicator').hidden=false;get('risk-indicator').classList.toggle('attention',!!findings.size);get('rail').classList.toggle('has-risks',!!findings.size);
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
  function level(entry){return entry.row.severity==='high'&&entry.row.category!=='possible_spam'?'danger':'caution';}
  function pill(entry){return entry.status!=='current'?'EARLIER':level(entry)==='danger'?'DANGEROUS':'CAUTION';}
  const detailNode=get('detail'),flag=(node,prop,value)=>{if(node[prop]!==value)node[prop]=value;};
  function renderList(){
    for(const [key,item] of rows)if(!findings.has(key)){if(item.contains(detailNode))get('pane-findings').append(detailNode);item.remove();rows.delete(key);}
    for(const [key,entry] of findings){
      let item=rows.get(key);
      if(!item){item=document.createElement('li');const button=document.createElement('button');button.className='finding-row';button.dataset.findingKey=key;button.onclick=()=>selectFinding(key,true);for(const name of ['num','type','text','pill']){const span=document.createElement('span');span.className=name;button.append(span);}item.append(button);rows.set(key,item);get('findings').append(item);}
      const button=item.firstElementChild,tone=level(entry);button.classList.toggle('previous',entry.status!=='current');button.classList.toggle('spam',entry.row.category==='possible_spam');button.classList.toggle('danger',tone==='danger');attr(button,'aria-pressed',String(selected===key));attr(button,'data-element-id',entry.row.element_id);attr(button,'data-kind',entry.kind);attr(button,'title',entry.row.title+' — '+statusText(entry));
      const kind=entry.kind.charAt(0).toUpperCase()+entry.kind.slice(1);const text=[String(entry.number),kind,entry.label,pill(entry)];
      Array.from(button.children).forEach((child,index)=>{if(child.textContent!==text[index])child.textContent=text[index];});
      attr(button.lastElementChild,'class','pill'+(entry.status!=='current'?' old':tone==='danger'?' danger':''));
    }
    const detail=detailNode,owner=selected&&rows.get(selected);if(owner){if(detail.parentNode!==owner)owner.append(detail);flag(detail,'hidden',false);}else{flag(detail,'hidden',true);if(detail.parentNode!==get('pane-findings'))get('pane-findings').append(detail);}
    setText('list-count',String(findings.size));flag(get('empty'),'hidden',!!findings.size);
    setText('list-title','All findings ('+findings.size+') · click one to see why');
  }
  function renderDetails(){
    const entry=findings.get(selected);setText('title',guarded?'Pause before you continue':entry?.row.category==='possible_spam'?'Possible promotional spam':findings.size?'Possible security risks':'Your page checks');
    const summary=entry?entry.row.title:latest?.verdict==='inconclusive'?'Some checks are incomplete. The page has not been verified.':'Unmarked elements are not verified safe. These checks can miss threats.';setText('summary',summary);
    flag(get('finding-status'),'hidden',!entry || entry.status==='current');if(entry)setText('finding-status',statusText(entry)+'. Use Check again for a fresh review.');
    const lines=entry?entry.row.evidence:(latest?.unknowns || []).slice(0,2);
    const factsKey=JSON.stringify(lines);if(get('facts').dataset.contentKey!==factsKey){get('facts').dataset.contentKey=factsKey;get('facts').replaceChildren(...lines.map(text=>{const li=document.createElement('li');li.textContent=text;return li;}));}
    setText('advice',entry?entry.row.next_step:'Verify unusual requests through a separate trusted contact route.');
    flag(get('trust-action'),'disabled',!entry?.node?.isConnected);
    get('guard-note').hidden=!guarded;get('continue').hidden=!guarded;
    const danger=[...findings.values()].some(row=>row.status==='current'&&level(row)==='danger'),tone=guarded||danger?'danger':findings.size?'caution':'clear';
    attr(get('banner'),'class','banner '+tone);setText('banner-icon',tone==='danger'?'✕':tone==='clear'?'✓':'!');
    const detailTone=entry?level(entry):'caution';attr(get('detail'),'class','detail '+detailTone);setText('detail-title',detailTone==='danger'?'Do not click this':'Treat with care');
    setText('info-result',!latest?'Waiting for a check':entry&&entry.status!=='current'?'From an earlier scan':'Latest scan');
  }
  function reputation(result){
    const rep=result.reputation || {status:'disabled',domains:[]};
    const report=rep.domains?.find(row=>row.domain===previewDomain) || rep.domains?.find(row=>['malicious','suspicious'].includes(row.status)) || rep.domains?.find(row=>row.domain===location.hostname) || rep.domains?.[0];
    const labels={local_findings:'Local checks already found warning signs. No external lookup was needed.',disabled:'VirusTotal checks are off. Enable them in the extension popup.',not_configured:'VirusTotal key is not configured. Domain reputation is unavailable.',no_public_domains:'No eligible public domains to query.',pending:'Domain check pending.',rate_limited:'VirusTotal quota reached. This domain was not checked.',unknown:'VirusTotal has no usable report for this domain.',stale:'VirusTotal report is old. Treat its status as unknown.',unavailable:'VirusTotal check unavailable.',not_checked:'This domain has not been checked.',no_reported_detections:'No reported detections. This does not establish safety.',malicious:'Reported malicious detections. Avoid this destination.',suspicious:'Reported suspicious detections. Verify independently.'};
    const repText=report?report.domain+' · '+(labels[report.status] || report.status)+(report.analyzed_at?' · report '+new Date(report.analyzed_at).toLocaleDateString():''):labels[rep.status] || 'Domain checks are incomplete; some destinations remain unchecked.';setText('reputation',repText);const off=['disabled','not_configured'].includes(rep.status);get('partial').hidden=!off&&!result.coverage?.truncated;setText('partial-text',off?(rep.status==='disabled'?'VirusTotal is off.':'VirusTotal key is not set up.'):'Part of this page was not checked.');
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
    if(host.getAttribute('data-status')!=='unavailable')host.setAttribute('data-status','pending');host.removeAttribute('data-scan-id');
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
    if(!active || (document.hidden && ['periodic','mutation','visible'].includes(reason)))return;
    routeScope();pruneCurrent();
    if(reset){manualRequested=true;manualGeneration++;header();}
    if(inFlight){enqueue(reason,reset);return;}
    inFlight=true;const requestRevision=globalThis.TDefenseSnapshot.revision;const generation=manualGeneration;const requestScope=scopeUrl;const requestTrust=trustGeneration;
    try{
      const collected=await globalThis.TDefenseSnapshot.filterTrusted(await globalThis.TDefenseSnapshot.collectAsync(reason,reason==='interaction' && previewNode?.isConnected?previewNode:null),trusted);if(!active)return;if(requestTrust!==trustGeneration || requestRevision!==globalThis.TDefenseSnapshot.revision || requestScope!==location.href){enqueue('manual');return;}trustedTargets=collected.trustedTargets || new Map();
      let response=await chrome.runtime.sendMessage({type:'TDEFENSE_SNAPSHOT',snapshot:collected.snapshot,revision:requestRevision,scopeToken});if(!active)return;
      if(response?.code==='TRANSIENT'){await new Promise(resolve=>setTimeout(resolve,600));if(!active)return;if(requestTrust!==trustGeneration || requestScope!==location.href || generation!==manualGeneration){enqueue('mutation');return;}response=await chrome.runtime.sendMessage({type:'TDEFENSE_SNAPSHOT',snapshot:collected.snapshot,revision:requestRevision,scopeToken});if(!active)return;}
      if(!response?.ok){if(response?.code==='PAUSED'){stop();return;}if(response?.code==='RETRY'){pending();enqueue('manual',reset || manualRequested);return;}throw new Error(response?.error || 'Local page checks are unavailable.');}
      if(requestTrust!==trustGeneration || requestScope!==location.href || generation!==manualGeneration || requestRevision!==globalThis.TDefenseSnapshot.revision){pending();enqueue('mutation',reset || manualRequested);return;}
      const focused=collected.snapshot.elements.find(row=>collected.nodes.get(row.element_id)===previewNode);previewDomain=focused?.target_origin?new URL(focused.target_origin).hostname:null;
      render(response.result,collected,reset);
    }catch(error){if(active){if(requestScope!==location.href || generation!==manualGeneration || requestTrust!==trustGeneration){routeScope();enqueue('mutation');}else unavailable(error.message || 'Local page checks are unavailable.');}}
    finally{inFlight=false;if(active && queued){const again=queued;queued=null;setTimeout(()=>scan(again.reason,again.reset),250);}}
  }
  function schedule(reason){if(!scheduleStarted)scheduleStarted=performance.now();clearTimeout(timer);timer=setTimeout(()=>{scheduleStarted=0;scan(reason);},Math.max(0,Math.min(800,1600-(performance.now()-scheduleStarted))));}
  function warningFor(element){
    const direct=[...findings.values()].find(entry=>entry.node===element);if(direct)return direct;
    return [...findings.values()].find(entry=>entry.node?.isConnected && entry.node.contains(element)) || null;
  }
  function localConcern(element){
    const data=globalThis.TDefenseSnapshot.collect('interaction',element);
    const signal=data.snapshot.elements.find(row=>data.nodes.get(row.element_id)===element) || data.snapshot.elements.find(row=>data.nodes.get(row.element_id)?.contains(element));
    if(!signal)return false;
    if(signal.kind==='link' && globalThis.TDefenseSnapshot.brandLookalike(signal.target_origin))return true;
    return signal.social_signals?.length || signal.download || signal.target_scheme==='data' || signal.gift_code_request || (signal.urgency && signal.sensitive_request) || (signal.email_context && signal.account_action && signal.has_link) || (signal.kind==='form' && signal.sensitive_fields.length && (location.protocol==='http:' || signal.target_origin?.startsWith('http:') || (signal.target_origin && signal.target_origin!==location.origin))) || (signal.displayed_origin && signal.target_origin && new URL(signal.displayed_origin).hostname!==new URL(signal.target_origin).hostname);
  }
  function actionSignature(element,submitter){return JSON.stringify([element.ownerDocument.baseURI,element.href,element.target,element.download,element.action,element.method,element.enctype,submitter?.formAction,submitter?.formMethod,submitter?.formTarget]);}
  function pauseAction(event,element,kind){
    const signature=actionSignature(element,event.submitter);
    if(isLocallyTrusted(element))return;
    if(bypass.has(element)){const approved=bypass.get(element);bypass.delete(element);if(approved===signature)return;}
    if(!warningFor(element) && !localConcern(element))return;
    event.preventDefault();event.stopImmediatePropagation();if(!host.isConnected)(document.body || document.documentElement).append(host);guarded={element,kind,submitter:event.submitter || null,signature,download:kind==='link'?downloadIntent(element):null};previewNode=element;expanded=true;renderDetails();get('continue').disabled=true;header();details();scan('interaction');
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
  const observer=new MutationObserver(changes=>{const relevant=changes.filter(change=>change.target!==host && !host.contains(change.target) && !(change.type==='childList' && [...change.addedNodes,...change.removedNodes].every(node=>node===host)));if(!relevant.length)return;globalThis.TDefenseSnapshot.invalidate(relevant);routeScope();if(pendingFrame===null)pendingFrame=requestAnimationFrame(()=>{pendingFrame=null;if(active)pending();});schedule('mutation');});
  observer.observe(document.documentElement,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['href','action','type','autocomplete','role','download','form','formaction','formmethod','formtarget','method','enctype','target','name','id','placeholder','class','hidden','style','disabled','readonly','required']});
  function liveNode(node){return !!node?.isConnected && !!node.getClientRects().length && getComputedStyle(node).visibility!=='hidden';}
  function pruneCurrent(){let changed=false;for(const [key,entry] of findings)if(!liveNode(entry.node)){findings.delete(key);changed=true;}if(changed){if(!findings.has(selected))selected=findings.keys().next().value || null;renderList();renderDetails();header();queueHighlights();}}
  function routeScope(){if(scopeUrl!==location.href){scopeUrl=location.href;scopeToken=crypto.randomUUID();manualGeneration++;globalThis.TDefenseSnapshot.reset();findings.clear();rows.forEach(row=>row.remove());rows.clear();nodes.clear();previewNode=null;selected=null;guarded=null;latest=null;expanded=false;place(null);details();renderList();renderDetails();header();queueHighlights();return true;}return false;}
  async function refreshTrust(){const generation=++trustGeneration;trusted=new Set();trustedTargets.clear();const result=await chrome.runtime.sendMessage({type:'TDEFENSE_TRUST_LIST'});if(!result?.ok)throw new Error('Local trust settings could not be read. Elements will be checked.');if(generation===trustGeneration)trusted=new Set(result.entries);}
  function isLocallyTrusted(element){const target=globalThis.TDefenseSnapshot.reviewTarget(element);const expected=trustedTargets.get(target);return !!expected && globalThis.TDefenseSnapshot.identitySource(target)?.source===expected;}
  const hostStyle=(name,value)=>host.style.setProperty(name,value,'important');
  function movePanel(left,top){hostStyle('left','auto');hostStyle('right','16px');hostStyle('top',top+'px');hostStyle('bottom','auto');clampPanel();}
  function clampPanel(){if(host.style.top && host.style.top!=='auto'){const bounds=get('rail').getBoundingClientRect();hostStyle('top',Math.max(8,Math.min(parseFloat(host.style.top)||16,innerHeight-bounds.height-8))+'px');}}
  function place(){hostStyle('left','auto');hostStyle('top','auto');hostStyle('right','16px');hostStyle('bottom','16px');}
  const routeEvent=()=>{if(routeScope()){pending();schedule('visible');}};
  window.addEventListener('hashchange',routeEvent);window.addEventListener('popstate',routeEvent);
  get('move').onpointerdown=event=>{if(!event.isTrusted)return;const rect=get('rail').getBoundingClientRect();drag={y:event.clientY,top:rect.top};get('move').setPointerCapture(event.pointerId);event.preventDefault();};
  get('move').onpointermove=event=>{if(drag)movePanel(0,drag.top+event.clientY-drag.y);};
  get('move').onpointerup=get('move').onpointercancel=()=>{drag=null;};
  get('move').onkeydown=event=>{const delta={ArrowUp:-20,ArrowDown:20}[event.key];if(delta===undefined)return;event.preventDefault();movePanel(0,get('rail').getBoundingClientRect().top+delta);};
  const routeInterval=setInterval(routeEvent,1000);
  const interval=setInterval(()=>{if(!document.hidden)scan('periodic');},8000);
  function stop(){
    active=false;queued=null;if(pendingFrame!==null)cancelAnimationFrame(pendingFrame);globalThis.TDefenseSnapshot.reset();window.removeEventListener('hashchange',routeEvent);window.removeEventListener('popstate',routeEvent);clearTimeout(timer);clearTimeout(hoverTimer);clearInterval(interval);clearInterval(routeInterval);if(frame!==null)cancelAnimationFrame(frame);observer.disconnect();
    window.removeEventListener('click',click,true);window.removeEventListener('submit',submit,true);window.removeEventListener('contextmenu',inspect,true);window.removeEventListener('scroll',scroll,true);window.removeEventListener('resize',resize);
    document.removeEventListener('mouseover',hover,true);document.removeEventListener('focusin',focus,true);document.removeEventListener('visibilitychange',visible);try{chrome.runtime.onMessage.removeListener(messageHandler);}catch{/* Extension reloaded. */}host.remove();markerNodes.clear();trustedTargets.clear();findings.clear();rows.clear();nodes.clear();guarded=null;delete globalThis.TDefenseGuard;
  }
  get('close').onclick=()=>{expanded=false;details();};
  get('risk-indicator').onclick=()=>{expanded=true;unread=false;details();header();};
  get('toggle').onclick=()=>{expanded=!expanded;if(expanded)unread=false;details();header();};
  get('trust-action').onclick=async event=>{if(!event.isTrusted || !findings.get(selected)?.node?.isConnected)return;try{const response=await chrome.runtime.sendMessage({type:'TDEFENSE_OPEN_TRUST'});get('finding-status').textContent=response?.ok?'Review and confirm this selection in the genuine extension toolbar.':'Open the genuine extension toolbar to preview and confirm this selected content.';}catch{get('finding-status').textContent='Open the genuine extension toolbar to confirm this selected content.';}get('finding-status').hidden=false;};
  function showTab(info){get('pane-info').hidden=!info;get('pane-findings').hidden=info;get('tab-info').classList.toggle('on',info);get('tab-findings').classList.toggle('on',!info);attr(get('tab-info'),'aria-selected',String(info));attr(get('tab-findings'),'aria-selected',String(!info));}
  get('tab-findings').onclick=()=>showTab(false);get('tab-info').onclick=()=>showTab(true);
  get('locate-finding').onclick=()=>{if(selected)selectFinding(selected,true);};
  get('scan').onclick=()=>scan('manual',true);
  get('pause').onclick=()=>chrome.runtime.sendMessage({type:'TDEFENSE_PAUSE'}).catch(()=>stop());
  // Sites such as chat apps create a temporary blob link, click it, then remove/revoke it at once.
  // Capture the file while the link is still valid so "Continue anyway" can still deliver it.
  function downloadIntent(element){
    const href=element.href || '';const scheme=href.split(':')[0];
    if(!element.hasAttribute('download') && scheme!=='blob' && scheme!=='data')return null;
    let file=null;if(scheme==='blob' || scheme==='data'){file=fetch(href).then(response=>response.ok?response.blob():null).catch(()=>null);}
    return {href,name:element.getAttribute('download') || '',target:element.target || '',file};
  }
  async function replayLink(action){
    const intent=action.download || {href:action.element.href,name:null,target:action.element.target || '',file:null};
    let href=intent.href,temporary=null;
    if(intent.file){const blob=await intent.file;if(blob){temporary=URL.createObjectURL(blob);href=temporary;}}
    const anchor=document.createElement('a');anchor.href=href;if(intent.name!==null)anchor.download=intent.name;if(intent.target)anchor.target=intent.target;anchor.rel='noopener';anchor.style.display='none';
    (document.body || document.documentElement).append(anchor);bypass.set(anchor,actionSignature(anchor,null));
    try{anchor.click();}finally{bypass.delete(anchor);anchor.remove();if(temporary)setTimeout(()=>URL.revokeObjectURL(temporary),60000);}
  }
  get('continue').onclick=()=>{const action=guarded;if(action?.kind==='link' && (action.download || !action.element.isConnected)){guarded=null;replayLink(action).catch(()=>{}).finally(renderDetails);return;}if(!action || !action.element.isConnected){guarded=null;renderDetails();return;}if(action.signature!==actionSignature(action.element,action.submitter)){action.signature=actionSignature(action.element,action.submitter);pending();scan('interaction');return;}guarded=null;bypass.set(action.element,action.signature);try{if(action.kind==='link')action.element.click();else action.element.requestSubmit(action.submitter?.isConnected?action.submitter:undefined);}finally{bypass.delete(action.element);renderDetails();}};
  function messageHandler(message,sender,reply){if(sender.id!==chrome.runtime.id)return false;if(message.type==='TDEFENSE_REVIEW'){const entry=[...findings.entries()].find(([,entry])=>entry.row.element_id===message.elementId);if(entry){selectFinding(entry[0],host.isConnected);reply({ok:true});}else reply({ok:false});return false;}if(message.type==='TDEFENSE_SELECTION'){const entry=findings.get(selected);globalThis.TDefenseSnapshot.identity(entry?.node).then(value=>reply(value?{fingerprint:value.fingerprint,origin:value.origin,kind:value.kind,preview:value.preview}:null));return true;}if(message.type==='TDEFENSE_TRUST_CHANGED'){refreshTrust().then(()=>scan('manual')).catch(error=>{unavailable(error.message);scan('manual');});reply({ok:true});return false;}if(message.type==='TDEFENSE_RESET_POSITION'){place();reply({ok:true});return false;}if(message.type==='TDEFENSE_DOCUMENT_CURRENT'){reply({active:active && (message.revision===undefined || message.revision===globalThis.TDefenseSnapshot.revision) && (!message.scopeToken || message.scopeToken===scopeToken) && scopeUrl===location.href});return false;}if(message.type==='TDEFENSE_STOP'){stop();reply({ok:true});}else if(message.type==='TDEFENSE_RESTART_CHECK'){pending();scan('manual');reply({ok:true});}else if(message.type==='TDEFENSE_SCAN'){scan('manual',true);reply({ok:true});}return false;}
  place();details();chrome.runtime.onMessage.addListener(messageHandler);globalThis.TDefenseGuard={version,scan,stop};refreshTrust().catch(()=>{}).then(()=>{if(active)scan('initial');});
})();
