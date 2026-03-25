#!/usr/bin/env python3
"""
115 网盘视频分类器
"""

import os
import re
from typing import Dict, List, Optional
from cloud115 import Cloud115


class Cloud115Classifier:
    """115 网盘视频分类器"""
    
    def __init__(self, client: Cloud115, categories: List[Dict], root_cid: str = '0'):
        self.client = client
        self.categories = categories
        self.root_cid = root_cid  # 根目录 ID，默认 0
        self.category_folders = {}  # 缓存分类文件夹 ID
    
    def ensure_category_folders(self) -> Dict[str, str]:
        """确保所有分类文件夹存在，返回 {分类名：文件夹 ID}"""
        # 获取现有文件夹
        existing = self.client.get_folders(self.root_cid)
        existing_names = {f['file_name']: f['cid'] for f in existing}
        
        # 创建缺失的分类文件夹
        for category in self.categories:
            name = category.get('target', category['name'])
            if name not in existing_names:
                result = self.client.create_folder(self.root_cid, name)
                if result:
                    existing_names[name] = result.get('cid')
                    print(f"✅ 创建分类文件夹：{name}")
                else:
                    print(f"❌ 创建分类文件夹失败：{name}")
        
        self.category_folders = existing_names
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
    
    def classify_all(self, source_cid: str = '0', dry_run: bool = False) -> Dict:
        """批量分类所有文件
        
        Args:
            source_cid: 源目录 ID
            dry_run: 预览模式
        """
        results = {'success': 0, 'skipped': 0, 'errors': 0, 'total': 0}
        
        # 确保分类文件夹存在
        self.ensure_category_folders()
        
        # 获取所有文件
        offset = 0
        limit = 100
        
        while True:
            data = self.client.get_files(source_cid, offset, limit)
            if not data:
                break
            
            files = data.get('data', [])
            if not files:
                break
            
            # 只处理视频文件
            video_files = [
                f for f in files 
                if f.get('is_dir') == 0 and 
                f.get('file_type') == 'video' and
                f.get('cate_id') == 4  # 视频分类
            ]
            
            results['total'] += len(video_files)
            
            # 按分类分组
            grouped = {}
            for file_info in video_files:
                category = self.detect_category(file_info['file_name'])
                if category not in grouped:
                    grouped[category] = []
                grouped[category].append(file_info['fid'])
            
            # 批量移动
            for category, file_ids in grouped.items():
                folder_cid = self.category_folders.get(category)
                if not folder_cid:
                    print(f"⚠️  分类文件夹不存在：{category}")
                    results['errors'] += len(file_ids)
                    continue
                
                if dry_run:
                    print(f"📋 [预览] 移动 {len(file_ids)} 个文件到 {category}")
                    results['success'] += len(file_ids)
                else:
                    # 分批移动，每批 50 个
                    for i in range(0, len(file_ids), 50):
                        batch = file_ids[i:i+50]
                        success = self.client.move_files(batch, folder_cid)
                        if success:
                            results['success'] += len(batch)
                            print(f"✅ 移动 {len(batch)} 个文件到 {category}")
                        else:
                            results['errors'] += len(batch)
                            print(f"❌ 移动失败")
                        time.sleep(0.5)  # 避免请求过快
            
            # 检查是否还有更多文件
            if len(files) < limit:
                break
            offset += limit
        
        return results
