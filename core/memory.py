from time import sleep
from unittest import result

from dashscope.cli.input import messages_from_text
from langchain_classic.memory import summary
from langchain_core import messages
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from core import facts_manager
from core.chat_history_manager import ChatHistoryManager
from core.facts_manager import FactManager
from core.summary_manager import SummaryManager

# 会话Key前缀
SESSION_KEY = "session"


class Memory:
    """记忆管理整合：组合三个独立的管理器"""

    def __init__(self, chat_session_id: str) -> None:
        self.chat_session_id = chat_session_id
        self.session_key = f"{SESSION_KEY}:{chat_session_id}"

        # 初始化三个子管理器
        self.history = ChatHistoryManager(self.session_key)
        self.summary = SummaryManager(self.session_key)
        self.facts = FactManager(self.session_key)

    # ===========对话历史============
    def get_session_history(self) -> BaseChatMessageHistory:
        """获取历史记录对象"""
        return self.history.get_history()

    def get_messages(self) -> list[BaseMessage]:
        """获取当前会话的所有消息"""
        return self.history.get_messages()

    def get_recent_messages(self, recent_n: int) -> list[BaseMessage]:
        """获取最近n条消息"""
        return self.history.get_recent_messages(recent_n)

    def get_recent_messages_text(self, recent_n: int) -> str:
        """将最近信息转换成str类型的"""
        messages = self.get_recent_messages(recent_n)
        messages_text = ""
        for msg in messages:
            if isinstance(msg, HumanMessage):
                messages_text += f"human:{msg.content}"
            if isinstance(msg, AIMessage):
                messages_text += f"ai:{msg.content}"
        return messages_text

    # ============添加消息(触发摘要)==========
    def add_user_messages(self, message: str, llm=None) -> None:
        """添加用户消息"""
        self.history.add_user_message(message)
        # summary计数器+1
        self.summary.increment_unsummarized_count(1)
        # 判断是否需要触发摘要更新
        self._trim_and_summarized(llm)

    def add_ai_messages(self, message: str, llm=None) -> None:
        """添加ai消息"""
        self.history.add_ai_message(message)
        # summary计数器+1
        self.summary.increment_unsummarized_count(1)
        # 判断是否需要触发摘要更新
        self._trim_and_summarized(llm)

    # ================关键事实===================
    def get_key_facts(self) -> dict[str, str]:
        """获取当前对话的所有关键事实信息"""
        return self.facts.get_all_facts()

    def update_key_facts(self, facts: dict[str, str]) -> None:
        """更新关键事实"""
        self.facts.update_facts(facts)

    def clear_key_facts(self) -> None:
        """清空当前会话的所有关键事实"""
        self.facts.clear_facts()

    # ================摘要相关===================
    def _trim_and_summarized(self, llm=None) -> None:
        """摘要触发与生成"""
        if not self.summary.should_trigger_summary():
            return

        history = self.history.get_history()
        if not history:
            return

        messages = self.get_messages()
        unsummarized_count = self.summary.get_unsummarized_count()
        total_count = len(messages)
        # 摘要消息数量等于总消息数减去未摘要消息数
        summarized_count = total_count - unsummarized_count

        # 获取未摘要的消息
        new_messages = messages[summarized_count:]
        if new_messages:
            # 获取旧的摘要
            old_summary = self.summary.get_summary()
            # 生成新摘要
            new_summary = self.summary.generate_incremental_summary(
                old_summary,
                new_messages,
                llm
            )
            # 更新摘要
            self.summary.update_summary(new_summary)
            # 重置未进行摘要的消息数量
            self.summary.reset_unsummarized_count()
            print("摘要生成！！！")

    # ==================准备LLM上下文(摘要，关键事实，最近消息)=================
    def prepare_memory_for_llm(self) -> list[BaseMessage]:
        """准备LLM上下文信息"""
        result = []
        # 1.添加关键事实
        facts = self.facts.get_all_facts()
        if facts:
            facts_text = " | ".join([f"{k}:{v}" for k, v in facts.items()])
            result.append(AIMessage(content=f"[关键事实] {facts_text}"))
        # 2.添加摘要
        summary = self.summary.get_summary()
        if summary:
            result.append(AIMessage(content=f"[摘要] {summary}"))
        # 3.添加最近未摘要的信息
        unsummarized_count = self.summary.get_unsummarized_count()
        if unsummarized_count > 0:
            messages = self.history.get_messages()
            recent_messages = messages[-unsummarized_count:]
            result.extend(recent_messages)

        return result
