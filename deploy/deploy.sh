#!/bin/bash

#################################################################
# Stock Daily Analyzer - 服务器部署脚本
# 用途: 一键部署项目到Linux服务器
#################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_NAME="stock-daily-analyzer"
DEPLOY_USER="${DEPLOY_USER:-$USER}"
INSTALL_DIR="${INSTALL_DIR:-$HOME/$PROJECT_NAME}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
LOG_DIR="/var/log/stock-analyzer"

# 打印彩色消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_warn "检测到root用户，建议使用普通用户部署"
        read -p "是否继续? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查系统依赖
check_dependencies() {
    print_info "检查系统依赖..."
    
    if ! command -v $PYTHON_BIN &> /dev/null; then
        print_error "Python3 未安装，请先安装 Python 3.9+"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_BIN --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    print_info "Python 版本: $PYTHON_VERSION"
    
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 未安装，请先安装 pip3"
        exit 1
    fi
    
    if ! command -v git &> /dev/null; then
        print_warn "Git 未安装，将无法直接从仓库部署"
    fi
}

# 创建项目目录
setup_directories() {
    print_info "创建项目目录..."
    
    # 创建安装目录
    if [ ! -d "$INSTALL_DIR" ]; then
        mkdir -p "$INSTALL_DIR"
        print_info "创建目录: $INSTALL_DIR"
    fi
    
    # 创建日志目录
    if [ ! -d "$LOG_DIR" ]; then
        sudo mkdir -p "$LOG_DIR"
        sudo chown $DEPLOY_USER:$DEPLOY_USER "$LOG_DIR"
        print_info "创建日志目录: $LOG_DIR"
    fi
    
    # 创建必要的子目录
    mkdir -p "$INSTALL_DIR/logs"
    mkdir -p "$INSTALL_DIR/reports"
}

# 复制项目文件
copy_files() {
    print_info "复制项目文件到 $INSTALL_DIR..."
    
    # 如果从当前目录部署
    if [ -f "main.py" ]; then
        cp -r *.py "$INSTALL_DIR/"
        cp requirements.txt "$INSTALL_DIR/"
        
        # 复制.env文件（如果存在）
        if [ -f ".env" ]; then
            cp .env "$INSTALL_DIR/"
            print_info "已复制 .env 配置文件"
        else
            print_warn ".env 文件不存在，请手动创建"
        fi
    else
        print_error "未找到项目文件，请在项目根目录运行此脚本"
        exit 1
    fi
}

# 安装Python依赖
install_dependencies() {
    print_info "安装Python依赖..."
    
    cd "$INSTALL_DIR"
    
    # 创建虚拟环境（推荐）
    if [ ! -d "venv" ]; then
        print_info "创建Python虚拟环境..."
        $PYTHON_BIN -m venv venv
    fi
    
    # 激活虚拟环境并安装依赖
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_info "依赖安装完成"
}

# 配置环境变量
setup_env() {
    print_info "配置环境变量..."
    
    if [ ! -f "$INSTALL_DIR/.env" ]; then
        print_warn "未找到 .env 文件，正在创建..."
        cat > "$INSTALL_DIR/.env" << EOF
ARK_API_KEY=your_api_key_here
ARK_MODEL_ID=your_model_endpoint_id
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3/chat/completions
EOF
        print_warn "请编辑 $INSTALL_DIR/.env 文件，填入你的API密钥"
        print_warn "vim $INSTALL_DIR/.env"
    else
        print_info ".env 文件已存在"
    fi
    
    # 设置文件权限
    chmod 600 "$INSTALL_DIR/.env"
}

# 配置systemd服务
setup_systemd() {
    print_info "配置 systemd 服务..."
    
    # 创建服务文件
    SERVICE_FILE="/tmp/stock-analyzer.service"
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Stock Daily Analyzer Service
After=network.target

[Service]
Type=oneshot
User=$DEPLOY_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/bin:/usr/local/bin"
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/main.py
StandardOutput=append:$LOG_DIR/output.log
StandardError=append:$LOG_DIR/error.log

# 资源限制
MemoryMax=2G
CPUQuota=80%

[Install]
WantedBy=multi-user.target
EOF

    # 安装服务文件
    sudo cp "$SERVICE_FILE" /etc/systemd/system/
    sudo systemctl daemon-reload
    
    print_info "systemd 服务配置完成"
    print_info "可以使用以下命令管理服务:"
    echo "  启动: sudo systemctl start stock-analyzer"
    echo "  停止: sudo systemctl stop stock-analyzer"
    echo "  状态: sudo systemctl status stock-analyzer"
}

# 配置cron定时任务
setup_cron() {
    print_info "配置定时任务..."
    
    # 创建cron任务
    CRON_CMD="30 15 * * 1-5 cd $INSTALL_DIR && $INSTALL_DIR/venv/bin/python $INSTALL_DIR/main.py >> $LOG_DIR/cron.log 2>&1"
    
    # 检查是否已存在
    if crontab -l 2>/dev/null | grep -q "stock-daily-analyzer"; then
        print_warn "定时任务已存在，跳过"
    else
        print_info "添加定时任务: 每个交易日 15:30 执行"
        (crontab -l 2>/dev/null; echo "# Stock Daily Analyzer"; echo "$CRON_CMD") | crontab -
        print_info "定时任务添加完成"
    fi
    
    print_info "当前定时任务列表:"
    crontab -l | grep -A1 "Stock"
}

# 测试运行
test_run() {
    print_info "执行测试运行..."
    
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    print_info "运行测试脚本..."
    if $PYTHON_BIN test_llm.py; then
        print_info "测试运行成功！"
    else
        print_error "测试运行失败，请检查配置"
        exit 1
    fi
}

# 显示部署信息
show_deployment_info() {
    echo ""
    echo "=========================================="
    print_info "部署完成！"
    echo "=========================================="
    echo ""
    echo "项目目录: $INSTALL_DIR"
    echo "日志目录: $LOG_DIR"
    echo "Python环境: $INSTALL_DIR/venv"
    echo ""
    echo "运行方式:"
    echo "  1. 手动运行:"
    echo "     cd $INSTALL_DIR"
    echo "     source venv/bin/activate"
    echo "     python main.py"
    echo ""
    echo "  2. 使用systemd服务:"
    echo "     sudo systemctl start stock-analyzer"
    echo ""
    echo "  3. 自动定时任务:"
    echo "     已配置为每个交易日 15:30 自动运行"
    echo ""
    echo "查看日志:"
    echo "  tail -f $LOG_DIR/output.log"
    echo "  tail -f $LOG_DIR/cron.log"
    echo ""
    echo "=========================================="
}

# 主函数
main() {
    echo "=========================================="
    echo "  Stock Daily Analyzer - 部署脚本"
    echo "=========================================="
    echo ""
    
    check_root
    check_dependencies
    setup_directories
    copy_files
    install_dependencies
    setup_env
    setup_systemd
    setup_cron
    test_run
    show_deployment_info
}

# 运行主函数
main
