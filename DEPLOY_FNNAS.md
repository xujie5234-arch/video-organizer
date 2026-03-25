# 飞牛 NAS 部署教程

## 📋 部署方式

### 方式一：Docker Compose（推荐）

#### 1️⃣ 创建项目目录

在飞牛 NAS 文件管理中创建一个文件夹，例如：
```
/mnt/data/docker/media-organizer/
```

在该目录下创建以下子目录：
```
media-organizer/
├── docker-compose.yml
├── data/
│   ├── config/    # 配置文件
│   └── db/        # 数据库
└── .env           # 环境变量（可选）
```

---

#### 2️⃣ 准备配置文件

**复制示例配置到 `data/config/config.yaml`：**

```yaml
# Media Organizer 配置文件

# ============ 目录配置 ============
# 注意：Docker 容器内路径已映射，不要修改
source_dir: /source
target_dir: /target

# 操作模式：move(移动) | link(软链接) | copy(复制)
mode: link

# ============ 文件配置 ============
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

# ============ 分类规则 ============
categories:
  - name: 国产
    keywords: [国产，中文，chinese, china, 国产自拍，selfie]
    target: 国产
    
  - name: 日本
    keywords: [日本，jav, japanese, 日系，HD-, SSIS, IPX, ABW, ADX, MIDE]
    target: 日本
    
  - name: 欧美
    keywords: [欧美，western, american, europe, 欧美]
    target: 欧美
    
  - name: 韩国
    keywords: [韩国，korean, korea, 韩系]
    target: 韩国
    
  - name: 其他
    keywords: []
    target: 其他

# ============ 数据库配置 ============
database: /app/data/media.db

# ============ 日志配置 ============
log_level: INFO
```

---

#### 3️⃣ 修改 docker-compose.yml

**编辑 `docker-compose.yml`，修改卷映射路径：**

```yaml
volumes:
  # 修改为你的 115 网盘挂载路径
  - /mnt/115/videos:/source:ro
  
  # 修改为你的 NAS 存储路径
  - /mnt/nas/media:/target
  
  # 配置文件（保持不变）
  - ./data/config:/app/config
  
  # 数据库（保持不变）
  - ./data/db:/app/data
```

**📌 路径说明：**
- `/mnt/115/videos` → 替换为你实际的 115 网盘挂载路径
- `/mnt/nas/media` → 替换为你想存放分类后文件的路径

---

#### 4️⃣ 在飞牛 NAS Docker 中部署

**步骤：**

1. **打开飞牛 NAS → Docker 管理**

2. **创建项目**
   - 项目名称：`media-organizer`
   - 项目路径：选择 `media-organizer` 文件夹
   - 点击"创建"

3. **等待镜像构建**
   - 首次需要下载基础镜像（约 5-10 分钟）
   - 如果下载慢，可以修改 Docker 镜像源：
     - 进入 Docker → 设置 → 镜像仓库
     - 改为：`https://docker.1ms.run` 或 `https://docker.1panel.live`

4. **启动容器**
   - 构建完成后自动启动
   - 状态变为绿色表示运行正常

---

#### 5️⃣ 运行分类任务

**方式 A：通过日志查看**
```bash
# 在飞牛 Docker 管理界面查看容器日志
```

**方式 B：手动执行（推荐）**
```bash
# SSH 登录飞牛 NAS
docker exec -it media-organizer python main.py --dry-run  # 预览模式
docker exec -it media-organizer python main.py            # 正式运行
```

---

### 方式二：定时任务（可选）

如果想定期自动运行，可以在飞牛 NAS 的"任务计划"中添加：

```bash
# 每天凌晨 2 点运行
docker exec media-organizer python main.py
```

---

## 🔧 常见问题

### Q1: 找不到 115 网盘路径？
**A:** 确保 cd2 已经正确挂载，路径通常是：
- `/mnt/115/`
- `/media/115/`
- 或其他你自定义的挂载点

可以用 `ls /mnt/` 查看。

---

### Q2: 分类后文件不见了？
**A:** 默认使用**软链接模式**（`mode: link`），原文件不会移动，只是创建链接。
- 原文件位置不变
- 分类目录是软链接，指向原文件
- 删除链接不影响原文件

如果要实际移动文件，修改配置：
```yaml
mode: move  # 移动文件
```

---

### Q3: 如何添加更多分类规则？
**A:** 编辑 `config.yaml`，在 `categories` 部分添加：

```yaml
categories:
  - name: 你的分类名
    keywords: [关键词 1, 关键词 2, 关键词 3]
    target: 目标文件夹名
```

---

### Q4: 如何查看分类统计？
**A:** 运行：
```bash
docker exec -it media-organizer python main.py --scan-only
```

---

## 📊 目录结构示例

```
/mnt/nas/media/          # 目标目录
├── 国产/
│   ├── 视频 1.mp4
│   └── 视频 2.mkv
├── 日本/
│   ├── SSIS-001.mp4
│   └── IPX-123.mkv
├── 欧美/
│   └── video.mp4
└── 其他/
    └── unknown.mp4
```

---

## 🎯 下一步

1. **配置分类规则** - 根据你的文件特点添加关键词
2. **测试运行** - 先用 `--dry-run` 预览
3. **正式运行** - 确认无误后执行
4. **设置定时任务** - 定期自动整理新文件

---

有问题随时问老徐！👍
