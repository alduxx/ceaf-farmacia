# Gunicorn configuration file for CEAF Farmacia application

import multiprocessing
import os

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = min(multiprocessing.cpu_count() * 2 + 1, 8)  # Cap at 8 workers
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True
timeout = 30
keepalive = 2

# Logging
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
accesslog = "/opt/farmacia/logs/gunicorn_access.log"
errorlog = "/opt/farmacia/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'farmacia_gunicorn'

# Server mechanics
daemon = False
pidfile = '/opt/farmacia/logs/gunicorn.pid'
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment and configure if using HTTPS directly with Gunicorn)
# keyfile = "/path/to/ssl/private.key"
# certfile = "/path/to/ssl/certificate.crt"

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Farmacia application...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading Farmacia application...")

def worker_init(worker):
    """Called just after a worker has been forked."""
    worker.log.info(f"Worker spawned (pid: {worker.pid})")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.info(f"Worker received SIGABRT signal (pid: {worker.pid})")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info(f"Worker about to be forked (pid: {worker.pid})")