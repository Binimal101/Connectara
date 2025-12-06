import token
import src

import aiohttp, os
import asyncio
from typing import Any, Dict

from dotenv import load_dotenv

from src.api.Image import Image

load_dotenv(src.env_path)

assert src.env_path is not None, "Environment file not found"

class ChatAPIHandler:
    def __init__(self, api_token: str | None = os.getenv("API_TOKEN")):
        self.api_token = api_token
    
    async def fetch_chats(self, page: int = 1, per_page: int = 25) -> Dict[str, Any]:
        url = f"{src.base_url}/chats"
        
        headers = {
            "accept": "application/json",
        }

        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        params = {
            "page": page,
            "per_page": per_page,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                return await response.json()

    async def fetch_chat_messages(self, chat_id: int):
        url = f"{src.base_url}/chats/{chat_id}/chat_messages"
        
        headers = {
            "accept": "application/json",
        }

        if  token := self.api_token:
            headers["Authorization"] = f"Bearer {token}"

        params = {
            "chat_id": chat_id,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                return await response.json()

    async def send_chat_message(self, chat_id: int, message: str, image: Image | None = None):
        url = f"{src.base_url}/chats/{chat_id}/chat_messages"
        
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }

        if  token := self.api_token:
            headers["Authorization"] = f"Bearer {token}"

        params = {
            "chat_id": chat_id,
        }

        message_body = {"text": message}
        if image is not None:
            message_body["attachments"] = [{ # type: ignore
                "data_base64": image.b64,
                "filename": image.filename,
                "mime_type": image.mime_type,
            }]
        
        body = {"message": message_body}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, params=params, json=body) as response:
                response.raise_for_status()
                return await response.json()

    async def mark_as_read(self, chat_id: int):
        url = f"{src.base_url}/chats/{chat_id}/mark_as_read"
        
        headers = {
            "accept": "application/json",
        }

        if token := self.api_token:
            headers["Authorization"] = f"Bearer {token}"

        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers) as response:
                response.raise_for_status()
                if response.status == 204:
                    return None
                return await response.json()
    
    async def start_typing(self, chat_id: int):
        url = f"{src.base_url}/chats/{chat_id}/start_typing"
        
        headers = {
            "accept": "application/json",
        }

        if token := self.api_token:
            headers["Authorization"] = f"Bearer {token}"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                response.raise_for_status()
                return await response.json()
    
    async def stop_typing(self, chat_id: int):
        url = f"{src.base_url}/chats/{chat_id}/stop_typing"
        
        headers = {
            "accept": "application/json",
        }

        if token := self.api_token:
            headers["Authorization"] = f"Bearer {token}"

        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=headers) as response:
                response.raise_for_status()
                return await response.json()

