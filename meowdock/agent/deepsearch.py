import asyncio
from typing import List, Union, Dict, Any, Optional
import json

from meowdock.docking.docking_factory import DockingFactory
from meowdock.cmd.execute.executors.executors_factory import get_executor


async def async_deepsearch(
    query: str,
    engines: Union[List[str], str] = ["baidu", "bing"],
    count: int = 10,
    executor: str = "yuanbao",
    **kwargs,
) -> str:
    """
    Perform deep search asynchronously, combining results from multiple search engines and process results with specified executor

    Args:
        query: Search query
        engines: Search engine or list of engines to use
        count: Total number of results to get
        executor: Executor for processing results, default is 'yuanbao'
        **kwargs: Additional search parameters

    Returns:
        Formatted search results
    """
    # Initialize factory
    factory = DockingFactory()

    # Ensure engines is a list type
    engines_list = [engines] if isinstance(engines, str) else engines

    # Create multiple search tasks
    tasks = []
    for engine in engines_list:
        # Get corresponding docking instance based on engine type
        docking = factory.get_docking(engine)
        if docking:
            # Create async task
            task = asyncio.create_task(
                asyncio.to_thread(
                    docking.run, query, count=count // len(engines_list) + 1, **kwargs
                )
            )
            tasks.append(task)

    # Return empty result if no valid search engines
    if not tasks:
        return "No valid search engines specified"

    # Wait for all searches to complete
    results = await asyncio.gather(*tasks)

    # Merge all results
    markdown_results = "\n\n".join(results)

    # Get executor instance
    executor_instance = get_executor(executor)

    # If executor is specified, pass the query and results to the executor
    combined_prompt = f"Please answer the question based on the following search results:\n\nQuestion: {query}\n\nSearch Results:\n{markdown_results}"
    result = await executor_instance.execute(combined_prompt)
    return result if result is not None else markdown_results


def deepsearch(
    query: str,
    engines: Union[List[str], str] = ["baidu", "bing"],
    count: int = 10,
    executor: str = "yuanbao",
    **kwargs,
) -> str:
    """
    Perform deep search, combining results from multiple search engines and process results with specified executor
    This is a synchronous wrapper around the async_deepsearch function

    Args:
        query: Search query
        engines: Search engine or list of engines to use
        count: Total number of results to get
        executor: Executor for processing results, default is 'yuanbao'
        **kwargs: Additional search parameters

    Returns:
        Formatted search results
    """
    return asyncio.run(
        async_deepsearch(query=query, engines=engines, count=count, executor=executor, **kwargs)
    )
