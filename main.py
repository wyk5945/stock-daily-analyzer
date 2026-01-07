#!/usr/bin/env python3
"""
Stock Daily Analyzer - Main Entry Point
每日股票分析自动化系统

功能:
1. 每天下午2点自动运行A股分析（全市场，除创业板外）
2. 保存分析结果到SQLite数据库
3. 回顾历史推荐的准确性
4. 通过macOS系统通知提醒用户
"""
import sys
import os
import logging
from datetime import datetime, date
from pathlib import Path

# 确保可以导入本地模块
sys.path.insert(0, str(Path(__file__).parent))

from config import LOG_DIR, REPORT_DIR, BACKTEST_DAYS
from database import init_database, save_recommendations, get_overall_accuracy
from analyzer import run_daily_analysis
from backtester import run_backtest
from notifier import send_analysis_complete_notification, send_error_notification
from llm import llm_enabled, select_top_picks


def setup_logging():
    """设置日志"""
    log_file = LOG_DIR / f"analysis_{date.today().isoformat()}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def generate_report(backtest_result, recommendations, summary, llm_picks: dict = None) -> str:
    """生成完整报告"""
    lines = [
        "=" * 60,
        f"股票分析日报 - {date.today().isoformat()}",
        "=" * 60,
        "",
    ]

    # 回测部分
    if backtest_result:
        lines.extend([
            "【历史回测】",
            f"  验证{BACKTEST_DAYS}天前推荐: {backtest_result['total_recommendations']}只股票",
            f"  正确: {backtest_result['correct_count']}只 | 一般: {backtest_result['neutral_count']}只 | 错误: {backtest_result['wrong_count']}只",
            f"  准确率: {backtest_result['accuracy_rate']:.0%}",
            f"  平均收益: {backtest_result['avg_return']:+.2%}",
        ])
        if backtest_result.get('best_pick'):
            lines.append(f"  最佳: {backtest_result['best_pick']} {backtest_result['best_return']:+.2%}")
        if backtest_result.get('worst_pick'):
            lines.append(f"  最差: {backtest_result['worst_pick']} {backtest_result['worst_return']:+.2%}")
        lines.append("")
    else:
        lines.extend(["【历史回测】", "  暂无历史数据可回测", ""])

    # 今日推荐
    lines.append("【今日推荐】")
    lines.append(f"  扫描股票数: {summary.get('total_scanned', 0)}")
    lines.append("")

    for rec_type, stocks in summary.get('recommendations', {}).items():
        lines.append(f"  类型: {rec_type}")
        if stocks:
            for s in stocks:
                lines.append(f"    - {s['name']}({s['code']}): ¥{s['price']:.2f} | RSI:{s['rsi']:.0f} | 量比:{s['vol_ratio']:.2f}")
        else:
            lines.append("    (无符合条件标的)")
        lines.append("")

    if llm_picks:
        lines.append("【LLM智能精选】")
        for rec_type, pick in llm_picks.items():
            lines.append(f"  类型: {rec_type}")
            lines.append(f"    最值得买: {pick.get('name')}({pick.get('ticker')})")
            lines.append(f"    理由: {pick.get('reason')}")
            lines.append("")

    # 风险提示
    lines.extend([
        "=" * 60,
        "风险提示: 以上分析仅供参考，不构成投资建议。股市有风险，投资需谨慎。",
        "=" * 60,
    ])

    return '\n'.join(lines)


def save_report(report: str):
    """保存报告到文件"""
    report_file = REPORT_DIR / f"report_{date.today().isoformat()}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    return report_file


def main():
    """主函数"""
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info("开始每日股票分析")
    logger.info("=" * 50)

    try:
        # 1. 初始化数据库
        init_database()
        logger.info("数据库初始化完成")

        # 2. 运行回测（验证历史推荐）
        logger.info(f"开始回测验证{BACKTEST_DAYS}天前的推荐...")
        backtest_result, backtest_report = run_backtest()
        if backtest_result:
            logger.info(f"回测完成: 准确率 {backtest_result['accuracy_rate']:.0%}")
        else:
            logger.info("暂无历史数据可回测")

        # 3. 运行今日分析
        logger.info("开始今日市场分析...")
        recommendations, summary = run_daily_analysis()
        logger.info(f"分析完成: 扫描{summary.get('total_scanned', 0)}只股票")

        # 3.5 LLM智能精选
        llm_picks = {}
        if llm_enabled():
            logger.info("调用LLM生成类型内首选...")
            llm_picks = select_top_picks(summary.get('recommendations', {}))
            if llm_picks:
                logger.info(f"LLM精选完成: {list(llm_picks.keys())}")
            else:
                logger.info("LLM未返回精选结果")

        # 4. 保存推荐到数据库
        if recommendations:
            saved_count = save_recommendations(recommendations)
            logger.info(f"保存{saved_count}条推荐记录")

        # 5. 生成并保存报告
        report = generate_report(backtest_result, recommendations, summary, llm_picks)
        report_file = save_report(report)
        logger.info(f"报告已保存: {report_file}")

        # 6. 打印报告
        print("\n" + report)

        # 7. 发送通知
        total_recommendations = sum(summary.get('counts', {}).values())
        overall_accuracy = get_overall_accuracy()
        send_analysis_complete_notification(total_recommendations, overall_accuracy, str(report_file))
        logger.info("已发送系统通知")

        logger.info("每日分析完成!")
        return 0

    except Exception as e:
        logger.error(f"分析过程出错: {e}", exc_info=True)
        send_error_notification(str(e)[:100])
        return 1


if __name__ == "__main__":
    sys.exit(main())
