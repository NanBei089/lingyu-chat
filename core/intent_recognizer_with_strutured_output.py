import logging

from langchain_community.chat_models import ChatTongyi
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate
from .prompts import INTENT_RECOGNIZE_WITH_STRUCTURED_OUTPUT_PROMPT
from typing import Literal
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


IntentName = Literal["track_shipping", "change_address", "refund", "complaint", "general"]

class Slots(BaseModel):
    order_id: str | None = Field(default=None, description="订单号；用户未提及则为 null")
    new_address: str | None = Field(default=None, description="新的收货地址；用户未提及则为 null")

class IntentResult(BaseModel):
    """意图识别结果：由大模型识别用户输入得到的结构化数据。"""
    intents: list[IntentName] = Field(description="命中的意图，可多个；无法判断时为 general")
    slots: Slots = Field(description="从用户输入抽取的槽位；未提及的槽位置为 null")
    confidence: float = Field(ge=0, le=1, description="意图判断置信度，0~1")


class StructuredIntentRecognizer:
    """
    意图识别器：通过大语言模型识别用户输入的意图，输出IntentResult对象
    """

    def __init__(self, llm: ChatTongyi):
        # chain = prompt | model
        self._prompt = ChatPromptTemplate.from_messages([
            ("system", INTENT_RECOGNIZE_WITH_STRUCTURED_OUTPUT_PROMPT),
            ("ai", "上下文内容：{chat_history}"),
            ("human", "用户输入：{user_input}")
        ])
        self._llm = llm.with_structured_output(IntentResult)
        self._chain = self._prompt | self._llm

    def recognize(self, user_input: str, chat_history: str | None = None) -> IntentResult:
        chat_history = chat_history if chat_history else ""
        try:
            result = self._chain.invoke(
                input={"chat_history": chat_history, "user_input": user_input}
            )
        except (ValidationError, OutputParserException) as e:
            logger.warning(
                "结构化输出失败: user_input=%r, error=%s", user_input, e
            )
            return IntentResult(intents=["general"], slots=Slots(), confidence=0.0)
        if result is None:
            logger.warning("模型没有返回 tool call: user_input=%r", user_input)
            return IntentResult(intents=["general"], slots=Slots(), confidence=0.0)

        return result
