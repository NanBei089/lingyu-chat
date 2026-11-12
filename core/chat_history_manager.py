# 全局存储：对话历史 (key是chat_session_id，value是BaseChatMessageHistory的实现类)
from langchain_core.chat_history import BaseChatMessageHistory

_session_store: dict[str, BaseChatMessageHistory] = {}