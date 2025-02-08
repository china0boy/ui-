import logging
import os
import time
from config.PathConfig import Config


class Logger:
    _logger = None  # 单例的 Logger 实例

    def __init__(self, logger_name="Log", log_level=logging.DEBUG):
        """
        初始化 Logger
        :param logger_name: Logger 的名称
        :param log_level: 日志级别
        """
        if Logger._logger is None:
            # 创建全局 Logger 实例
            Logger._logger = logging.getLogger(logger_name)
            Logger._logger.setLevel(log_level)

            # 获取日志文件路径
            log_path = Config().get_path("log_dir")
            os.makedirs(log_path, exist_ok=True)  # 确保目录存在
            now = time.strftime("%Y-%m-%d_%H_%M_%S")
            log_file = os.path.join(log_path, f"log_{now}.log")

            # 创建文件 Handler
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(log_level)

            # 创建控制台 Handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)

            # 定义日志格式
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # 添加 Handler 到 Logger
            Logger._logger.addHandler(file_handler)
            Logger._logger.addHandler(console_handler)

    def getlog(self):
        return Logger._logger
