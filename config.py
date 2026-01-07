"""
Stock Daily Analyzer - Configuration
"""
from pathlib import Path

# 项目路径
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "stock_analysis.db"
LOG_DIR = BASE_DIR / "logs"
REPORT_DIR = BASE_DIR / "reports"

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except Exception:
    pass

# 确保目录存在
LOG_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

# 股票筛选配置
STOCK_FILTER = {
    "exclude_prefix": ["300", "301"],  # 排除创业板 (300/301开头)
    "include_prefix": ["000", "001", "002", "003", "600", "601", "603", "605"],  # 主板+中小板
    "min_market_cap": 50_0000_0000,  # 最小市值50亿（可选筛选）
}

# 热门板块配置（用于分类展示，可自定义）
SECTOR_STOCKS = {
    "黄金/有色": ["601899", "600489", "603993", "600547", "601212"],
    "券商金融": ["601995", "600030", "601688", "600958", "601377"],
    "新能源": ["002594", "601012", "600438", "002129", "600406"],
    "半导体": ["002371", "603986", "002049", "603501", "688008"],
    "AI/科技": ["002415", "000977", "002230", "000066", "002236"],
    "白酒消费": ["600519", "000858", "000568", "000596", "603589"],
    "医药生物": ["600276", "000538", "002007", "600196", "000963"],
    "银行": ["601398", "600036", "601166", "600000", "601288"],
    "地产基建": ["001979", "600048", "000002", "600340", "601668"],
    "汽车": ["600104", "000625", "601238", "600660", "000800"],
}

# 技术指标参数
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
RSI_OVERSOLD_SCREEN = 45  # 筛选时的超卖阈值（宽松一些）

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2

MA_PERIODS = [5, 10, 20, 60]

# 回测参数
BACKTEST_DAYS = 3  # 验证N天前的推荐
CORRECT_THRESHOLD = 0.01  # 涨幅>1%算正确
WRONG_THRESHOLD = -0.01  # 跌幅>1%算错误

# 数据获取
DATA_PERIOD = "2mo"  # 获取最近2个月数据
DATA_TIMEOUT = 10  # 数据获取超时秒数

# 筛选输出配置
MAX_RECOMMENDATIONS_PER_TYPE = 5  # 每类最多推荐数量
MIN_VOLUME_RATIO = 1.2  # 放量筛选最小量比

# 市场分析配置
MARKET_INDICES = {
    "上证指数": "000001.SS",
    "深证成指": "399001.SZ",
    "创业板指": "399006.SZ",
}


def get_yfinance_ticker(code: str) -> str:
    """将A股代码转换为yfinance格式"""
    code = code.replace(".SS", "").replace(".SZ", "")
    if code.startswith(("6",)):
        return f"{code}.SS"  # 上海
    elif code.startswith(("0", "3")):
        return f"{code}.SZ"  # 深圳
    return code


def is_valid_stock(code: str) -> bool:
    """检查是否为有效的非创业板股票"""
    code = code.replace(".SS", "").replace(".SZ", "")
    # 排除创业板
    for prefix in STOCK_FILTER["exclude_prefix"]:
        if code.startswith(prefix):
            return False
    # 检查是否为有效主板股票
    for prefix in STOCK_FILTER["include_prefix"]:
        if code.startswith(prefix):
            return True
    return False
