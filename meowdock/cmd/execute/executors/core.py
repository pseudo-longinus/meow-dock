import asyncio
import traceback
from browser_use.controller.registry.views import ActionModel
from browser_use.dom.history_tree_processor.view import DOMHistoryElement
from pydantic import BaseModel, field_validator, PrivateAttr
import logging
from pydantic_core import core_schema
from typing import Any, Awaitable, Callable, Dict, Generic, List, Optional, TypeVar, Union
from browser_use.agent.views import (
    ActionResult,
    AgentHistoryList,
    AgentOutput,
    AgentState,
)
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext
from browser_use.browser.views import BrowserState
from browser_use.controller.registry.views import ActionModel
from browser_use.controller.service import Controller
from browser_use.dom.history_tree_processor.service import (
    DOMHistoryElement,
    HistoryTreeProcessor,
)
from browser_use.dom.views import DOMBaseNode
from browser_use.telemetry.service import ProductTelemetry
from browser_use.utils import time_execution_async, time_execution_sync
import numbers
from typing import Any
from meowdock.library.utils.ndarray import NDArray
import numpy as np
import io


_log = io.StringIO()
logger = logging.getLogger(__name__)
stream_handler = logging.StreamHandler(_log)
stream_handler.setLevel(logging.NOTSET)
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s [%(name)s] %(message)s'))
logger.addHandler(stream_handler)

ActionModelRuntime = TypeVar('ActionModelRuntime', bound=ActionModel)
T = TypeVar("T", bound=numbers.Number)

class XPathError(Exception): ...


class FallbackToRootError(Exception): ...


class SimplifiedHistoryActionNode(BaseModel, Generic[ActionModelRuntime]):
    '''Base node for history action.'''

    interacted_element: list[DOMHistoryElement | None]
    action: list[ActionModelRuntime]
    delay: float = 3.0


class SimplifiedHistoryActionList(BaseModel, Generic[ActionModelRuntime]):
    '''Simplified history action list.'''

    history: list[SimplifiedHistoryActionNode[ActionModelRuntime]]

class SimplifiedHistoryActionTreeNode(BaseModel, Generic[ActionModelRuntime]):
    '''Base node for history action tree node.	
    '''
    data: SimplifiedHistoryActionNode[ActionModelRuntime]
    children: list['SimplifiedHistoryActionTreeNode[ActionModelRuntime]'] = []
    probability: Optional[NDArray[np.float64]] = None
    _acted_count: NDArray[np.int_] = PrivateAttr()
    _searched: NDArray[np.bool] = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.probability == None:
            arr = np.ones(shape=(len(self.children)), dtype=np.float64) / len(self.children)
            self.probability = NDArray[np.float64](arr)
            
        self.__init_private_attributes__()

    def __init_private_attributes__(self):
        self._acted_count = NDArray[np.int_](np.zeros(shape=(len(self.children)), dtype=int))
        self._searched = NDArray[np.bool](np.zeros(shape=(len(self.children)), dtype=bool))

    def _update(self, max_retry: int = 3) -> np.bool:
        if len(self.children) == 0: return np.False_
        for i, e in enumerate(self.children):
            if not self._searched[i]:
                self._searched[i] |= e._update(max_retry)
        np.bitwise_or(self._searched.arr, self._acted_count.arr >= max_retry, out=self._searched.arr)
        return np.all(self._searched.arr)

    def get_real_probability(self, mode='random') -> np.ndarray:
        p = self.probability.arr * (1 - self._searched.arr)
        return p / np.sum(p) if np.sum(p) > 0 else p

    def get_next_node_index(self, mode='fixed') -> Optional[int]:
        '''Get next node index
        
        Args:
            mode ('fixed' | 'random'):

        Returns:
            idx (int): -1 if no child, -2 if all children are searched
        '''
        self._update()
        if len(self.children) == 0:
            return -1
        if np.all(self._searched.arr):
            print(self._searched.arr
         )
            return -2
        if mode == 'random':
            next_node_index = np.random.choice(range(len(self.children)), p=self.get_real_probability(mode=mode))
        else:
            masked_min_idx = self._acted_count.arr[~self._searched.arr].argmin()
            next_node_index = np.flatnonzero(~self._searched.arr)[masked_min_idx]
        return int(next_node_index)
    
    def to_str(self, prefix: str='', is_last: bool = True, highlight: list['SimplifiedHistoryActionTreeNode'] = []) -> str:
        caption = [list(a.model_dump(exclude_none=True).keys())[0] for a in self.data.action]
        if self in highlight:
            caption = tuple(caption)
            caption = '\033[1m' + str(caption) + '\033[22m'
        else:
            caption = str(caption)
        connector = "└──" if is_last else "├──"
        result = prefix + connector + caption + "\n"
        
        prefix_ = prefix + ("   " if is_last else "│  ")
        for i, child in enumerate(self.children):
            s = child.to_str(prefix_, i == len(self.children) - 1, highlight=highlight)
            if self._searched[i]:
                s = '\033[42m' + s + '\033[49m'
            result += s
        return result


