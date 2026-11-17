"""Non-streaming Chat Completions transport; no response rewriting or retries."""
from dataclasses import dataclass
import json
import os
import urllib.error
import urllib.parse
import urllib.request


class ProviderError(RuntimeError):
    """Transport/protocol failure whose message contains no response body/key."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        fp.close()
        raise ProviderError('API redirect refused; configure the final endpoint')


@dataclass(frozen=True)
class Completion:
    text: str
    usage: dict | None
    response_id: str | None
    finish_reason: str | None


class ChatCompletions:
    def __init__(self, model, base_url='https://api.openai.com/v1',
                 key_env='OPENAI_API_KEY', reasoning_effort=None,
                 max_completion_tokens=None, timeout=180, local_fixture=False):
        url = urllib.parse.urlsplit(base_url)
        if url.username or url.password or url.query or url.fragment or not url.hostname:
            raise ValueError('Use a base URL without credentials, query or fragment')
        loopback = url.hostname in ('localhost', '127.0.0.1', '::1')
        if url.scheme != 'https' and not (url.scheme == 'http' and loopback):
            raise ValueError('HTTP is supported only for loopback fixtures; use HTTPS')
        if local_fixture and not loopback:
            raise ValueError('A local fixture must use a loopback address')
        if not isinstance(model, str) or not model.strip():
            raise ValueError('An explicit model ID is required')
        if timeout <= 0 or (max_completion_tokens is not None and max_completion_tokens <= 0):
            raise ValueError('Timeout and token limit must be positive')
        self.base_url = base_url.rstrip('/')
        self.endpoint = self.base_url + '/chat/completions'
        self.model, self.reasoning_effort = model, reasoning_effort
        self.max_completion_tokens, self.timeout = max_completion_tokens, timeout
        self.local_fixture = local_fixture
        self.key = None if local_fixture else os.environ.get(key_env)
        if not local_fixture and not self.key:
            raise ValueError('API credential environment variable is not set')
        self.opener = urllib.request.build_opener(NoRedirect())

    def metadata(self):
        return dict(model=dict(provider='local_http_fixture' if self.local_fixture else 'openai_compatible',
                               model_id=self.model, reasoning_effort=self.reasoning_effort,
                               temperature=None, seed=None, max_completion_tokens=self.max_completion_tokens,
                               service_url=self.base_url),
                    execution_mode='api_protocol_validation' if self.local_fixture else 'model_api',
                    model_context_policy='fresh_api_messages_per_stage_continuous_history',
                    llm_api_used=not self.local_fixture, formal_llm_enabled=not self.local_fixture)

    def complete(self, messages):
        payload = dict(model=self.model, messages=messages, stream=False)
        if self.reasoning_effort is not None:
            payload['reasoning_effort'] = self.reasoning_effort
        if self.max_completion_tokens is not None:
            payload['max_completion_tokens'] = self.max_completion_tokens
        headers = {'Content-Type': 'application/json'}
        if self.key:
            headers['Authorization'] = 'Bearer ' + self.key
        request = urllib.request.Request(self.endpoint, data=json.dumps(payload).encode('utf-8'), headers=headers)
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                data = json.load(response)
        except urllib.error.HTTPError as exc:
            code = exc.code
            exc.close()
            raise ProviderError('API HTTP failure: ' + str(code) + '; no automatic retry') from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ProviderError('API connection/timeout failure; outcome unknown; no automatic retry') from None
        except (ValueError, UnicodeError):
            raise ProviderError('API returned an unreadable response') from None
        try:
            choice = data['choices'][0]
            content = choice['message']['content']
            if not isinstance(content, str):
                raise ValueError()
        except (KeyError, IndexError, TypeError, ValueError):
            raise ProviderError('API returned no textual assistant completion') from None
        raw = data.get('usage')
        usage = None
        if isinstance(raw, dict):
            values = [raw.get(name) for name in ('prompt_tokens', 'completion_tokens', 'total_tokens')]
            if all(type(v) is int and v >= 0 for v in values):
                usage = dict(zip(('input_tokens', 'output_tokens', 'total_tokens'), values))
        return Completion(content, usage, data.get('id'), choice.get('finish_reason'))
