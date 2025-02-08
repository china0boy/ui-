from selenium import webdriver
import pytest

from engine.action_engine import ActionEngine


class Test_baidu:

    def setup_class(self):
        self.driver = webdriver.Chrome()
        self.ActionEngine = ActionEngine(self.driver)
        pass

    def test_baidu(self):
        ctx = {}

        data_assert = {
            "data": "Bing"
        }
        self.ActionEngine.run("sou", "op", ctx)
        b = self.ActionEngine.run("assert", "assert", None)

        assert b == data_assert
