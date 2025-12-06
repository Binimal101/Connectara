import src

import aiohttp, os
import asyncio
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv(src.env_path)

assert src.env_path is not None, "Environment file not found"

async def fetch_chats(page: int = 1, per_page: int = 25, token: str | None = os.getenv("API_TOKEN")) -> Dict[str, Any]:
    url = f"{src.base_url}/chats"
    
    headers = {
        "accept": "application/json",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    params = {
        "page": page,
        "per_page": per_page,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            response.raise_for_status()
            return await response.json()

async def main():
    data = await fetch_chats(
        page=1,
        per_page=25,
        token=os.getenv("API_TOKEN"),
    )
    print(data)

if __name__ == "__main__":
    asyncio.run(main())