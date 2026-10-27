"""API clients against fake HTTP responses - no ckan import, no network."""

import pytest

from ckanext.citations.lib import datacite_events_client, http


class FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


@pytest.fixture
def responses(monkeypatch):
    queue = []
    monkeypatch.setattr(http.requests, 'get', lambda *a, **k: queue.pop(0))
    monkeypatch.setattr(http.time, 'sleep', lambda s: None)
    return queue


def _event(subj, obj):
    # The real API's attribute names are hyphenated.
    return {'attributes': {'subj-id': subj, 'obj-id': obj}}


def test_datacite_citing_dois_are_the_objects_of_this_dois_events(responses):
    responses.append(
        FakeResponse(
            200,
            {
                'data': [
                    _event('https://doi.org/10.1/OURS', 'https://doi.org/10.2/a'),
                    _event('https://doi.org/10.1/ours', 'https://doi.org/10.2/A'),
                    # Our dataset citing something else: not a citation of it.
                    _event('https://doi.org/10.9/other', 'https://doi.org/10.1/ours'),
                    _event('https://doi.org/10.1/ours', 'https://example.org/x'),
                ]
            },
        )
    )

    assert datacite_events_client.get_citing_dois('10.1/ours') == ['10.2/a']


def test_get_json_retries_then_returns_the_body(responses):
    responses.extend(
        [FakeResponse(503), FakeResponse(429), FakeResponse(200, {'ok': 1})]
    )

    assert http.get_json('https://api.test/x', {}, RuntimeError) == {'ok': 1}


def test_get_json_404_is_none_and_other_errors_raise(responses):
    responses.extend([FakeResponse(404), FakeResponse(400)])

    assert http.get_json('https://api.test/x', {}, RuntimeError) is None
    with pytest.raises(RuntimeError):
        http.get_json('https://api.test/x', {}, RuntimeError)


def test_get_json_never_puts_the_api_key_in_its_errors(monkeypatch, responses):
    def unreachable(*args, **kwargs):
        # requests quotes the URL, query string included.
        raise http.requests.ConnectionError(
            'Max retries with url: /works?api_key=s3cret'
        )

    monkeypatch.setattr(http.requests, 'get', unreachable)
    with pytest.raises(RuntimeError) as failure:
        http.get_json('https://api.test/x', {'api_key': 's3cret'}, RuntimeError)
    assert 's3cret' not in str(failure.value)

    responses.append(FakeResponse(403, 'Invalid api_key s3cret'))
    monkeypatch.setattr(http.requests, 'get', lambda *a, **k: responses.pop(0))
    with pytest.raises(RuntimeError) as failure:
        http.get_json('https://api.test/x', {'api_key': 's3cret'}, RuntimeError)
    assert 's3cret' not in str(failure.value)


@pytest.mark.ckan_config('ckanext.citations.openalex_api_key', 'k3y')
def test_openalex_requests_carry_the_configured_api_key(monkeypatch):
    from ckanext.citations.lib import openalex_client

    sent = []
    monkeypatch.setattr(
        http, 'get_json', lambda url, params, error_cls: sent.append(params) or {}
    )
    openalex_client.get_work('W1', contact_email='team@example.org')

    assert sent == [{'mailto': 'team@example.org', 'api_key': 'k3y'}]
