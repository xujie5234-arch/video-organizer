# Media Organizer - 影视文件分类工具

自动扫描、识别、分类本地影视文件，**支持 Web 界面可视化操作**！

## 功能

- 📁 递归扫描视频文件
- 🏷️ 智能识别文件名（演员、系列、标签）
- 📂 按规则自动分类
- 🔗 支持移动或软链接
- 📊 SQLite 索引数据库
- ⚙️ YAML 配置文件
- 🌐 **Web 界面可视化操作**
- 🔄 **一键在线更新**

## 快速开始

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 配置
cp config.example.yaml config.yaml
# 编辑 config.yaml 设置源目录、分类规则

# 运行
python main.py

# 预览模式（不实际移动文件）
python main.py --dry-run
```

### Docker 部署（飞牛 NAS）

详见 [DEPLOY_FNNAS.md](DEPLOY_FNNAS.md)

```bash
# 使用 docker-compose 运行
docker-compose up -d

# 查看日志
docker-compose logs -f

# Web UI 访问
# http://localhost:5000
```

### 🔄 更新项目

**方式 1：Web UI 更新（推荐）**

1. 访问 `http://your-nas:5000/update`
2. 点击"检查更新"
3. 点击"立即更新"
4. 等待完成，自动重启

**方式 2：SSH 手动更新**

```bash
# SSH 登录飞牛 NAS
ssh xujie@your-nas

# 执行更新脚本
bash /vol1/1000/docker/media-organizer/update.sh
```

**方式 3：Git 更新（开发模式）**

```bash
cd /vol1/1000/docker/media-organizer/app
git pull origin main
docker-compose restart
```

## 目录结构

```
media-organizer/
├── main.py              # 主程序
├── scanner.py           # 文件扫描
├── classifier.py        # 分类引擎
├── database.py          # SQLite 数据库
├── config.example.yaml  # 配置示例
├── requirements.txt     # Python 依赖
└── README.md
```

## 配置说明

编辑 `config.yaml`:

```yaml
source_dir: /mnt/115/videos      # 源目录
target_dir: /mnt/nas/media       # 目标目录
mode: link                       # move=移动，link=软链接

categories:
  - name: 国产
    keywords: [国产，中文，chinese]
  - name: 日本
    keywords: [日本，jav, japanese]
  - name: 欧美
    keywords: [欧美，western, american]

tags:
  - name: 演员名
    keywords: [演员关键词]
```

## 许可证

MIT
