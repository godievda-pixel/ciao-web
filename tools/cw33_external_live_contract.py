from pathlib import Path

text = Path('index.html').read_text(encoding='utf-8')

required = [
    "ciao-external-predictions-live-v1",
    "externalMatchId",
]
for needle in required:
    assert needle in text, f"missing fixed contract marker: {needle}"

forbidden = [
    "const id=Number(card.getAttribute('data-cwmt-match'))",
    "const id=Number(card.getAttribute('data-cwpred-match'))",
    "__cwHomeOpenExternalCenter(el.getAttribute('data-cw-home-match'),el.getAttribute('data-cw-home-competition'))",
]
for needle in forbidden:
    assert needle not in text, f"legacy broken path still present: {needle}"

print('cw33 frontend contract: GREEN')
