from collections.abc import AsyncIterator
from typing import Callable
from agents import Agent, Runner, TResponseInputItem, function_tool, FileSearchTool
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from agents.voice import VoiceWorkflowBase, VoiceWorkflowHelper
import asyncio
from dataclasses import dataclass
from openai import OpenAI
from agent_component import rag

client = OpenAI()
rag = rag.RAGSystem(vector_store_name="Restaurant Details")
vector_store_id = rag.get_vector_store_id()

end_call_agent = Agent(
    name = "end call agent",
    instructions = (
        "You are a courteous and professional assistant responsible for ending the conversation. "
    ))

@function_tool
def human_in_the_loop():
    return 0

@function_tool
def send_reservation_guidance(phone_number: str, booking_link: str) -> str:
    return 0

reservation_guidance = Agent(
    name="Reservation",
    handoff_description="reservation guidance agent",
    instructions=prompt_with_handoff_instructions(
        "Make reservation",
    ),
    model="gpt-4o-mini",
    tools = [send_reservation_guidance, end_call_agent.as_tool(
    tool_name = "end_call",
    tool_description = (
        "End the call"
    ))])

query_answering_agent = Agent(
    name="Query",
    handoff_description="query answering agent.",
    instructions=prompt_with_handoff_instructions(
        "Call the tool every time and answer the question with the help of the retrieved data",
    ),
    model="gpt-4o-mini",
    tools=[ FileSearchTool(
            max_num_results=1,
            vector_store_ids=[vector_store_id],
        ),end_call_agent.as_tool(
     tool_name = "end_call",
    tool_description = (
        "End the call"
    ))])

agent = Agent(
    name="Intent Detector",
    instructions=prompt_with_handoff_instructions(
        """
        You are part of a multi-agent system called the Agents SDK, designed to make agent coordination and execution easy. Agents uses two primary abstraction: **Agents** and **Handoffs**. An agent encompasses instructions and tools and can hand off a conversation to another agent when appropriate. Handoffs are achieved by calling a handoff function, generally named `transfer_to_<agent_name>`. Transfers between agents are handled seamlessly in the background; do not mention or draw attention to these transfers in your conversation with the user.
        """,
    ),
    model="gpt-4o-mini",
    handoffs=[query_answering_agent, reservation_guidance],
    tools=[end_call_agent.as_tool(
    tool_name = "end_call",
    tool_description = (
        "End the call"
    ))])


class MyWorkflow(VoiceWorkflowBase):
    def __init__(self, secret_word: str, on_start: Callable[[str], None]):
        self._input_history: list[TResponseInputItem] = []
        self._current_agent = agent
        self._secret_word = secret_word.lower()
        self._on_start = on_start

    async def run(self, transcription: str) -> AsyncIterator[str]:
        self._on_start(transcription)

        self._input_history.append({
            "role": "user",
            "content": transcription,
        })

        # Run the agent with current input
        result = Runner.run_streamed(self._current_agent, self._input_history)

        async for chunk in VoiceWorkflowHelper.stream_text_from(result):
            yield chunk

        # Compare agent before and after
        previous_agent = self._current_agent
        self._current_agent = result.last_agent
        self._input_history = result.to_input_list()

        # If agent changed, notify
        if self._current_agent.name != previous_agent.name:
            indicator = f"[Agent Change] 🧠 Switched from '{previous_agent.name}' to '{self._current_agent.name}'"
            print(indicator)
