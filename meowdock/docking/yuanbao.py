import asyncio
from typing import Any

from .docking_factory import Docking, DockingFactory
from ..cmd.execute.executors.executors_factory import get_executor


@DockingFactory.register('yuanbao')
class YuanbaoDocking(Docking):
    def __init__(self):
        super().__init__()
        # Get the specific executor instance here, or potentially in run if needed
        # We get it here assuming the executor factory is synchronous and quick.
        try:
            self.executor_instance = get_executor('yuanbao')
        except ValueError as e:
            # Handle the case where the executor is not found
            print(f"Error getting yuanbao executor: {e}")  # Or log it
            self.executor_instance = None  # Or raise the exception

    def run(self, prompt: str, *args, **kwargs) -> Any:
        """
        Run the yuanbao executor with the given prompt.

        Args:
            prompt: The input prompt for the executor.

        Returns:
            Any: The result from the executor, or None if the executor was not found.
        """
        if not self.executor_instance:
            print("Yuanbao executor not available.")
            return None
        try:
            return asyncio.run(self._async_run(prompt))
        except Exception as e:
            print(f"Error running yuanbao executor: {e}")
            return None

    async def _async_run(self, prompt: str) -> Any:
        """
        Asynchronously run the yuanbao executor.
        """
        # Pass the prompt to the executor's execute method
        result = await self.executor_instance.execute(prompt)
        return result
