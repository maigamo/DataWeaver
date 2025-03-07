import os
import time
import shutil
from pathlib import Path
import logging
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cleanup.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("cleanup")

def cleanup_export_files(output_dir="output", max_age_days=7):
    """
    清理超过指定天数的导出文件
    
    Args:
        output_dir: 导出文件目录
        max_age_days: 文件保留的最大天数
    """
    try:
        logger.info(f"开始清理 {output_dir} 目录中超过 {max_age_days} 天的文件")
        
        # 确保目录存在
        output_path = Path(output_dir)
        if not output_path.exists():
            logger.warning(f"目录 {output_dir} 不存在，无需清理")
            return
            
        # 计算截止时间
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        deleted_count = 0
        total_size = 0
        
        # 遍历目录中的所有文件
        for file_path in output_path.iterdir():
            if file_path.is_file():
                # 获取文件的修改时间
                mtime = file_path.stat().st_mtime
                
                # 如果文件超过了最大保留时间
                if mtime < cutoff_time:
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    
                    # 删除文件
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"已删除文件: {file_path.name} (大小: {file_size/1024:.2f} KB, 修改时间: {datetime.fromtimestamp(mtime)})")
        
        logger.info(f"清理完成，共删除 {deleted_count} 个文件，释放空间 {total_size/1024/1024:.2f} MB")
    except Exception as e:
        logger.error(f"清理过程中发生错误: {str(e)}")

def run_cleanup_task():
    """
    运行清理任务的主函数
    """
    logger.info("开始执行定时清理任务")
    cleanup_export_files()
    logger.info("定时清理任务执行完毕")

if __name__ == "__main__":
    run_cleanup_task()