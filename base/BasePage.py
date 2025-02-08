import os
import time
import traceback
import allure
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from config.LogConfig import Logger
from config.PathConfig import Config

# 创建 Logger 实例
logger = Logger().getlog()


class BasePage:

    def __init__(self, driver: WebDriver):
        """
        :param driver: 浏览器驱动实例
        """
        self.driver = driver
        self.driver.maximize_window()
        self.conf = Config()


    def _format_locator(self, loc):
        """
        格式化定位符，支持字符串和数组输入，并自动识别定位方式。
        :param loc: 定位符，可以是字符串或数组。
            - 如果是字符串，自动判断定位方式。
            - 如果是数组，长度为1时自动识别定位方式；长度为2时第一个元素为定位方式。
        :return: (By, value) 格式的定位符元组
        """
        if isinstance(loc, str):
            # 自动识别字符串的定位方式
            if loc.startswith("//") or loc.startswith("(//"):  # XPath 表达式
                return By.XPATH, loc
            elif loc.startswith("#"):  # CSS 选择器（ID 选择器）
                return By.CSS_SELECTOR, loc
            elif loc.startswith("."):  # CSS 选择器（类选择器）
                return By.CSS_SELECTOR, loc
            elif "=" in loc and "[" in loc and "]" in loc:  # 自定义表达式支持
                return By.XPATH, loc
            elif loc.isalnum():  # 可能是 ID
                return By.ID, loc
            else:  # 默认返回 CSS_SELECTOR
                return By.CSS_SELECTOR, loc

        elif isinstance(loc, (list, tuple)):
            # 处理数组输入
            if len(loc) == 1:  # 如果长度为1，自动识别
                return self._format_locator(loc[0])
            elif len(loc) == 2:  # 如果长度为2，按指定方式返回
                return loc[0], loc[1]

        # 如果输入不合法
        raise ValueError(f"无法识别的定位符格式: {loc}")

    def log_and_raise(self, error_message, exception):
        """
        记录错误日志并抛出异常，同时生成截图和报告。
        :param error_message: 错误信息
        :param exception: 要抛出的异常
        """
        # 截图文件路径
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_name = f"error_{timestamp}.png"
        screenshot_path = os.path.join('./report/screenshot', screenshot_name)

        # 截图并保存
        try:
            self.driver.save_screenshot(screenshot_path)
            logger.error(f"{error_message}，截图已保存: {screenshot_path}")
            # 添加截图到 Allure 报告
            with open(screenshot_path, "rb") as image_file:
                allure.attach(image_file.read(), name="Error Screenshot", attachment_type=allure.attachment_type.PNG)
        except Exception as screenshot_error:
            logger.error(f"生成截图失败: {screenshot_error}")

        # 记录堆栈信息到日志
        logger.error(traceback.format_exc())

        # 抛出异常
        raise exception

    def open(self, url):
        """打开网页"""
        logger.info(f'打开网页: {url}')
        try:
            self.driver.get(url)
            # 等待页面加载完成
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except Exception as e:
            self.log_and_raise(f'打开网页失败: {url}', Exception(f"打开网页失败: {e}"))

    def find_element(self, loc):
        """获取单个元素"""
        loc = self._format_locator(loc)
        try:
            element = WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located(loc))
            logger.info(f'找到元素: {loc}')
            return element
        except TimeoutException:
            self.log_and_raise(f'查找元素超时: {loc}', TimeoutException(f"元素 {loc} 超时"))
        except NoSuchElementException:
            self.log_and_raise(f'找不到定位元素: {loc}', NoSuchElementException(f"元素 {loc} 不存在"))

    def click(self, loc):
        """点击元素"""
        loc = self._format_locator(loc)
        try:
            time.sleep(0.5)
            logger.info(f'点击元素 by {loc[0]}: {loc[1]}')
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(loc)).click()
        except AttributeError as e:
            self.log_and_raise(f'无法点击元素: {loc}', AttributeError(f"点击元素失败: {e}"))
        except TimeoutException:
            self.log_and_raise(f'元素 {loc} 无法点击', TimeoutException(f"点击超时: {loc}"))

    def input(self, loc, text):
        """输入文本框内容"""
        loc = self._format_locator(loc)
        logger.info(f'清空文本框内容: {loc[1]}')
        try:
            element = self.find_element(loc)
            element.clear()
            logger.info(f'输入内容: {text}')
            element.send_keys(text)
        except Exception as e:
            self.log_and_raise(f'输入内容失败: {loc}', Exception(f"输入失败: {e}"))

    def get_page_title(self):
        """获取页面标题"""
        try:
            title = self.driver.title
            logger.info(f'当前页面的title为: {title}')
            return title
        except Exception as e:
            self.log_and_raise(f'获取页面标题失败', Exception(f"获取失败: {e}"))

    def get_text(self, loc):
        """获取元素文本"""
        loc = self._format_locator(loc)
        try:
            element = self.find_element(loc)
            text = element.text
            logger.info(f'获取元素文本: {text}')
            return text
        except Exception as e:
            self.log_and_raise(f'获取元素文本失败: {loc}', Exception(f"获取失败: {e}"))