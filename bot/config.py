import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Create .env from .env.example")


def _parse_allowed_chats(raw: str | None) -> list[int]:
    if not raw:
        return []
    result = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        result.append(int(item))
    return result


ALLOWED_CHATS = _parse_allowed_chats(os.getenv("ALLOWED_CHATS"))
