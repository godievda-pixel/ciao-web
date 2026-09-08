from pathlib import Path
import sys

P=Path('index.html')
MARKER='cw25-next-match-savebar-style'

def check(src: str):
    errors=[]
    if "function __cwHomeLegacyTime(match){const exact=Date.parse(match?.kickoff_at||'');" not in src or "match?.nominal_date" not in src[src.find('function __cwHomeLegacyTime'):src.find('function __cwHomeStatus')]:
        errors.append('Home legacy ordering does not fall back to nominal_date')
    label_start=src.find('function __cwHomeMatchLabel(match)')
    label_end=src.find('function __cwHomeMatchScore',label_start)
    label=src[label_start:label_end] if label_start>=0 and label_end>label_start else ''
    if "raw?.nominal_date" not in label or "время уточняется" not in label:
        errors.append('Home match label does not handle unknown kickoff time')
    if MARKER not in src:
        errors.append('frontend fix style marker missing')
    if "background:linear-gradient(135deg,var(--club-accent),var(--club-accent-2))!important" not in src:
        errors.append('favorite club profile button is not using opaque two-club-color gradient')
    if "#ciao-miniapp-root .cwpred-savebar{position:static!important" not in src:
        errors.append('prediction savebar is still sticky/floating')
    if errors:
        print('CONTRACT FAIL:')
        for e in errors: print(' -',e)
        raise SystemExit(1)
    print('CONTRACT PASS')

def once(src,old,new,label):
    n=src.count(old)
    if n!=1: raise RuntimeError(f'{label}: expected 1 occurrence, got {n}')
    return src.replace(old,new,1)

def apply(src: str):
    if MARKER in src: return src
    src=once(src,
        "function __cwHomeLegacyTime(match){const n=Date.parse(match?.kickoff_at||'');return Number.isFinite(n)?n:Number.MAX_SAFE_INTEGER}",
        "function __cwHomeLegacyTime(match){const exact=Date.parse(match?.kickoff_at||'');if(Number.isFinite(exact))return exact;const nominal=Date.parse(match?.nominal_date||'');return Number.isFinite(nominal)?nominal+12*3600000:Number.MAX_SAFE_INTEGER}",
        'legacy nominal-date ordering')
    src=once(src,
        "if(typeof fmt==='function')return fmt(raw.kickoff_at)}catch(_e){}return ''}",
        "if(raw?.kickoff_at&&typeof fmt==='function')return fmt(raw.kickoff_at);if(raw?.nominal_date){try{return new Intl.DateTimeFormat('ru-RU',{day:'2-digit',month:'2-digit'}).format(new Date(String(raw.nominal_date)+'T12:00:00'))+' · время уточняется'}catch(_e){}}return 'Время уточняется'}catch(_e){}return 'Время уточняется'}",
        'unknown kickoff label')
    src=once(src,
        "background:linear-gradient(135deg,var(--club-accent),var(--club-accent-2-soft))!important",
        "background:linear-gradient(135deg,var(--club-accent),var(--club-accent-2))!important",
        'favorite profile opaque club colors')
    style='''\n<style id="cw25-next-match-savebar-style">\n/* Ciao v25 — correct TBD fixtures + in-flow predictions save */\n#ciao-miniapp-root .cwpred-savebar{position:static!important;bottom:auto!important;z-index:auto!important;margin:12px 0 18px!important;padding:0!important;background:transparent!important;backdrop-filter:none!important;-webkit-backdrop-filter:none!important}\n#ciao-miniapp-root .cwpred-savebar .cwpred-save{width:100%!important;margin:0!important}\n#ciao-miniapp-root .cw211-profile-btn.cw-home-profile-premium{background:linear-gradient(135deg,var(--club-accent),var(--club-accent-2))!important;border-color:var(--club-accent-faint)!important;box-shadow:0 10px 28px var(--club-accent-faint),inset 0 1px 0 rgba(255,255,255,.22)!important}\n</style>\n'''
    if '</head>' not in src: raise RuntimeError('head close not found')
    src=src.replace('</head>',style+'</head>',1)
    return src

def main():
    src=P.read_text(encoding='utf-8')
    mode=sys.argv[1] if len(sys.argv)>1 else 'check'
    if mode=='check': check(src)
    elif mode=='apply':
        out=apply(src);P.write_text(out,encoding='utf-8');print('PATCH APPLIED')
    else: raise SystemExit('usage: check|apply')

if __name__=='__main__': main()
