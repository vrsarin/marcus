import shutil
import os

dirs = [
    '__pycache__', 
    '.pytest_cache', 
    '.mypy_cache', 
    '.ruff_cache',
    '.venv', 
    'node_modules',     
    'build'
]

files = ['requirements.txt','.env']

for d in dirs:
    shutil.rmtree(d, ignore_errors=True)

for f in files:
    try:
        os.remove(f)
    except OSError:
        pass