(() => {
  if (globalThis.TDefenseSnapshot) return;
  const ids = new WeakMap(); let nextId = 0;
  const excluded = 'input,textarea,select,[contenteditable]:not([contenteditable="false"]),#tdefense-page-guard,script,style,noscript';
  function safeText(node, limit = 1200) {
    if (!node || node.closest?.(excluded)) return '';
    const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
    let text = ''; let count = 0;
    while (walker.nextNode() && text.length < limit && count++ < 180) {
      const parent = walker.currentNode.parentElement;
      if (!parent || parent.closest(excluded)) continue;
      const style = getComputedStyle(parent);
      if (style.display === 'none' || style.visibility === 'hidden') continue;
      text += ' ' + walker.currentNode.textContent;
    }
    return text.slice(0, limit).replace(/\s+/g, ' ').trim();
  }
  function flags(text) {
    const lower = text.toLowerCase();
    const negative = /(?:never|do not|don't|avoid)\s+(?:enter|share|send|give|provide|reveal)/.test(lower);
    const request = /(?:enter|share|send|give|provide|confirm|verify|reply with|pay)/.test(lower);
    const secret = /password|passcode|one[ -]?time|verification code|security code|card (?:number|details)|social security|ssn/.test(lower);
    return {
      urgency: /suspend|immediately|act now|final notice|within \d+|expires? (?:today|soon)|urgent|only \d+.*left/.test(lower),
      sensitive_request: request && secret && !negative,
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
  function collect(reason = 'manual') {
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
    const selector='a[href],form,[data-tdefense-message],[role="article"],[role="listitem"],[class*="message"],[class*="chat-bubble"]';
    const candidates = [...new Set(roots.flatMap(scope => [...scope.querySelectorAll(selector)]))].filter(node => !node.closest(excluded) && node.isConnected);
    const elements=[]; const nodes=new Map();
    for (const node of candidates.slice(0,200)) {
      const isForm=node.tagName==='FORM'; const isLink=node.tagName==='A';
      const kind=isForm?'form':isLink?'link':'message';
      const context=isLink?(node.closest('[data-tdefense-message],[role="article"],[role="listitem"],li,p') || node):node;
      const text=safeText(context); const localFlags=flags(text);
      const item={kind,...localFlags,has_link:isLink || !!node.querySelector('a[href]'),download:false,file_kind:'other',target_scheme:'other',target_origin:null,displayed_origin:null,sensitive_fields:[]};
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
          const url=new URL(node.getAttribute('href'),location.href);
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
    return {snapshot:{page_origin:location.origin,reason,elements,coverage:{elements_seen:Math.min(candidates.length,100000),elements_scanned:elements.length,truncated:candidates.length>200 || domTruncated,frames_unchecked:Math.min(roots.reduce((count,root)=>count+root.querySelectorAll('iframe,frame').length,0),10000)}},nodes};
  }
  globalThis.TDefenseSnapshot={collect};
})();
