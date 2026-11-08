const id = location.pathname.split('/').pop();
const title = document.querySelector('#verdict');
const names = {likely_scam:'Likely scam',suspicious:'Suspicious',looks_fine:'No warning signs found',inconclusive:'We couldn’t check this'};
const icons = {likely_scam:'!',suspicious:'!',looks_fine:'✓',inconclusive:'?'};
const open = document.querySelector('#open-anyway');
const recoveryToggle = document.querySelector('#recovery-toggle');
let recoveryCategory = 'general';
function items(selector, lines) { document.querySelector(selector).replaceChildren(...lines.map(text => { const li=document.createElement('li'); li.textContent=text; return li; })); }
async function json(url,options) { const r=await fetch(url,options); if(!r.ok) throw Error(String(r.status)); return r.json(); }
function render(card) {
  const fields = card.investigation?.fields_requested || [];
  recoveryCategory = fields.includes('ssn') ? 'identity' : fields.includes('card_number') ? 'payment' : fields.includes('gift_card') ? 'gift_card' : card.triage?.category || 'general';
  const verdict = names[card.verdict] ? card.verdict : 'inconclusive';
  title.textContent=names[verdict]; const icon=document.querySelector('#status-icon'); icon.className='status-icon '+verdict; icon.textContent=icons[verdict];
  document.querySelector('#confidence').textContent=card.confidence.charAt(0).toUpperCase()+card.confidence.slice(1)+' confidence · '+card.confidence_reason;
  const simulated=card.investigation?.simulated;
  const live = card.status === 'done' && card.investigation?.mode === 'live';
  const recorded = card.investigation?.mode === 'replay' && card.investigation?.recorded;
  document.querySelector('#mode').textContent = simulated ? 'SIMULATED REPLAY · hand-written example · no live browser ran' : live ? 'LIVE DECOY CHECK · local demo pages only' : recorded ? 'RECORDED REPLAY · prior local browser check · not rechecked now' : card.investigation?.mode === 'replay' ? 'REPLAY CHECK UNAVAILABLE' : 'PAGE CHECK UNAVAILABLE';
  document.querySelector('#evidence-note').textContent = simulated ? 'Illustrative findings from the demo fixture.' : live ? 'Observed by the fixed-script decoy using fake data.' : recorded ? 'Recorded evidence from our fictional pages; not a new check.' : 'There is no completed browser evidence for this link.';
  items('#evidence',card.evidence.length?card.evidence:['No page evidence is available.']);items('#unknowns',card.unknowns);items('#next-steps',card.next_steps);
  document.querySelector('#details').hidden=false;
  open.hidden=!(card.status==='done' && ['suspicious','looks_fine'].includes(verdict));
  if(!open.hidden) open.href='/api/links/'+encodeURIComponent(id)+'/open'; else open.removeAttribute('href');
  const warning = document.querySelector('#action-warning');
  warning.hidden = verdict === 'looks_fine';
  document.querySelector('#warning-title').textContent = verdict === 'inconclusive' ? 'Pause — this link could not be checked' : 'Warning — stop before you continue';
  document.querySelector('#warning-text').textContent = 'Keep attachments closed. Do not enter passwords, card details, or codes through this link.';
  if (card.investigation?.download_attempted) {
    open.hidden = true; open.removeAttribute('href');
    document.querySelector('#warning-text').textContent = 'The page tried to download an attachment. Its contents were not scanned. Keep it closed and do not enter personal information.';
  }
  recoveryToggle.hidden=false;
}
function unavailable(expired=false) { render({status:'failed',verdict:'inconclusive',confidence:'low',confidence_reason:expired?'This demo link expired. Return to Messages and tap again.':'The page check did not finish.',evidence:[],unknowns:['The page could not be checked.','Temporary rules are not the provided baseline.'],next_steps:['Go back and leave this link closed.','Contact the company using the number on your bill or card.']}); }
recoveryToggle.addEventListener('click', async () => {
  const panel = document.querySelector('#recovery'); panel.hidden = !panel.hidden;
  recoveryToggle.setAttribute('aria-expanded', String(!panel.hidden));
  if (!panel.hidden) {
    try { const recovery = await json('/api/recovery?category=' + encodeURIComponent(recoveryCategory)); items('#recovery-steps', recovery.steps); }
    catch { items('#recovery-steps', ['Contact the company using the number on your bill or card.', 'Change the password you entered.', 'Turn on two-step verification and an account PIN.', 'Report the text by forwarding it to 7726 (SPAM).']); }
    panel.scrollIntoView({block:'nearest'});
  }
});
async function run() { try { await json('/api/links/'+encodeURIComponent(id)+'/investigate',{method:'POST'}); for(let i=0;i<15;i++){const card=await json('/api/links/'+encodeURIComponent(id)+'/verdict');if(card.status!=='pending'){render(card);return;}await new Promise(resolve=>setTimeout(resolve,1000));}unavailable(); } catch(error) {unavailable(error.message==='404');} }
run();
