import json

from forex_bot.config import Settings
from forex_bot.engine import TradingEngine


def main() -> None:
    print(json.dumps(TradingEngine(Settings()).run_cycle(), indent=2))


if __name__ == "__main__":
    main()
