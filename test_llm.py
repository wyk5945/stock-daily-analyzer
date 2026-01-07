import logging
from llm import select_top_picks, llm_enabled
import json

# 配置简单的日志输出到控制台，以便测试时能看到 llm.py 中的 logger 输出
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    print("LLM_ENABLED=", llm_enabled())
    recommendations = {
        "放量突破": [
            {
                "code": "600519",
                "name": "贵州茅台",
                "price": 1600.0,
                "rsi": 60.0,
                "weekly_change": 0.02,
                "daily_change": 0.011,
                "vol_ratio": 1.8,
                "macd_golden_cross": True,
                "ma_bullish": True,
            },
            {
                "code": "600941",
                "name": "中国移动",
                "price": 100.5,
                "rsi": 55.0,
                "weekly_change": 0.01,
                "daily_change": 0.006,
                "vol_ratio": 1.4,
                "macd_golden_cross": False,
                "ma_bullish": True,
            },
        ],
        "趋势向好": [
            {
                "code": "000858",
                "name": "五粮液",
                "price": 160.0,
                "rsi": 65.0,
                "weekly_change": 0.03,
                "daily_change": 0.012,
                "vol_ratio": 1.7,
                "macd_golden_cross": True,
                "ma_bullish": True,
            }
        ],
    }
    picks = select_top_picks(recommendations)
    print("LLM_PICKS=", json.dumps(picks, ensure_ascii=False))

if __name__ == "__main__":
    main()
