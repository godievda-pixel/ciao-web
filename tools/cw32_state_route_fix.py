from pathlib import Path
import sys

P=Path('index.html')
text=P.read_text(encoding='utf-8')
old_const="const API_BASE = 'https://dkefzepiiudehhzbbrjn.supabase.co/functions/v1/ciao-core-api-fast-v4'; // backend для GitHub Pages"
new_const=old_const+"\n  const STATE_API_BASE = 'https://dkefzepiiudehhzbbrjn.supabase.co/functions/v1/ciao-core-api-fast-v6'; // canonical state/rating"
old_api="const api = async (body) => { const r=await fetch(API_BASE,{method:'POST',headers:{'content-type':'application/json','x-telegram-init-data':initData},body:JSON.stringify(body)}); let j={}; try{j=await r.json()}catch(_e){} if(!r.ok||!j.ok){const e=new Error(j.error||'Ошибка');e.status=r.status;e.payload=j;throw e;} return j; };"
new_api="const api = async (body) => { const endpoint=String(body?.action||'')==='state'?STATE_API_BASE:API_BASE; const r=await fetch(endpoint,{method:'POST',headers:{'content-type':'application/json','x-telegram-init-data':initData},body:JSON.stringify(body)}); let j={}; try{j=await r.json()}catch(_e){} if(!r.ok||!j.ok){const e=new Error(j.error||'Ошибка');e.status=r.status;e.payload=j;throw e;} return j; };"
marker="ciao-core-api-fast-v6'; // canonical state/rating"

def red():
    assert old_const in text, 'RED setup: v4 API_BASE missing'
    assert marker not in text, 'RED expected state routing fix to be absent'
    assert old_api in text, 'RED setup: legacy api wrapper missing'
    print('RED observed: state still routes through v4 API_BASE')

def apply():
    global text
    if marker in text:
        print('already applied'); return
    assert text.count(old_const)==1, f'expected one API_BASE declaration, got {text.count(old_const)}'
    assert text.count(old_api)==1, f'expected one api wrapper, got {text.count(old_api)}'
    text=text.replace(old_const,new_const,1).replace(old_api,new_api,1)
    P.write_text(text,encoding='utf-8')
    print('applied canonical state route')

def green():
    t=P.read_text(encoding='utf-8')
    checks=[
      marker in t,
      "String(body?.action||'')==='state'?STATE_API_BASE:API_BASE" in t,
      old_const in t,
      "ciao-v29-native-score-picker-20260908" in t,
      "el.id='cw29-score-picker'" in t,
    ]
    assert all(checks), checks
    assert t.count("const STATE_API_BASE = 'https://dkefzepiiudehhzbbrjn.supabase.co/functions/v1/ciao-core-api-fast-v6';")==1
    print('GREEN state route contract: PASS')

mode=sys.argv[1]
{'red':red,'apply':apply,'green':green}[mode]()
