import gevent.monkey
gevent.monkey.patch_all()

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path("/home/deploy/env-files/.env"), override=True)
load_dotenv(Path("/home/deploy/env-files/.env.prod"), override=True)

from app import create_app
app = create_app()
