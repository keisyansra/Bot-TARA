import os

from sqlalchemy import create_engine
from dotenv import load_dotenv


load_dotenv()


def get_engine():
    return create_engine(os.environ["DATABASE_URL"])