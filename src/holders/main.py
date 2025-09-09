# gunicorn.conf.py - Production FastAPI Configuration
import os
import multiprocessing


def get_container_resources():
    """
    Get actual container CPU and memory limits from cgroups.
    Falls back to system resources if cgroup limits aren't available.
    """
    cpu_count = multiprocessing.cpu_count()
    memory_bytes = None
    
    # Try to read Docker/K8s cgroup limits
    try:
        # CPU limit from cgroups v1
        with open('/sys/fs/cgroup/cpu/cpu.cfs_quota_us', 'r') as f:
            cpu_quota = int(f.read().strip())
        with open('/sys/fs/cgroup/cpu/cpu.cfs_period_us', 'r') as f:
            cpu_period = int(f.read().strip())
        
        if cpu_quota > 0 and cpu_period > 0:
            cpu_count = max(1, cpu_quota // cpu_period)
    except (FileNotFoundError, ValueError):
        # Try cgroups v2
        try:
            with open('/sys/fs/cgroup/cpu.max', 'r') as f:
                cpu_max = f.read().strip()
                if cpu_max != 'max':
                    quota, period = cpu_max.split()
                    cpu_count = max(1, int(quota) // int(period))
        except (FileNotFoundError, ValueError):
            pass
    
    try:
        # Memory limit from cgroups v1
        with open('/sys/fs/cgroup/memory/memory.limit_in_bytes', 'r') as f:
            mem_limit = int(f.read().strip())
            if mem_limit < (1 << 62):  # Valid limit (not max value)
                memory_bytes = mem_limit
    except (FileNotFoundError, ValueError):
        # Try cgroups v2
        try:
            with open('/sys/fs/cgroup/memory.max', 'r') as f:
                mem_max = f.read().strip()
                if mem_max != 'max':
                    memory_bytes = int(mem_max)
        except (FileNotFoundError, ValueError):
            pass
    
    # Fallback to /proc/meminfo if cgroups not available
    if memory_bytes is None:
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        memory_kb = int(line.split()[1])
                        memory_bytes = memory_kb * 1024
                        break
        except (FileNotFoundError, ValueError):
            pass
    
    return cpu_count, memory_bytes


def calculate_workers(cpu_count, memory_bytes, app_type):
    """Calculate optimal worker count based on resources and app type."""
    memory_gb = memory_bytes / (1024**3) if memory_bytes else 2.0
    
    # Base worker calculation by app type
    if app_type == "cpu_intensive":
        base_workers = cpu_count
    elif app_type == "io_intensive":
        base_workers = cpu_count * 3
    else:  # web/api (default)
        base_workers = cpu_count * 2
    
    # Memory constraint (assuming 100-150MB per worker for FastAPI)
    memory_per_worker_gb = 0.12  # 120MB per worker
    max_workers_by_memory = max(1, int(memory_gb / memory_per_worker_gb))
    
    # Apply constraints
    workers = min(base_workers, max_workers_by_memory)
    
    # Reasonable bounds
    workers = max(1, min(workers, 32))
    
    return workers


# =======================
# Resource Detection
# =======================
cpu_count, memory_bytes = get_container_resources()
memory_gb = memory_bytes / (1024**3) if memory_bytes else 2.0

# App type affects worker calculation
APP_TYPE = os.getenv("APP_TYPE", "web")  # web, api, cpu_intensive, io_intensive

# =======================
# Server Socket
# =======================
bind = "0.0.0.0:8000"
backlog = 2048

# =======================
# Worker Processes
# =======================
workers = int(os.getenv("GUNICORN_WORKERS", calculate_workers(cpu_count, memory_bytes, APP_TYPE)))
worker_class = "uvicorn.workers.UvicornWorker"

# Worker connections based on memory
if memory_gb < 1:
    worker_connections = 500
elif memory_gb < 2:
    worker_connections = 1000
elif memory_gb < 4:
    worker_connections = 1500
else:
    worker_connections = 2000

worker_connections = int(os.getenv("WORKER_CONNECTIONS", worker_connections))

# =======================
# Timeouts
# =======================
# Request timeout
timeout_map = {
    "web": 30,
    "api": 30,
    "cpu_intensive": 120,
    "io_intensive": 60,
    "ml": 300
}
timeout = int(os.getenv("GUNICORN_TIMEOUT", timeout_map.get(APP_TYPE, 30)))

# Keep-alive timeout
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", 5 if memory_gb > 1 else 2))

# Graceful timeout (should be less than timeout)
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", min(timeout // 3, 30)))

# =======================
# Worker Lifecycle
# =======================
# Restart workers after this many requests to prevent memory leaks
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", 1000 if memory_gb > 2 else 500))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", max_requests // 20))

# Worker timeout (time to kill unresponsive workers)
worker_tmp_dir = "/dev/shm" if os.path.exists("/dev/shm") else None

# =======================
# Logging
# =======================
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
accesslog = "-"  # stdout
errorlog = "-"   # stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# =======================
# Process Management
# =======================
proc_name = os.getenv("PROC_NAME", "fastapi-gunicorn")
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None

# Preload application for better memory usage in production
preload_app = os.getenv("PRELOAD_APP", "true").lower() == "true"

# =======================
# Security
# =======================
# Limit request line size
limit_request_line = 8192
limit_request_fields = 200
limit_request_field_size = 8192

# =======================
# Development Overrides
# =======================
if os.getenv("ENV") == "development":
    workers = 1
    reload = True
    loglevel = "debug"
    preload_app = False
    timeout = 120  # More generous timeout for debugging

# =======================
# Startup Info
# =======================
def on_starting(server):
    server.log.info(f"🚀 Starting FastAPI with Gunicorn")
    server.log.info(f"📊 Resources: {cpu_count} CPUs, {memory_gb:.1f}GB RAM")
    server.log.info(f"👷 Workers: {workers} ({APP_TYPE} workload)")
    server.log.info(f"🔌 Connections per worker: {worker_connections}")
    server.log.info(f"⏱️  Timeout: {timeout}s, Keepalive: {keepalive}s")
    server.log.info(f"📝 Max requests per worker: {max_requests}")
    server.log.info(f"🔄 Preload app: {preload_app}")

def on_reload(server):
    server.log.info("🔄 Reloading application...")

def worker_int(worker):
    worker.log.info(f"Worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def post_fork(server, worker):
    server.log.info(f"Worker {worker.pid} booted")

def worker_abort(worker):
    worker.log.info(f"Worker {worker.pid} aborted")

# =======================
# Error Handling
# =======================
def on_exit(server):
    server.log.info("👋 Shutting down FastAPI server...")

def worker_exit(server, worker):
    server.log.info(f"Worker {worker.pid} exited")

# =======================
# SSL Configuration (uncomment if needed)
# =======================
# keyfile = "/path/to/keyfile.pem"
# certfile = "/path/to/certfile.pem"
# ssl_version = 2  # TLS 1.2
# ciphers = "HIGH:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA"