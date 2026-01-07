#!/bin/bash

#################################################################
# Docker 运行脚本
#################################################################

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 检查.env文件
if [ ! -f "../../.env" ]; then
    print_warn ".env 文件不存在，正在创建模板..."
    cat > ../../.env << EOF
ARK_API_KEY=your_api_key_here
ARK_MODEL_ID=your_model_endpoint_id
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3/chat/completions
EOF
    print_warn "请编辑 .env 文件，填入你的API密钥"
    exit 1
fi

# 构建并运行
print_info "构建 Docker 镜像..."
docker-compose build

print_info "启动容器..."
docker-compose up -d

print_info "容器已启动！"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止容器: docker-compose down"
echo "重启容器: docker-compose restart"
