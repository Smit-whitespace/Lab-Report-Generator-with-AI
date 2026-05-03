import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-local-dev-secret")
ALLOWED_IPS = [
    ip.strip()
    for ip in os.getenv("ALLOWED_IPS", "").split(",")
    if ip.strip()
]
