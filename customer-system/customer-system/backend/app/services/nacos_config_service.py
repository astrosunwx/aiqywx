"""
Nacos动态配置服务
支持配置热更新、配置监听
"""
import json
import logging
from typing import Dict, Any, Callable, Optional
from nacos import NacosClient

logger = logging.getLogger(__name__)


class NacosConfigService:
    """Nacos配置服务"""
    
    def __init__(
        self,
        server_addresses: str = "localhost:8848",
        namespace: str = "public",
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        初始化Nacos客户端
        
        Args:
            server_addresses: Nacos服务器地址（如：localhost:8848 或 192.168.1.1:8848,192.168.1.2:8848）
            namespace: 命名空间ID
            username: 用户名（Nacos 1.2.0+需要认证）
            password: 密码
        """
        self.client = NacosClient(
            server_addresses=server_addresses,
            namespace=namespace,
            username=username,
            password=password
        )
        
        # 配置监听器
        self.listeners = {}
        
        logger.info(f"[Nacos] 已连接到: {server_addresses}")
    
    def get_config(
        self,
        data_id: str,
        group: str = "DEFAULT_GROUP",
        timeout: int = 3
    ) -> Optional[str]:
        """
        获取配置
        
        Args:
            data_id: 配置ID（如：message-config.json）
            group: 配置分组
            timeout: 超时时间（秒）
        
        Returns:
            配置内容（字符串）
        """
        try:
            config = self.client.get_config(data_id, group, timeout)
            logger.info(f"[Nacos] 获取配置: {data_id}")
            return config
            
        except Exception as e:
            logger.error(f"[Nacos] 获取配置失败 {data_id}: {e}")
            return None
    
    def get_config_json(
        self,
        data_id: str,
        group: str = "DEFAULT_GROUP"
    ) -> Optional[Dict[str, Any]]:
        """获取JSON格式配置"""
        config = self.get_config(data_id, group)
        
        if config:
            try:
                return json.loads(config)
            except json.JSONDecodeError as e:
                logger.error(f"[Nacos] 解析JSON失败 {data_id}: {e}")
                return None
        
        return None
    
    def publish_config(
        self,
        data_id: str,
        content: str,
        group: str = "DEFAULT_GROUP",
        config_type: str = "json"
    ) -> bool:
        """
        发布配置
        
        Args:
            data_id: 配置ID
            content: 配置内容
            group: 配置分组
            config_type: 配置类型（json/yaml/properties）
        
        Returns:
            是否成功
        """
        try:
            result = self.client.publish_config(
                data_id,
                group,
                content,
                config_type=config_type
            )
            
            if result:
                logger.info(f"[Nacos] 发布配置成功: {data_id}")
            else:
                logger.warning(f"[Nacos] 发布配置失败: {data_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"[Nacos] 发布配置异常 {data_id}: {e}")
            return False
    
    def remove_config(
        self,
        data_id: str,
        group: str = "DEFAULT_GROUP"
    ) -> bool:
        """删除配置"""
        try:
            result = self.client.remove_config(data_id, group)
            
            if result:
                logger.info(f"[Nacos] 删除配置成功: {data_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"[Nacos] 删除配置异常 {data_id}: {e}")
            return False
    
    def add_config_listener(
        self,
        data_id: str,
        callback: Callable[[str], None],
        group: str = "DEFAULT_GROUP"
    ):
        """
        添加配置监听器
        
        Args:
            data_id: 配置ID
            callback: 回调函数（参数为新配置内容）
            group: 配置分组
        """
        def listener_callback(args):
            """监听器回调"""
            content = args.get('content')
            logger.info(f"[Nacos] 配置更新: {data_id}")
            
            try:
                callback(content)
            except Exception as e:
                logger.error(f"[Nacos] 配置回调异常 {data_id}: {e}")
        
        # 注册监听器
        self.client.add_config_watcher(data_id, group, listener_callback)
        
        # 保存监听器引用
        listener_key = f"{group}:{data_id}"
        self.listeners[listener_key] = listener_callback
        
        logger.info(f"[Nacos] 已添加配置监听: {data_id}")
    
    def remove_config_listener(
        self,
        data_id: str,
        group: str = "DEFAULT_GROUP"
    ):
        """移除配置监听器"""
        listener_key = f"{group}:{data_id}"
        
        if listener_key in self.listeners:
            self.client.remove_config_watcher(
                data_id,
                group,
                self.listeners[listener_key]
            )
            
            del self.listeners[listener_key]
            logger.info(f"[Nacos] 已移除配置监听: {data_id}")


class DynamicConfig:
    """动态配置管理器"""
    
    def __init__(self, nacos_service: NacosConfigService):
        self.nacos = nacos_service
        self.configs = {}
    
    def register_config(
        self,
        config_name: str,
        data_id: str,
        group: str = "DEFAULT_GROUP",
        on_update: Optional[Callable[[Dict], None]] = None
    ):
        """
        注册配置
        
        Args:
            config_name: 配置名称（本地引用）
            data_id: Nacos配置ID
            group: 配置分组
            on_update: 配置更新回调
        """
        # 初始加载配置
        config = self.nacos.get_config_json(data_id, group)
        
        if config:
            self.configs[config_name] = config
            logger.info(f"[动态配置] 加载配置: {config_name}")
        
        # 添加监听器
        def update_callback(content: str):
            try:
                new_config = json.loads(content)
                self.configs[config_name] = new_config
                
                logger.info(f"[动态配置] 配置已更新: {config_name}")
                
                # 触发回调
                if on_update:
                    on_update(new_config)
                    
            except Exception as e:
                logger.error(f"[动态配置] 更新配置失败 {config_name}: {e}")
        
        self.nacos.add_config_listener(data_id, update_callback, group)
    
    def get(self, config_name: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.configs.get(config_name, default)


# 使用示例
"""
# 1. 初始化Nacos客户端
nacos = NacosConfigService(
    server_addresses="localhost:8848",
    namespace="public"
)

# 2. 获取配置
config = nacos.get_config_json("message-config.json")

# 3. 发布配置
nacos.publish_config(
    "message-config.json",
    json.dumps({"max_retry": 3, "timeout": 30}),
    config_type="json"
)

# 4. 添加配置监听
def on_config_change(content):
    config = json.loads(content)
    print(f"配置已更新: {config}")

nacos.add_config_listener("message-config.json", on_config_change)

# 5. 使用动态配置管理器
dynamic_config = DynamicConfig(nacos)

dynamic_config.register_config(
    "message",
    "message-config.json",
    on_update=lambda cfg: print(f"消息配置更新: {cfg}")
)

# 获取配置
max_retry = dynamic_config.get("message", {}).get("max_retry", 3)
"""
