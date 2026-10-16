const status = document.getElementById('status');
document.getElementById('go').addEventListener('click', async () => {
  status.textContent = 'Checking FPL session…';
  try {
    const [tab] = await chrome.tabs.query({active:true,currentWindow:true});
    if (!tab || !tab.url || !tab.url.startsWith('https://fantasy.premierleague.com/')) throw Error('Open fantasy.premierleague.com in the active tab first.');
    const results = await chrome.scripting.executeScript({
      target:{tabId:tab.id},
      world:'MAIN',
      func: async () => {
        const entryId = 1052748;
        const response = await fetch('/api/my-team/' + entryId + '/', {credentials:'include',headers:{Accept:'application/json'}});
        if (!response.ok) throw Error('FPL account access unavailable (HTTP ' + response.status + '). Sign in and check that this is your team.');
        const d = await response.json();
        if (!Array.isArray(d.picks) || d.picks.length !== 15 || !d.transfers || typeof d.transfers.bank !== 'number') throw Error('Unexpected FPL response. Nothing exported.');
        return {schema_version:1,team_id:entryId,exported_at:new Date().toISOString(),picks:d.picks.map(p=>({element:p.element,position:p.position,selling_price:p.selling_price,purchase_price:p.purchase_price,is_captain:p.is_captain,is_vice_captain:p.is_vice_captain})),transfers:{bank:d.transfers.bank,limit:d.transfers.limit,made:d.transfers.made}};
      }
    });
    const data = results?.[0]?.result;
    if (!data) throw Error('No FPL data returned.');
    const blob = new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href=url; a.download='fpl-my-team.json'; a.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
    status.textContent='Saved fpl-my-team.json. Upload it to your Streamlit dashboard. No data was sent to this extension developer.';
  } catch(e) {status.textContent=String(e.message||e);}
});