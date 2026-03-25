# Magnet Crawler + Video Organizer

基于 magnet-crawler 的磁力链接爬取 + 视频自动分类系统

## 功能特性

### 🕷️ 磁力爬取
- DHT 网络爬取磁力链接
- 自动下载种子文件
- 解析种子文件信息
- 存储到数据库

### 📂 视频分类
- 自动识别视频文件
- 按番号/演员/系列分类
- 在 115 网盘内整理
- 支持 CloudDrive2

### 🌐 Web 管理
- 实时仪表盘
- 种子管理
- 视频分类
- 统计报表

## 快速开始

### Docker 部署

```bash
docker run -d \
  --name magnet-crawler \
  -p 8080:8080 \
  -v ./data:/app/data \
  -v ./config:/app/config \
  -e CD2_URL=http://192.168.31.74:19798 \
  -e CLASSIFY_ENABLED=true \
  shutu736/magnet-crawler:latest
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CD2_URL` | CloudDrive2 地址 | `http://127.0.0.1:19798` |
| `CLASSIFY_ENABLED` | 启用视频分类 | `true` |
| `AUTO_CLASSIFY` | 自动分类新视频 | `false` |
| `CLASSIFY_PATH` | 分类根路径 | `/115` |

## 工作流程

```
1. DHT 爬取 → 获取磁力链接
   ↓
2. Aria2 下载 → 下载种子文件
   ↓
3. 解析种子 → 提取文件信息
   ↓
4. 存储数据库 → SQLite/MySQL
   ↓
5. 视频识别 → 检测视频文件
   ↓
6. 自动分类 → 移动到分类目录
```

## 分类规则

```yaml
categories:
  - name: 日本
    keywords: [SSIS, IPX, ABW, ADX, MIDE, JAV]
    target: /115/Japanese
    
  - name: 国产
    keywords: [国产，中文，selfie, chinese]
    target: /115/Chinese
    
  - name: 欧美
    keywords: [western, american, europe]
    target: /115/Western
    
  - name: 韩国
    keywords: [Korean, korea]
    target: /115/Korean
```

## API 接口

### 种子管理
- `GET /api/torrents` - 获取种子列表
- `POST /api/torrents/download` - 下载种子
- `DELETE /api/torrents/:id` - 删除种子

### 视频分类
- `GET /api/videos` - 获取视频列表
- `POST /api/videos/classify` - 批量分类
- `GET /api/videos/stats` - 分类统计

### 系统设置
- `GET /api/settings` - 获取配置
- `PUT /api/settings` - 更新配置

## 数据库结构

### torrents 表
```sql
CREATE TABLE torrents (
    id INTEGER PRIMARY KEY,
    info_hash TEXT UNIQUE,
    name TEXT,
    size BIGINT,
    files_count INTEGER,
    created_at TIMESTAMP
);
```

### videos 表
```sql
CREATE TABLE videos (
    id INTEGER PRIMARY KEY,
    torrent_id INTEGER,
    file_path TEXT,
    file_name TEXT,
    file_size BIGINT,
    category TEXT,
    tags TEXT,
    classified BOOLEAN,
    FOREIGN KEY (torrent_id) REFERENCES torrents(id)
);
```

## 技术栈

- **后端**: Python + Flask
- **数据库**: SQLite / MySQL
- **前端**: HTML + JavaScript
- **下载**: Aria2 RPC
- **云盘**: CloudDrive2 API

## License

MIT
