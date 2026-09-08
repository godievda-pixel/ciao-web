from pathlib import Path
import re, sys

P = Path('index.html')
MARKER = 'cw24-premium-nav-stability-style'


def check(src: str) -> None:
    errors = []
    if MARKER not in src:
        errors.append('premium style marker missing')
    if "if(scope!=='overall'&&clubViewTab==='squad')clubViewTab='overview'" not in src:
        errors.append('squad is not reset when leaving overall scope')
    if "scope==='overall'?__cw16ClubTabs:__cw16ClubTabs.filter(([k])=>k!=='squad')" not in src:
        errors.append('squad tab is not limited to overall scope')
    polish_start = src.find('function __cw23PolishFavorite(scope)')
    polish_end = src.find('function __cw23PolishPredictionStages', polish_start)
    polish = src[polish_start:polish_end] if polish_start >= 0 and polish_end > polish_start else ''
    if 'Открыть матч-центр' in polish:
        errors.append('favorite match hint is still rendered')
    if "typeof __cwHomeExternalLoadedAt!=='undefined'&&!Number(__cwHomeExternalLoadedAt)" not in src:
        errors.append('boot cover does not wait for external home data')
    if "__cw23PolishToday(main);__cw23PolishFavorite(main);__cwHomeBindPolish()" not in src:
        errors.append('home external refresh still lacks in-place patch path')
    if "el.dataset.cwHomeBound==='1'" not in src:
        errors.append('home external binding is not idempotent')
    if 'width="48" height="48" decoding="async"' not in src:
        errors.append('favorite/local crest intrinsic dimensions missing')
    if 'width="34" height="34" loading="eager" fetchpriority="high"' not in src:
        errors.append('favorite opponent crest priority/dimensions missing')
    if '#ciao-miniapp-root .cw23-club-tabs.cw17-sticky-tabs{background:transparent!important' not in src:
        errors.append('tab backing plate is not removed')
    if '#ciao-miniapp-root .cw211-profile-btn.cw-home-profile-premium{background:linear-gradient(135deg,var(--club-accent),var(--club-accent-2-soft))!important' not in src:
        errors.append('favorite profile button is not using club colors')
    if errors:
        print('CONTRACT FAIL:')
        for e in errors:
            print(' -', e)
        raise SystemExit(1)
    print('CONTRACT PASS')


def once(src: str, old: str, new: str, label: str) -> str:
    count = src.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 occurrence, got {count}')
    return src.replace(old, new, 1)


def last_once(src: str, old: str, new: str, label: str) -> str:
    count = src.count(old)
    if count < 1:
        raise RuntimeError(f'{label}: expected at least 1 occurrence, got 0')
    head, tail = src.rsplit(old, 1)
    return head + new + tail