Context = TypeVar('Context')


class Executor(Generic[Context]):
    @time_execution_sync('--init (agent)')
    def __init__(
        self,
        # Optional parameters
        browser: Browser | None = None,
        browser_context: BrowserContext | None = None,
        controller: Controller[Context] = Controller(),
        # Initial agent run parameters
        sensitive_data: Optional[Dict[str, str]] = None,
        initial_actions: Optional[List[Dict[str, Dict[str, Any]]]] = None,
        # Cloud Callbacks
        register_new_step_callback: Union[
            Callable[['BrowserState', 'AgentOutput', int], None],  # Sync callback
            Callable[['BrowserState', 'AgentOutput', int], Awaitable[None]],  # Async callback
            None,
        ] = None,
        register_done_callback: Union[
            Callable[['AgentHistoryList'], Awaitable[None]],  # Async Callback
            Callable[['AgentHistoryList'], None],  # Sync Callback
            None,
        ] = None,
        register_external_agent_status_raise_error_callback: (
            Callable[[], Awaitable[bool]] | None
        ) = None,
        available_file_paths: Optional[list[str]] = None,
        # Inject state
        injected_agent_state: Optional[AgentState] = None,
        #
        context: Context | None = None,
        detailed_logging: bool = False,
    ):

        # Core components
        self.controller = controller
        self.sensitive_data = sensitive_data

        self.available_file_paths = available_file_paths
        # Initialize state
        self.state = injected_agent_state or AgentState()
        # Action setup
        self._setup_action_models()
        self.initial_actions = (
            self._convert_initial_actions(initial_actions) if initial_actions else None
        )

        # Initialize available actions for system prompt (only non-filtered actions)
        # These will be used for the system prompt to maintain caching
        self.unfiltered_actions = self.controller.registry.get_prompt_description()

        # Browser setup
        self.injected_browser = browser is not None
        self.injected_browser_context = browser_context is not None
        self.browser = browser or Browser()
        self.browser_context = browser_context or BrowserContext(
            browser=self.browser, config=self.browser.config.new_context_config
        )

        # Callbacks
        self.register_new_step_callback = register_new_step_callback
        self.register_done_callback = register_done_callback
        self.register_external_agent_status_raise_error_callback = (
            register_external_agent_status_raise_error_callback
        )

        # Context
        self.context = context

        # Telemetry
        self.telemetry = ProductTelemetry()
        self.detailed_logger = None
        if detailed_logging:
            from meowdock.library.utils.printer import Printer
            self.detailed_logger = Printer('exector_detail_pipe')

        self._current_multi_act = {
            'action': None,
            'element': None
        }
        self._current_action = {
            'action': None,
            'element': None
        }
        self._idx_hist = []

    def _setup_action_models(self) -> None:
        """Setup dynamic action models from controller's registry"""
        # Initially only include actions with no filters
        self.ActionModel = self.controller.registry.create_action_model()
        # Create output model with the dynamic actions
        self.AgentOutput = AgentOutput.type_with_custom_actions(self.ActionModel)

        # used to force the done action when max_steps is reached
        self.DoneActionModel = self.controller.registry.create_action_model(
            include_actions=['done']
        )
        self.DoneAgentOutput = AgentOutput.type_with_custom_actions(self.DoneActionModel)

    def _convert_initial_actions(
        self, actions: List[Dict[str, Dict[str, Any]]]
    ) -> List[ActionModel]:
        """Convert dictionary-based actions to ActionModel instances"""
        converted_actions = []
        action_model = self.ActionModel
        for action_dict in actions:
            # Each action_dict should have a single key-value pair
            action_name = next(iter(action_dict))
            params = action_dict[action_name]

            # Get the parameter model for this action from registry
            action_info = self.controller.registry.registry.actions[action_name]
            param_model = action_info.param_model

            # Create validated parameters using the appropriate param model
            validated_params = param_model(**params)

            # Create ActionModel instance with the validated parameters
            action_model = self.ActionModel(**{action_name: validated_params})
            converted_actions.append(action_model)

        return converted_actions

    # @observe(name='controller.multi_act')
    @time_execution_async('--multi-act (agent)')
    async def multi_act(
        self,
        actions: list[ActionModel],
        check_for_new_elements: bool = True,
    ) -> list[ActionResult]:
        """Execute multiple actions"""
        self._current_multi_act['action'] = [a.model_dump(exclude_unset=True) for a in actions]
        results = []

        cached_selector_map = await self.browser_context.get_selector_map()
        cached_path_hashes = set(e.hash.branch_path_hash for e in cached_selector_map.values())

        for i, act in enumerate(actions):
            l = []
            idx = act.get_index()
            l.append(cached_selector_map.get(idx, None))
        self._current_multi_act['element'] = l

        if self.detailed_logger:
            self.detailed_logger.writeline('Selector Map:')
            self.detailed_logger.writeline(
                [
                    f'	[{j}]: {"+" if e.is_interactive else " "} <{e.tag_name}> {e.xpath} {list(e.attributes.keys())}'
                    for j, e in cached_selector_map.items()
                ]
            )
            self.detailed_logger.writeline('-' * 80)
            self.detailed_logger.writeline('Actions to be executed: Press Enter to start')
            for i, action in enumerate(actions):
                a = action.model_dump(exclude_none=True)
                k = list(a.keys())[0]
                self.detailed_logger.writeline(f'[{i+1:3}]: {k} {a[k]}')
                if len(cached_selector_map) > 0:
                    self.detailed_logger.writeline(f' xpath: {cached_selector_map[i].xpath}')
            self.detailed_logger.waitkey()

        await self.browser_context.remove_highlights()

        for i, action in enumerate(actions):
            if self.detailed_logger:
                self.detailed_logger.writeline('=' * 80)
                self.detailed_logger.writeline(
                    f'Current Action {i+1}/{len(actions)}: {action.model_dump(exclude_none=True)}'
                )

            if action.get_index() is not None and i != 0:  # TODO: throw error
                new_state = await self.browser_context.get_state()
                new_path_hashes = set(
                    e.hash.branch_path_hash for e in new_state.selector_map.values()
                )
                if check_for_new_elements and not new_path_hashes.issubset(cached_path_hashes):
                    # next action requires index but there are new elements on the page
                    msg = f'Something new appeared after action {i} / {len(actions)}'
                    logger.info(msg)
                    results.append(ActionResult(extracted_content=msg, include_in_memory=True))
                    break

                if self.detailed_logger:
                    self.detailed_logger.writeline('Selector Map changed after Action:')
                    self.detailed_logger.writeline(
                        [
                            f'	[{j}]: {"+" if e.is_interactive else " "} <{e.tag_name}> {e.xpath} {list(e.attributes.keys())}'
                            for j, e in cached_selector_map.items()
                        ]
                    )

            try:
                if self.detailed_logger:
                    self.detailed_logger.writeline('Executing action...')
                self._current_action['action'] = action.model_dump(exclude_unset=True)
                self._current_action['element'] = cached_selector_map.get(act.get_index(), None)
                result = await self.controller.act(
                    action,
                    self.browser_context,
                    self.sensitive_data,
                    self.available_file_paths,
                    context=self.context,
                )

                results.append(result)
                if self.detailed_logger:
                    self.detailed_logger.writeline(
                        f'Step {i+1} / {len(actions)} execution result: {result.model_dump(exclude_unset=True, exclude_none=True, exclude_defaults=True)}'
                    )

                logger.debug(f'Executed action {i + 1} / {len(actions)}')
                if results[-1].is_done or results[-1].error or i == len(actions) - 1:
                    break

                await asyncio.sleep(self.browser_context.config.wait_between_actions)
                # hash all elements. if it is a subset of cached_state its fine - else break (new elements on page)

            except asyncio.CancelledError:
                # Gracefully handle task cancellation
                logger.info(f'Action {i + 1} was cancelled due to Ctrl+C')
                if not results:
                    # Add a result for the cancelled action
                    results.append(
                        ActionResult(
                            error='The action was cancelled due to Ctrl+C', include_in_memory=True
                        )
                    )
                raise InterruptedError('Action cancelled by user')

            if i < len(actions) - 1:
                if self.detailed_logger:
                    self.detailed_logger.writeline(
                        f'Step {i+1} / {len(actions)} completed. Proceeding to the next step'
                    )
                    self.detailed_logger.waitkey()

        if self.detailed_logger:
            self.detailed_logger.writeline(
                'This multi_act session has ended. Continuing will clear the screen'
            )
            self.detailed_logger.waitkey()
            self.detailed_logger.clear()

        return results

    async def _update_action_indices(
        self,
        historical_element: Optional[DOMHistoryElement],
        action: ActionModel,  # Type this properly based on your action model
        current_state: BrowserState,
    ) -> Optional[ActionModel]:
        """
        Update action indices based on current page state.
        Returns updated action or None if element cannot be found.
        """
        if not historical_element or not current_state.element_tree:
            return action

        current_element = HistoryTreeProcessor.find_history_element_in_tree(
            historical_element, current_state.element_tree
        )

        if not current_element or current_element.highlight_index is None:
            return None

        old_index = action.get_index()
        if old_index != current_element.highlight_index:
            action.set_index(current_element.highlight_index)
            logger.info(
                f'Element moved in DOM, updated index from {old_index} to {current_element.highlight_index}'
            )

        return action

    async def _execute_simplified_history_action_step(
        self, history_step: SimplifiedHistoryActionNode
    ):
        '''Execute a single step from history
        mimicking _execute_history_step
        '''
        state = await self.browser_context.get_state(False)
        if not state:
            raise ValueError('Invalid state')
        updated_actions = []
        for i, action in enumerate(history_step.action):
            updated_action = await self._update_action_indices(
                history_step.interacted_element[i],
                action,
                state,
            )
            updated_actions.append(updated_action)

            if updated_action is None:
                xpath = (
                    history_step.interacted_element[i].xpath
                    if history_step.interacted_element[i]
                    else ''
                )
                raise XPathError(f'Failed to locate the element "{xpath}" on current page. ')

        result = await self.multi_act(updated_actions)

        await asyncio.sleep(history_step.delay)
        return result

    async def rerun_list_history(
        self,
        history: SimplifiedHistoryActionList,
        max_retries: int = 3,
        delay_between_retries: float = 3.0,
    ) -> list[ActionResult]:
        """
        mimicking rerun_history

        Args:
                history: The history to replay
                max_retries: Maximum number of retries per action
                delay_between_retries: Delay between actions in seconds

        Returns:
                List of action results
        """
        try:
            if self.detailed_logger:
                self.detailed_logger.open()
            # Execute initial actions if provided
            if self.initial_actions:
                result = await self.multi_act(self.initial_actions)
                self.state.last_result = result

            results = []
            bb = False
            for i, history_item in enumerate(history.history):
                self._idx_hist.append(0)
                logger.info(
                    f'Step {i + 1}: Started {list(map(lambda x: x.model_dump_json(exclude_none=True), history_item.action))}'
                )
                if not history_item.action or history_item.action == [None]:
                    logger.warning(f'Step {i + 1}: No action to replay, skipping')
                    results.append(ActionResult(error='No action to replay'))
                    continue

                retry_count = 0
                while retry_count < max_retries:
                    try:
                        result = await self._execute_simplified_history_action_step(history_item)
                        results.extend(result)
                        break

                    except Exception as e:
                        retry_count += 1
                        if retry_count == max_retries:
                            error_msg = (
                                f'Step {i + 1} failed after {max_retries} attempts: {str(e)}'
                            )
                            logger.error(error_msg)
                            results.append(ActionResult(error=error_msg))
                            # raise RuntimeError(error_msg)
                            tb_str = traceback.format_exc()
                            bb = True
                            raise
                        else:
                            logger.warning(
                                f'Step {i + 1} failed (attempt {retry_count}/{max_retries}), retrying...'
                            )
                            await asyncio.sleep(delay_between_retries)
                if bb:
                    break

            return results
        finally:
            if self.detailed_logger:
                self.detailed_logger.close()

    async def rerun_tree_history(self,
                              history_tree: SimplifiedHistoryActionTreeNode[ActionModelRuntime],
                              max_retries: int = 3,
                              delay_between_retries: float = 3.0,
                              mode: str = 'fixed',
                              random_seed: Optional[int]=None) -> list[ActionResult]:
        """
        rerun the history tree

        Args:
                history_tree: The history tree to replay
                max_retries: Maximum number of retries per action
                delay_between_retries: Delay between actions in seconds
                mode ('fixed' | 'random'): Iteration method
                random_seed: Random seed for random and monte carlo tree search

        Returns:
                List of action results
        """
        try:
            if self.detailed_logger: self.detailed_logger.open()
            # Execute initial actions if provided
            if self.initial_actions:
                result = await self.multi_act(self.initial_actions)
                self.state.last_result = result

            results = []
            bb = False
            i = 0

            ROOT = SimplifiedHistoryActionTreeNode[self.ActionModel](
                data={"interacted_element":[None],"action":[{"done":{"text":"This is the ROOT.","success": False}}]},
                children=[history_tree.model_dump(exclude_unset=True)],
            )
            node_stack = [ROOT]
            node = ROOT
            while True:
                if len(node.children) == 0:
                    logger.info(f'Step {i + 1}: No more actions to replay, stopping')
                    break

                idx = node.get_next_node_index(mode)
                self._idx_hist.append(idx)
                if idx <= -1:
                    logger.info(f'Step {i + 1}: All children have been acted, falling back to the parent node')
                    curr_node = node_stack.pop()
                    node = node_stack[-1]
                    if node_stack[-1] == ROOT:
                        error_msg = f'Step {i + 1}: Falling back to ROOT. '
                        logger.error(error_msg)
                        results.append(ActionResult(error=error_msg))
                        raise FallbackToRootError(error_msg)
                    curr_idx = node.children.index(curr_node)
                    node._searched[curr_idx] = True
                    continue
                else:
                    node = node.children[idx]
                    node_stack.append(node)
                if self.detailed_logger:
                    self.detailed_logger.writeline(ROOT.to_str(highlight=[node]))
                logger.info(f'Step {i + 1}: Started {list(map(lambda x: x.model_dump_json(exclude_none=True), node.data.action))}')
                if (
                    not node.data.action
                    or node.data.action == [None]
                ):
                    logger.warning(f'Step {i + 1}: No action to replay, skipping')
                    results.append(ActionResult(error='No action to replay'))
                    continue

                retry_count = 0
                while retry_count < max_retries:
                    try:
                        if self.detailed_logger:
                            self.detailed_logger.writeline(ROOT.to_str(highlight=[node]))
                        node_stack[-2]._acted_count[idx] += 1
                        result = await self._execute_simplified_history_action_step(node.data)
                        results.extend(result)
                        break

                    except Exception as e:
                        retry_count += 1
                        if retry_count == max_retries:
                            traceback.format_exception(e)
                            error_msg = f'Step {i + 1} failed after {max_retries} attempts: {str(e)}'
                            logger.error(error_msg)
                            results.append(ActionResult(error=error_msg))
                            node_stack.pop()
                            node = node_stack[-1]
                            node._searched[idx] = True
                            break
                        else:
                            logger.warning(
                                f'Step {i + 1} failed (attempt {retry_count}/{max_retries}), retrying...')
                            await asyncio.sleep(delay_between_retries)
                if bb:
                    break
                i += 1

            return results
        finally:
            if self.detailed_logger: self.detailed_logger.close()   
    
    async def export_error_log(self, compressed=True, **kw):
        '''Output crash log. Screenshots, current html page, current json dom tree, current interactable 
        elements, all registered functions, current actions, action history, and log will be exported.
        Any additional keyword args will also be added to executor_state.json.

        Args:
            compressed (bool): Whether zipped or not 
        '''
        try:
            import datetime, json, os

            dir = 'crashlog' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            
            ctx = self.browser_context
            page = await ctx.get_current_page()
            await page.bring_to_front()
            await page.wait_for_load_state()

            screenshot = await page.screenshot(
                full_page=False,
                animations='disabled',
            )
            screenshot_full = await page.screenshot(
                full_page=True,
                animations='disabled',
            )
            ses = await ctx.get_session()
            if ses.cached_state:
                selector_map = ses.cached_state.selector_map
                element_tree = ses.cached_state.element_tree
            else:
                selector_map = {}
                element_tree = {}
                
            def json_default(obj):
                if hasattr(obj, 'to_json'):
                    return obj.to_json()
                elif hasattr(obj, 'model_dump_json'):  # pydantic BaseModel
                    return obj.model_dump_json(exclude_unset=True)
                elif hasattr(obj, '__json__'):
                    return obj.__json__()
                raise TypeError()
            
            executor_state = {
                'avaliable_functions': list(self.controller.registry.registry.actions.keys()),
                'current_multi_act': self._current_multi_act,
                'current_action': self._current_action,
                'selector_map': selector_map,
                'element_tree': element_tree,
                'index_history': self._idx_hist
            }
            executor_state |= { k: v for k, v in kw.items() if k not in executor_state.keys() }
            d = {
                'screenshot.png': screenshot,
                'screenshot_full.png': screenshot_full,
                'executor_state.json': json.dumps(executor_state, default=json_default, ensure_ascii=False).encode('utf-8'),
                'content.html': (await page.content()).encode('utf-8'),
                'log.txt': _log.getvalue()
            }
            if compressed:
                import zipfile
                zipped = io.BytesIO()
                with zipfile.ZipFile(zipped, mode='w', compression=zipfile.ZIP_LZMA) as f:
                    for k, v in d.items():
                        f.writestr(f"{dir}/{k}", v)
                zipped.seek(0)

                if not os.path.isdir(f'log/executor'):
                    os.makedirs(f'log/executor', exist_ok=True)
                with open(f'log/executor/{dir}.zip', 'wb') as f:
                    f.write(zipped.read())
            else:
                if not os.path.isdir(f'log/executor/{dir}'):
                    os.makedirs(f'log/executor/{dir}', exist_ok=True)
                for k, v in d.items():
                    with open(f'log/executor/{dir}/{k}', 'wb') as f:
                        f.write(v)
        except Exception as e:
            traceback.print_exception(e)

