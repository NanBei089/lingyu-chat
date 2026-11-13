from langchain_classic.retrievers import elastic_search_bm25
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from core.prompts import SUMMARY_GENERATION_PROMPT

# 会话摘要 (key是chat_session_id，value是摘要)
_summary_store: dict[str, str] = {}
# 未摘要消息数量(key是chat_session_id，value未摘要消息数量)
_unsummarized_count: dict[str, int] = {}

# 默认配置
SUMMARY_BATCH_SIZE = 12

str_out_parser = StrOutputParser()


class SummaryManager:
    """负责会话摘要的生成与存储"""

    def __init__(self, chat_session_id: str):
        self.chat_session_id = chat_session_id
        # 初始化摘要
        if chat_session_id not in _summary_store:
            _summary_store[chat_session_id] = ""
        if chat_session_id not in _unsummarized_count:
            _unsummarized_count[chat_session_id] = 0

    def get_summary(self):
        """获取当前会话的摘要"""
        return _summary_store.get(self.chat_session_id, "")

    def update_summary(self, new_summary: str) -> None:
        """更新当前会话的摘要"""
        _summary_store[self.chat_session_id] = new_summary

    def get_unsummarized_count(self) -> int:
        """获取未摘要的消息数量"""
        return _unsummarized_count.get(self.chat_session_id, 0)

    def increment_unsummarized_count(self, delta: int = 1) -> None:
        """增加未摘要消息计数"""
        current = _unsummarized_count.get(self.chat_session_id, 0)
        _unsummarized_count[self.chat_session_id] = current + delta

    def reset_unsummarized_count(self) -> None:
        """重置未摘要消息计数"""
        _unsummarized_count[self.chat_session_id] = 0

    def should_trigger_summary(self) -> bool:
        """检查是否达到摘要生成阈值"""
        return self.get_unsummarized_count() >= SUMMARY_BATCH_SIZE

    def generate_incremental_summary(
            self,
            old_summary: str,
            new_messages: list[BaseMessage],
            llm: ChatTongyi | None = None
    ) -> str:
        """生成增量摘要"""

        # 提取新的消息文本
        messages_text = ""
        for msg in new_messages:
            if isinstance(msg, HumanMessage):
                messages_text += f"human:{msg.content}\n"
            elif isinstance(msg, AIMessage):
                messages_text += f"ai:{msg.content}\n"

        # 如果没有提供llm，就使用简易方式生成摘要
        if not llm:
            return self._simple_summary(old_summary, messages_text)

        # 使用LLM，生成摘要
        try:
            summary_prompt = ChatPromptTemplate.from_messages([
                ("system", SUMMARY_GENERATION_PROMPT),
                ("human", f"旧的摘要：{old_summary}\n新消息：{messages_text}")
            ])
            chain = summary_prompt | llm | str_out_parser
            result = chain.invoke(input={})
            return result.strip()
        except:
            return self._simple_summary(old_summary, messages_text)

    def _simple_summary(self, old_summary: str, messages_text: str):
        if old_summary and old_summary != "[摘要] 无":
            old_part = old_summary[:150] if len(old_summary) >= 150 else old_summary
            new_part = messages_text[:150] if len(messages_text) >= 150 else messages_text
            return f"[摘要] {old_part}...{new_part}"
        else:
            new_part = messages_text[:150] if len(messages_text) >= 150 else messages_text
            return f"[摘要] {new_part}"
