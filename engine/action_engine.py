import copy
import os
import json
import re

import toml
import traceback
import allure
from selenium.webdriver.common.by import By
from base.BasePage import BasePage
from config.LogConfig import Logger
from config.PathConfig import Config
from engine.action_manager import action_manager


class ActionEngine(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.logger = Logger(logger_name="ActionEngine").getlog()
        actions_dir = Config().get_path("actions_dir")
        self.actions = self._load_actions(actions_dir)

    def _merge_actions(self, actions, file_actions, file_path, file_type):
        for k in file_actions:
            if k in actions:
                raise ValueError(
                    f"[_merge_actions] 行为名称 '{k}' 重复，文件: {file_path}"
                )
        actions.update(file_actions)
        self.logger.info(f"成功加载 {file_type} 行为文件: {file_path}")

    def _load_actions(self, directory):
        """
        递归加载指定目录及其子目录中的所有 JSON/TOML 文件。
        不再做 _normalize_all_actions；直接原样保存到 self.actions。
        """
        actions = {}
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith(".json"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            file_actions = json.load(f)
                        self._merge_actions(actions, file_actions, file_path, file_type="JSON")
                    except Exception as e:
                        self.logger.error(f"加载 JSON 文件失败: {file_path}, 错误: {e}")
                elif file.endswith(".toml"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            file_actions = toml.load(f)
                        self._merge_actions(actions, file_actions, file_path, file_type="TOML")
                    except Exception as e:
                        self.logger.error(f"加载 TOML 文件失败: {file_path}, 错误: {e}")
                else:
                    self.logger.debug(f"忽略非 JSON/TOML 文件: {file_path}")

        return actions

    def resolve_data(self, ctx, data_reference):
        """
        支持在 selector 或 param 中使用 $. / $['xxx']，
        只要字符串里写 $xxx => eval(data_reference.replace("$", "ctx"), eval_context)...
        """
        if not data_reference:
            return None

        eval_context = {"ctx": ctx}

        if isinstance(data_reference, str) and data_reference.startswith("$"):
            try:
                return eval(data_reference.replace("$", "ctx"))
            except SyntaxError:
                pass
            except Exception as e:
                raise ValueError(f"解析数据引用失败: {data_reference}, 错误: {e}, 上下文: {ctx}")

        if isinstance(data_reference, str):
            matches = re.findall(r"\$\.(\w+)|\$\['(.*?)']", data_reference)
            for match in matches:
                key = match[0] if match[0] else match[1]
                if key in ctx:
                    value = ctx[key]
                    data_reference = data_reference.replace(f"$.{key}", str(value))
                    data_reference = data_reference.replace(f"$['{key}']", str(value))
                else:
                    raise ValueError(f"上下文中未找到变量: {key}")

        return data_reference

    def perform_action(self, step_dict, ctx):
        """
        统一在这里执行动作（无论是 op/assert）。
        step_dict 示例:
          {
            "desc": "点击新增",
            "action": "click",
            "selector": "//span[text()=\"新增分类\"]",
            "param": "...",
          }
        或者在 'assert' 类型中, 我们把 'logical' -> 'action', 'value' -> 'param' 之后再传进来.
        """
        name = step_dict.get("desc", "")
        action = step_dict.get("action", None)
        locator = step_dict.get("selector", None)
        data_ref = step_dict.get("param", None)

        # 解析 $xxx
        locator = self.resolve_data(ctx, locator)
        data = self.resolve_data(ctx, data_ref)

        self.logger.info(f"执行行为: {name}, 动作: {action}, 定位符: {locator}, 数据: {data}")

        action_class = action_manager.get_action(action)
        if not action_class:
            raise ValueError(f"不支持或无法识别的动作: {action}")

        try:
            action_instance = action_class(self.driver, self.logger)
            return action_instance.execute(locator, data)
        except Exception as e:
            self.logger.error(f"执行行为 '{name}' 失败: {e}")
            self.log_and_raise(f"执行行为 '{name}' 出现异常", e)
            raise

    def run(self, action_name, action_type, ctx):
        """
        用法示例：
          engine.run("add_classify2.step1", "op", ctx)
          engine.run("classify_assert2", "assert", assetData)

        逻辑：
          1) 解析 action_name 是否含有 '.' (父子)
          2) 根据父 key (如 "classify_assert2") 找到 data
          3) 如果有子 key (如 "step1")，再深入 data[子key]
          4) 检查 "type" == action_type ? 不同则抛异常
          5) 取到 "steps" => 如果 type=="assert"，把 step["logical"] -> step["action"], step["value"] -> step["param"]
          6) 执行 steps
        """

        # 1) 解析 action_name
        if '.' in action_name:
            parent_key, child_key = action_name.split('.', 1)
        else:
            parent_key, child_key = action_name, None

        # 2) 找到 parent data
        if parent_key not in self.actions:
            raise ValueError(f"行为 '{parent_key}' 未定义")
        action_data = self.actions[parent_key]

        # 如果 child_key 存在，就进一步找
        if child_key:
            if child_key not in action_data:
                raise ValueError(f"在 '{parent_key}' 下未找到子行为 '{child_key}'")
            action_data = action_data[child_key]

        # 3) 检查 type
        real_type = action_data.get("type", None)
        if real_type != action_type:
            raise ValueError(
                f"动作类型不匹配：配置中的 type='{real_type}', 但调用时指定='{action_type}'"
            )

        # 4) 拿到 steps
        steps = action_data.get("steps", [])
        if not isinstance(steps, list):
            raise ValueError(f"'{action_name}' 的 steps 必须是一个 list")

        # 5) 如果是 assert，需要把 step["logical"] -> step["action"], step["value"] -> step["param"]
        if action_type == "assert":
            for step_dict in steps:
                if "logical" in step_dict:
                    step_dict["action"] = step_dict.pop("logical")  # logical -> action
                if "value" in step_dict:
                    step_dict["param"] = step_dict.pop("value")  # value -> param

        self.logger.info(f"[run] 开始执行: {action_name} (type={action_type})")
        if "title" in action_data:
            allure.dynamic.title(action_data["title"])
        if "description" in action_data:
            allure.dynamic.description(action_data["description"])

        # 6) 逐步执行
        ctx_data = json.loads(ctx) if isinstance(ctx, str) else ctx
        results = {}
        for step_dict in steps:
            result = self.perform_action(step_dict, ctx_data)
            if isinstance(result, dict):
                results.update(result)
            elif result is not None:
                self.logger.info(f"[run] 返回不是字典, 类型={type(result)}, 值={result}")

        return results




