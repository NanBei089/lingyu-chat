# 全局存储：关键事实(key是chat_session_id, value是slots插槽  order_id 和 new_address)
_facts_store: dict[str, dict[str, str]] = {}


class FactManager:
    def __init__(self, chat_session_id: str):
        self.chat_session_id = chat_session_id
        # 初始化关键事实
        if chat_session_id not in _facts_store:
            _facts_store[chat_session_id] = {}

    def get_all_facts(self) -> dict[str, str]:
        """获取所有的事实信息"""
        return _facts_store.get(self.chat_session_id, {}).copy()

    def get_fact(self, key: str) -> str:
        """获取单个事实"""
        return self.get_all_facts().get(key, "")

    def update_facts(self, facts: dict[str, str]) -> None:
        """更新关键事实"""
        if self.chat_session_id not in _facts_store:
            _facts_store[self.chat_session_id] = {}
        _facts_store[self.chat_session_id].update({
            k: v for k, v in facts.items() if v
        })

    def set_fact(self, key: str, value: str) -> None:
        """设置单个事实"""
        if self.chat_session_id not in _facts_store:
            _facts_store[self.chat_session_id] = {}
        if value:
            _facts_store[self.chat_session_id][key] = value

    def clear_facts(self) -> None:
        """清空当前会话的所有关键事实"""
        if self.chat_session_id in _facts_store:
            _facts_store[self.chat_session_id] = {}

    def delete_session(self) -> None:
        """删除当前会话的事实记录"""
        if self.chat_session_id in _facts_store:
            del _facts_store[self.chat_session_id]
