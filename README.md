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
# 构建镜像
docker build -t media-organizer .

# 使用 docker-compose 运行
docker-compose up -d

# 查看日志
docker-compose logs -f
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