async def main():
    handler = ChatAPIHandler()
    
    # Test sending a message to chat_id 1702292
    response = await handler.send_chat_message(
        chat_id=1702107,
        message="Test message from API handler",
        image=Image("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46L733zokuj+CQPZ7z/n9D3R/aHTX4zur3jxpOj+rnu3R/cv2bghur/2gOzf56ah06L747b/U3TfBQBQSgAASgkAQCkBACglAAClBACglAAAlBIAgFICAFBKAABKCQBAKQEAKCUAAKUEAKCUAACUEgCAUgIAUEoAAEoJAEApAQAoJQAApQQAoJQAAJQSAIBSAgBQSgAASgkAQCkBACglAAClBACglAAAlBr40cUnRh/48Nat0f2/PnhbdH/WMWOi+0+fMj26f/nt74nuz71yanT/h+svj+6fvOS3o/uHzPiN6P6StTOj++O3fC+6v/bMj0T3Vy7M/v955G+fjO6f+9iL0X0XAEApAQAoJQAApQQAoJQAAJQSAIBSAgBQSgAASgkAQCkBACglAAClBACglAAAlBIAgFICAFBKAABKCQBAKQEAKCUAAKUEAKCUAACUEgCAUgIAUEoAAEoJAEApAQAoJQAApQQAoJQAAJQSAIBSAgBQauBTJ2yOPjBu3e9E90867oXo/nMnfS26/+TUS6P7Z78+HN2/cMMT0f3tOw+K7v902QnR/a9c9Nno/vw9K6P7D1z9h9H92fOz33/hpCuj+08P/zy6v+vam6P7LgCAUgIAUEoAAEoJAEApAQAoJQAApQQAoJQAAJQSAIBSAgBQSgAASgkAQCkBACglAAClBACglAAAlBIAgFICAFBKAABKCQBAKQEAKCUAAKUEAKCUAACUEgCAUgIAUEoAAEoJAEApAQAoJQAApQQAoNTgwb80FH3g/Sfvi+7/9Nil0f2Pnbopuv+vD98Z3V+87fLo/oThW6L731/0F9H9NUPbo/tHvn54dH/5Zx6O7r/0L5Oi+3NmfDu6f+j9r2b3D9wW3V+34uXovgsAoJQAAJQSAIBSAgBQSgAASgkAQCkBACglAAClBACglAAAlBIAgFICAFBKAABKCQBAKQEAKCUAAKUEAKCUAACUEgCAUgIAUEoAAEoJAEApAQAoJQAApQQAoJQAAJQSAIBSAgBQSgAASgkAQCkBACg1MH7lmOgDb7/90ej+Va88GN1f+4Up0f1/fO23ovvzfvBSdP8bV2+J7t/2vYei+++/4X+j+xPvOCO6f97IedH96zYtjO4/dstp0f0pc5dH97/45s7o/qjDD4zuuwAASgkAQCkBACglAAClBACglAAAlBIAgFICAFBKAABKCQBAKQEAKCUAAKUEAKCUAACUEgCAUgIAUEoAAEoJAEApAQAoJQAApQQAoJQAAJQSAIBSAgBQSgAASgkAQCkBACglAAClBACglAAAlBIAgFKD13zo+9EHtp71dnT/v+5fH93/zoOjovuzfuXS6P6xP/pAdP+qQ74Z3f+Tg/ZG919bfV10/9dXHBPdH/X5cdH9M06dEN1/YP7S6P4L95wW3R81Yk50/9GfzIjuuwAASgkAQCkBACglAAClBACglAAAlBIAgFICAFBKAABKCQBAKQEAKCUAAKUEAKCUAACUEgCAUgIAUEoAAEoJAEApAQAoJQAApQQAoJQAAJQSAIBSAgBQSgAASgkAQCkBACglAAClBACglAAAlBIAgFIDu5ePiT6waMYp0f35142K7t+84GvR/Uk3Xh/dH//7w9H92Useje4vf+/46P7uuw6I7v/b5K9H9x+/67Do/tDa06L74++4LLp/w/Sh6P7Y0cuj+ye+86XovgsAoJQAAJQSAIBSAgBQSgAASgkAQCkBACglAAClBACglAAAlBIAgFICAFBKAABKCQBAKQEAKCUAAKUEAKCUAACUEgCAUgIAUEoAAEoJAEApAQAoJQAApQQAoJQAAJQSAIBSAgBQSgAASgkAQCkBACg1eMUVs6IPvPvZp6P7q+77WXT/gqsuie5PvunL0f1bT47Ov+u8/YdE9786c3l0/+aJfxPd//qU86P7+6Y8H92fNPmy6P68uz8T3b/pL8+L7k+eMC+6v+25x6P7LgCAUgIAUEoAAEoJAEApAQAoJQAApQQAoJQAAJQSAIBSAgBQSgAASgkAQCkBACglAAClBACglAAAlBIAgFICAFBKAABKCQBAKQEAKCUAAKUEAKCUAACUEgCAUgIAUEoAAEoJAEApAQAoJQAApQQAoNT/BwAA//+0p4WlUmRolQAAAABJRU5ErkJggg==",
              "random.png", "image/png")
    )
    print("Message sent successfully!")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())