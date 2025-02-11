import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MESSAGE_LIMIT = os.getenv("MESSAGE_LIMIT")