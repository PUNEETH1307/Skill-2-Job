"""Gunicorn production configuration for Skill2Job backend."""

import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

# Worker processes
workers = int(os.environ.get('WEB_CONCURRENCY', 3))
worker_class = 'sync'
timeout = 120

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Security
limit_request_line = 8190
limit_request_fields = 100
