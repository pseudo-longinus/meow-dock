from meowdock.cmd.execute.executors.base import ListExecutor, TreeExecutor
from meowdock.cmd.execute.executors.executors_factory import register

@register('yuanbao-list')
class YuanbaoListExecutor(ListExecutor):
    history_str_path = './meowdock/resources/yuanbao_list_history.json'

@register('yuanbao')
class YuanbaoTreeExecutor(TreeExecutor):
    history_str_path = './meowdock/resources/yuanbao_tree_history.json'
