from abc import ABC, abstractmethod


class Docking(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def run(self, prompt, *args, **kwargs):
        pass


class DockingFactory:
    _registry = {}

    def __init__(self):
        pass

    def get_docking(self, dock_type: str, **kargs) -> Docking:
        return self._registry.get(dock_type)(**kargs)

    @classmethod
    def register(cls, dock_type: str):
        def decorator(docking_cls):
            cls._registry[dock_type] = docking_cls
            return docking_cls

        return decorator
