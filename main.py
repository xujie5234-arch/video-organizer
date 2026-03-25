#!/usr/bin/env python3
"""
Media Organizer - 影视文件分类工具
主程序入口
"""

import os
import sys
import yaml
import click
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

from scanner import VideoScanner
from classifier import Classifier
from database import MediaDatabase

console = Console()


def load_config(config_path: str = "config.yaml") -> dict:
    """加载配置文件"""
    if not os.path.exists(config_path):
        console.print(f"[yellow]配置文件不存在：{config_path}[/]")
        console.print(f"[yellow]正在使用示例配置...[/]")
        config_path = "config.example.yaml"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@click.command()
@click.option('--config', '-c', default='config.yaml', help='配置文件路径')
@click.option('--dry-run', '-d', is_flag=True, help='预览模式，不实际移动文件')
@click.option('--scan-only', '-s', is_flag=True, help='仅扫描，不分类')
@click.option('--reindex', '-r', is_flag=True, help='重建索引')
def main(config, dry_run, scan_only, reindex):
    """
    Media Organizer - 影视文件分类工具
    
    自动扫描、识别、分类本地影视文件。
    """
    console.print("[bold blue]🎬 Media Organizer v1.0[/]")
    console.print(f"[dim]启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/]\n")
    
    # 加载配置
    cfg = load_config(config)
    
    # 初始化数据库
    db = MediaDatabase(cfg.get('database', './media.db'))
    if reindex:
        console.print("[yellow]重建索引...[/]")
        db.rebuild()
    
    # 初始化扫描器
    scanner = VideoScanner(
        source_dir=cfg.get('source_dir', '.'),
        extensions=cfg.get('video_extensions', ['.mp4', '.mkv', '.avi']),
        ignore_folders=cfg.get('ignore_folders', [])
    )
    
    # 初始化分类器
    classifier = Classifier(
        categories=cfg.get('categories', []),
        tags=cfg.get('tags', []),
        target_dir=cfg.get('target_dir', './sorted'),
        mode=cfg.get('mode', 'link')
    )
    
    # 扫描文件
    console.print(f"[bold]📁 扫描目录：{scanner.source_dir}[/]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        task = progress.add_task("扫描中...", total=None)
        files = scanner.scan()
        progress.update(task, completed=len(files))
    
    console.print(f"[green]✅ 找到 {len(files)} 个视频文件[/]\n")
    
    if scan_only:
        # 仅显示扫描结果
        table = Table(title="扫描结果")
        table.add_column("文件路径", style="cyan")
        table.add_column("大小", style="green")
        
        for f in files[:20]:  # 只显示前 20 个
            size_mb = f['size'] / 1024 / 1024
            table.add_row(str(f['path']), f"{size_mb:.1f} MB")
        
        if len(files) > 20:
            table.add_row(f"... 还有 {len(files) - 20} 个文件", "")
        
        console.print(table)
        return
    
    # 分类文件
    console.print(f"[bold]🏷️  开始分类（模式：{cfg.get('mode', 'link')})[/]")
    if dry_run:
        console.print("[yellow]⚠️  预览模式 - 不会实际移动文件[/]\n")
    
    results = {'moved': 0, 'skipped': 0, 'errors': 0}
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        task = progress.add_task("分类中...", total=len(files))
        
        for file_info in files:
            try:
                result = classifier.classify(file_info, dry_run=dry_run)
                
                if result['action'] == 'moved':
                    results['moved'] += 1
                    if not dry_run:
                        db.add_record(file_info, result)
                elif result['action'] == 'skipped':
                    results['skipped'] += 1
                else:
                    results['errors'] += 1
                    
            except Exception as e:
                console.print(f"[red]错误：{file_info['path']} - {e}[/]")
                results['errors'] += 1
            
            progress.update(task, advance=1)
    
    # 显示结果
    console.print("\n[bold]📊 分类结果[/]")
    console.print(f"  成功：[green]{results['moved']}[/]")
    console.print(f"  跳过：[yellow]{results['skipped']}[/]")
    console.print(f"  错误：[red]{results['errors']}[/]")
    
    if not dry_run and results['moved'] > 0:
        console.print(f"\n[green]✅ 数据库已更新，共 {db.count()} 条记录[/]")


if __name__ == '__main__':
    main()
