from abc import ABC, abstractmethod
from typing import List

from pydantic import BaseModel, Field

from eidolon_sdk.cpu.agent_bus import BusEvent, CallContext
from eidolon_sdk.cpu.processing_unit import ProcessingUnit
from eidolon_sdk.cpu.bus_messages import READ_PORT, WRITE_PORT
from eidolon_sdk.cpu.llm_message import AssistantMessage, LLMMessage, ToolCallMessage
from eidolon_sdk.reference_model import Specable


class CompletionUsage(BaseModel):
    completion_tokens: int
    """Number of tokens in the generated completion."""

    prompt_tokens: int
    """Number of tokens in the prompt."""

    total_tokens: int
    """Total number of tokens used in the request (prompt + completion)."""


class LLMUnitConfig(BaseModel):
    llm_read: READ_PORT = Field("Conversation", description="A port that, when bound to an event, will read the conversation, or message, from the bus and execute it.")
    llm_write: WRITE_PORT = Field("Response", description="A port that, when bound to an event, will write the response from the LLM to the bus.")
    lt_write: WRITE_PORT = Field(default=None, description="A port that, when bound to an event, will write the tool calls from the LLM to the bus.")


class LLMUnit(ProcessingUnit, Specable[LLMUnitConfig], ABC):
    def __init__(self, spec: LLMUnitConfig = None):
        self.spec = spec

    async def bus_read(self, event: BusEvent):
        if event.event_type == self.spec.llm_read:
            await self.process_llm_event(event.call_context, event.messages)

    @abstractmethod
    async def process_llm_event(self, call_context: CallContext, messages: List[LLMMessage]):
        pass

    def write_llm_response(self, call_context: CallContext, message: AssistantMessage):
        self.request_write(BusEvent(
            call_context,
            self.spec.llm_write,
            [message]
        ))

    def write_llm_tool_calls(self, call_context: CallContext, tool_calls: List[ToolCallMessage]):
        self.request_write(BusEvent(
            call_context,
            self.spec.lt_write,
            tool_calls))
