import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def write_report(output_dir, trades, predictions, equity, metrics, configuration):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    trades.to_csv(out / "trades.csv", index=False)
    predictions.to_csv(out / "predictions.csv", index=False)
    equity.to_csv(out / "equity.csv", index=False)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2, allow_nan=False))
    (out / "summary.json").write_text(
        json.dumps({"configuration": configuration, "metrics": metrics}, indent=2, allow_nan=False)
    )
    plots = {
        "equity": (equity.get("timestamp"), equity.get("equity")),
        "drawdown": (equity.get("timestamp"), equity.get("drawdown")),
        "returns": (None, equity.get("equity", pd.Series(dtype=float)).pct_change()),
        "trade_pnl": (None, trades.get("net_pnl", pd.Series(dtype=float))),
    }
    for name, (x, y) in plots.items():
        fig, ax = plt.subplots()
        ax.plot(x, y) if x is not None else ax.hist(y.dropna(), bins=20)
        ax.set_title(name.replace("_", " ").title())
        fig.tight_layout()
        fig.savefig(out / f"{name}.png")
        plt.close(fig)
    if len(predictions):
        buckets = pd.cut(predictions.p_success, [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 1.0])
        analysis = (
            predictions.assign(bucket=buckets)
            .groupby("bucket", observed=False)
            .agg(
                trade_count=("p_success", "size"),
                expected_win_rate=("p_success", "mean"),
                average_ev=("expected_value", "mean"),
            )
            .reset_index()
        )
        analysis["bucket"] = analysis.bucket.astype(str)
        analysis.to_csv(out / "confidence_analysis.csv", index=False)
        for column, title in (
            ("expected_win_rate", "confidence_vs_win_rate"),
            ("average_ev", "confidence_vs_expected_value"),
        ):
            fig, ax = plt.subplots()
            ax.plot(analysis.bucket, analysis[column], marker="o")
            ax.tick_params(axis="x", rotation=45)
            fig.tight_layout()
            fig.savefig(out / f"{title}.png")
            plt.close(fig)
