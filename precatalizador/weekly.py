#!/usr/bin/env python3
"""Refresh a curated screen; alert only on a newly crossed 6/7 threshold."""
import json, os, subprocess, sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

HERE=Path(__file__).resolve().parent
SNAPSHOT=HERE/'scan.json'
prior=json.loads(SNAPSHOT.read_text()) if SNAPSHOT.exists() else None
subprocess.run([sys.executable,str(HERE/'scanner.py')],check=True)
latest=json.loads(SNAPSHOT.read_text())
old={r['ticker']:r for r in (prior or {}).get('results',[])}
valid=[r for r in latest['results'] if 'error' not in r]
if not valid:
    if prior:SNAPSHOT.write_text(json.dumps(prior,indent=2,ensure_ascii=False)+'\n')
    raise SystemExit('All quotes failed; preserved the last valid public snapshot. No alerts sent.')
# Initial run establishes a baseline, not a "new" threshold crossing.
entered=[r for r in valid if r.get('score',0)>=6 and r['ticker'] in old and old[r['ticker']].get('score',0)<6 and 'error' not in old[r['ticker']]]
if entered:
    token=os.environ.get('TELEGRAM_BOT_TOKEN')
    chat=os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat:
        if prior:SNAPSHOT.write_text(json.dumps(prior,indent=2,ensure_ascii=False)+'\n')
        raise SystemExit('Telegram credentials missing; retained prior snapshot to retry alerts.')
    for r in entered:
        text=(f"UMBRAL | RADAR PRECATALIZADOR\n{r['ticker']} cruza a {r['score']}/7 en una lista SEMILLA curada, no el mercado global.\n"
              f"Evento: {r['catalyst']['description']} (ventana hasta {r['catalyst']['window_end']}).\n"
              f"Fuente: {r['catalyst']['source_url']}\n"
              f"Fecha del barrido: {r['as_of']}. Revisar hechos, dilución y precio antes de actuar. "
              f"6/7 NO es señal de compra.\nhttps://davizz-dev13.github.io/umbral/precatalizador.html")
        payload=urlencode({'chat_id':chat,'text':text}).encode()
        try:
            with urlopen(Request(f'https://api.telegram.org/bot{token}/sendMessage',data=payload),timeout=20) as response:
                answer=json.load(response)
            if not answer.get('ok'):raise ValueError('Telegram did not accept message')
        except Exception as exc:
            if prior:SNAPSHOT.write_text(json.dumps(prior,indent=2,ensure_ascii=False)+'\n')
            raise SystemExit('Telegram send failed; prior snapshot restored; retry may duplicate earlier alerts in this batch') from exc
print(f"Valid {len(valid)}/{len(latest['results'])}; threshold entries sent: {len(entered)}")
