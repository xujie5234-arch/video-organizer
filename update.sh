#!/bin/bash
# 项目更新脚本 - 从 GitHub 拉取最新代码并重新部署

set -e

DEPLOY_DIR="/vol1/1000/docker/media-organizer"
REPO_URL="https://github.com/xujie5234-arch/video-organizer/archive/refs/heads/main.tar.gz"

echo "🚀 开始更新 Media Organizer..."

# 1. 备份当前配置
echo "📦 备份配置文件..."
if [ -d "$DEPLOY_DIR/data/config" ]; then
    cp -r "$DEPLOY_DIR/data/config" "$DEPLOY_DIR/data/config.bak.$(date +%Y%m%d%H%M%S)"
fi

# 2. 停止容器
echo "⏹️  停止容器..."
docker stop media-organizer 2>/dev/null || true
docker rm media-organizer 2>/dev/null || true

# 3. 下载最新代码
echo "📥 下载最新代码..."
cd "$DEPLOY_DIR/app"
rm -rf *.py templates/ __pycache__/ 2>/dev/null || true
curl -sL "$REPO_URL" | tar xz --strip-components=1

# 4. 恢复配置
echo "♻️  恢复配置..."
if [ -d "$DEPLOY_DIR/data/config.bak."* ]; then
    LATEST_BAK=$(ls -t "$DEPLOY_DIR"/data/config.bak.* | head -1)
    cp -r "$LATEST_BAK"/* "$DEPLOY_DIR/data/config/" 2>/dev/null || true
fi

# 5. 重新创建容器
echo "🔄 重新创建容器..."
cd "$DEPLOY_DIR"
docker-compose up -d --build

# 6. 清理旧备份（保留最近 3 个）
echo "🧹 清理旧备份..."
cd "$DEPLOY_DIR/data"
ls -t | grep config.bak | tail -n +4 | xargs rm -rf 2>/dev/null || true

echo ""
echo "✅ 更新完成！"
echo ""
echo "📊 容器状态："
docker ps | grep media-organizer
echo ""
echo "🌐 Web UI: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "📝 查看日志：docker logs -f media-organizer"
