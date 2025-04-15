from meowdock.cmd.execute.executors.base import ListExecutor, TreeExecutor
from meowdock.cmd.execute.executors.executors_factory import register

@register('yuanbao')
class YuanbaoListExecutor(ListExecutor):
    history_str_path = './meowdock/resources/yuanbao_history.json'

@register('yuanbao2')
class YuanbaoTreeExecutor(TreeExecutor):
    history_str_path = './meowdock/resources/yuanbao_history2.json'
