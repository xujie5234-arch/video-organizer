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

@app.route('/folders')
def folders_page():
    """文件夹浏览页面"""
    return render_template('folders.html')

@app.route('/logs')
def logs_page():
    """运行日志页面"""
    return render_template('logs.html')


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


@app.route('/api/folders')
def api_folders():
    """获取文件夹列表"""
    import subprocess
    try:
        # 列出源目录下的所有文件夹
        result = subprocess.run(
            ['find', SOURCE_DIR, '-maxdepth', '2', '-type', 'd'],
            capture_output=True, text=True, timeout=10
        )
        folders = [f for f in result.stdout.strip().split('\n') if f]
        return jsonify({'folders': folders})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/folders/<path:folder_path>')
def api_folder_files(folder_path):
    """获取指定文件夹下的文件"""
    import subprocess
    try:
        folder = '/' + folder_path  # 重建绝对路径
        result = subprocess.run(
            ['find', folder, '-maxdepth', '1', '-type', 'f', '-name', '*.mp4', '-o', '-name', '*.mkv', '-o', '-name', '*.avi'],
            capture_output=True, text=True, timeout=10
        )
        files = []
        for f in result.stdout.strip().split('\n'):
            if f:
                stat_result = subprocess.run(['stat', '-c', '%s', f], capture_output=True, text=True)
                size = int(stat_result.stdout.strip()) if stat_result.returncode == 0 else 0
                files.append({'path': f, 'name': os.path.basename(f), 'size': size})
        return jsonify({'total': len(files), 'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/logs')
def api_logs():
    """获取 Docker 容器日志"""
    import subprocess
    try:
        result = subprocess.run(
            ['docker', 'logs', 'media-organizer', '--tail', '100'],
            capture_output=True, text=True, timeout=10
        )
        return jsonify({
            'stdout': result.stdout,
            'stderr': result.stderr
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 115 Cookie 存储
COOKIE_FILE = '/app/data/115_cookie.txt'

# cd2 配置存储
CD2_CONFIG_FILE = '/app/data/cd2_config.json'

def load_115_cookie():
    """加载 115 Cookie"""
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, 'r') as f:
            return f.read().strip()
    return None

def save_115_cookie(cookie):
    """保存 115 Cookie"""
    with open(COOKIE_FILE, 'w') as f:
        f.write(cookie)


@app.route('/115')
def page_115():
    """115 网盘整理页面"""
    return render_template('115.html')

@app.route('/cd2')
def page_cd2():
    """CloudDrive2 整理页面"""
    return render_template('cd2.html')

# cd2 配置相关 API
def load_cd2_config():
    """加载 cd2 配置"""
    if os.path.exists(CD2_CONFIG_FILE):
        with open(CD2_CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {'url': 'http://127.0.0.1:19766', 'token': ''}

def save_cd2_config(config):
    """保存 cd2 配置"""
    with open(CD2_CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def get_cd2_client():
    """获取 cd2 客户端"""
    from clouddrive2 import CloudDrive2
    config = load_cd2_config()
    return CloudDrive2(config.get('url', 'http://127.0.0.1:19766'), config.get('token', ''))


@app.route('/api/cd2/status')
def api_cd2_status():
    """检查 cd2 连接状态"""
    try:
        config = load_cd2_config()
        client = get_cd2_client()
        if client.test_connection():
            return jsonify({'connected': True, 'url': config.get('url')})
    except:
        pass
    return jsonify({'connected': False})


@app.route('/api/cd2/config', methods=['POST'])
def api_cd2_config():
    """保存 cd2 配置"""
    data = request.json
    config = {
        'url': data.get('url', 'http://127.0.0.1:19766'),
        'token': data.get('token', '')
    }
    save_cd2_config(config)
    return jsonify({'success': True})


@app.route('/api/cd2/test', methods=['POST'])
def api_cd2_test():
    """测试 cd2 连接"""
    data = request.json
    try:
        from clouddrive2 import CloudDrive2
        client = CloudDrive2(data.get('url', 'http://127.0.0.1:19766'), data.get('token', ''))
        if client.test_connection():
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '无法连接 cd2'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/cd2/folders')
def api_cd2_folders():
    """获取 cd2 文件夹列表"""
    path = request.args.get('path', '/115')
    try:
        client = get_cd2_client()
        files = client.get_files(path)
        folders = [{'name': f['name'], 'path': f['path']} for f in files if f.get('is_dir')]
        return jsonify({'folders': folders})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cd2/files')
def api_cd2_files():
    """获取 cd2 文件列表"""
    path = request.args.get('path', '/115')
    try:
        client = get_cd2_client()
        files = client.get_files(path)
        # 只返回视频文件
        video_files = [
            {'name': f['name'], 'path': f['path'], 'size': f.get('size', 0)}
            for f in files
            if not f.get('is_dir') and f.get('name', '').lower().endswith(('.mp4', '.mkv', '.avi', '.mov'))
        ]
        return jsonify({'files': video_files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cd2/classify', methods=['POST'])
def api_cd2_classify():
    """分类 cd2 文件"""
    try:
        import yaml
        from clouddrive2_classifier import CloudDrive2Classifier
        
        # 加载配置
        config_path = os.environ.get('CONFIG_PATH', '/app/config/config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        client = get_cd2_client()
        classifier = CloudDrive2Classifier(client, config.get('categories', []), '/115')
        
        data = request.json
        file_paths = data.get('file_paths', [])
        
        results = classifier.classify_files(file_paths)
        return jsonify({
            'success': results.get('success', 0),
            'errors': results.get('errors', 0)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/115/status')
def api_115_status():
    """检查 115 登录状态"""
    cookie = load_115_cookie()
    if not cookie:
        return jsonify({'logged_in': False})
    
    try:
        from cloud115 import Cloud115
        client = Cloud115(cookie)
        if client.verify_cookie():
            user = client.get_user_info()
            return jsonify({
                'logged_in': True,
                'user_id': user.get('user_id'),
                'user_name': user.get('user_name')
            })
    except Exception as e:
        pass
    
    return jsonify({'logged_in': False})


@app.route('/api/115/storage')
def api_115_storage():
    """获取 115 存储信息"""
    cookie = load_115_cookie()
    if not cookie:
        return jsonify({'error': '未登录'}), 401
    
    try:
        from cloud115 import Cloud115
        client = Cloud115(cookie)
        storage = client.get_storage_info()
        if storage:
            return jsonify({
                'total': storage.get('total', 0),
                'free': storage.get('free', 0),
                'used': storage.get('used', 0)
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': '获取失败'}), 500


@app.route('/api/115/folders')
def api_115_folders():
    """获取 115 文件夹列表"""
    cookie = load_115_cookie()
    cid = request.args.get('cid', '0')
    
    if not cookie:
        return jsonify({'error': '未登录'}), 401
    
    try:
        from cloud115 import Cloud115
        client = Cloud115(cookie)
        folders = client.get_folders(cid)
        return jsonify({
            'folders': [{'cid': f['cid'], 'name': f['file_name']} for f in folders]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/115/files')
def api_115_files():
    """获取 115 文件列表"""
    cookie = load_115_cookie()
    cid = request.args.get('cid', '0')
    
    if not cookie:
        return jsonify({'error': '未登录'}), 401
    
    try:
        from cloud115 import Cloud115
        client = Cloud115(cookie)
        data = client.get_files(cid, 0, 100)
        if data:
            files = [
                {'fid': f['fid'], 'name': f['file_name'], 'size': f['file_size']}
                for f in data.get('data', [])
                if f.get('is_dir') == 0 and f.get('cate_id') == 4
            ]
            return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return jsonify({'files': []})


@app.route('/api/115/cookie', methods=['POST'])
def api_115_cookie():
    """保存 115 Cookie"""
    data = request.json
    cookie = data.get('cookie', '')
    
    if not cookie:
        return jsonify({'success': False, 'error': 'Cookie 不能为空'})
    
    try:
        from cloud115 import Cloud115
        client = Cloud115(cookie)
        if client.verify_cookie():
            save_115_cookie(cookie)
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Cookie 无效'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/115/test', methods=['POST'])
def api_115_test():
    """测试 115 Cookie"""
    data = request.json
    cookie = data.get('cookie', '')
    
    try:
        from cloud115 import Cloud115
        client = Cloud115(cookie)
        if client.verify_cookie():
            user = client.get_user_info()
            return jsonify({
                'success': True,
                'user_id': user.get('user_id'),
                'user_name': user.get('user_name')
            })
        else:
            return jsonify({'success': False, 'error': 'Cookie 无效'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/115/classify', methods=['POST'])
def api_115_classify():
    """分类 115 文件"""
    cookie = load_115_cookie()
    if not cookie:
        return jsonify({'success': False, 'error': '未登录'}), 401
    
    data = request.json
    file_ids = data.get('file_ids', [])
    
    if not file_ids:
        return jsonify({'success': False, 'error': '没有选择文件'})
    
    try:
        from cloud115 import Cloud115, Cloud115Classifier
        import yaml
        
        # 加载配置
        config_path = os.environ.get('CONFIG_PATH', '/app/config/config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        client = Cloud115(cookie)
        classifier = Cloud115Classifier(client, config.get('categories', []))
        
        # 确保分类文件夹存在
        folders = classifier.ensure_category_folders()
        
        # 按分类分组文件
        grouped = {}
        for fid in file_ids:
            # 这里需要根据文件 ID 获取文件名来判断分类
            # 简化处理：假设前端已经传了文件名
            category = '其他'  # 实际需要获取文件信息
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(fid)
        
        # 批量移动
        results = {'success': 0, 'errors': 0}
        for category, fids in grouped.items():
            folder_cid = folders.get(category)
            if folder_cid:
                success = client.move_files(fids, folder_cid)
                if success:
                    results['success'] += len(fids)
                else:
                    results['errors'] += len(fids)
            else:
                results['errors'] += len(fids)
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
