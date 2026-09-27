"""Explicitly invoked P0-C2 experiment; never performs live calls on import."""

from copy import deepcopy
import os

from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig
from google.adk.models import BaseLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from bible_reference_tool import bible_reference_tool

INSTRUCTION = (
    'When asked to normalize or identify a Bible passage reference, call '
    'normalize_bible_reference with the reference text as supplied. Use the tool '
    'result to answer briefly. If the tool reports an error, explain it and ask '
    'for clarification; do not invent a corrected reference or a successful result. '
    'Your final answer is presentation; the tool result is the canonical data.'
)
EXAMPLES = (
    ('Please normalize 約三16', '約三16'),
    ('What passage is Jn 3:16?', 'Jn 3:16'),
    ('請把創世紀1-3章標準化', '創世紀1-3章'),
    ('Normalize Jude 5', 'Jude 5'),
    ('Please normalize John 3:16,18', 'John 3:16,18'),
)


def create_agent(model: str | BaseLlm) -> Agent:
    """Construct one agent without invoking a model or loading credentials."""
    return Agent(name='caif_reference_experiment', model=model,
                 instruction=INSTRUCTION, tools=[bible_reference_tool])


def _live_model() -> str:
    """Preflight for this experiment's Gemini Developer API route only."""
    if os.environ.get('GOOGLE_GENAI_USE_VERTEXAI', '').lower() in ('1', 'true'):
        raise RuntimeError('This experiment uses Gemini Developer API; set GOOGLE_GENAI_USE_VERTEXAI=FALSE.')
    model = os.environ.get('CAIF_ADK_MODEL')
    if not model:
        raise RuntimeError('Set CAIF_ADK_MODEL to an available Gemini model ID before running live.')
    if not (os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')):
        raise RuntimeError('Configure GOOGLE_API_KEY or GEMINI_API_KEY locally before running live.')
    return model


async def run_live_experiment() -> list[dict]:
    """Explicit live entry point. Returns observations, not a CAIF result contract."""
    return await _run_experiment(_live_model())


async def _run_experiment(model: str | BaseLlm) -> list[dict]:
    """Shared capture path; offline tests supply a scripted BaseLlm only."""
    observed = []

    def capture(tool, args, tool_context, tool_response):
        observed.append({'call_id': tool_context.function_call_id,
                         'name': tool.name, 'arguments': deepcopy(args),
                         'result': deepcopy(tool_response)})
        # Returning None leaves the actual ADK tool response unchanged.

    agent = create_agent(model)
    agent.after_tool_callback = capture
    sessions = InMemorySessionService()
    runner = Runner(agent=agent, app_name='caif_p0_c2', session_service=sessions)
    records = []
    try:
        for index, (message, span) in enumerate(EXAMPLES):
            observed.clear()
            session = await sessions.create_session(app_name='caif_p0_c2',
                                                    user_id='experiment', session_id=str(index))
            record = {'user': message, 'reference_span': span, 'model': agent.model if isinstance(agent.model, str) else agent.model.model,
                      'events': [], 'tool_calls': [], 'tool_responses': [], 'final_responses': []}
            async for event in runner.run_async(
                user_id='experiment', session_id=session.id,
                new_message=types.Content(role='user', parts=[types.Part(text=message)]),
                run_config=RunConfig(max_llm_calls=5),
            ):
                record['events'].append(event.model_dump(mode='json', exclude_none=True))
                for call in event.get_function_calls():
                    record['tool_calls'].append(call.model_dump(mode='json', exclude_none=True))
                for response in event.get_function_responses():
                    record['tool_responses'].append(response.model_dump(mode='json', exclude_none=True))
                if event.is_final_response() and event.content:
                    record['final_responses'].append(''.join(
                        part.text for part in event.content.parts or [] if part.text and not part.thought))
            record['adapter_returns'] = deepcopy(observed)
            record['checks'] = []
            for response in record['tool_responses']:
                matches = [item for item in observed if item['call_id'] == response.get('id') and item['name'] == response['name']]
                result = response['response']
                record['checks'].append({
                    'call_id': response.get('id'),
                    'event_equals_adapter_return': len(matches) == 1 and matches[0]['result'] == result,
                    'raw_reference_matches_user_span': matches[0]['arguments'].get('raw_reference') == span if len(matches) == 1 else None,
                    'original_text_matches_user_span': result.get('original_text') == span if 'schema_version' in result else None,
                    'adapter_error': 'error' in result,
                })
            records.append(record)
    finally:
        await runner.close()
    return records
