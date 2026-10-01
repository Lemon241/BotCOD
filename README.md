# Forex AI Trader — Multi-timeframe research engine

Motore quantitativo **research-first** per EUR/USD. La pipeline è esplicitamente
`Data → Forecast → Decision → Risk → Execution`: il modello stima la probabilità
che il take profit preceda lo stop loss, ma non può inviare ordini né modificare le
regole di rischio. La modalità predefinita è `BACKTEST`; non esiste un adapter live.

> Software sperimentale, non consulenza finanziaria. Nessun backtest garantisce
> risultati futuri. `NO_TRADE` è un risultato previsto e auspicabile senza edge.

## Strategia MVP

- **M15**: contesto (trend, forza, regime e volatilità), usando solo candele chiuse;
- **M5**: feature e probabilità LONG/SHORT con Logistic Regression o gradient boosting;
- **M1**: primo ingresso valido, spread e simulazione cronologica di SL/TP/timeout;
- target: `P(TP_FIRST | market state)`, non colore della candela successiva;
- decisione: `EV = p × TP - (1-p) × SL - spread - slippage - commissioni`;
- stop obbligatorio, massimo una posizione, sizing percentuale e circuit breaker;
- LONG entra ad ASK ed esce a BID; SHORT entra a BID ed esce ad ASK tramite costi
  espliciti. Le candele con TP e SL contemporanei sono perdite per default.

## Avvio

```bash
docker compose run --rm research
# oppure
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
python scripts/backtest.py --config config/research.yaml
```

Senza `--data` viene usato un dataset riproducibile sintetico. Per dati reali:

```bash
python scripts/backtest.py --config config/research.yaml --data data/raw/EURUSD_M1.csv
```

Il CSV richiede `timestamp,open,high,low,close`; `spread` (pip) e `tick_volume`
sono consigliati. I timestamp sono convertiti in UTC e la geometria OHLC viene
validata. Nessun valore mancante viene sostituito con un prezzo arbitrario.

## Output

In `data/output/` vengono prodotti `summary.json`, `metrics.json`, `trades.csv`,
`predictions.csv`, `equity.csv`, analisi per confidence bucket e grafici di equity,
drawdown, rendimenti, PnL, confidence/win-rate e confidence/EV.

`trades.csv` registra prezzi, direzione, spread, slippage, PnL lordo/netto, costi,
probabilità, EV, regime e versione modello. Le metriche includono profit factor,
expectancy, maximum drawdown, Sharpe, Sortino, win rate ed esposizione.

## Configurazione e causalità

Tutti i parametri strategici risiedono in `config/*.yaml`: timeframe, finestre,
barriere fisse/ATR, soglie probabilistiche e EV, costi, rischio e ambiguous policy.
Lo split è temporale, senza shuffle. Imputer e scaler sono fit soltanto sul train;
la calibrazione Platt/isotonica usa validation. Il test non partecipa al fitting.

Le aggregazioni usano intervalli chiusi a sinistra e timestamp di chiusura; il join
M5/M15 è backward-as-of, quindi alle 10:25 è visibile al massimo la M15 chiusa alle
10:15. Feature rolling, EMA e ATR usano esclusivamente righe fino a `t`.

## Modelli

`model.type: logistic` è la baseline. `gradient_boosting` seleziona
`HistGradientBoostingClassifier`; installando l'extra `boosting`, `xgboost` seleziona
anche `XGBClassifier`. Le probabilità possono essere calibrate con `sigmoid`
(Platt) o `isotonic`. I seed sono controllati.

## Limiti intenzionali

Questa milestone non offre streaming, paper/live broker o ottimizzazione sul test.
Prima del paper trading servono dati bid/ask reali, walk-forward su più periodi,
analisi di regime, stabilità delle feature, realistiche commissioni/swap, conteggio
trade adeguato e expectancy out-of-sample positiva dopo i costi.

## Test

```bash
ruff check .
pytest
```

La suite copre OHLC, ATR e candle feature, barriere (TP/SL/timeout/ambiguo), causalità,
allineamento M1/M5/M15, decisione NO_TRADE, sizing, circuit breaker e drawdown.
