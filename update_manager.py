#!/usr/bin/env python3
"""
Web UI 更新管理页面
"""

from flask import Blueprint, render_template, request, jsonify
import subprocess
import os

update_bp = Blueprint('update', __name__)

@update_bp.route('/update')
def update_page():
    """更新管理页面"""
    return render_template('update.html')

@update_bp.route('/api/update', methods=['POST'])
def api_update():
    """执行更新"""
    try:
        # 在后台执行更新脚本
        result = subprocess.run(
            ['bash', '/app/update.sh'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return jsonify({
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr
        })
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': '更新超时（超过 5 分钟）'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@update_bp.route('/api/version')
def api_version():
    """获取当前版本信息"""
    try:
        # 从 git 获取版本
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%h - %s (%ci)'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        version = result.stdout.strip() if result.returncode == 0 else 'unknown'
        
        # 检查是否有更新
        result = subprocess.run(
            ['git', 'fetch', 'origin', 'main'],
            capture_output=True,
            text=True,
            cwd='/app',
            timeout=10
        )
        
        result = subprocess.run(
            ['git', 'rev-list', '--count', 'HEAD..origin/main'],
            capture_output=True,
            text=True,
            cwd='/app'
        )
        
        updates_available = int(result.stdout.strip()) if result.returncode == 0 and result.stdout.strip().isdigit() else 0
        
        return jsonify({
            'version': version,
            'updates_available': updates_available
        })
    except Exception as e:
        return jsonify({
            'version': 'unknown',
            'updates_available': 0,
            'error': str(e)
        })
