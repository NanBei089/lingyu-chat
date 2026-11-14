import logging
import os
import time
from operator import ifloordiv
from urllib import response

from langchain_community.chat_models import ChatTongyi
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config import *
from core.intent_recognizer import IntentRecognizer
from core.memory import Memory
from core.protocol import *

logger = logging.getLogger(__name__)

# 置信度阈值，低于这个值判定置信度过低
CONFIDENCE_THRESHOLD = 0.3

# 获取最近消息的条数
RECENT_MESSAGES = 3 * 2


def _handle_low_confidence(
        intent_result,
        user_input: str
) -> str :
    return "抱歉，我没太理解您的需求。请问您是想：\n" \
           "1️⃣ 查询物流进度\n" \
           "2️⃣ 修改收货地址\n" \
           "3️⃣ 申请退货退款\n" \
           "4️⃣ 投诉建议\n" \
           "请回复数字或具体需求。"


def _system_prompt_by_intent(intent: str) -> str:
    mapping = {
        "track_shipping": "你是电商物流查询客服。先要订单号/运单号；如果缺失就追问。",
        "change_address": "你是电商改地址客服。先确认是否已发货；需要订单号+新地址。",
        "refund": "你是电商退货退款客服。先给3步结论，再给注意事项，最后引导用户提供订单号。",
        "complaint": "你是电商投诉处理客服。先安抚，再收集订单号与问题细节，给出处理时效。",
        "general": "你是一个友好、简洁的聊天助手。",
    }
    return mapping.get(intent.strip(), mapping["general"])


class ChatService:
    def __init__(self, api_key: str | None = None) -> None:
        # 初始化日志记录器
        if not logging.root.handlers:
            logging.basicConfig(level=logging.INFO)

        # 初始化llm
        if api_key:
            os.environ['DASHSCOPE_API_KEY'] = api_key
        if not os.environ.get('DASHSCOPE_API_KEY'):
            raise RuntimeError('DASHSCOPE_API_KEY not set')

        self._intent_recognizer = IntentRecognizer(INTENT_RECONIZE_MODEL)
        self._llm = ChatTongyi(model=TONGYI_MODEL)
        self._memory_cache:dict[str,Memory]={}

    def _get_memory(self,chat_session_id:str)->Memory:
        """根据chat_session_id获取memory"""
        if chat_session_id not in self._memory_cache:
            self._memory_cache[chat_session_id]=Memory(chat_session_id)
        return self._memory_cache[chat_session_id]

    def handle(self,request:ChatRequest)->ChatResponse:
        """处理消息请求"""
        #请求开始时间
        start_time=time.time()
        #获取memory
        memory=self._get_memory(request.chat_session_id)

        try:
            #1.意图识别
            intent_result=self._intent_recognizer.recognize(
                request.user_input,
                memory.get_recent_messages_text(RECENT_MESSAGES)
            )
            #2.低置信度处理
            if intent_result.confidence<=CONFIDENCE_THRESHOLD:
                low_conf=_handle_low_confidence(intent_result,request.user_input)
                return ChatResponse(
                    user_id=request.user_id,
                    chat_session_id=request.chat_session_id,
                    trace_id=request.trace_id,
                    response=low_conf
                )
            #3.确定主要意图，路由到对应的链路（单意图处理）
            intents=intent_result.intents
            primary_intent=intents[0] if intents else "general"
            #4.构建prompt
            prompt=ChatPromptTemplate.from_messages([
                ("system",_system_prompt_by_intent(primary_intent)),
                MessagesPlaceholder("chat_history"),
                ("human","用户输入：{user_input}")
            ])

            #5.记忆管理
            memory_messages = memory.prepare_memory_for_llm()
            #6.llm调用
            chain = prompt | self._llm | StrOutputParser()
            answer=chain.invoke(input={"chat_history":memory_messages,"user_input":request.user_input})
            #7.写回历史消息
            memory.add_user_messages(message=request.user_input,llm=self._llm)
            memory.add_ai_messages(message=answer,llm=self._llm)
            #8.更新事实
            memory.update_key_facts(intent_result.slots)
            #9.日志
            self._log(
                req=request,
                intents=intents,
                confidence=intent_result.confidence,
                action="normal",
                latency_ms=int((time.time() - start_time) * 1000)
            )

            return ChatResponse(
                user_id=request.user_id,
                chat_session_id=request.chat_session_id,
                trace_id=request.trace_id,
                response=answer
            )

        except Exception as e:
            self._log(
                req=request,
                intents=["error"],
                confidence=0.0,
                action="error",
                latency_ms=int((time.time() - start_time) * 1000),
                error=str(e),
            )
            raise e

    def _log(self,
              *,
              req: ChatRequest,
              intents: list[str],
              confidence: float,
              action: str,
              latency_ms: int,
              error: str | None = None):
        payload = {
            "trace_id": req.trace_id,
            "user_id": req.user_id,
            "session_id": req.chat_session_id,
            "intents": intents,
            "confidence": confidence,
            "action": action,
            "latency_ms": latency_ms
        }
        # 如果有错误信息，记录为错误日志error，否则记录为普通日志info
        if error:
            payload["error"] = error
            logger.error(payload)
        else:
            logger.info(payload)




























