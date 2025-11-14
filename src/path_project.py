from pathlib import Path

def project_dir():
    return Path(__file__).resolve().parent.parent