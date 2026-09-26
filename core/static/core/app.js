function el(tag, cls, text){ const e=document.createElement(tag); if(cls) e.className=cls; if(text!==undefined) e.textContent=text; return e; }
function csrfToken(){ return document.querySelector('#csrf-holder [name=csrfmiddlewaretoken]').value; }

document.querySelectorAll('.tab').forEach(t=>t.addEventListener('click', ()=>{
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));
  t.classList.add('active');
  document.getElementById('panel-'+t.dataset.tab).classList.add('active');
}));

const chatlog = document.getElementById('chatlog');
const askbox = document.getElementById('askbox');
const asksend = document.getElementById('asksend');
let turns = [];

async function sendAsk(text){
  if(!text || !text.trim()) return;
  chatlog.appendChild(el('div','msg user',text));
  turns.push({role:'user', content:text});
  const botDiv = el('div','msg bot','Thinking…');
  chatlog.appendChild(botDiv);
  askbox.value=''; asksend.disabled = true;
  try{
    const res = await fetch('/api/ask', {
      method:'POST',
      headers:{'Content-Type':'application/json', 'X-CSRFToken': csrfToken()},
      body: JSON.stringify({turns})
    });
    const data = await res.json();
    if(!res.ok){ botDiv.textContent = data.error || "Something went wrong."; return; }
    botDiv.textContent = data.answer;
    turns.push({role:'assistant', content:data.answer});
  }catch(e){
    botDiv.textContent = "Network error - please try again.";
  }finally{
    asksend.disabled = false;
  }
}
asksend.addEventListener('click', ()=> sendAsk(askbox.value));
askbox.addEventListener('keydown', e=>{ if(e.key==='Enter'){ sendAsk(askbox.value); } });
document.getElementById('chips').addEventListener('click', e=>{
  if(e.target.classList.contains('chip')) sendAsk(e.target.textContent);
});

const doctext = document.getElementById('doctext');
const checksend = document.getElementById('checksend');
const checkstatus = document.getElementById('checkstatus');
const results = document.getElementById('results');

checksend.addEventListener('click', async ()=>{
  const text = doctext.value.trim();
  if(!text){ checkstatus.textContent = "Paste some contract text first."; return; }
  results.innerHTML=''; checksend.disabled = true;
  checkstatus.textContent = "Reading the document…";
  try{
    const res = await fetch('/api/analyze', {
      method:'POST',
      headers:{'Content-Type':'application/json', 'X-CSRFToken': csrfToken()},
      body: JSON.stringify({text})
    });
    const data = await res.json();
    if(!res.ok){ checkstatus.textContent = data.error || "Something went wrong."; return; }
    checkstatus.textContent = "";
    const items = data.items || [];
    if(!items.length){ checkstatus.textContent = "No clauses returned - try a longer excerpt."; }
    items.forEach(item=>{
      const risk = ['low','medium','high'].includes(item.risk) ? item.risk : 'medium';
      const card = el('div','clause '+risk);
      card.appendChild(el('span','tag', risk.toUpperCase()+' RISK'));
      card.appendChild(el('div','excerpt','"'+(item.excerpt||'')+'"'));
      card.appendChild(el('div','why', item.why||''));
      results.appendChild(card);
    });
  }catch(e){
    checkstatus.textContent = "Network error - please try again.";
  }finally{
    checksend.disabled = false;
  }
});
