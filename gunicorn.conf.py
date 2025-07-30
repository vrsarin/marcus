bind = "0.0.0.0:8000"
# Thumb rule vCPU x 2 -1 e.g. 4 CPU container is 4x2-1 = 7 workers
workers = 4 
worker_class = "uvicorn.workers.UvicornWorker"
loglevel = "info"
accesslog = "-"
errorlog = "-"
# Set True for development, False for production
reload = False
timeout = 60
keepalive = 2
