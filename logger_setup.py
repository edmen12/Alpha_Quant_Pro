"""
日志系统模块 (Logger Setup)

配置和管理整个应用的日志系统。
支持文件日志、控制台输出和 GUI 实时显示。

主要功能：
1. 文件日志 - 自动轮转，最大 10MB，保留 5 个备份
2. 控制台输出 - 实时显示到终端
3. GUI 队列 - 供 UI 日志视图实时读取
"""
import logging
import logging.handlers
import sys
from pathlib import Path
import queue
from path_manager import PathManager

class LoggerSetup:
    """
    日志配置管理器 (Logger Setup Manager)
    
    采用单例模式，确保整个应用使用统一的日志配置。
    所有模块通过 LoggerSetup.get_logger(name) 获取日志记录器。
    """
    
    _instance = None
    _log_queue = queue.Queue()  # GUI 日志队列
    
    @staticmethod
    def get_logger(name):
        """
        获取日志记录器 (Get Logger)
        
        为指定模块创建或获取日志记录器。
        
        Args:
            name (str): 模块名称（通常使用 __name__）
            
        Returns:
            logging.Logger: 配置好的日志记录器
            
        Example:
            logger = LoggerSetup.get_logger(__name__)
            logger.info("Engine started")
        """
        return logging.getLogger(name)
        
    @staticmethod
    def setup_logging(app_name="AlphaQuant", log_dir=None):
        """
        初始化日志系统 (Setup Logging)
        
        配置三个日志处理器：
        1. 文件处理器 - 写入 logs/AlphaQuant.log（自动轮转）
        2. 控制台处理器 - 输出到 stdout
        3. 队列处理器 - 供 GUI 实时显示
        
        Args:
            app_name (str): 应用名称，用于日志文件命名
            log_dir (str): 日志文件目录，默认为 AppData/Local/logs
        """
        # 创建日志目录
        if log_dir is None:
            log_path = PathManager.get_logs_dir()
        else:
            log_path = Path(log_dir)
            
        log_path.mkdir(parents=True, exist_ok=True)
        
        # 根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # 日志格式：[时间] [级别] [模块] 消息
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 1. 文件处理器 - 自动轮转（10MB 上限，保留 5 个备份）
        file_handler = logging.handlers.RotatingFileHandler(
            log_path / f"{app_name}.log",
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        
        # 2. 控制台处理器 - 实时输出到终端
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        root_logger.addHandler(console_handler)
        
        # 3. 队列处理器 - 供 GUI 日志视图轮询
        # GUI 通过 LoggerSetup.get_log_queue() 获取日志消息
        queue_handler = logging.handlers.QueueHandler(LoggerSetup._log_queue)
        queue_handler.setLevel(logging.INFO)
        root_logger.addHandler(queue_handler)
        
        logging.info(f"日志系统已初始化: {app_name}")

    @staticmethod
    def get_log_queue():
        """
        获取 GUI 日志队列 (Get Log Queue)
        
        GUI 日志视图通过轮询此队列来实时显示日志。
        
        Returns:
            queue.Queue: 日志消息队列
            
        Example:
            log_queue = LoggerSetup.get_log_queue()
            while not log_queue.empty():
                record = log_queue.get_nowait()
                print(record.getMessage())
        """
        return LoggerSetup._log_queue

