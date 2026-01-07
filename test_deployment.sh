#!/bin/bash

#################################################################
# 本地测试部署脚本（用于开发环境测试）
#################################################################

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "=========================================="
echo "  Stock Daily Analyzer - 本地测试"
echo "=========================================="
echo ""

# 检查Python
print_info "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    print_error "Python3 未安装"
    exit 1
fi
python3 --version

# 检查.env
print_info "检查环境配置..."
if [ ! -f ".env" ]; then
    print_error ".env 文件不存在"
    exit 1
fi

# 检查API密钥
if grep -q "your_api_key_here" .env; then
    print_error "请先在 .env 文件中填入真实的API密钥"
    exit 1
fi
print_info "环境配置已就绪"

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    print_info "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
print_info "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
print_info "检查依赖..."
pip install -q -r requirements.txt

# 创建必要目录
mkdir -p logs reports

# 运行测试
print_info "运行LLM测试..."
if python test_llm.py; then
    print_info "测试成功！"
else
    print_error "测试失败"
    exit 1
fi

echo ""
echo "=========================================="
print_info "本地测试通过！可以部署到服务器了。"
echo "=========================================="
echo ""
echo "部署到服务器的方法："
echo ""
echo "1. 一键部署（推荐）："
echo "   scp -r . user@server:/path/to/project"
echo "   ssh user@server"
echo "   cd /path/to/project"
echo "   ./deploy/deploy.sh"
echo ""
echo "2. Docker部署："
echo "   cd deploy/docker"
echo "   ./run.sh"
echo ""
echo "3. 查看详细文档："
echo "   cat DEPLOYMENT.md"
echo "   cat QUICK_DEPLOY.md"
echo ""
