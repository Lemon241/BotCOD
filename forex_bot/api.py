import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, HTTPException

from forex_bot.config import Settings
from forex_bot.engine import TradingEngine

settings = Settings()
engine = TradingEngine(settings)


async def worker() -> None:
    while True:
        try:
            await asyncio.to_thread(engine.run_cycle)
        except (OSError, ValueError, RuntimeError):
            # API remains healthy; production should route this to structured alerting.
            pass
        await asyncio.sleep(settings.cycle_seconds)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(worker()) if settings.auto_trade else None
    yield
    if task:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="Forex Quant Bot", version="0.1.0", lifespan=lifespan)


@app.get("/")
def root() -> dict:
    return {"name": "Forex Quant Bot", "mode": "paper", "docs": "/docs"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/status")
def status() -> dict:
    return engine.broker.state.model_dump(mode="json")


@app.get("/metrics")
def metrics() -> dict:
    state = engine.broker.state
    return {
        "balance": state.balance,
        "equity": state.equity,
        "realized_pnl": state.realized_pnl,
        "orders": len(state.orders),
    }


@app.post("/run-cycle")
def run_cycle() -> dict:
    try:
        return engine.run_cycle()
    except (OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
