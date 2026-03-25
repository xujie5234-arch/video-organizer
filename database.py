#!/usr/bin/env python3
"""
SQLite 数据库模块
记录视频文件信息和分类历史
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class MediaDatabase:
    """媒体文件数据库"""
    
    def __init__(self, db_path: str = "./media.db"):
        self.db_path = Path(db_path)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 媒体文件表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS media_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_name TEXT NOT NULL,
                    file_size INTEGER,
                    category TEXT,
                    tags TEXT,
                    target_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 分类历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    action TEXT NOT NULL,
                    old_path TEXT,
                    new_path TEXT,
                    category TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON media_files(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_name ON media_files(file_name)')
            
            conn.commit()
    
    def add_record(self, file_info: Dict, result: Dict) -> int:
        """
        添加文件记录
        
        Args:
            file_info: 文件信息
            result: 分类结果
            
        Returns:
            int: 记录 ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            tags_str = ','.join(result.get('tags', []))
            
            cursor.execute('''
                INSERT OR REPLACE INTO media_files 
                (file_path, file_name, file_size, category, tags, target_path, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_info['path'],
                file_info['name'],
                file_info['size'],
                result.get('category', ''),
                tags_str,
                result.get('target', ''),
                datetime.now()
            ))
            
            record_id = cursor.lastrowid
            
            # 记录历史
            cursor.execute('''
                INSERT INTO history 
                (file_path, action, old_path, new_path, category, tags)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                file_info['path'],
                result.get('action', ''),
                result.get('source', ''),
                result.get('target', ''),
                result.get('category', ''),
                tags_str
            ))
            
            conn.commit()
            return record_id
    
    def get_by_category(self, category: str) -> List[Dict]:
        """
        按分类查询文件
        
        Args:
            category: 分类名称
            
        Returns:
            List[Dict]: 文件列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM media_files WHERE category = ?
                ORDER BY file_name
            ''', (category,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_by_tag(self, tag: str) -> List[Dict]:
        """
        按标签查询文件
        
        Args:
            tag: 标签名称
            
        Returns:
            List[Dict]: 文件列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM media_files 
                WHERE tags LIKE ?
                ORDER BY file_name
            ''', (f'%{tag}%',))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def search(self, keyword: str) -> List[Dict]:
        """
        搜索文件
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            List[Dict]: 文件列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM media_files 
                WHERE file_name LIKE ? OR tags LIKE ?
                ORDER BY file_name
            ''', (f'%{keyword}%', f'%{keyword}%'))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 总数
            cursor.execute('SELECT COUNT(*) FROM media_files')
            total = cursor.fetchone()[0]
            
            # 按分类统计
            cursor.execute('''
                SELECT category, COUNT(*) as count 
                FROM media_files 
                GROUP BY category
            ''')
            by_category = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 总大小
            cursor.execute('SELECT SUM(file_size) FROM media_files')
            total_size = cursor.fetchone()[0] or 0
            
            return {
                'total_files': total,
                'total_size_gb': total_size / 1024 / 1024 / 1024,
                'by_category': by_category
            }
    
    def count(self) -> int:
        """获取记录总数"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM media_files')
            return cursor.fetchone()[0]
    
    def rebuild(self):
        """重建数据库（清空所有数据）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM media_files')
            cursor.execute('DELETE FROM history')
            conn.commit()
    
    def list_categories(self) -> List[str]:
        """列出所有分类"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT category FROM media_files')
            return [row[0] for row in cursor.fetchall()]
