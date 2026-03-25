#!/usr/bin/env python3
"""
视频文件分类器
根据规则自动分类视频文件
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Classifier:
    """视频文件分类器"""
    
    def __init__(
        self,
        categories: List[Dict],
        tags: List[Dict],
        target_dir: str,
        mode: str = 'link'
    ):
        self.categories = categories
        self.tags = tags
        self.target_dir = Path(target_dir)
        self.mode = mode  # move, link, copy
    
    def classify(self, file_info: Dict, dry_run: bool = False) -> Dict:
        """
        分类单个文件
        
        Args:
            file_info: 文件信息
            dry_run: 预览模式
            
        Returns:
            Dict: 分类结果
        """
        filename = file_info['name']
        source_path = Path(file_info['path'])
        
        # 识别分类
        category = self._detect_category(filename)
        
        # 识别标签
        detected_tags = self._detect_tags(filename)
        
        # 构建目标路径
        target_path = self._build_target_path(category, filename, detected_tags)
        
        # 检查是否已存在
        if target_path.exists():
            return {
                'action': 'skipped',
                'reason': '目标文件已存在',
                'source': str(source_path),
                'target': str(target_path),
                'category': category,
                'tags': detected_tags
            }
        
        if dry_run:
            return {
                'action': 'preview',
                'source': str(source_path),
                'target': str(target_path),
                'category': category,
                'tags': detected_tags
            }
        
        # 执行操作
        try:
            self._execute_action(source_path, target_path)
            
            return {
                'action': 'moved',
                'source': str(source_path),
                'target': str(target_path),
                'category': category,
                'tags': detected_tags
            }
            
        except Exception as e:
            return {
                'action': 'error',
                'error': str(e),
                'source': str(source_path),
                'target': str(target_path)
            }
    
    def _detect_category(self, filename: str) -> str:
        """
        检测文件分类
        
        Args:
            filename: 文件名
            
        Returns:
            str: 分类名称
        """
        filename_lower = filename.lower()
        
        for category in self.categories:
            keywords = category.get('keywords', [])
            for keyword in keywords:
                if keyword.lower() in filename_lower:
                    return category.get('target', category['name'])
        
        # 默认分类
        return '其他'
    
    def _detect_tags(self, filename: str) -> List[str]:
        """
        检测文件标签
        
        Args:
            filename: 文件名
            
        Returns:
            List[str]: 标签列表
        """
        detected = []
        filename_lower = filename.lower()
        
        for tag in self.tags:
            keywords = tag.get('keywords', [])
            for keyword in keywords:
                if keyword.lower() in filename_lower:
                    detected.append(tag['name'])
                    break
        
        return detected
    
    def _build_target_path(
        self,
        category: str,
        filename: str,
        tags: List[str]
    ) -> Path:
        """
        构建目标路径
        
        Args:
            category: 分类
            filename: 文件名
            tags: 标签列表
            
        Returns:
            Path: 目标路径
        """
        # 基础路径：/target_dir/category/filename
        target_path = self.target_dir / category / filename
        
        # 如果有标签，可以按标签创建子目录
        # 例如：/target_dir/category/演员 A/filename
        if tags:
            target_path = self.target_dir / category / tags[0] / filename
        
        return target_path
    
    def _execute_action(self, source: Path, target: Path):
        """
        执行文件操作
        
        Args:
            source: 源路径
            target: 目标路径
        """
        # 确保目标目录存在
        target.parent.mkdir(parents=True, exist_ok=True)
        
        if self.mode == 'move':
            shutil.move(str(source), str(target))
        elif self.mode == 'copy':
            shutil.copy2(str(source), str(target))
        elif self.mode == 'link':
            # 创建软链接
            if target.exists():
                target.unlink()
            # 使用相对路径创建链接
            target.symlink_to(source.resolve())
    
    def get_category_stats(self, files: List[Dict]) -> Dict[str, int]:
        """
        统计各类别文件数量
        
        Args:
            files: 文件列表
            
        Returns:
            Dict[str, int]: 类别统计
        """
        stats = {}
        for file_info in files:
            category = self._detect_category(file_info['name'])
            stats[category] = stats.get(category, 0) + 1
        return stats
