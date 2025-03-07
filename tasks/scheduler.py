import logging
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from cleanup import run_cleanup_task

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("scheduler")

# 默认关闭文件清理功能
ENABLE_CLEANUP = True

def initialize_scheduler():
    """
    初始化并启动定时任务调度器
    """
    try:
        logger.info("正在初始化定时任务调度器...")
        scheduler = BackgroundScheduler()
        
        # 只有在启用清理功能时才添加清理任务
        if ENABLE_CLEANUP:
            # 添加清理任务，每天凌晨2点执行
            scheduler.add_job(
                run_cleanup_task,
                trigger=CronTrigger(hour=2, minute=0),
                id='cleanup_task',
                name='清理过期导出文件',
                replace_existing=True
            )
            logger.info("已启用文件自动清理功能")
        else:
            logger.info("文件自动清理功能已关闭")
        
        # 启动调度器
        scheduler.start()
        logger.info("定时任务调度器已启动")
        return scheduler
    except Exception as e:
        logger.error(f"初始化定时任务调度器失败: {str(e)}")
        return None

if __name__ == "__main__":
    # 初始化调度器
    scheduler = initialize_scheduler()
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        if scheduler:
            scheduler.shutdown()
            logger.info("定时任务调度器已关闭")