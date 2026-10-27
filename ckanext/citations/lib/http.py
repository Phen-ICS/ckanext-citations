"""GET with retries, shared by the OpenAlex and DataCite Event Data clients:
a refresh run calls these APIs for every citing work of every reference of
every dataset, so transient failures are the common case, not the exception.
"""

import logging
import time

import requests

log = logging.getLogger(__name__)

REQUEST_TIMEOUT = 20
MAX_RETRIES = 4
INITIAL_BACKOFF_SECONDS = 1.0


def _redact(text, params):
    """requests' error messages quote the URL with its query string: an API
    key passed there must not reach the logs."""
    secret = params.get('api_key')
    return text.replace(secret, '[REDACTED]') if secret else text


def get_json(url, params, error_cls):
    """The parsed JSON body, or None for a 404. Retries 429, 5xx and network
    errors with exponential backoff; any other status, or running out of
    retries, raises error_cls. Messages never contain params['api_key']."""
    backoff = INITIAL_BACKOFF_SECONDS
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as e:
            last_error = _redact(f'request failed: {e}', params)
        else:
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 404:
                return None
            if resp.status_code != 429 and resp.status_code < 500:
                raise error_cls(
                    _redact(
                        f'{url} returned {resp.status_code}: {resp.text[:200]}', params
                    )
                )
            last_error = _redact(
                f'returned {resp.status_code}: {resp.text[:200]}', params
            )
        log.warning(
            '%s %s (attempt %s/%s, retrying in %.1fs)',
            url,
            last_error,
            attempt,
            MAX_RETRIES,
            backoff,
        )
        time.sleep(backoff)
        backoff *= 2.0

    raise error_cls(f'{url} failed after {MAX_RETRIES} attempts: {last_error}')
