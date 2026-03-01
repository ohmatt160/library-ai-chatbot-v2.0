"""Gunicorn configuration for production deployment"""
import os
import logging

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stdout
loglevel = "info"

# Worker processes
workers = 1
threads = 4
worker_class = "gthread"

# Timeout
timeout = 120
keepalive = 5

# Startup message
def on_starting(server):
    print(f"🚀 Gunicorn starting on {bind}")

def on_ready(server):
    print("✅ Gunicorn is ready and accepting connections")