def apply(src: str) -> str:
    if MARKER in src:
        return src

    src = once(
        src,
        "clubViewScope=scope;const cached=__cw16ScopeCacheGet(clubViewId,scope);",
        "clubViewScope=scope;if(scope!=='overall'&&clubViewTab==='squad')clubViewTab='overview';const cached=__cw16ScopeCacheGet(clubViewId,scope);",
        'scope squad reset',
    )

    src = last_once(
        src,
        "${__cw16ClubTabs.map(([k,l])=>`<button type=\"button\" class=\"cw16-club-tab ${clubViewTab===k?'active':''}\" data-club-tab=\"${k}\" role=\"tab\" aria-selected=\"${clubViewTab===k?'true':'false'}\">${l}</button>`).join('')}",
        "${(scope==='overall'?__cw16ClubTabs:__cw16ClubTabs.filter(([k])=>k!=='squad')).map(([k,l])=>`<button type=\"button\" class=\"cw16-club-tab ${clubViewTab===k?'active':''}\" data-club-tab=\"${k}\" role=\"tab\" aria-selected=\"${clubViewTab===k?'true':'false'}\">${l}</button>`).join('')}",
        'visible club tabs',
    )

    src = once(
        src,
        '<span class="cw-home-favorite-hint">Открыть матч-центр <i>→</i></span>',
        '',
        'favorite match hint',
    )

    src = once(
        src,
        "function __cw225ReleaseStartCover(){if(!__cw225HasRendered)return;try{document.documentElement.classList.remove('cw225-booting');document.getElementById('cw225-start-cover')?.remove()}catch(_e){}}",
        "function __cw225ReleaseStartCover(){if(!__cw225HasRendered)return;try{if(tab==='predict'&&!__cwHomeExternalCenter&&typeof __cwHomeExternalLoadedAt!=='undefined'&&!Number(__cwHomeExternalLoadedAt))return;document.documentElement.classList.remove('cw225-booting');document.getElementById('cw225-start-cover')?.remove()}catch(_e){}}",
        'boot cover gate',
    )

    src = once(
        src,
        "__cwHomeExternalLoadedAt=Date.now();\n    if(tab==='predict'&&!__cwHomeExternalCenter)try{render()}catch(_e){}",
        "__cwHomeExternalLoadedAt=Date.now();\n    if(tab==='predict'&&!__cwHomeExternalCenter)try{if(document.getElementById('cw225-start-cover'))render();else{__cw23PolishToday(main);__cw23PolishFavorite(main);__cwHomeBindPolish()}}catch(_e){}",
        'in-place home refresh',
    )

    src = once(
        src,
        "root.querySelectorAll?.('[data-cw-home-match][data-cw-home-competition]').forEach(el=>{if(String(el.getAttribute('data-cw-home-competition')||'')==='serie_a')return;const open=ev=>",
        "root.querySelectorAll?.('[data-cw-home-match][data-cw-home-competition]').forEach(el=>{if(String(el.getAttribute('data-cw-home-competition')||'')==='serie_a')return;if(el.dataset.cwHomeBound==='1')return;el.dataset.cwHomeBound='1';const open=ev=>",
        'idempotent home binding',
    )

    old_logo = "function __cw18Logo(t,cls=''){return t?.custom_emoji_id?`<img class=\"${cls}\" src=\"${API_BASE}?asset=emoji&id=${encodeURIComponent(t.custom_emoji_id)}\" alt=\"\">`:'<span>⚽</span>'}"
    new_logo = "function __cw18Logo(t,cls=''){const eager=String(cls||'').includes('fav-logo-big')||String(cls||'').includes('home-opponent-logo'),load=eager?' loading=\"eager\" fetchpriority=\"high\"':' loading=\"lazy\"';return t?.custom_emoji_id?`<img class=\"${cls}\" width=\"48\" height=\"48\" decoding=\"async\"${load} src=\"${API_BASE}?asset=emoji&id=${encodeURIComponent(t.custom_emoji_id)}\" alt=\"\">`:'<span>⚽</span>'}"
    src = once(src, old_logo, new_logo, 'intrinsic local crest size')

    src = once(
        src,
        '<img class="cw-home-opponent-logo" loading="lazy" decoding="async" src="',
        '<img class="cw-home-opponent-logo" width="34" height="34" loading="eager" fetchpriority="high" decoding="async" src="',
        'favorite opponent crest size',
    )
    src = once(
        src,
        '<img class="cw-home-today-crest" loading="lazy" decoding="async" src="',
        '<img class="cw-home-today-crest" width="27" height="27" loading="lazy" decoding="async" src="',
        'today crest size',
    )

    style = r'''<style id="cw24-premium-nav-stability-style">
/* Ciao v24 — premium club controls + stable Home boot */
#ciao-miniapp-root .cw23-club-tabs.cw17-sticky-tabs{background:transparent!important;backdrop-filter:none!important;-webkit-backdrop-filter:none!important;border-radius:0!important;box-shadow:none!important;padding:4px 0 10px!important;margin:0 0 8px!important}
#ciao-miniapp-root.club-profile-open .cw23-club-tabs.cw17-sticky-tabs{background:transparent!important;backdrop-filter:none!important;-webkit-backdrop-filter:none!important}
#ciao-miniapp-root .cw23-scope-strip{gap:8px!important;padding:3px 1px 11px!important}
#ciao-miniapp-root .cw23-scope-strip button,#ciao-miniapp-root .cw23-club-tabs .cw16-club-tab{position:relative!important;overflow:hidden!important;isolation:isolate!important;border:1px solid rgba(255,255,255,.085)!important;background:linear-gradient(180deg,rgba(255,255,255,.065),rgba(255,255,255,.018))!important;color:#aab6d4!important;box-shadow:0 8px 22px rgba(0,0,0,.15),inset 0 1px 0 rgba(255,255,255,.055)!important;backdrop-filter:blur(9px)!important;-webkit-backdrop-filter:blur(9px)!important;transition:transform .16s ease,border-color .16s ease,box-shadow .16s ease!important}
#ciao-miniapp-root .cw23-scope-strip button::before,#ciao-miniapp-root .cw23-club-tabs .cw16-club-tab::before{content:'';position:absolute;z-index:-1;left:10%;right:10%;top:0;height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,.26),transparent);pointer-events:none}
#ciao-miniapp-root .cw23-scope-strip button:active,#ciao-miniapp-root .cw23-club-tabs .cw16-club-tab:active{transform:scale(.975)}
#ciao-miniapp-root .cw23-scope-strip button.active,#ciao-miniapp-root .cw23-club-tabs .cw16-club-tab.active{color:#fff!important;border-color:var(--club-accent-faint)!important;background:radial-gradient(circle at 24% -20%,rgba(255,255,255,.16),transparent 45%),linear-gradient(135deg,var(--club-accent-soft),var(--club-accent-2-soft)),rgba(15,24,48,.96)!important;box-shadow:0 10px 28px var(--club-accent-faint),inset 0 1px 0 rgba(255,255,255,.14),inset 0 -1px 0 rgba(0,0,0,.18)!important}
#ciao-miniapp-root .cw23-scope-strip button.active::after,#ciao-miniapp-root .cw23-club-tabs .cw16-club-tab.active::after{content:'';position:absolute;left:20%;right:20%;bottom:0;height:1px;border-radius:999px;background:var(--club-accent-light);box-shadow:0 0 10px var(--club-accent);opacity:.72}
#ciao-miniapp-root .cw211-profile-btn.cw-home-profile-premium{background:linear-gradient(135deg,var(--club-accent),var(--club-accent-2-soft))!important;border-color:rgba(255,255,255,.20)!important;color:#fff!important;box-shadow:0 10px 26px var(--club-accent-faint),inset 0 1px 0 rgba(255,255,255,.22)!important;text-shadow:0 1px 8px rgba(0,0,0,.28)!important}
#ciao-miniapp-root .cw-home-user-card{min-height:76px!important;box-sizing:border-box!important}
#ciao-miniapp-root .cw211-favorite-logo,#ciao-miniapp-root .cw211-favorite-logo img{width:44px!important;height:44px!important;min-width:44px!important;min-height:44px!important;aspect-ratio:1/1!important}
#ciao-miniapp-root .cw-home-opponent-logo{width:34px!important;height:34px!important;min-width:34px!important;min-height:34px!important;aspect-ratio:1/1!important}
#ciao-miniapp-root .cw-home-today-crest{width:27px!important;height:27px!important;min-width:27px!important;min-height:27px!important;aspect-ratio:1/1!important}
</style>
'''
    if '</head>' not in src:
        raise RuntimeError('head close not found')
    src = src.replace('</head>', style + '</head>', 1)
    return src


def main():
    src = P.read_text(encoding='utf-8')
    mode = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if mode == 'check':
        check(src)
    elif mode == 'apply':
        out = apply(src)
        P.write_text(out, encoding='utf-8')
        print('PATCH APPLIED')
    else:
        raise SystemExit('usage: check|apply')


if __name__ == '__main__':
    main()
