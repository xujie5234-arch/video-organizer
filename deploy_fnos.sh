#!/bin/bash
# 飞牛 NAS 部署脚本 - Media Organizer
# 使用方法：在飞牛 NAS 上执行 bash deploy.sh

set -e

echo "🚀 开始部署 Media Organizer..."

# 创建目录
DEPLOY_DIR="/vol1/1000/docker/media-organizer"
echo "📁 创建目录：$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"/{data/config,data/db}

# 创建 docker-compose.yml
cat > "$DEPLOY_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  media-organizer:
    image: python:3.11-slim
    container_name: media-organizer
    restart: unless-stopped
    working_dir: /app
    
    # 卷映射
    volumes:
      # 源目录：请修改为你的 115 网盘挂载路径
      - /mnt/115/videos:/source:ro
      
      # 目标目录：请修改为你的 NAS 存储路径
      - /vol1/1000/media/sorted:/target
      
      # 配置文件
      - ./data/config:/app/config
      
      # 代码目录
      - ./app:/app
      
      # 数据库持久化
      - ./data/db:/app/data
    
    # 环境变量
    environment:
      - TZ=Asia/Shanghai
    
    # 命令：首次运行安装依赖并执行
    command: >
      sh -c "pip install -r requirements.txt && python main.py --config /app/config/config.yaml"

networks:
  default:
    name: media-organizer-net
EOF

# 创建 config.yaml
cat > "$DEPLOY_DIR/data/config/config.yaml" << 'EOF'
# Media Organizer 配置文件

source_dir: /source
target_dir: /target
mode: link  # link=软链接，move=移动，copy=复制

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

# 创建 app 目录并下载代码
mkdir -p "$DEPLOY_DIR/app"

echo "📥 下载应用代码..."
cd "$DEPLOY_DIR/app"

# 从 GitHub 下载
curl -sL https://github.com/xujie5234-arch/video-organizer/archive/refs/heads/main.tar.gz | tar xz --strip-components=1

# 或者手动创建文件（如果 curl 失败）
if [ ! -f "main.py" ]; then
    echo "⚠️  GitHub 下载失败，创建基础文件..."
    
    # main.py
    cat > main.py << 'MAINEOF'
#!/usr/bin/env python3
import os, sys, yaml
from pathlib import Path
from scanner import VideoScanner
from classifier import Classifier
from database import MediaDatabase

def load_config(path="config.yaml"):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

if __name__ == '__main__':
    cfg = load_config("/app/config/config.yaml")
    scanner = VideoScanner(cfg['source_dir'], cfg.get('video_extensions', []), cfg.get('ignore_folders', []))
    files = scanner.scan()
    print(f"找到 {len(files)} 个视频文件")
    
    classifier = Classifier(cfg.get('categories', []), [], cfg['target_dir'], cfg.get('mode', 'link'))
    for f in files:
        result = classifier.classify(f)
        print(f"{f['name']} -> {result.get('category', '未知')}")
MAINEOF

    # scanner.py
    cat > scanner.py << 'SCANEOF'
import os
from pathlib import Path

class VideoScanner:
    def __init__(self, source_dir, extensions=None, ignore_folders=None):
        self.source_dir = Path(source_dir)
        self.extensions = set(extensions or ['.mp4', '.mkv', '.avi'])
        self.ignore_folders = set(ignore_folders or ['@eaDir'])
    
    def scan(self):
        files = []
        for root, dirs, filenames in os.walk(self.source_dir):
            dirs[:] = [d for d in dirs if d not in self.ignore_folders]
            for fn in filenames:
                p = Path(root) / fn
                if p.suffix.lower() in self.extensions:
                    stat = p.stat()
                    files.append({'path': str(p), 'name': fn, 'size': stat.st_size})
        return files
SCANEOF

    # classifier.py
    cat > classifier.py << 'CLSEOF'
import os, shutil
from pathlib import Path

class Classifier:
    def __init__(self, categories, tags, target_dir, mode='link'):
        self.categories = categories
        self.target_dir = Path(target_dir)
        self.mode = mode
    
    def classify(self, file_info):
        filename = file_info['name'].lower()
        category = '其他'
        for cat in self.categories:
            for kw in cat.get('keywords', []):
                if kw.lower() in filename:
                    category = cat.get('target', cat['name'])
                    break
        target = self.target_dir / category / file_info['name']
        target.parent.mkdir(parents=True, exist_ok=True)
        if self.mode == 'link' and not target.exists():
            target.symlink_to(file_info['path'])
        elif self.mode == 'move':
            shutil.move(file_info['path'], str(target))
        return {'category': category, 'target': str(target)}
CLSEOF
fi

echo ""
echo "✅ 文件准备完成！"
echo ""
echo "📂 部署目录：$DEPLOY_DIR"
echo ""
echo "⚙️  下一步："
echo "1. 编辑 docker-compose.yml 修改路径映射"
echo "2. 编辑 data/config/config.yaml 修改分类规则"
echo "3. 在飞牛 Docker 管理界面创建项目"
echo ""
echo "🎉 部署脚本执行完成！"
