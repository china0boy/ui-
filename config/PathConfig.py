import os
import configparser


class Config:
    def __init__(self):
        # 获取项目的根路径
        self.BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # 配置文件路径
        self.CONFIG_FILE = os.path.join(self.BASE_PATH, 'data', 'config.ini')
        self.config = configparser.ConfigParser()
        self.config.read(self.CONFIG_FILE)

        # 统一管理路径
        self.paths = {
            "base_path": self.BASE_PATH,
            "config_file": self.CONFIG_FILE,
            "log_dir": os.path.join(self.BASE_PATH, 'logs'),
            "report_dir": os.path.join(self.BASE_PATH, 'report'),
            "screenshot_dir": os.path.join(self.BASE_PATH, 'report', 'screenshot'),
            "data_dir": os.path.join(self.BASE_PATH, 'data'),
            "test_cases_dir": os.path.join(self.BASE_PATH, 'tests'),
            "actions_dir": os.path.join(self.BASE_PATH, 'actions'),
        }

    def get(self, section, key):
        """
        从配置文件中读取配置值
        :param section: 配置文件中的节名
        :param key: 配置项
        :return: 配置值
        """
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            raise ValueError(f"配置文件中未找到 {section}.{key}: {e}")

    def get_path(self, name):
        """
        获取路径
        :param name: 路径名称
        :return: 路径值
        """
        if name not in self.paths:
            raise ValueError(f"路径名称 '{name}' 未定义，请检查 PathConfig 配置")
        return self.paths[name]
