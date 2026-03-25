#!/usr/bin/env python3
"""
115 网盘 API 客户端
"""

import requests
import json
import time
from typing import Dict, List, Optional

class Cloud115:
    """115 网盘客户端"""
    
    def __init__(self, cookie: str):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': cookie,
            'Referer': 'https://115.com/'
        })
        self.base_url = 'https://webapi.115.com'
        self.upload_url = 'http://uplb.115.com'
    
    def get_user_info(self) -> Optional[Dict]:
        """获取用户信息"""
        try:
            resp = self.session.get(f'{self.base_url}/user/info', timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('state'):
                    return data.get('data', {})
        except Exception as e:
            print(f"获取用户信息失败：{e}")
        return None
    
    def get_storage_info(self) -> Optional[Dict]:
        """获取存储空间信息"""
        try:
            resp = self.session.get(f'{self.base_url}/user/storage', timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('state'):
                    return data.get('data', {})
        except Exception as e:
            print(f"获取存储信息失败：{e}")
        return None
    
    def get_files(self, cid: str = '0', offset: int = 0, limit: int = 100) -> Optional[Dict]:
        """获取文件列表"""
        try:
            params = {
                'cid': cid,
                'offset': offset,
                'limit': limit,
                'asc': 0,
                'order': 'file_name',
                'format': 'json',
                'show_dir': 1,
                'type': 0,
                'star': 0,
                'is_q': 1,
                'record_open_time': 1,
                'code': ''
            }
            resp = self.session.get(f'{self.base_url}/files', params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('state'):
                    return data.get('data', {})
        except Exception as e:
            print(f"获取文件列表失败：{e}")
        return None
    
    def get_folders(self, cid: str = '0') -> List[Dict]:
        """获取指定目录下的所有文件夹"""
        folders = []
        try:
            data = self.get_files(cid, 0, 1000)
            if data and 'path' in data:
                folders = [f for f in data.get('path', []) if f.get('is_dir') == 1]
        except Exception as e:
            print(f"获取文件夹失败：{e}")
        return folders
    
    def create_folder(self, parent_cid: str, folder_name: str) -> Optional[Dict]:
        """创建文件夹"""
        try:
            data = {
                'parentid': parent_cid,
                'file_name': folder_name
            }
            resp = self.session.post(f'{self.base_url}/files/add_folder', data=data, timeout=10)
            if resp.status_code == 200:
                result = resp.json()
                if result.get('state'):
                    return result.get('data', {})
        except Exception as e:
            print(f"创建文件夹失败：{e}")
        return None
    
    def move_files(self, files: List[str], folder_cid: str) -> bool:
        """移动文件到新文件夹
        
        Args:
            files: 文件 ID 列表
            folder_cid: 目标文件夹 ID
        """
        try:
            data = {
                'fid': ','.join(files),
                'pid': folder_cid
            }
            resp = self.session.post(f'{self.base_url}/files/move', data=data, timeout=30)
            if resp.status_code == 200:
                result = resp.json()
                return result.get('state', False)
        except Exception as e:
            print(f"移动文件失败：{e}")
        return False
    
    def search_files(self, keyword: str, cid: str = '0') -> List[Dict]:
        """搜索文件"""
        results = []
        try:
            params = {
                'search_key': keyword,
                'cid': cid,
                'type': 4,  # 视频
                'limit': 100,
                'offset': 0
            }
            resp = self.session.get(f'{self.base_url}/files/search', params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('state'):
                    results = data.get('data', [])
        except Exception as e:
            print(f"搜索文件失败：{e}")
        return results
    
    def verify_cookie(self) -> bool:
        """验证 Cookie 是否有效"""
        user_info = self.get_user_info()
        return user_info is not None and 'user_id' in user_info
