import json
import re
from dataclasses import dataclass
from typing import Any

from langchain_community.chat_models import ChatTongyi
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .prompts import INTENT_RECOGNIZE_PROMPT

@dataclass(frozen=True)
class IntentResult:
    """
    意图识别结果：
    - intents: 意图列表, 每个元素为一个意图名称
    - slots: slot值字典, 键为slot名称, 值为slot值
    - confidence: 置信度分数, 取值范围 0~1, 越大表示越信该意图
    """
    intents: list[str]
    slots: dict[str, Any]
    confidence: float
