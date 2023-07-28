import os

from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

ACCESS_TOKEN_EXPIRE = 1
ACCESS_TOKEN_SECRET = "THISISASECRETKEY"
DATABASE_URL = "sqlite:///./test.db"
EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
REFRESH_TOKEN_EXPIRE = 7
REFRESH_TOKEN_SECRET = "THISISAREFRESHSECRETKEY"
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SMTP_PORT = os.getenv('SMTP_PORT')
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
TEST_DATABASE_URL = "sqlite:///./testing.db"
