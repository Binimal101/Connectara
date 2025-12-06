"""
LangGraph skeleton that mirrors the simplified routing diagram.

Each rectangular shape in the diagram becomes a LangGraph node. Edges that contain
textual annotations mutate `AgentState` accordingly. All business logic hooks are
represented as empty functions so downstream teams can supply the real behavior.
"""

from __future__ import annotations

from typing import Annotated, Callable, List, Literal, TypedDict

import asyncio  
from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from src.langgraph.user_classes import Profile, LinkedInPiloterrAdapter
from src.api.api_handler import ChatAPIHandler
# ---------------------------------------------------------------------------
# State definition
# ---------------------------------------------------------------------------

api = ChatAPIHandler()
linkedinPiloterr = LinkedInPiloterrAdapter()
    
class AgentState(TypedDict, total=False):
    """Minimal state container shared across nodes."""
    user: Profile
    messages: Annotated[List[BaseMessage], add_messages]
    get_new_message: Callable  # Callable that blocks until a new message for the chat_id is available
    agent_phone_number: str
    chat_id: int
    has_registered_account: bool
    current_node: Literal["check_phone_number", "create_account", "listen_for_matches"]  # Used for persistence
    matches: List[dict]


# ---------------------------------------------------------------------------
# Placeholder behaviors
# ---------------------------------------------------------------------------

async def check_phone_number(state: AgentState) -> AgentState:
    """
    Entry node: determine whether the phone number exists and has a registered account.
    """

    return state

async def create_account(state: AgentState) -> AgentState:
    """Square node: collect user details and create an account."""
    print("Creating account...")
    await api.send_chat_message(state["chat_id"], "Let's get you registered! What is your linkedin profile URL (https://linkedin.com/in/USERNAME)?") # type: ignore
    
    # Get message and validate it's a properly formatted LinkedIn profile URL
    profile : Profile | None = await linkedinPiloterr.get_profile(message := state["get_new_message"]())  # type: ignore
    while (profile == None): # type: ignore
        await api.send_chat_message(state["chat_id"], "That doesn't look like a valid LinkedIn profile URL. Please provide a URL in the format: https://linkedin.com/in/USERNAME") # type: ignore
        profile = await linkedinPiloterr.get_profile(message := state["get_new_message"]().split("/")[-1])  # type: ignore
    
    # Store the validated LinkedIn URL
    state["user"] = profile # type: ignore = message 
    state["has_registered_account"] = True
    #TODO AnalyzeProfileUseCase.execute(profile) from Neo4JAdapter
    await api.send_chat_message(state["chat_id"], "Great! Your account has been created") # type: ignore
    return state

async def listen_for_matches(state: AgentState) -> AgentState:
    """Square node: user has an account, so we listen for match requests."""
    return state

async def choose_match(state: AgentState) -> AgentState:
    """Square node: user has an account, and has generated matches; time to choose"""

    return state

# ---------------------------------------------------------------------------
# Routing helpers
# ---------------------------------------------------------------------------


async def route_after_check(state: AgentState) -> Literal["create_account", "listen_for_matches"]:
    if state.get("has_registered_account"):
        return "listen_for_matches"
    return "create_account"


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------


async def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("check_phone_number", check_phone_number)
    graph.add_node("create_account", create_account)
    graph.add_node("listen_for_matches", listen_for_matches)

    graph.add_edge(START, "check_phone_number")
    graph.add_conditional_edges(
        "check_phone_number",
        route_after_check,
        {
            "create_account": "create_account",
            "listen_for_matches": "listen_for_matches",
        },
    )
    graph.add_edge("create_account", "listen_for_matches")
    graph.add_edge("listen_for_matches", END)

    return graph.compile()



async def begin_agentic_workflow(user_phone: str, agent_phone: str, chat_id: int, initial_message: str, get_new_message: Callable):
    """Create and run a new LangGraph workflow from the START node."""
    
    # Build the compiled graph
    app = await build_graph()
    
    #TODO create persistence layer to store state across restarts, initialize new workflow with prior state if exists
    #TODO when persistence layer is ready, change start node to last saved node instead of always START

    # Initialize state with required fields

    lookup_phonenumber = lambda uphoneNum: uphoneNum
    
    user: object | None = lookup_phonenumber(user_phone)

    if True or user is None: #TODO ignore short circuit post-test
        initial_state: AgentState = {
            "user": Profile(
                phone_number=user_phone
            ),
           "has_registered_account": False,
           "agent_phone_number": agent_phone,
           "chat_id": chat_id,
           "messages": [],
           "get_new_message": get_new_message,
        } 
    else:
        initial_state: AgentState = {
            "user": user.profile, # type: ignore
            "has_registered_account": True,
            "messages": [],
            "get_new_message": get_new_message,
            "agent_phone_number": agent_phone,
            "chat_id": chat_id,
            "message_history": initial_message + user.profile.raw_data.get("message_history", ""), # type: ignore
        }
    
    # Invoke the workflow
    print("Starting workflow...")
    result = app.invoke(initial_state)
    
    print("Workflow completed.")
    print(f"Final state: {result}")
    
    return result

# if __name__ == "__main__":
    # asyncio.run(begin_agentic_workflow()) 
