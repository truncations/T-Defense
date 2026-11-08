(() => {
  if (globalThis.TDefenseSnapshot) return;
  const ids = new WeakMap(); let nextId = 0;
  const excluded = 'input,textarea,select,[contenteditable]:not([contenteditable="false"]),#tdefense-page-guard,script,style,noscript';
  function safeText(node, limit = 1200, budget=180) {
    if (!node || node.closest?.(excluded)) return '';
    const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
    let text = ''; let count = 0;
    while (walker.nextNode() && text.length < limit && count++ < budget) {
      const parent = walker.currentNode.parentElement;
      if (!parent || parent.closest(excluded)) continue;
      const style = getComputedStyle(parent);
      if (style.display === 'none' || style.visibility === 'hidden') continue;
      text += ' ' + walker.currentNode.textContent;
    }
    return text.slice(0, limit).replace(/\s+/g, ' ').trim();
  }
  const messageSelector='[data-tdefense-message],[data-message-id],[data-legacy-message-id],[data-tdefense-email],.a3s,[data-list-item-id^="chat-messages"],[id^="message-content-"],[class*="messageContent"],[class*="chat-bubble"],article,[role="article"],[role="listitem"]';
  function socialFlags(text) {
    const normalized=text.normalize('NFKC').toLowerCase().replace(/[\u200B-\u200D\uFEFF]/g,'').replace(/[’‘]/g,"'");
    // Remove locally negated safety instructions, not attacker claims like "not a scam".
    const t=normalized.replace(/\b(?:never|do not|don't|avoid)\s+(?:pay(?:ing)?|send(?:ing)?|shar(?:e|ing)|connect(?:ing)?|disabl(?:e|ing)|install(?:ing)?|download(?:ing)?|run(?:ning)?|enter(?:ing)?)\b[^.!?;]{0,180}/g,' ');
    const reward=/\bfree\b|giveaway|giving away|reward|prize|gift (?:subscription|membership|code|voucher)|\bbonus\b|\byou(?:'ve| have)? won\b/.test(t);
    const account=/(?:connect|link|verify|confirm|unlock|authorize|log\s?in|sign\s?in).{0,45}(?:your |the )?(?:[a-z0-9]+ )?account|(?:scan|use).{0,25}qr.{0,25}(?:log|account|verify)/.test(t);
    const claim=/claim|redeem|unlock|collect|activate/.test(t);
    const pressure=/urgent|immediately|act now|before.{0,40}expir|offer.{0,25}expir|limited.{0,25}(?:offer|time|spots|subscriptions)|only \d+|first \d+|giving away \d+|expires?/.test(t);
    const cryptoTransfer=/(?:send|transfer|deposit).{0,30}\d+(?:[.,]\d+)?\s*(?:eth|btc|usdt|usdc|bitcoin|ethereum|crypto)\b/.test(t);
    const multiplier=/(?:receive|get|earn).{0,30}\d+(?:[.,]\d+)?\s*(?:eth|btc|usdt|usdc|bitcoin|ethereum)|\b\d{1,3}x\b|double|triple|multiply/.test(t);
    const instant=/instantly|instant|in (?:\d+ )?minutes|giveaway/.test(t);
    const money=/(?:send|pay|transfer|deposit|wire|buy).{0,45}(?:money|funds|crypto|bitcoin|fee|deposit|gift.?card|dollars|\$)|(?:pay|deposit|transfer)\s*(?:now|today|\$?\d+)/.test(t);
    const software=/crack(?:ed)?|keygen|pirated|mod menu|game cheats?|free cheats?|license bypass/.test(t);
    const install=/download|install|run|execute/.test(t);
    const disable=/(?:disable|turn off|bypass).{0,35}(?:antivirus|anti-virus|security|defender|smartscreen|protection)|ignore.{0,30}(?:browser|security).{0,20}warning|(?:paste|copy).{0,40}(?:powershell|terminal|command prompt).{0,40}(?:run|enter)|(?:run|execute).{0,30}(?:powershell|terminal|command).{0,30}(?:paste|copied)/.test(t);
    const locked=/(?:your|all).{0,25}files.{0,25}(?:locked|encrypted)|(?:locked|encrypted).{0,25}your files/.test(t);
    const recovery=/decrypt|recover|unlock|restore/.test(t);
    const returns=/guaranteed.{0,30}(?:profit|return)|risk.free.{0,25}(?:investment|profit)|double your money|\d+%\s*(?:daily|weekly|return|profit)/.test(t);
    const relationship=/love you|my love|darling|our relationship|trust me|trust our/.test(t);
    const emergency=/emergency|urgent|hospital|arrested|stranded|in trouble|immediately/.test(t);
    const secret=/don't tell|do not tell|keep.{0,20}secret|between (?:us|you and me)|hide.{0,25}(?:parents|family|friends)/.test(t);
    const support=/support|technician|security team/.test(t) && /infected|virus|compromised|hacked|account.{0,20}(?:locked|blocked)/.test(t);
    const access=/remote access|remote control|anydesk|teamviewer|install.{0,25}support|call.{0,30}(?:number|support|technician)|grant.{0,25}(?:access|control)/.test(t);
    const exposure=/(?:leak|expose|publish|release|share).{0,35}(?:private|intimate|photos|images|pictures|secrets)|dox(?:x)?|hurt you/.test(t);
    const demand=/unless|or (?:i|we) will|if you (?:don't|do not)|pay|send.{0,20}(?:more|images|photos)|do what/.test(t);
    const privateImages=/private.{0,20}(?:image|photo|picture)|intimate.{0,20}(?:image|photo)|your (?:photos|images|pictures)/.test(t);
    const personal=/private (?:chat|message)|move.{0,30}(?:chat|platform)|send.{0,25}(?:photo|picture|address|location)|meet.{0,20}(?:alone|me)|your (?:address|school)/.test(t);
    const authority=/(?:i am|i'm|we are|this is).{0,25}(?:support|staff|admin|moderator)|official.{0,20}(?:staff|support|admin)/.test(t);
    const sensitive=/password|verification code|one.time code|security code/.test(t);
    const relative=/(?:your|i'm|i am).{0,18}(?:son|daughter|mother|father|brother|sister|relative)|family emergency/.test(t);
    const signals=[];const add=(name,condition)=>{if(condition)signals.push(name);};
    add('crypto-multiplier',cryptoTransfer && multiplier && instant);
    add('reward-account-lure',reward && account && (claim || pressure));
    add('reward-pressure',reward && claim && pressure);
    add('software-bait',software && install);
    add('disable-security',disable);
    add('ransom-demand',locked && recovery && money);
    add('investment-lure',returns && money);
    add('relationship-payment-pressure',relationship && money && (emergency || secret));
    add('remote-support-pressure',support && (access || money));
    add('private-image-extortion',exposure && privateImages && demand);
    add('coercive-threat',exposure && demand);
    add('secrecy-isolation',secret && personal);
    add('authority-sensitive-request',authority && (sensitive || account || money));
    add('emergency-identity-pressure',relative && emergency && (money || sensitive));
    add('upfront-release-fee',money && /(?:release|unlock|withdraw|collect).{0,35}(?:funds|winnings|prize|reward|withdrawal)|(?:fee|deposit).{0,35}(?:release|unlock|withdraw)/.test(t));
    return signals;
  }
  function flags(text) {
    const lower = text.toLowerCase();
    const negative = /(?:never|do not|don't|avoid)\s+(?:enter|share|send|give|provide|reveal)/.test(lower);
    const request = /(?:enter|share|send|give|provide|confirm|verify|reply with|pay)/.test(lower);
    const secret = /password|passcode|one[ -]?time|verification code|security code|card (?:number|details)|social security|ssn/.test(lower);
    return {
      social_signals:socialFlags(text),
      urgency: /suspend|immediately|act now|final notice|within \d+|expires? (?:today|soon)|urgent|only \d+.*left|before.{0,40}expir|offer.{0,25}expir|giving away \d+/.test(lower),
      sensitive_request: request && secret && !negative,
      account_action: /(?:verify|confirm|update|restore|unlock|secure|review).{0,35}(?:account|billing|identity|payment)|(?:account|password).{0,25}(?:suspend|expire|reset|locked)/.test(lower),
      gift_code_request: request && /gift[ -]?card/.test(lower) && /code|pin/.test(lower) && !negative
    };
  }
  function origin(value) {
    try { const url = new URL(value, location.href); return ['http:','https:'].includes(url.protocol) ? url.origin : null; }
    catch { return null; }
  }
  function fieldKind(input) {
    // Metadata only. Never read input.value, selected options or editable text.
    if (input.disabled || input.readOnly) return null;
    const meta = [input.type,input.name,input.id,input.autocomplete,input.getAttribute('placeholder') || '', ...Array.from(input.labels || []).map(label => safeText(label,160))].join(' ').toLowerCase();
    if (input.type === 'password') return 'password';
    if (/cc-number|card.?number|card.?details|credit.?card|cvv|cvc/.test(meta)) return 'payment';
    if (/one-time-code|one.?time|\botp\b|verification.?code|security.?code/.test(meta)) return 'otp';
    if (/social.?security|\bssn\b/.test(meta)) return 'identity';
    if (/gift.?card/.test(meta)) return 'gift_card';
    return null;
  }
  function identify(node, signature) { const old=ids.get(node); if (!old || old.signature!==signature) ids.set(node,{signature,id:'td_'+(++nextId)}); return ids.get(node).id; }
  function destination(node){
    let url=new URL(node.getAttribute('href'),location.href);let wrapped=false;
    for(let depth=0;depth<2;depth++){
      if(!['www.google.com','google.com'].includes(url.hostname) || url.pathname!=='/url')break;
      const value=url.searchParams.get('q') || url.searchParams.get('url');
      if(!value)break;const next=new URL(value);if(!['http:','https:'].includes(next.protocol))break;url=next;wrapped=true;
    }return {url,wrapped};
  }
  function collect(reason = 'manual', focusNode=null) {
    const roots = [document]; let domTruncated = false;
    // Inspect open component trees within a bounded discovery budget.
    for (let i=0;i<roots.length && i<12;i++) {
      const elements=roots[i].querySelectorAll('*');
      if (elements.length>3500) domTruncated=true;
      for (const element of Array.from(elements).slice(0,3500)) {
        if (element.id==='tdefense-page-guard') continue;
        if (element.shadowRoot) {if(roots.length<12)roots.push(element.shadowRoot);else domTruncated=true;}
      }
    }
    const emailSelector='.a3s,[data-message-id],[data-legacy-message-id],[data-tdefense-email]';
    const selector='a[href],form,article,p,[data-list-item-id^="chat-messages"],[id^="message-content-"],[class*="messageContent"],[data-tdefense-message],[role="article"],[role="listitem"],[class*="message"],[class*="chat-bubble"],'+emailSelector;
    const visible=node=>node.isConnected && !!node.getClientRects().length && getComputedStyle(node).visibility!=='hidden';
    const candidates = [...new Set(roots.flatMap(scope => [...scope.querySelectorAll(selector)]))].filter(node => !node.closest(excluded) && visible(node) && !(node.tagName==='P' && node.parentElement?.closest(messageSelector)) && !(!['A','FORM','P'].includes(node.tagName) && node.querySelector(messageSelector)));
    const rank=node=>node===focusNode || (focusNode && node.contains(focusNode))?0:node.tagName==='A' && node.closest(emailSelector)?1:node.tagName==='FORM'?2:node.closest(emailSelector)?3:node.getBoundingClientRect().top>=0 && node.getBoundingClientRect().top<innerHeight?4:5;
    candidates.sort((left,right)=>rank(left)-rank(right));
    const elements=[]; const nodes=new Map();
    for (const node of candidates.slice(0,199)) {
      const isForm=node.tagName==='FORM'; const isLink=node.tagName==='A';
      const kind=isForm?'form':isLink?'link':'message';
      const context=isLink?(node.closest(messageSelector) || node.closest('li,p') || node):node;
      const text=safeText(context,4000); const localFlags=flags(text);
      const emailBody=node.closest(emailSelector);const emailText=emailBody?safeText(emailBody,4000):'';
      const commercial=/stop overpaying|programs? starting|prices? start|transparent pricing|no hidden fees|limited.time sale|buy now|special offer|\bdiscount\b|unsubscribe|weight.loss|glp.?1|medications?/.test(emailText.toLowerCase());
      const calls= emailBody?Array.from(emailBody.querySelectorAll('a')).filter(a=>/get started|shop now|buy now|order now|claim offer/i.test(safeText(a,100))).length:0;
      const emailLinks=emailBody?.querySelectorAll('a[href]').length || 0;
      const largeLinkedImage=emailBody?Array.from(emailBody.querySelectorAll('a[href] img')).some(img=>{const box=img.getBoundingClientRect();return box.width>=250 && box.height>=150;}):false;
      if(emailBody && location.hostname==='mail.google.com' && /^#spam(?:\/|$)/.test(location.hash))localFlags.social_signals.push('mail-spam-folder');
      if(emailBody && commercial && (calls>=2 || /\$\s*\d+/.test(emailText)))localFlags.social_signals.push('promotional-email');
      if(emailBody && largeLinkedImage && emailLinks && emailText.length<180)localFlags.social_signals.push('image-heavy-email');
      const item={kind,...localFlags,email_context:!!node.closest(emailSelector),wrapped_destination:false,has_link:isLink || !!node.querySelector('a[href]'),download:false,file_kind:'other',target_scheme:'other',target_origin:null,displayed_origin:null,sensitive_fields:[]};
      if (isForm) {
        const controls=Array.from(node.elements);if(controls.length>200)domTruncated=true;
        const bounded=controls.slice(0,200);
        const targets=[origin(node.action || location.href),...bounded.filter(control=>control.hasAttribute('formaction')).map(control=>origin(control.formAction))].filter(Boolean);
        item.target_origin=targets.find(value=>value.startsWith('http:')) || targets.find(value=>value!==location.origin) || targets[0] || null;
        item.sensitive_fields=[...new Set(bounded.filter(control=>control.tagName==='INPUT').map(fieldKind).filter(Boolean))];
        if (item.sensitive_fields.includes('gift_card')) item.gift_code_request=true;
      }
      if (isLink) {
        try {
          const decoded=destination(node);const url=decoded.url;item.wrapped_destination=decoded.wrapped;
          const scheme=url.protocol.slice(0,-1);item.target_scheme=['http','https','data','blob','javascript'].includes(scheme)?scheme:'other';
          item.target_origin=origin(url.href);
          const shown=safeText(node,250).match(/(?:https?:\/\/)?(?:www\.)?[a-z0-9-]+(?:\.[a-z0-9-]+)+(?:[/:?#]|$)/i);
          if (shown) item.displayed_origin=origin(/^https?:/i.test(shown[0])?shown[0]:'https://'+shown[0]);
          const file=(node.getAttribute('download') || url.pathname).split('.').pop().toLowerCase().split(/[?#]/)[0];
          const types=['exe','msi','scr','bat','cmd','ps1','js','vbs','jar','apk','dmg','iso','zip'];
          if (types.includes(file)) {item.download=true;item.file_kind=file;}
          if (node.hasAttribute('download')) item.download=true;
        } catch { /* Invalid destinations are not trusted as evidence. */ }
      }
      // Local-only text signature distinguishes recycled message nodes. Text never leaves this collector.
      const element_id=identify(node,JSON.stringify(item)+'|'+text);item.element_id=element_id;
      elements.push(item); nodes.set(element_id,node);
    }
    const pageItem={element_id:identify(document.documentElement,'page:'+location.origin),kind:'page',target_origin:location.origin};elements.push(pageItem);nodes.set(pageItem.element_id,document.documentElement);
    return {snapshot:{page_origin:location.origin,reason,elements,coverage:{elements_seen:Math.min(candidates.length+1,100000),elements_scanned:elements.length,truncated:candidates.length>199 || domTruncated,frames_unchecked:Math.min(roots.reduce((count,root)=>count+root.querySelectorAll('iframe,frame').length,0),10000)}},nodes};
  }
  function reviewTarget(node){return node?.closest(messageSelector) || node?.closest('form') || node;}
  function identitySource(node){
    const target=reviewTarget(node);if(!target || target===document.documentElement || !target.isConnected || !target.getClientRects().length)return null;
    const kind=target.tagName==='FORM'?'form':target.tagName==='A'?'link':'message';
    const walker=document.createTreeWalker(target,NodeFilter.SHOW_TEXT);let textNodes=0;while(walker.nextNode())if(++textNodes>1800)return null;
    const text=safeText(target,16385,1801);if(text.length>16384 || target.querySelectorAll('*').length>1200)return null;
    // Include resolved destinations and security-relevant metadata, but never input values.
    const forms=[...(target.tagName==='FORM'?[target]:[]),...target.querySelectorAll('form')];
    const controls=[...new Set([target,...target.querySelectorAll('a[href],form,input,button,img'),...forms.flatMap(form=>Array.from(form.elements))])];if(controls.length>300)return null;
    const attributes=controls.map(element=>[element.tagName,element.href || '',element.action || '',element.formAction || '',element.method || '',element.formMethod || '',element.target || '',element.formTarget || '',element.getAttribute('download') || '',element.getAttribute('type') || '',element.getAttribute('name') || '',element.getAttribute('autocomplete') || '',element.getAttribute('src') || '',element.getAttribute('alt') || '',element.tagName==='INPUT'?element.id:'',element.getAttribute('placeholder') || '',!!element.disabled,!!element.readOnly,!!element.required,element.enctype || '',element.getAttribute('pattern') || '',element.form?forms.indexOf(element.form):-1,...Array.from(element.labels || []).map(label=>safeText(label,16385,1801))]);
    if(attributes.some(values=>values.some(value=>typeof value==='string' && value.length>16384)))return null;
    const source=JSON.stringify([location.origin,kind,text,attributes]);if(source.length>65536)return null;
    return {source,origin:location.origin,kind,preview:safeText(target,100),target};
  }
  async function identity(node){
    const descriptor=identitySource(node);if(!descriptor || !crypto.subtle)return null;
    const hash=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(descriptor.source));
    const fingerprint=Array.from(new Uint8Array(hash),byte=>byte.toString(16).padStart(2,'0')).join('');
    return {...descriptor,fingerprint};
  }
  async function filterTrusted(collected,trusted){
    if(!trusted.size)return {...collected,ignoredNodes:new Set(),trustedTargets:new Map()};
    const cache=new Map(),ignoredNodes=new Set(),trustedTargets=new Map(),elements=[];
    for(const item of collected.snapshot.elements){
      const node=collected.nodes.get(item.element_id);const target=reviewTarget(node);
      if(item.kind==='page'){elements.push(item);continue;}
      if(!cache.has(target))cache.set(target,identity(target));
      const descriptor=await cache.get(target);
      if(descriptor && trusted.has(descriptor.fingerprint)){ignoredNodes.add(node);trustedTargets.set(descriptor.target,descriptor.source);}else elements.push(item);
    }
    const nodes=new Map(elements.map(item=>[item.element_id,collected.nodes.get(item.element_id)]));
    return {snapshot:{...collected.snapshot,elements,coverage:{...collected.snapshot.coverage,elements_scanned:elements.length,trusted_skipped:ignoredNodes.size}},nodes,ignoredNodes,trustedTargets};
  }
  globalThis.TDefenseSnapshot={collect,identity,identitySource,filterTrusted,reviewTarget,describe:node=>safeText(node,90)};
})();
