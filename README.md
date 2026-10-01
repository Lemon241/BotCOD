# Forex Quant Bot

MVP in Python per sperimentare strategie Forex basate su **regressione lineare** e
**interpolazione**, con un broker simulato e controlli di rischio. Il progetto parte
deliberatamente in modalita `paper`: non invia ordini a broker reali.

> **Avvertenza:** e un progetto didattico, non una consulenza finanziaria. Backtest e
> risultati passati non garantiscono risultati futuri. Validare strategia, costi,
> slippage e requisiti normativi prima di collegare denaro reale.

## Come funziona

1. legge candele OHLC da CSV (o genera una serie sintetica per la demo);
2. ripulisce la serie interpolando valori mancanti nel tempo;
3. stima il trend con regressione lineare sugli ultimi `LOOKBACK` close;
4. apre una posizione solo se pendenza normalizzata e qualita (`R²`) superano le
   soglie configurate;
5. dimensiona l'ordine in base a capitale, stop loss e rischio massimo;
6. applica stop loss/take profit e salva ordini/stato su disco.

## Avvio rapido con Docker

```bash
cp .env.example .env
docker compose up --build
```

La dashboard JSON sara disponibile su <http://localhost:8000>, lo stato su
`/status`, le metriche su `/metrics` e un ciclo manuale su `POST /run-cycle`.
La documentazione OpenAPI e su `/docs`.

```bash
curl -X POST http://localhost:8000/run-cycle
curl http://localhost:8000/status
```

Per usare dati propri, montare un CSV con colonne `timestamp,open,high,low,close`
e impostare `DATA_CSV=/data/EURUSD.csv`. Il volume e opzionale.

## Esecuzione locale

Richiede Python 3.12+.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn forex_bot.api:app --reload
```

Esecuzione di un solo ciclo dalla CLI:

```bash
python -m forex_bot
```

## Configurazione

Le variabili principali sono documentate in `.env.example`. Le impostazioni piu
importanti sono:

- `RISK_PER_TRADE`: quota del capitale rischiata (default 0,5%);
- `MAX_POSITION_UNITS`: tetto assoluto alla posizione;
- `STOP_LOSS_PIPS` / `TAKE_PROFIT_PIPS`;
- `LOOKBACK`, `MIN_SLOPE` e `MIN_R2`: filtro statistico del segnale;
- `CYCLE_SECONDS`: frequenza del worker automatico.

Il container esegue API e worker. Per disabilitare i cicli automatici e mantenere
solo l'API, impostare `AUTO_TRADE=false`.

## Qualita e test

```bash
ruff check .
pytest
```

## Limiti prima della produzione

- Il `PaperBroker` e una simulazione minimale: spread e slippage sono configurabili,
  ma non modella liquidita, swap, commissioni o rifiuti degli ordini.
- La regressione descrive un trend locale, non predice da sola il mercato.
- Serve un feed affidabile e un adapter broker autenticato, con idempotenza,
  riconciliazione, retry limitati e kill switch.
- Occorrono backtest walk-forward, account demo, monitoraggio e revisione normativa.

## Struttura

```text
forex_bot/        motore, strategia, rischio, feed, broker e API
tests/            test unitari e di integrazione del ciclo
data/             stato runtime (ignorato da Git)
Dockerfile        immagine non-root con healthcheck
docker-compose.yml
```
