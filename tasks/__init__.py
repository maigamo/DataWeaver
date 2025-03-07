from .scheduler import initialize_scheduler

# 在应用启动时初始化调度器
def init_tasks():
    """
    初始化所有定时任务
    """
    scheduler = initialize_scheduler()
    return scheduler