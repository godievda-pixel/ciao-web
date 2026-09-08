from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

repls = [
    (
        "const __CWPRED_EXTERNAL_API='https://dkefzepiiudehhzbbrjn.supabase.co/functions/v1/ciao-external-predictions';",
        "const __CWPRED_EXTERNAL_API='https://dkefzepiiudehhzbbrjn.supabase.co/functions/v1/ciao-external-predictions-live-v1';"
    ),
    (
        "const id=Number(card.getAttribute('data-cwmt-match'));if(id>0)openMatchCenter(id,'external')",
        "const key=String(card.getAttribute('data-cwmt-match')||'');const match=(__cwMtPayload?.matches||[]).find(row=>String(row?.matchId||'')===key);const id=Number(match?.externalMatchId);if(id>0)openMatchCenter(id,'external')"
    ),
    (
        "const id=Number(card.getAttribute('data-cwpred-match'));if(id>0)openMatchCenter(id,'external')",
        "const key=String(card.getAttribute('data-cwpred-match')||'');const match=(__cwPredSelectedGroup()?.matches||[]).find(row=>String(row?.matchId||'')===key);const id=Number(match?.externalMatchId);if(id>0)openMatchCenter(id,'external')"
    ),
    (
        "__cwHomeOpenExternalCenter(el.getAttribute('data-cw-home-match'),el.getAttribute('data-cw-home-competition'))",
        "(()=>{const key=String(el.getAttribute('data-cw-home-match')||''),competition=String(el.getAttribute('data-cw-home-competition')||''),match=__cwHomeExternalRows().find(row=>String(row?.matchId||'')===key&&String(row?.competition||'')===competition),id=Number(match?.externalMatchId);if(id>0)openMatchCenter(id,'external')})()"
    ),
]

for old, new in repls:
    count = s.count(old)
    if count != 1:
        raise SystemExit(f'expected exactly one occurrence, got {count}: {old[:100]}')
    s = s.replace(old, new, 1)

marker = '/* ciao-v33-external-live-navigation-fix-20260908 */'
if marker not in s:
    anchor = '/* /ciao-v32-external-match-center-20260908 */'
    if s.count(anchor) != 1:
        raise SystemExit('v32 anchor missing or duplicated')
    s = s.replace(anchor, anchor + '\n  ' + marker, 1)

p.write_text(s, encoding='utf-8')
print('cw33 patch applied')
