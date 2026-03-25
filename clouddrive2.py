#!/usr/bin/env python3
"""
CloudDrive2 API 客户端
"""

import requests
import json
from typing import Dict, List, Optional

class CloudDrive2:
    """CloudDrive2 API 客户端"""
    
    def __init__(self, base_url: str = 'http://127.0.0.1:19798', token: str = ''):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if token:
            self.session.headers.update({'Authorization': f'Bearer {token}'})
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            resp = self.session.get(f'{self.base_url}/api/fs/get', timeout=10)
            return resp.status_code == 200
        except:
            return False
    
    def get_drives(self) -> List[Dict]:
        """获取所有挂载的云盘"""
        try:
            resp = self.session.get(f'{self.base_url}/api/fs/list', timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('content', [])
        except Exception as e:
            print(f"获取云盘列表失败：{e}")
        return []
    
    def get_files(self, path: str = '/') -> List[Dict]:
        """获取指定路径的文件列表"""
        try:
            resp = self.session.get(f'{self.base_url}/api/fs/list', 
                                   params={'path': path}, 
                                   timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('content', [])
        except Exception as e:
            print(f"获取文件列表失败：{e}")
        return []
    
    def get_file_info(self, path: str) -> Optional[Dict]:
        """获取文件信息"""
        try:
            resp = self.session.get(f'{self.base_url}/api/fs/get', 
                                   params={'path': path}, 
                                   timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"获取文件信息失败：{e}")
        return None
    
    def create_folder(self, path: str) -> bool:
        """创建文件夹"""
        try:
            resp = self.session.post(f'{self.base_url}/api/fs/mkdir', 
                                    params={'path': path}, 
                                    timeout=10)
            return resp.status_code == 200
        except Exception as e:
            print(f"创建文件夹失败：{e}")
        return False
    
    def move_file(self, src_path: str, dst_path: str) -> bool:
        """移动/重命名文件"""
        try:
            data = {
                'src': src_path,
                'dst': dst_path
            }
            resp = self.session.post(f'{self.base_url}/api/fs/move', 
                                    json=data, 
                                    timeout=30)
            return resp.status_code == 200
        except Exception as e:
            print(f"移动文件失败：{e}")
        return False
    
    def copy_file(self, src_path: str, dst_path: str) -> bool:
        """复制文件"""
        try:
            data = {
                'src': src_path,
                'dst': dst_path
            }
            resp = self.session.post(f'{self.base_url}/api/fs/copy', 
                                    json=data, 
                                    timeout=30)
            return resp.status_code == 200
        except Exception as e:
            print(f"复制文件失败：{e}")
        return False
    
    def delete_file(self, path: str) -> bool:
        """删除文件"""
        try:
            resp = self.session.post(f'{self.base_url}/api/fs/remove', 
                                    params={'path': path}, 
                                    timeout=10)
            return resp.status_code == 200
        except Exception as e:
            print(f"删除文件失败：{e}")
        return False
    
    def get_storage_info(self) -> Optional[Dict]:
        """获取存储信息"""
        try:
            # cd2 可能没有直接的存储信息 API，这里尝试获取根目录信息
            resp = self.session.get(f'{self.base_url}/api/fs/get', 
                                   params={'path': '/'}, 
                                   timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    'total': data.get('size', 0),
                    'used': data.get('size', 0),
                    'free': 0  # cd2 可能不提供这个信息
                }
        except Exception as e:
            print(f"获取存储信息失败：{e}")
        return None
    
    def search_files(self, keyword: str, path: str = '/') -> List[Dict]:
        """搜索文件"""
        try:
            # cd2 的搜索 API 可能不同，这里使用通用方法
            resp = self.session.get(f'{self.base_url}/api/search', 
                                   params={'keywords': keyword, 'path': path}, 
                                   timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('content', [])
        except Exception as e:
            print(f"搜索文件失败：{e}")
        return []
