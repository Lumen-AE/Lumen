import json
import os
import unittest
from unittest.mock import patch

from lumen.commands.api import initial_messages
from lumen.paths import public_files
from lumen.providers.openai_compatible import ChatCompletions, ProviderError
from tests.api_fixture import http_fixture, response


class ApiTests(unittest.TestCase):
    def test_literal_unicode_usage_and_options(self):
        wire = '```json\n{"note":"café"}\n```\n'
        with http_fixture(lambda p, n: (200, response(wire, dict(prompt_tokens=2, completion_tokens=3, total_tokens=5)), {})) as (url, calls):
            with patch.dict(os.environ, {'LUMEN_UNIT_KEY': 'unit-test-only-not-a-real-key'}):
                provider = ChatCompletions('fixture', url, 'LUMEN_UNIT_KEY', 'low', 123)
                result = provider.complete([dict(role='user', content='hello')])
            self.assertEqual(result.text, wire)
            self.assertEqual(result.usage['total_tokens'], 5)
            self.assertEqual(calls[0]['path'], '/v1/chat/completions')
            self.assertEqual(calls[0]['payload']['reasoning_effort'], 'low')
            self.assertEqual(calls[0]['payload']['max_completion_tokens'], 123)
            self.assertEqual(calls[0]['authorization'], 'Bearer unit-test-only-not-a-real-key')
            self.assertNotIn('unit-test-only', json.dumps(provider.metadata()))

    def test_unknown_usage_and_null_completion(self):
        with http_fixture(lambda p, n: (200, response('bad json' if n == 1 else None), {})) as (url, calls):
            client = ChatCompletions('fixture', url, local_fixture=True)
            self.assertIsNone(client.complete([]).usage)
            with self.assertRaises(ProviderError):
                client.complete([])
            self.assertEqual(len(calls), 2)
            self.assertTrue(all(c['authorization'] is None for c in calls))

    def test_http_errors_are_not_retried_or_echoed(self):
        with http_fixture(lambda p, n: (429, dict(error='private-server-message'), {})) as (url, calls):
            with self.assertRaises(ProviderError) as raised:
                ChatCompletions('fixture', url, local_fixture=True).complete([])
            self.assertEqual(len(calls), 1)
            self.assertIn('429', str(raised.exception))
            self.assertNotIn('private-server-message', str(raised.exception))

    def test_redirect_does_not_forward_credentials(self):
        with http_fixture(lambda p, n: (307, {}, {'Location': 'https://example.invalid/'})) as (url, calls):
            with self.assertRaises(ProviderError):
                ChatCompletions('fixture', url, local_fixture=True).complete([])
            self.assertEqual(len(calls), 1)

    def test_endpoint_and_missing_key(self):
        for url in ('https://user:pass@example.com/v1', 'https://example.com/v1?key=secret', 'http://example.com/v1'):
            with self.assertRaises(ValueError):
                ChatCompletions('fixture', url)
        with self.assertRaises(ValueError):
            ChatCompletions('fixture', 'https://example.com/v1', local_fixture=True)
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
            ChatCompletions('fixture')

    def test_public_materials_are_complete_and_stage_specific(self):
        base, bmanifest = initial_messages('base')
        evidence, emanifest = initial_messages('evidence')
        self.assertNotEqual(base[1], evidence[1])
        self.assertEqual(base[2:], evidence[2:])
        self.assertEqual(bmanifest[1:], emanifest[1:])
        for message, (name, path) in zip(base[1:], public_files('base')):
            self.assertEqual(message['content'], '=== ' + name + ' ===\n' + path.read_bytes().decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
