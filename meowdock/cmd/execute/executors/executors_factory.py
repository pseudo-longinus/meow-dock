from warnings import warn
from typing import Dict, Type
from meowdock.cmd.execute.executors.base import ExecutorWrapper


_EXECUTORS: Dict[str, Type[ExecutorWrapper]] = {}


def register(name):
    def deco(cls: Type[ExecutorWrapper]):
        if not issubclass(cls, ExecutorWrapper):
            warn(f'WARNING: {cls.__name__} is not a subclass of ExecutorWrapper.')
        if name in _EXECUTORS.keys():
            warn(f'WARNING: {name} ExecutorWrapper has been rewritten.')
        _EXECUTORS[name] = cls
        return cls
    return deco


def get_executor(executor: str, **kwargs) -> ExecutorWrapper:
    """
    Factory method that returns a executor instance based on the engine name

    Args:
        engine: executor name, e.g. 'yuanbao'
        **kwargs: Parameters passed to the executor constructor

    Returns:
        ExecutorWrapper: executor instance

    Raises:
        ValueError: If the specified engine is not supported
    """
    executor = executor.lower().strip()

    if executor not in _EXECUTORS:
        supported = ", ".join(_EXECUTORS.keys())
        raise ValueError(
            f"Unsupported executor: {executor}. Supported executors: {supported}")

    return _EXECUTORS[executor](**kwargs)
