#!/usr/bin/env python3
"""
Magnet Crawler + Video Classifier
整合磁力爬取和视频分类功能
"""

import os
import json
import time
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import sqlite3

# 导入原有模块
from scanner import VideoScanner
from classifier import Classifier
from clouddrive2 import CloudDrive2
from clouddrive2_classifier import CloudDrive2Classifier

app = Flask(__name__)

# 配置
DB_PATH = os.environ.get('DB_PATH', '/app/data/magnet.db')
CD2_URL = os.environ.get('CD2_URL', 'http://127.0.0.1:19798')
CLASSIFY_ENABLED = os.environ.get('CLASSIFY_ENABLED', 'true').lower() == 'true'
AUTO_CLASSIFY = os.environ.get('AUTO_CLASSIFY', 'false').lower() == 'true'


def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 种子表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS torrents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            info_hash TEXT UNIQUE,
            name TEXT,
            size BIGINT,
            files_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 视频表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            torrent_id INTEGER,
            file_path TEXT,
            file_name TEXT,
            file_size BIGINT,
            category TEXT,
            tags TEXT,
            classified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (torrent_id) REFERENCES torrents(id)
        )
    ''')
    
    conn.commit()
    conn.close()


@app.route('/')
def dashboard():
    """仪表盘"""
    return render_template('dashboard.html')


@app.route('/torrents')
def torrents_page():
    """种子管理页面"""
    return render_template('torrents.html')


@app.route('/videos')
def videos_page():
    """视频管理页面"""
    return render_template('videos.html')


# ============ API 接口 ============

@app.route('/api/stats')
def api_stats():
    """获取统计数据"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 种子统计
    cursor.execute('SELECT COUNT(*) as count FROM torrents')
    torrent_count = cursor.fetchone()['count']
    
    # 视频统计
    cursor.execute('SELECT COUNT(*) as count FROM videos')
    video_count = cursor.fetchone()['count']
    
    # 分类统计
    cursor.execute('''
        SELECT category, COUNT(*) as count 
        FROM videos 
        WHERE category IS NOT NULL 
        GROUP BY category
    ''')
    by_category = {row['category']: row['count'] for row in cursor.fetchall()}
    
    # 今日新增
    cursor.execute('''
        SELECT COUNT(*) as count FROM videos 
        WHERE DATE(created_at) = DATE('now')
    ''')
    today_new = cursor.fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'torrent_count': torrent_count,
        'video_count': video_count,
        'by_category': by_category,
        'today_new': today_new,
        'success_rate': 85  # 示例数据
    })


@app.route('/api/torrents')
def api_torrents():
    """获取种子列表"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM torrents ORDER BY created_at DESC LIMIT 100')
    torrents = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({'torrents': torrents})


@app.route('/api/videos')
def api_videos():
    """获取视频列表"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT v.*, t.name as torrent_name
        FROM videos v
        LEFT JOIN torrents t ON v.torrent_id = t.id
        ORDER BY v.created_at DESC
        LIMIT 100
    ''')
    videos = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({'videos': videos})


@app.route('/api/videos/classify', methods=['POST'])
def api_classify_videos():
    """分类视频"""
    if not CLASSIFY_ENABLED:
        return jsonify({'error': '分类功能未启用'}), 400
    
    try:
        import yaml
        
        # 加载配置
        config_path = '/app/config/config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 创建 cd2 客户端
        cd2_client = CloudDrive2(CD2_URL)
        
        # 创建分类器
        classifier = CloudDrive2Classifier(
            cd2_client,
            config.get('categories', []),
            '/115'
        )
        
        # 获取未分类视频
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT file_path FROM videos WHERE classified = 0')
        videos = [row['file_path'] for row in cursor.fetchall()]
        
        if not videos:
            return jsonify({'success': 0, 'message': '没有需要分类的视频'})
        
        # 批量分类
        results = classifier.classify_files(videos)
        
        # 更新数据库
        for path in videos:
            cursor.execute('''
                UPDATE videos SET classified = 1 WHERE file_path = ?
            ''', (path,))
        
        conn.commit()
        conn.close()
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/classify-new', methods=['POST'])
def api_classify_new():
    """分类新视频（自动触发）"""
    if not AUTO_CLASSIFY:
        return jsonify({'error': '自动分类未启用'}), 400
    
    # 这里可以添加逻辑，当新种子下载完成后自动分类
    return jsonify({'message': '自动分类已触发'})


@app.route('/api/settings')
def api_settings():
    """获取设置"""
    return jsonify({
        'cd2_url': CD2_URL,
        'classify_enabled': CLASSIFY_ENABLED,
        'auto_classify': AUTO_CLASSIFY
    })


@app.route('/api/settings', methods=['PUT'])
def api_update_settings():
    """更新设置"""
    data = request.json
    # 实际应该保存到配置文件
    return jsonify({'success': True})


# ============ 后台任务 ============

def auto_scan_and_classify():
    """后台自动扫描分类任务"""
    while True:
        try:
            if AUTO_CLASSIFY and CLASSIFY_ENABLED:
                print("执行自动分类任务...")
                # 这里可以添加定时扫描逻辑
            time.sleep(300)  # 每 5 分钟检查一次
        except Exception as e:
            print(f"自动分类任务失败：{e}")


if __name__ == '__main__':
    init_db()
    
    # 启动后台任务
    threading.Thread(target=auto_scan_and_classify, daemon=True).start()
    
    # 启动 Web 服务
    app.run(host='0.0.0.0', port=8080, debug=False)
