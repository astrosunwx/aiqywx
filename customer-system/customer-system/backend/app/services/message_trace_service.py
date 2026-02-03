"""
Redis链路追踪服务
记录消息处理的每个环节
"""
import redis
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class MessageTracer:
    """消息链路追踪器"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.trace_prefix = "msg_trace:"
        self.trace_ttl = 7 * 24 * 3600  # 7天过期
    
    def generate_trace_id(self) -> str:
        """生成追踪ID"""
        return f"trace_{uuid.uuid4().hex}"
    
    def start_trace(self, trace_id: str, message_data: Dict) -> None:
        """开始追踪"""
        trace_key = f"{self.trace_prefix}{trace_id}"
        
        trace_data = {
            "trace_id": trace_id,
            "started_at": datetime.now().isoformat(),
            "message_data": message_data,
            "nodes": []
        }
        
        self.redis.setex(
            trace_key,
            self.trace_ttl,
            json.dumps(trace_data, ensure_ascii=False)
        )
        
        logger.info(f"[追踪] 开始追踪: {trace_id}")
    
    def add_node(
        self,
        trace_id: str,
        node_name: str,
        node_type: str,
        input_data: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """添加追踪节点"""
        trace_key = f"{self.trace_prefix}{trace_id}"
        
        try:
            # 获取现有追踪数据
            trace_json = self.redis.get(trace_key)
            if not trace_json:
                logger.warning(f"[追踪] 追踪ID不存在: {trace_id}")
                return None
            
            trace_data = json.loads(trace_json)
            
            # 创建新节点
            node_id = f"node_{len(trace_data['nodes']) + 1}"
            node = {
                "node_id": node_id,
                "node_name": node_name,
                "node_type": node_type,
                "started_at": datetime.now().isoformat(),
                "input_data": input_data or {},
                "metadata": metadata or {},
                "status": "processing"
            }
            
            trace_data["nodes"].append(node)
            
            # 更新追踪数据
            self.redis.setex(
                trace_key,
                self.trace_ttl,
                json.dumps(trace_data, ensure_ascii=False)
            )
            
            logger.debug(f"[追踪] 添加节点: {trace_id} -> {node_name}")
            return node_id
            
        except Exception as e:
            logger.error(f"[追踪] 添加节点失败: {e}")
            return None
    
    def finish_node(
        self,
        trace_id: str,
        node_id: str,
        status: str = "success",
        output_data: Optional[Dict] = None,
        error_message: Optional[str] = None
    ) -> None:
        """完成追踪节点"""
        trace_key = f"{self.trace_prefix}{trace_id}"
        
        try:
            # 获取现有追踪数据
            trace_json = self.redis.get(trace_key)
            if not trace_json:
                return
            
            trace_data = json.loads(trace_json)
            
            # 查找并更新节点
            for node in trace_data["nodes"]:
                if node["node_id"] == node_id:
                    finished_at = datetime.now()
                    started_at = datetime.fromisoformat(node["started_at"])
                    duration_ms = (finished_at - started_at).total_seconds() * 1000
                    
                    node["finished_at"] = finished_at.isoformat()
                    node["duration_ms"] = duration_ms
                    node["status"] = status
                    node["output_data"] = output_data or {}
                    if error_message:
                        node["error_message"] = error_message
                    break
            
            # 更新追踪数据
            self.redis.setex(
                trace_key,
                self.trace_ttl,
                json.dumps(trace_data, ensure_ascii=False)
            )
            
            logger.debug(f"[追踪] 完成节点: {trace_id} -> {node_id} ({status})")
            
        except Exception as e:
            logger.error(f"[追踪] 完成节点失败: {e}")
    
    def finish_trace(self, trace_id: str, final_status: str = "success") -> None:
        """结束追踪"""
        trace_key = f"{self.trace_prefix}{trace_id}"
        
        try:
            trace_json = self.redis.get(trace_key)
            if not trace_json:
                return
            
            trace_data = json.loads(trace_json)
            
            finished_at = datetime.now()
            started_at = datetime.fromisoformat(trace_data["started_at"])
            total_duration_ms = (finished_at - started_at).total_seconds() * 1000
            
            trace_data["finished_at"] = finished_at.isoformat()
            trace_data["total_duration_ms"] = total_duration_ms
            trace_data["final_status"] = final_status
            
            # 更新追踪数据
            self.redis.setex(
                trace_key,
                self.trace_ttl,
                json.dumps(trace_data, ensure_ascii=False)
            )
            
            logger.info(f"[追踪] 结束追踪: {trace_id} ({final_status}, {total_duration_ms:.2f}ms)")
            
        except Exception as e:
            logger.error(f"[追踪] 结束追踪失败: {e}")
    
    def get_trace(self, trace_id: str) -> Optional[Dict]:
        """获取追踪数据"""
        trace_key = f"{self.trace_prefix}{trace_id}"
        
        try:
            trace_json = self.redis.get(trace_key)
            if trace_json:
                return json.loads(trace_json)
            return None
        except Exception as e:
            logger.error(f"[追踪] 获取追踪数据失败: {e}")
            return None
    
    def get_recent_traces(self, limit: int = 100) -> List[Dict]:
        """获取最近的追踪记录"""
        try:
            # 扫描所有追踪key
            keys = self.redis.keys(f"{self.trace_prefix}*")
            traces = []
            
            for key in keys[:limit]:
                trace_json = self.redis.get(key)
                if trace_json:
                    traces.append(json.loads(trace_json))
            
            # 按时间排序
            traces.sort(key=lambda x: x.get("started_at", ""), reverse=True)
            return traces
            
        except Exception as e:
            logger.error(f"[追踪] 获取最近追踪记录失败: {e}")
            return []
    
    def get_statistics(self, time_range_hours: int = 24) -> Dict:
        """获取追踪统计"""
        try:
            keys = self.redis.keys(f"{self.trace_prefix}*")
            
            total_count = 0
            success_count = 0
            failed_count = 0
            total_duration_ms = 0
            node_stats = {}
            
            for key in keys:
                trace_json = self.redis.get(key)
                if not trace_json:
                    continue
                
                trace_data = json.loads(trace_json)
                
                # 检查时间范围
                started_at = datetime.fromisoformat(trace_data["started_at"])
                if datetime.now() - started_at > timedelta(hours=time_range_hours):
                    continue
                
                total_count += 1
                
                if trace_data.get("final_status") == "success":
                    success_count += 1
                elif trace_data.get("final_status") == "failed":
                    failed_count += 1
                
                total_duration_ms += trace_data.get("total_duration_ms", 0)
                
                # 统计各节点
                for node in trace_data.get("nodes", []):
                    node_name = node["node_name"]
                    if node_name not in node_stats:
                        node_stats[node_name] = {
                            "count": 0,
                            "total_duration_ms": 0,
                            "success_count": 0,
                            "failed_count": 0
                        }
                    
                    node_stats[node_name]["count"] += 1
                    node_stats[node_name]["total_duration_ms"] += node.get("duration_ms", 0)
                    
                    if node.get("status") == "success":
                        node_stats[node_name]["success_count"] += 1
                    elif node.get("status") == "failed":
                        node_stats[node_name]["failed_count"] += 1
            
            # 计算平均值
            avg_duration_ms = total_duration_ms / total_count if total_count > 0 else 0
            
            for node_name, stats in node_stats.items():
                if stats["count"] > 0:
                    stats["avg_duration_ms"] = stats["total_duration_ms"] / stats["count"]
            
            return {
                "time_range_hours": time_range_hours,
                "total_count": total_count,
                "success_count": success_count,
                "failed_count": failed_count,
                "success_rate": (success_count / total_count * 100) if total_count > 0 else 0,
                "avg_duration_ms": avg_duration_ms,
                "node_statistics": node_stats
            }
            
        except Exception as e:
            logger.error(f"[追踪] 获取统计数据失败: {e}")
            return {}


# 使用示例
"""
# 初始化追踪器
tracer = MessageTracer(redis_client)

# 开始追踪
trace_id = tracer.generate_trace_id()
tracer.start_trace(trace_id, {"phone": "13800138000", "content": "测试消息"})

# 添加节点
node_id1 = tracer.add_node(trace_id, "消息队列", "queue")
# ... 处理逻辑
tracer.finish_node(trace_id, node_id1, "success", {"queue_pos": 123})

node_id2 = tracer.add_node(trace_id, "AI处理", "process")
# ... AI处理
tracer.finish_node(trace_id, node_id2, "success", {"intent": "售前咨询"})

node_id3 = tracer.add_node(trace_id, "消息发送", "send")
# ... 发送消息
tracer.finish_node(trace_id, node_id3, "success", {"msg_id": "abc123"})

# 结束追踪
tracer.finish_trace(trace_id, "success")

# 查询追踪
trace_data = tracer.get_trace(trace_id)
statistics = tracer.get_statistics(24)
"""
