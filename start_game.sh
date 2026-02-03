#!/bin/bash

echo "======================================"
echo "团队矛盾冲突模拟器启动脚本"
echo "======================================"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查配置文件
if [ ! -f "config.json" ]; then
    echo "错误: 未找到config.json配置文件"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装Python依赖..."
pip install -q -r backend/requirements.txt

# 检查端口是否被占用
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "警告: 端口5000已被占用，尝试关闭..."
    kill -9 $(lsof -t -i:5000) 2>/dev/null
    sleep 1
fi

# 启动后端服务
echo "启动后端服务..."
cd backend
python3 app.py &
BACKEND_PID=$!
cd ..

# 等待后端启动
echo "等待后端服务启动..."
sleep 3

# 检查后端是否成功启动
if ! ps -p $BACKEND_PID > /dev/null; then
    echo "错误: 后端服务启动失败"
    exit 1
fi

echo ""
echo "======================================"
echo "服务启动成功！"
echo "======================================"
echo "后端API: http://localhost:5000"
echo "前端界面: http://localhost:5000"
echo ""
echo "请在浏览器中打开: http://localhost:5000"
echo ""
echo "按 Ctrl+C 停止服务"
echo "======================================"

# 等待用户中断
trap "echo ''; echo '正在停止服务...'; kill $BACKEND_PID 2>/dev/null; exit 0" INT

# 保持脚本运行
wait $BACKEND_PID
