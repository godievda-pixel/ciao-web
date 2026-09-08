from pathlib import Path

# Run the main source patcher first.
exec(Path('tools/cw29_native_score_picker.py').read_text(encoding='utf-8'), {'__name__':'__main__'})

p=Path('index.html')
s=p.read_text(encoding='utf-8')
s=s.replace('  let __cw29PickerActive=null;','  var __cw29PickerActive=null;')
old="  root.addEventListener('click',e=>{const b=e.target.closest('[data-cwpred-pick]');if(!b)return;e.preventDefault();e.stopPropagation();__cw29PickerOpen(b)});\n  document.addEventListener('keydown',e=>{if(e.key==='Escape')__cw29PickerClose()});"
new="  if(!root.dataset.cw29PickerBound){root.dataset.cw29PickerBound='1';root.addEventListener('click',e=>{const b=e.target.closest('[data-cwpred-pick]');if(!b)return;e.preventDefault();e.stopPropagation();__cw29PickerOpen(b)});document.addEventListener('keydown',e=>{if(e.key==='Escape')__cw29PickerClose()})}"
if old not in s:
    raise SystemExit('picker listener block not found')
s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
