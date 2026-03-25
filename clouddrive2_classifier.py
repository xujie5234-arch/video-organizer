#!/usr/bin/env python3
"""
CloudDrive2 视频分类器
"""

import os
from typing import Dict, List
from clouddrive2 import CloudDrive2


class CloudDrive2Classifier:
    """CloudDrive2 视频分类器"""
    
    def __init__(self, client: CloudDrive2, categories: List[Dict], root_path: str = '/115'):
        self.client = client
        self.categories = categories
        self.root_path = root_path  # cd2 挂载路径，默认 /115
        self.category_paths = {}  # 缓存分类文件夹路径
    
    def ensure_category_folders(self) -> Dict[str, str]:
        """确保所有分类文件夹存在"""
        # 获取现有文件夹
        existing = self.client.get_files(self.root_path)
        existing_names = {f['name']: f['path'] for f in existing if f.get('is_dir')}
        
        # 创建缺失的分类文件夹
        for category in self.categories:
            name = category.get('target', category['name'])
            if name not in existing_names:
                folder_path = f"{self.root_path}/{name}"
                success = self.client.create_folder(folder_path)
                if success:
                    existing_names[name] = folder_path
                    print(f"✅ 创建分类文件夹：{folder_path}")
                else:
                    print(f"❌ 创建分类文件夹失败：{folder_path}")
        
        self.category_paths = existing_names
        return existing_names
    
    def detect_category(self, filename: str) -> str:
        """检测文件分类"""
        filename_lower = filename.lower()
        
        for category in self.categories:
            keywords = category.get('keywords', [])
            for keyword in keywords:
                if keyword.lower() in filename_lower:
                    return category.get('target', category['name'])
        
        return '其他'
    
    def classify_files(self, file_paths: List[str]) -> Dict:
        """批量分类文件
        
        Args:
            file_paths: 文件路径列表
        """
        results = {'success': 0, 'errors': 0, 'total': len(file_paths)}
        
        # 确保分类文件夹存在
        self.ensure_category_folders()
        
        # 按分类分组
        grouped = {}
        for file_path in file_paths:
            filename = os.path.basename(file_path)
            category = self.detect_category(filename)
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(file_path)
        
        # 批量移动
        for category, paths in grouped.items():
            folder_path = self.category_paths.get(category)
            if not folder_path:
                print(f"⚠️ 分类文件夹不存在：{category}")
                results['errors'] += len(paths)
                continue
            
            for src_path in paths:
                filename = os.path.basename(src_path)
                dst_path = f"{folder_path}/{filename}"
                
                success = self.client.move_file(src_path, dst_path)
                if success:
                    results['success'] += 1
                    print(f"✅ 移动：{filename} → {category}")
                else:
                    results['errors'] += 1
                    print(f"❌ 移动失败：{filename}")
        
        return results
