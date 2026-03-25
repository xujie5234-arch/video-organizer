#!/bin/bash
# 飞牛 NAS 部署脚本

set -e

DEPLOY_DIR="/vol1/1000/docker/media-organizer"

echo "📁 创建目录结构..."
ssh xujie@192.168.31.74 "mkdir -p $DEPLOY_DIR/{data/config,data/db}"

echo "📥 下载代码..."
ssh xujie@192.168.31.74 "curl -sL https://github.com/xujie5234-arch/video-organizer/archive/refs/heads/main.tar.gz | tar xz --strip-components=1 -C $DEPLOY_DIR/app/"

echo "📝 创建 docker-compose.yml..."
ssh xujie@192.168.31.74 "cat > $DEPLOY_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  media-organizer:
    image: python:3.11-slim
    container_name: media-organizer
    restart: unless-stopped
    working_dir: /app
    
    volumes:
      - /mnt/115/videos:/source:ro
      - /vol1/1000/docker/media-organizer/target:/target
      - ./data/config:/app/config
      - ./app:/app
      - ./data/db:/app/data
    
    environment:
      - TZ=Asia/Shanghai
    
    command: >
      sh -c "pip install -r requirements.txt && python main.py --config /app/config/config.yaml"
EOF

echo "⚙️  创建配置文件..."
ssh xujie@192.168.31.74 "cat > $DEPLOY_DIR/data/config/config.yaml" << 'EOF'
source_dir: /source
target_dir: /target
mode: link

video_extensions:
  - .mp4
  - .mkv
  - .avi
  - .mov
  - .wmv
  - .flv
  - .webm
  - .m4v

ignore_folders:
  - "@eaDir"
  - ".DS_Store"
  - "@Recycle"

categories:
  - name: 国产
    keywords: [国产，中文，chinese, china, 国产自拍，selfie]
    target: 国产
    
  - name: 日本
    keywords: [日本，jav, japanese, 日系，HD-, SSIS, IPX, ABW, ADX, MIDE]
    target: 日本
    
  - name: 欧美
    keywords: [欧美，western, american, europe]
    target: 欧美
    
  - name: 韩国
    keywords: [韩国，korean, korea, 韩系]
    target: 韩国
    
  - name: 其他
    keywords: []
    target: 其他

database: /app/data/media.db
log_level: INFO
EOF

echo ""
echo "✅ 部署完成！"
echo ""
echo "📂 部署目录：$DEPLOY_DIR"
echo ""
echo "⚙️  下一步："
echo "1. 编辑 docker-compose.yml 修改 /mnt/115/videos 为你的实际挂载路径"
echo "2. 在飞牛 Docker 管理界面创建项目，路径选择：$DEPLOY_DIR"
echo "3. 启动容器运行分类任务"
echo ""
