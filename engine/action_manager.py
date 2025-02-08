from base.BasePage import BasePage


class ActionManager:
    """行为管理器"""
    def __init__(self):
        self.actions = {}

    def register(self, action_name):
        """装饰器，用于注册行为"""
        def decorator(action_class):
            if not issubclass(action_class, ActionBase):
                raise ValueError(f"{action_class} 必须继承 ActionBase")
            self.actions[action_name] = action_class
            return action_class
        return decorator

    def get_action(self, action_name):
        """获取行为类"""
        return self.actions.get(action_name)

class ActionBase(BasePage):
    """行为基类，所有具体行为类需要继承这个类"""
    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger

    def execute(self, locator, data):
        """执行行为的方法，子类需要实现此方法"""
        raise NotImplementedError("子类必须实现 execute 方法")


# 初始化全局行为管理器
action_manager = ActionManager()


# 使用装饰器自动注册行为
@action_manager.register("click")
class ClickAction(ActionBase):
    """点击行为"""
    def execute(self, locator, data=None):
        self.click(locator)


@action_manager.register("input")
class InputAction(ActionBase):
    """输入行为"""
    def execute(self, locator, data):
        self.input(locator, data)


@action_manager.register("open")
class OpenAction(ActionBase):
    """打开网页行为"""
    def execute(self, locator, data):
        self.open(locator)

@action_manager.register("gettext")
class GetTextAction(ActionBase):
    """获取元素值"""
    def execute(self, locator, data):
        return {data: self.get_text(locator)}