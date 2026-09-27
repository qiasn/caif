"""First CKAIS application boundary; not a production application."""

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import sys

from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig
from google.adk.models import BaseLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


def _load_adapter():
    """Temporary checkout bridge; reuse the adapter, never copy its capability."""
    name = 'bible_reference_tool'
    source = Path(__file__).resolve().parents[2] / 'adapters/google-adk/bible_reference_tool.py'
    if name in sys.modules:
        module = sys.modules[name]
        if Path(module.__file__).resolve() != source:
            raise ImportError('Unexpected Bible reference adapter module')
        return module
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise ImportError('Cannot load the CAIF Google ADK adapter')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


_adapter = _load_adapter()
INSTRUCTION = (
    'You are the first CKAIS reference-assistance experiment. When asked to '
    'identify or normalize a Bible reference, call normalize_bible_reference '
    'with the reference text as supplied. Treat the tool result as authoritative '
    'structured data and present a brief useful answer. On a tool error, explain '
    'it and ask for clarification; never invent a corrected reference or success. '
    'Your final prose is presentation, not canonical data.'
)
EXAMPLES = (
    'Please normalize 約三16',
    'What passage is Jn 3:16?',
    '請把創世紀1-3章標準化',
    'Normalize Jude 5',
    'Please normalize John 3:16,18',
)


def create_agent(model: str | BaseLlm) -> Agent:
    return Agent(name='ckais_reference_assistant', model=model,
                 instruction=INSTRUCTION, tools=[_adapter.bible_reference_tool])


async def observe_requests(model: str | BaseLlm, messages) -> list[dict]:
    """Observe application requests; tool payloads and presentation stay separate.

    Records are local experiment observations, not a new CAIF result contract.
    Real model strings cause live calls; offline tests supply a scripted BaseLlm.
    """
    agent = create_agent(model)
    sessions = InMemorySessionService()
    runner = Runner(agent=agent, app_name='ckais_p1', session_service=sessions)
    observations = []
    try:
        for index, message in enumerate(messages):
            session = await sessions.create_session(app_name='ckais_p1', user_id='experiment', session_id=str(index))
            record = {'user': message, 'tool_calls': [], 'canonical_results': [],
                      'tool_errors': [], 'presentation': []}
            async for event in runner.run_async(
                user_id='experiment', session_id=session.id,
                new_message=types.Content(role='user', parts=[types.Part(text=message)]),
                run_config=RunConfig(max_llm_calls=5),
            ):
                for call in event.get_function_calls():
                    record['tool_calls'].append(call.model_dump(mode='json', exclude_none=True))
                for response in event.get_function_responses():
                    if response.name == _adapter.bible_reference_tool.name:
                        payload = deepcopy(response.response)
                        destination = 'tool_errors' if 'error' in payload else 'canonical_results'
                        record[destination].append({'call_id': response.id, 'payload': payload})
                if event.is_final_response() and event.content:
                    record['presentation'].append(''.join(
                        part.text for part in event.content.parts or [] if part.text and not part.thought))
            observations.append(record)
    finally:
        await runner.close()
    return observations


async def run_live_experiment() -> list[dict]:
    """Explicit Gemini Developer API experiment using only local environment."""
    if os.environ.get('GOOGLE_GENAI_USE_VERTEXAI', '').lower() in ('true', '1'):
        raise RuntimeError('Set GOOGLE_GENAI_USE_VERTEXAI=FALSE for this Developer API experiment.')
    model = os.environ.get('CAIF_ADK_MODEL')
    if not model:
        raise RuntimeError('Set CAIF_ADK_MODEL to an available Gemini model ID.')
    if not (os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')):
        raise RuntimeError('Configure GEMINI_API_KEY or GOOGLE_API_KEY locally.')
    return await observe_requests(model, EXAMPLES)
