const demoButtons = document.querySelectorAll('[data-demo-scenario]');
demoButtons.forEach(button => button.addEventListener('click', () => {
  const link = document.querySelector('.message[data-message-id="' + button.dataset.demoScenario + '"] a');
  if (link) link.click();
}));
const badgeNames = {likely_scam:'Likely scam',suspicious:'Suspicious',unsure:'Not sure',no_signs:'No warning signs'};
const list = document.querySelector('#messages');
const notification = document.querySelector('#risk-notification');
document.querySelector('#dismiss-notification').addEventListener('click', () => { notification.hidden = true; });
function closeExplanations(except) {
  document.querySelectorAll('.risk-wrapper').forEach(wrapper => {
    if (wrapper === except) return;
    const panel = wrapper.querySelector('.risk-details');
    if (panel) panel.hidden = true;
    wrapper.dataset.pinned = 'false';
    wrapper.querySelector('.badge').setAttribute('aria-expanded', 'false');
  });
}
document.addEventListener('pointerdown', event => closeExplanations(event.target.closest('.risk-wrapper')));
document.addEventListener('keydown', event => { if (event.key === 'Escape') closeExplanations(); });
function attachExplanation(wrapper, badge, assessment, index) {
  const details = element('div', 'risk-details'); details.hidden = true; details.id = 'risk-details-' + index; details.setAttribute('role', 'note');
  details.append(element('strong', '', badgeNames[assessment.badge] || 'Not sure'));
  const reasons = element('ul');
  for (const reason of assessment.triage.reasons) reasons.append(element('li', '', reason));
  details.append(reasons, element('p', '', 'Text scan only. Check the link for page evidence and its limits.'));
  wrapper.append(details);
  badge.disabled = false; badge.setAttribute('aria-label', (badgeNames[assessment.badge] || 'Not sure') + ': show message warning details');
  badge.setAttribute('aria-controls', details.id); badge.setAttribute('aria-expanded', 'false');
  function show() { closeExplanations(wrapper); details.hidden = false; badge.setAttribute('aria-expanded', 'true'); }
  function hide() { details.hidden = true; badge.setAttribute('aria-expanded', 'false'); }
  badge.addEventListener('mouseenter', show);
  badge.addEventListener('focus', show);
  wrapper.addEventListener('mouseleave', () => { if (wrapper.dataset.pinned !== 'true' && !wrapper.contains(document.activeElement)) hide(); });
  wrapper.addEventListener('focusout', event => { if (!wrapper.contains(event.relatedTarget)) { wrapper.dataset.pinned = 'false'; hide(); } });
  badge.addEventListener('click', () => {
    const pinned = wrapper.dataset.pinned === 'true'; wrapper.dataset.pinned = String(!pinned);
    if (pinned) hide(); else show();
  });
}
function element(tag, className, text) { const el = document.createElement(tag); if (className) el.className = className; if (text !== undefined) el.textContent = text; return el; }
async function json(url, options) { const response = await fetch(url, options); if (!response.ok) throw new Error(`Request failed (${response.status})`); return response.json(); }
async function load() {
  try {
    const health = await json('/api/health'); document.querySelector('#health').textContent = 'Backend OK';
    document.querySelector('.mode-banner').textContent = (health.demo_mode === 'live' ? 'LIVE LOCAL CHECKS' : 'REPLAY DEMO') + ' · TEMPORARY TEXT RULES';
    const flagged = [];
    const scenarios = await json('/api/scenarios'); list.replaceChildren(); document.querySelector('#count').textContent = scenarios.length;
    for (const [index, row] of scenarios.entries()) {
      const article = element('article', 'message'); article.dataset.messageId = row.message_id;
      const head = element('div','message-head'); head.append(element('span','avatar', row.sender.slice(0,1)), element('span','sender',row.sender), element('span','message-index',String(index+1).padStart(2,'0')));
      const badge = element('button','badge unsure','Checking…'); badge.type = 'button'; badge.disabled = true;
      const wrapper = element('div','risk-wrapper'); wrapper.append(badge); article.append(head,wrapper);
      // All message content uses text nodes. Links point only to opaque check tokens.
      article.append(element('p','message-text',row.text),element('span','source','SYNTHETIC PLACEHOLDER'));
      list.append(article);
      try {
        const assessment = await json('/api/assess',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message_id:row.message_id,text:row.text})});
        badge.className = 'badge ' + assessment.badge; badge.textContent = badgeNames[assessment.badge] || 'Not sure';
        attachExplanation(wrapper, badge, assessment, index);
        if (['likely_scam', 'suspicious'].includes(assessment.badge)) flagged.push({article, badge});
        const body=article.querySelector('.message-text'); body.replaceChildren();
        const pattern=/https?:\/\/[^\s<>"']+/g; let last=0; let linkIndex=0;
        for(const match of row.text.matchAll(pattern)) {
          body.append(document.createTextNode(row.text.slice(last,match.index)));
          const link=assessment.links[linkIndex++];
          if(link && /^\/check\/[A-Za-z0-9_-]+$/.test(link.check_url)) { const a=element('a','message-link',link.display_text);a.href=link.check_url;body.append(a); }
          else body.append(document.createTextNode(match[0]));
          last=match.index+match[0].length;
        }
        body.append(document.createTextNode(row.text.slice(last)));
        if (article.querySelector('a')) {
          const button = document.querySelector('[data-demo-scenario="' + row.message_id + '"]');
          if (button) button.disabled = false;
        }


      } catch { badge.textContent = 'Not sure'; badge.className = 'badge unsure'; }
    }
    if (flagged.length) {
      notification.hidden = false;
      document.querySelector('#notification-text').textContent = flagged.length + ' sample messages triggered a warning.';
      document.querySelector('#review-notification').onclick = () => {
        notification.hidden = true;
        flagged[0].article.scrollIntoView({block:'center', behavior:'instant'});
        flagged[0].badge.focus({preventScroll:true});
      };
    }
    document.querySelector('#demo-status').textContent = [...demoButtons].every(button => !button.disabled) ? 'Ready. Pick an example to begin.' : 'Some examples are unavailable. Please refresh.';
  } catch { document.querySelector('#demo-status').textContent = 'Demo unavailable. Please refresh.'; document.querySelector('#health').textContent = 'Backend DOWN'; list.replaceChildren(element('p','error','We couldn’t load the demo. Please refresh.')); }
}
load();

document.querySelector('#reset-demo').addEventListener('click', async event => {
  const button = event.currentTarget; button.disabled = true; button.textContent = 'Resetting…';
  try { await json('/api/reset'); location.reload(); }
  catch { button.disabled = false; button.textContent = 'Try reset again'; }
});
