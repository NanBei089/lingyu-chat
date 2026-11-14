import json
import math
import re
from dataclasses import dataclass
from operator import ifloordiv
from typing import Any

from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
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


def _str_to_json(text: str) -> dict[str, Any]:
    # 定义默认返回值
    default = {
        "intents": ["general"],
        "slots": {},
        "confidence": 0.0
    }
    # 判断字符串是否为空
    if not text or not text.strip():
        return default

    # 去除字符串首尾的空白字符
    text = text.strip()

    # 创建 JSON 解码器
    decoder = json.JSONDecoder()

    # 遍历字符串中的每一个字符及其索引
    for index, char in enumerate(text):
        # 只在遇到左大括号时，才尝试解析 JSON
        if char != "{":
            continue
        try:
            # 从当前左大括号的位置开始解析 JSON
            # raw_decode() 返回两个值：
            # result：解析得到的 Python 对象
            # end：JSON 字符串结束的位置
            result, end = decoder.raw_decode(text[index:])

            # 判断解析结果是否为字典
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            # 当前左大括号解析失败，继续寻找下一个左大括号
            continue
    # 遍历结束仍然没有找到有效 JSON，返回默认值
    return default


class IntentRecognizer:
    """
      意图识别器：通过大语言模型识别用户输入的意图，输出IntentResult对象
    """
    def __init__(self,model:str):
        #chain=prompt|llm|parser
        self._prompt=ChatPromptTemplate.from_messages([
            ("system",INTENT_RECOGNIZE_PROMPT),
            ("ai","{chat_history}"),
            ("human","{human_message}")
        ])

        self._llm=ChatTongyi(model=model)
        self._chain=self._prompt|self._llm|StrOutputParser()

    def recognize(self,user_input:str,chat_history:str|None=None):
        """
        识别用户输入的意图
        :param chat_history:上下文内容
        :param user_input:用户输入的文本
        :return:意图识别结果
        """
        # 1.调用llm去识别用户的意图，输出str格式的json字符串
        chat_history=chat_history if chat_history else ""
        result = self._chain.invoke(input={"chat_history": chat_history,
                                            "human_message": user_input})
        # 2.解析大模型输出
        # 2.0 将str转换成json（dict）
        data= _str_to_json(result)
        # 2.1. 解析intents意图
        intents=data.get("intents")
        if not isinstance(intents, list):
            intent = data.get("intent")
            intents = [intent] if isinstance(intent, str) else []

        # 2.2. 解析slots插槽
        slots=data.get("slots") if isinstance(data.get("slots"), dict) else {}
        # 2.3. 解析confidence置信度
        try:
            confidence = float(data.get("confidence", 0.0))
            if not math.isfinite(confidence):
                confidence = 0.0
        except (TypeError, ValueError):
            confidence = 0.0

        confidence = max(0.0, min(1.0, confidence))

        # 3.返回结果
        return IntentResult(intents=intents, slots=slots, confidence=confidence)































