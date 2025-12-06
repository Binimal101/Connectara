from typing import Any, Dict, Generator, Set, Tuple
import asyncio
import threading

from src.api.api_handler import *
from src.api.Image import Image

from src.consumer import get_next_message
from src.langgraph.langgraph import begin_agentic_workflow

chat_id_set: Set[int] = set() #ID

# Background event loop for async tasks
_loop = None
_loop_thread = None

def _start_background_loop():
    """Start a background event loop in a separate thread."""
    global _loop
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _loop.run_forever()

def _ensure_event_loop():
    """Ensure background event loop is running."""
    global _loop, _loop_thread
    if _loop is None or not _loop.is_running():
        _loop_thread = threading.Thread(target=_start_background_loop, daemon=True)
        _loop_thread.start()
        # Wait for loop to be ready
        import time
        while _loop is None:
            time.sleep(0.01)

def get_chat_messages(requested_chat_id: int) -> Generator[Dict[str, Any], None, None]:
    """Yield only messages matching the requested chat id."""
    target_chat_id = str(requested_chat_id)

    print(f"Starting message demux for chat id {requested_chat_id}...")
    for message in get_next_message():
        if not isinstance(message, dict):
            continue

        data = message.get("data")
        if not isinstance(data, dict):
            continue

        chat_id = data.get("chat_id")
        if chat_id == requested_chat_id or str(chat_id) == target_chat_id:
            yield message #returned to langgraph process
        elif chat_id and chat_id not in chat_id_set:
            chat_id_set.add(chat_id)
            # Run the workflow in the background without blocking
            chat_handles = data.get("chat_handles")
            if chat_handles and len(chat_handles) == 2:
                h1, h2 = chat_handles[0], chat_handles[1]
                if h1.get("display_name") == "You":
                    agent_phone = h1.get("phone_number")
                    user_phone = h2.get("phone_number")
                else:
                    agent_phone = h2.get("phone_number")
                    user_phone = h1.get("phone_number")
                
                print("spawning workflow for chat id", chat_id)
                # Schedule the coroutine on the background event loop
                _ensure_event_loop()
                asyncio.run_coroutine_threadsafe(
                    begin_agentic_workflow(user_phone, agent_phone, chat_id, data.get("text", ""), get_chat_messages),
                    _loop # type: ignore
                )



if __name__ == "__main__":
    # Consume the generator to keep the script running and processing messages
    for _ in get_chat_messages(-1):  # assume id is never negative, this will never bear fruit
        pass  # Messages are handled internally by spawning workflows
