import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self.API_ID: int = int(os.environ.get("API_ID", 123456))  # Default ID
        self.API_HASH: str = os.environ.get("API_HASH", "your_api_hash")
        self.BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "your_bot_token")
        self.OWNER_ID: int = int(os.environ.get("OWNER_ID", 987654321))
        self.MONGODB_URL: str = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
        self.DATABASE_CHAT_ID: int = int(os.environ.get("DATABASE_CHAT_ID", -1001234567890))
        self.OWNER_USERNAME: str = os.environ.get("OWNER_USERNAME", "admin")

        # Optional setting
        self.SPONSOR_TEXT: str = os.environ.get("SPONSOR_TEXT", "🎉 Bot ini disponsori oleh Anime Bahasa Indonesia!")
        self.SPONSOR_PHOTO: str = os.environ.get("SPONSOR_PHOTO", "https://ibb.co/KjFbm1Bk")

        self._validate()

    def _validate(self):
        required = {
            "API_ID": self.API_ID,
            "API_HASH": self.API_HASH,
            "BOT_TOKEN": self.BOT_TOKEN,
            "OWNER_ID": self.OWNER_ID,
            "MONGODB_URL": self.MONGODB_URL,
            "DATABASE_CHAT_ID": self.DATABASE_CHAT_ID
        }
        for key, value in required.items():
            if not value:
                raise ValueError(f"{key}: Missed")

config: Config = Config()
