from pathlib import Path
import sys

p = Path(sys.argv[1] if len(sys.argv) > 1 else 'tools/cw30_core_v6.ts')
s = p.read_text(encoding='utf-8')

checks = {
    'season label': "const RATING_SEASON='2026/27'" in s,
    'season start': "2026-07-01T00:00:00Z" in s,
    'season end': "2027-07-01T00:00:00Z" in s,
    'all competitions': all(x in s for x in ["'all'","'serie_a'","'ucl'","'uel'","'uecl'","'coppa_italia'"]),
    'serie predictions query': 'cp_predictions' in s,
    'external predictions query': 'cp_external_predictions' in s,
    'external matches query': 'cp_external_matches' in s,
    'success rate': 'success_rate' in s,
    'streak': 'streak' in s,
    'trend': 'trend' in s,
    'direct standings action': 'action==="standings_scope"' in s or "action==='standings_scope'" in s,
    'competition response': 'standings_meta' in s and 'competition' in s,
    'zero users retained': 'is_active' in s and ('zeroActivity' in s or 'calculated:ps.length' in s or 'calculated:0' in s),
}

failed = [name for name, ok in checks.items() if not ok]
if failed:
    print('competition-aware standings missing:', ', '.join(failed))
    sys.exit(1)
print('rating backend contract: PASS')
