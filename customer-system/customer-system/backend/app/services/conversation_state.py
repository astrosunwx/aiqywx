"""对话状态管理服务 - 支持多轮对话"""
from typing import Dict, Optional
from datetime import datetime, timedelta
import json


class ConversationState:
    """对话状态存储"""
    
    def __init__(self):
        # 使用内存存储（生产环境应使用Redis）
        self._states: Dict[str, dict] = {}
    
    def get_state(self, user_id: str) -> Optional[dict]:
        """获取用户对话状态"""
        state = self._states.get(user_id)
        if state and state.get('expires_at') > datetime.now():
            return state
        return None
    
    def set_state(self, user_id: str, intent: str, data: dict, ttl_minutes: int = 30):
        """设置用户对话状态"""
        self._states[user_id] = {
            'intent': intent,
            'data': data,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=ttl_minutes)
        }
    
    def clear_state(self, user_id: str):
        """清除用户对话状态"""
        if user_id in self._states:
            del self._states[user_id]
    
    def update_state(self, user_id: str, key: str, value):
        """更新状态中的某个字段"""
        if user_id in self._states:
            self._states[user_id]['data'][key] = value


# 全局状态管理器
conversation_state = ConversationState()
