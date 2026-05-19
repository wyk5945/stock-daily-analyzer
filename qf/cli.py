import argparse
from pathlib import Path

from qf.experiment import run_experiment


def main() -> int:
    p = argparse.ArgumentParser(prog="stock-analyzer")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_bt = sub.add_parser("backtest")
    p_bt.add_argument("--config", required=True, help="实验配置文件路径，例如 experiments/default_a_share_daily.json")
    p_bt.add_argument("--out", default="reports/experiments", help="输出目录")

    sub.add_parser("run-daily")
    sub.add_parser("self-check")

    args = p.parse_args()

    if args.cmd == "backtest":
        _, _, summary_path = run_experiment(Path(args.config), Path(args.out))
        print(str(summary_path))
        return 0
    if args.cmd == "run-daily":
        import main as daily

        return int(daily.main())
    if args.cmd == "self-check":
        import self_check

        return int(self_check.main())

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
