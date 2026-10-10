import importlib
import inspect
import pkgutil

from oldhan.task.action.base import Action
from oldhan.task.action.builtin.action_listen import ActionListen
from oldhan.task.action.builtin.action_response import ActionResponse
from oldhan.task.action.registry import ActionRegistry
from oldhan.task.action.runner import ActionRunner


#注册自定义类
def register_custom_actions(registry:ActionRegistry):
    #完成自定义Action类的注册
    #1.导入oldhan.task.action.custom包
    package = importlib.import_module("oldhan.task.action.custom")
    #2.遍历包中的所有模块
    #  prefix 必须写:不加 prefix 时 name 是裸模块名(如 action_lookup_order_status),
    #  直接 import_module(name) 会 ModuleNotFoundError,必须补成完整包路径
    for __,name,is_pkg in pkgutil.walk_packages(package.__path__,prefix=f"{package.__name__}."):
        if is_pkg:
            continue
        #导入custom包中的模块
        module = importlib.import_module(name)
        for __,obj in inspect.getmembers(module,inspect.isclass):
            # 如果模块中的类是Action的子类，但不是Action类，则进行注册
            if issubclass(obj,Action) and obj is not Action:
                registry.register( obj() )

#注册内置Action
def register_builtin_actions(registry: ActionRegistry):
    registry.register(ActionResponse())
    registry.register(ActionListen())


#调用注册函数
def build_action_runner()->ActionRunner:
    registry = ActionRegistry()
    # 注册内置Action（静态注册）
    register_builtin_actions(registry)
    # 注册自定义Action（通过扫描包来完成自定义Action的注册）
    register_custom_actions(registry)
    return ActionRunner(registry)