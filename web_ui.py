#!/usr/bin/env python3
"""
Web UI for Media Organizer
提供可视化界面进行文件分类管理
"""

import os
import yaml
from flask import Flask, render_template, request, jsonify, send_from_directory
from pathlib import Path
from scanner import VideoScanner
from classifier import Classifier
from database import MediaDatabase
from update_manager import update_bp

app = Flask(__name__)
app.register_blueprint(update_bp, url_prefix='/update')

# 配置
CONFIG_PATH = os.environ.get('CONFIG_PATH', '/app/config/config.yaml')
SOURCE_DIR = os.environ.get('SOURCE_DIR', '/source')
TARGET_DIR = os.environ.get('TARGET_DIR', '/target')

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


@app.route('/')
def index():
    """首页 - 显示统计信息"""
    db = MediaDatabase('/app/data/media.db')
    stats = db.get_stats()
    return render_template('index.html', stats=stats)

@app.route('/update')
def update_page():
    """更新管理页面"""
    return render_template('update.html')

@app.route('/config')
def config_page():
    """配置管理页面"""
    return render_template('config.html')


@app.route('/files')
def files():
    """文件浏览页面"""
    return render_template('files.html')


@app.route('/api/files')
def api_files():
    """获取文件列表"""
    cfg = load_config()
    scanner = VideoScanner(
        SOURCE_DIR,
        cfg.get('video_extensions', ['.mp4', '.mkv', '.avi']),
        cfg.get('ignore_folders', [])
    )
    files = scanner.scan()
    
    # 分页
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    start = (page - 1) * per_page
    end = start + per_page
    
    return jsonify({
        'total': len(files),
        'page': page,
        'per_page': per_page,
        'files': files[start:end]
    })


@app.route('/api/classify', methods=['POST'])
def api_classify():
    """分类单个文件"""
    data = request.json
    file_path = data.get('path')
    category = data.get('category')
    
    if not file_path or not category:
        return jsonify({'error': '缺少参数'}), 400
    
    cfg = load_config()
    classifier = Classifier(
        cfg.get('categories', []),
        [],
        TARGET_DIR,
        cfg.get('mode', 'link')
    )
    
    file_info = {'path': file_path, 'name': os.path.basename(file_path)}
    result = classifier.classify(file_info, dry_run=False)
    
    return jsonify(result)


@app.route('/api/classify-all', methods=['POST'])
def api_classify_all():
    """批量分类所有文件"""
    cfg = load_config()
    scanner = VideoScanner(SOURCE_DIR, cfg.get('video_extensions', []), cfg.get('ignore_folders', []))
    files = scanner.scan()
    
    classifier = Classifier(cfg.get('categories', []), [], TARGET_DIR, cfg.get('mode', 'link'))
    
    results = {'success': 0, 'skipped': 0, 'errors': 0}
    
    for file_info in files:
        try:
            result = classifier.classify(file_info)
            if result['action'] == 'moved':
                results['success'] += 1
            elif result['action'] == 'skipped':
                results['skipped'] += 1
            else:
                results['errors'] += 1
        except Exception as e:
            results['errors'] += 1
    
    return jsonify(results)


@app.route('/api/config')
def api_get_config():
    """获取配置"""
    cfg = load_config()
    return jsonify(cfg)

@app.route('/api/config', methods=['PUT'])
def api_update_config():
    """更新配置"""
    new_config = request.json
    save_config(new_config)
    return jsonify({'status': 'ok'})


@app.route('/api/stats')
def api_stats():
    """获取统计信息"""
    db = MediaDatabase('/app/data/media.db')
    stats = db.get_stats()
    return jsonify(stats)


@app.route('/api/search')
def api_search():
    """搜索文件"""
    keyword = request.args.get('q', '')
    db = MediaDatabase('/app/data/media.db')
    results = db.search(keyword)
    return jsonify({'total': len(results), 'files': results[:100]})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
