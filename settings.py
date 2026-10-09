import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

TRANSPORTAPI_APP_ID = os.environ.get("TRANSPORTAPI_APP_ID")
TRANSPORTAPI_APP_KEY = os.environ.get("TRANSPORTAPI_APP_KEY")