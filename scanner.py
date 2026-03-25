#!/usr/bin/env python3
"""
视频文件扫描器
递归扫描目录，识别视频文件
"""

import os
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime


class VideoScanner:
    """视频文件扫描器"""
    
    def __init__(
        self,
        source_dir: str,
        extensions: List[str] = None,
        ignore_folders: List[str] = None
    ):
        self.source_dir = Path(source_dir)
        self.extensions = set(extensions or ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'])
        self.ignore_folders = set(ignore_folders or ['@eaDir', '.DS_Store', '@Recycle'])
    
    def scan(self) -> List[Dict]:
        """
        扫描源目录，返回视频文件列表
        
        Returns:
            List[Dict]: 文件信息列表，包含 path, name, size, mtime 等
        """
        files = []
        
        if not self.source_dir.exists():
            raise FileNotFoundError(f"源目录不存在：{self.source_dir}")
        
        for root, dirs, filenames in os.walk(self.source_dir):
            # 过滤忽略的文件夹
            dirs[:] = [d for d in dirs if d not in self.ignore_folders]
            
            for filename in filenames:
                file_path = Path(root) / filename
                
                # 检查扩展名
                if file_path.suffix.lower() not in self.extensions:
                    continue
                
                try:
                    stat = file_path.stat()
                    files.append({
                        'path': str(file_path),
                        'name': filename,
                        'size': stat.st_size,
                        'mtime': datetime.fromtimestamp(stat.st_mtime),
                        'relative_path': str(file_path.relative_to(self.source_dir))
                    })
                except (OSError, ValueError) as e:
                    print(f"警告：无法读取文件 {file_path}: {e}")
        
        # 按文件名排序
        files.sort(key=lambda x: x['name'])
        
        return files
    
    def get_stats(self, files: List[Dict]) -> Dict:
        """
        获取扫描统计信息
        
        Args:
            files: 文件列表
            
        Returns:
            Dict: 统计信息
        """
        if not files:
            return {'count': 0, 'total_size': 0, 'avg_size': 0}
        
        total_size = sum(f['size'] for f in files)
        
        return {
            'count': len(files),
            'total_size': total_size,
            'total_size_gb': total_size / 1024 / 1024 / 1024,
            'avg_size': total_size / len(files),
            'avg_size_mb': total_size / len(files) / 1024 / 1024
        }
