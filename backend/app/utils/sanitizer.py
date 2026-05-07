"""Input sanitization utility for the Skill2Job Placement System.

Strips common SQL injection patterns and XSS payloads from string inputs.
Applied as a before_request hook in the Flask app factory.

Requirements: 16.3, 14.4
"""

import re

from flask import request

# SQL injection patterns to strip
_SQL_PATTERNS = [
    re.compile(r"(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC|EXECUTE)\b\s)", re.IGNORECASE),
    re.compile(r"(--|;)\s*$", re.IGNORECASE),
    re.compile(r"'\s*(OR|AND)\s+'", re.IGNORECASE),
    re.compile(r"'\s*(OR|AND)\s+\d+\s*=\s*\d+", re.IGNORECASE),
    re.compile(r"1\s*=\s*1", re.IGNORECASE),
    re.compile(r"'\s*;\s*--", re.IGNORECASE),
]

# XSS patterns to strip
_XSS_PATTERNS = [
    re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<\s*script[^>]*>", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"<\s*iframe[^>]*>", re.IGNORECASE),
    re.compile(r"<\s*object[^>]*>", re.IGNORECASE),
    re.compile(r"<\s*embed[^>]*>", re.IGNORECASE),
]


def sanitize_string(value: str) -> str:
    """Sanitize a single string value by stripping SQL injection and XSS patterns.

    Args:
        value: The input string to sanitize.

    Returns:
        The sanitized string.
    """
    if not isinstance(value, str):
        return value

    result = value
    for pattern in _SQL_PATTERNS:
        result = pattern.sub("", result)
    for pattern in _XSS_PATTERNS:
        result = pattern.sub("", result)

    return result


def sanitize_data(data):
    """Recursively sanitize all string values in a data structure.

    Handles dicts, lists, and plain strings.

    Args:
        data: The data to sanitize (dict, list, or string).

    Returns:
        The sanitized data structure.
    """
    if isinstance(data, dict):
        return {k: sanitize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    elif isinstance(data, str):
        return sanitize_string(data)
    return data


def register_sanitizer(app):
    """Register a before_request hook that sanitizes JSON request bodies.

    Overrides ``request.get_json`` so that all route handlers automatically
    receive sanitized data.

    Args:
        app: The Flask application instance.
    """

    @app.before_request
    def _sanitize_request():
        if request.is_json and request.data:
            json_data = request.get_json(silent=True)
            if json_data is not None:
                sanitized = sanitize_data(json_data)
                # Monkey-patch get_json to return sanitized data
                request._sanitized_json = sanitized
                _original_get_json = request.get_json

                def _patched_get_json(**kwargs):
                    return request._sanitized_json

                request.get_json = _patched_get_json
