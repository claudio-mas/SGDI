"""
Gunicorn configuration file for Sistema GED
"""
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('GUNICORN_WORKERS', 4))
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5

# Process naming
proc_name = 'sistema_ged'

# Server mechanics
daemon = False
pidfile = '/tmp/gunicorn_sistema_ged.pid'
user = None
group = None
tmp_upload_dir = None

# Logging
accesslog = os.getenv('GUNICORN_ACCESS_LOG', 'logs/gunicorn_access.log')
errorlog = os.getenv('GUNICORN_ERROR_LOG', 'logs/gunicorn_error.log')
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
def on_starting(server):
    """Called just before the master process is initialized."""
    print("Starting Gunicorn server for Sistema GED")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    print("Reloading Gunicorn workers")

def when_ready(server):
    """Called just after the server is started."""
    print(f"Gunicorn server is ready. Listening on: {bind}")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    print("Shutting down Gunicorn server")

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# SSL (if needed)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'
# ca_certs = '/path/to/ca_certs'
# cert_reqs = 0  # ssl.CERT_NONE
# ssl_version = 2  # ssl.PROTOCOL_SSLv23
# ciphers = 'TLSv1'
