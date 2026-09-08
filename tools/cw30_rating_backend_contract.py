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
    'zero users retained': "eq('is_active',true)" in s and 'users.map(' in s and 'const ps=(by.get(Number(u.id))??[])' in s,
    'public predictor action': 'action==="public_predictor"' in s or "action==='public_predictor'" in s,
    'history limit clamp': 'history_limit' in s and 'Math.min(50' in s and 'Math.max(1' in s,
    'history cursor': 'history_cursor' in s and 'next_cursor' in s,
    'source aware cursor': 'source_id' in s and 'source' in s and 'btoa' in s and 'atob' in s,
    'recent summary': 'recent_summary' in s and 'sample_size' in s,
    'history page': 'history_page' in s and 'has_more' in s,
    'settled serie history': 'is_finished' in s and 'final_home' in s and 'final_away' in s,
    'settled external history': 'finalized_at' in s and 'status' in s and 'quality' in s,
    'history competition labels': 'competition_label' in s,
}

failed = [name for name, ok in checks.items() if not ok]
if failed:
    print('rating backend contract missing:', ', '.join(failed))
    sys.exit(1)
print('rating backend contract: PASS')
