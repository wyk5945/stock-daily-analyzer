import argparse
from pathlib import Path

from qf.experiment import run_experiment


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True, help="实验配置文件路径，例如 experiments/default_a_share_daily.json")
    p.add_argument("--out", default="reports/experiments", help="输出目录")
    args = p.parse_args()

    cfg_path = Path(args.config)
    out_dir = Path(args.out)
    _, _, summary_path = run_experiment(cfg_path, out_dir)
    print(str(summary_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

