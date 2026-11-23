"""MyIQ local onboarding POC. Run: python myiq_onboarding_poc.py
Local-only prototype; no Microsoft 365 access or production authentication.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import json, secrets, datetime, threading, webbrowser

HOST, PORT = '127.0.0.1', 8765
STORE = Path.home() / '.myiq-onboarding-poc'
STORE.mkdir(exist_ok=True)
TOKEN = secrets.token_urlsafe(24)

PAGE = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MyIQ | Onboarding</title><style>
:root{font-family:Segoe UI,Arial,sans-serif;color:#1b2435;background:#f4f6fb}*{box-sizing:border-box}body{margin:0}.shell{max-width:1050px;margin:28px auto;padding:0 20px}.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px}.brand{font-size:26px;font-weight:750;color:#3730a3}.tag{background:#e8e7ff;color:#4338ca;padding:7px 13px;border-radius:30px;font-size:12px;font-weight:700}.hero{background:linear-gradient(120deg,#312e81,#6366f1);color:white;padding:30px;border-radius:18px;margin-bottom:20px}.hero h1{margin:0 0 8px;font-size:30px}.hero p{margin:0;color:#e4e5ff}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.card{background:white;border:1px solid #e5e8f1;border-radius:16px;padding:22px;margin-bottom:18px;box-shadow:0 3px 15px #1f2b5010}.card h2{font-size:18px;margin:0 0 7px}.muted{font-size:13px;color:#68748a;margin-bottom:18px}.field{margin:12px 0}label{display:block;font-size:13px;font-weight:650;margin-bottom:6px}input[type=text],input[type=date],textarea{width:100%;padding:11px;border:1px solid #d5dbe8;border-radius:9px;font:inherit}textarea{min-height:80px;resize:vertical}.tabs{display:flex;gap:8px;flex-wrap:wrap;margin:15px 0}.tabs button{border:1px solid #dbe0ed;background:#f7f8fc;color:#45526c;border-radius:25px;padding:9px 15px;cursor:pointer}.tabs button.active{background:#e8e7ff;color:#3730a3;border-color:#a5a2ff}.item{display:flex;gap:12px;align-items:flex-start;padding:13px 10px;border-bottom:1px solid #edf0f6}.item input{width:18px;height:18px;accent-color:#4f46e5}.item strong{display:block}.item small{color:#68748a;display:block;margin-top:3px}.actions{display:flex;gap:10px;flex-wrap:wrap;margin:15px 0}.btn{padding:12px 20px;border:0;border-radius:10px;background:#4f46e5;color:white;font-weight:700;cursor:pointer}.secondary{background:#eef0f8;color:#3e4760}.status{padding:12px;border-radius:10px;background:#eef7f0;color:#176534;display:none}.notice{background:#fff8e6;color:#775514;padding:12px;border-radius:10px;font-size:13px;margin:12px 0}@media(max-width:700px){.grid{grid-template-columns:1fr}.hero h1{font-size:24px}}
</style></head><body><div class="shell"><header class="top"><div class="brand">✦ MyIQ <span style="font-size:12px;color:#7b86a0">DEV</span></div><span class="tag">ONBOARDING POC</span></header><section class="hero"><h1>Make MyIQ yours.</h1><p>Review your profile, choose what matters, and decide what MyIQ should prioritize.</p></section><div class="notice">Local demonstration only. Cowork/Teams/Outlook data is not connected yet. Suggested entries below are synthetic examples. Do not enter sensitive personal data.</div><div class="grid"><section class="card"><h2>1. Your profile</h2><p class="muted">Review or complete these fields.</p><div class="field"><label>Name</label><input id="name" type="text" placeholder="Your name"></div><div class="field"><label>Work email</label><input id="email" type="text" placeholder="name@organization.com"></div><div class="field"><label>Job title</label><input id="title" type="text"></div><div class="field"><label>Manager</label><input id="manager" type="text"></div><div class="field"><label>Department / team</label><input id="team" type="text"></div><div class="field"><label>Location</label><input id="location" type="text"></div><div class="field"><label>Professional aspirations</label><textarea id="aspirations" placeholder="What are you working toward?"></textarea></div><div class="field"><label>Preferred response style</label><textarea id="style" placeholder="e.g., concise, practical, with next steps"></textarea></div></section><section class="card"><h2>2. What matters to you</h2><p class="muted">Select or deselect suggestions. Add your own items below.</p><div class="tabs" id="tabs"></div><div id="items"></div><div class="field"><label>Add an item to the selected category</label><input id="newItem" type="text" placeholder="Name or goal"></div><button class="btn secondary" onclick="addItem()">+ Add item</button><div class="field"><label>Additional context</label><textarea id="notes" placeholder="Anything else MyIQ should know"></textarea></div></section></div><section class="card"><h2>3. Confirm your onboarding</h2><p class="muted">Your selections are stored in a local JSON file for this POC. You can export a copy.</p><div class="actions"><button class="btn" onclick="submitForm()">Save my onboarding</button><button class="btn secondary" onclick="exportJson()">Export JSON</button><button class="btn secondary" onclick="skip()">Skip for now</button></div><div class="status" id="status"></div></section></div><script>
const cats=['People','Projects','Goals','Tasks','Topics'];let active='People';let suggestions={People:[{name:'Alex Rivera',selected:true,source:'Sample Teams discussion'},{name:'Priya Nair',selected:false,source:'Sample Outlook email'}],Projects:[{name:'Project Atlas',selected:true,source:'Sample meeting'},{name:'Project Nova',selected:false,source:'Sample email'}],Goals:[{name:'Deliver first prototype',selected:true,source:'Sample goal'}],Tasks:[{name:'Review architecture',selected:false,source:'Sample follow-up'}],Topics:[{name:'Knowledge management',selected:true,source:'Sample discussion'}]};
function render(){document.getElementById('tabs').innerHTML=cats.map(c=>`<button class="${c===active?'active':''}" onclick="active='${c}';render()">${c} (${suggestions[c].filter(x=>x.selected).length})</button>`).join('');document.getElementById('items').innerHTML=suggestions[active].map((x,i)=>`<label class="item"><input type="checkbox" ${x.selected?'checked':''} onchange="suggestions[active][${i}].selected=this.checked;render()"><span><strong>${esc(x.name)}</strong><small>${esc(x.source||'Added by you')}</small></span></label>`).join('')||'<p class="muted">No items yet.</p>'}function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}function addItem(){let el=document.getElementById('newItem');let v=el.value.trim();if(v){suggestions[active].push({name:v,selected:true,source:'User entered'});el.value='';render()}}function val(id){return document.getElementById(id).value.trim()}function payload(status='completed'){return {status,profile:Object.fromEntries(['name','email','title','manager','team','location','aspirations','style'].map(k=>[k,val(k)])),priorities:Object.entries(suggestions).flatMap(([category,rows])=>rows.map(x=>({...x,category}))),notes:val('notes')}}async function submitForm(){try{let r=await fetch('/api/onboarding',{method:'POST',headers:{'Content-Type':'application/json','X-MyIQ-Token':window.MYIQ_TOKEN},body:JSON.stringify(payload())});if(!r.ok)throw Error('Save failed');show('Saved locally. Return to Cowork to test the future integration.')}catch(e){show(e.message)}}function exportJson(){let blob=new Blob([JSON.stringify(payload(),null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='myiq-onboarding.json';a.click();URL.revokeObjectURL(a.href)}async function skip(){await fetch('/api/onboarding',{method:'POST',headers:{'Content-Type':'application/json','X-MyIQ-Token':window.MYIQ_TOKEN},body:JSON.stringify(payload('skipped'))});show('Skipped for now.')}function show(s){let e=document.getElementById('status');e.style.display='block';e.textContent=s}async function init(){let r=await fetch('/api/onboarding',{headers:{'X-MyIQ-Token':window.MYIQ_TOKEN}});let d=await r.json();if(d.profile){for(let [k,v] of Object.entries(d.profile)){let el=document.getElementById(k);if(el)el.value=v||''}if(d.priorities){suggestions=Object.fromEntries(cats.map(c=>[c,d.priorities.filter(x=>x.category===c)]))}document.getElementById('notes').value=d.notes||''}render()}init();
</script></body></html>'''

class Handler(BaseHTTPRequestHandler):
    def send(self, status, content, mime='application/json'):
        body = content.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', mime+'; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers(); self.wfile.write(body)
    def authorized(self):
        return self.headers.get('X-MyIQ-Token') == TOKEN
    def do_GET(self):
        if urlparse(self.path).path == '/':
            self.send(200, PAGE.replace('</head>', '<script>window.MYIQ_TOKEN='+json.dumps(TOKEN)+'</script></head>'), 'text/html')
        elif self.path == '/api/onboarding':
            if not self.authorized(): return self.send(403,'{}')
            f = STORE/'onboarding.json'
            self.send(200, f.read_text(encoding='utf-8') if f.exists() else json.dumps({'status':'new'}))
        else: self.send(404,'{}')
    def do_POST(self):
        if self.path != '/api/onboarding': return self.send(404,'{}')
        if not self.authorized(): return self.send(403,'{}')
        try:
            length = int(self.headers.get('Content-Length','0'))
            if length > 200000 or length <= 0: return self.send(413,'{}')
            data = json.loads(self.rfile.read(length))
            if not isinstance(data,dict) or data.get('status') not in ('completed','skipped') or not isinstance(data.get('priorities'),list): return self.send(400,'{}')
            data['updatedAt'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            target = STORE/'onboarding.json'; tmp = STORE/'onboarding.tmp'
            tmp.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8');tmp.replace(target)
            self.send(200,json.dumps({'saved':True,'status':data['status']}))
        except (ValueError,TypeError): self.send(400,'{}')
    def log_message(self,*args): pass

if __name__ == '__main__':
    print(f'MyIQ local POC: http://{HOST}:{PORT}')
    print(f'JSON storage: {STORE / "onboarding.json"}')
    threading.Timer(0.6, lambda: webbrowser.open(f'http://{HOST}:{PORT}')).start()
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
