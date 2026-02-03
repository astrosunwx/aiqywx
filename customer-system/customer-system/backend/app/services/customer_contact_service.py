"""
客户联系服务
实现企业微信客户联系功能：
1. 聊天工具栏侧边栏
2. 客服消息发送
3. 进度通知自动推送
"""
from typing import Dict, Any, List, Optional
from ..utils.wechat_work_api import WeChatWorkAPI
from ..services.secure_link_service import SecureLinkService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import Project, Customer
import os


class CustomerContactService:
    """客户联系服务 - 对外沟通"""
    
    @staticmethod
    async def send_progress_to_customer(
        db: AsyncSession,
        project_id: int,
        customer_external_userid: str,
        sender_userid: str,
        wechat_api: WeChatWorkAPI = None
    ) -> Dict[str, Any]:
        """
        发送项目进度给客户
        
        Args:
            db: 数据库会话
            project_id: 项目ID
            customer_external_userid: 客户的external_userid
            sender_userid: 发送消息的员工UserID
            wechat_api: 企业微信API实例
            
        Returns:
            发送结果
        """
        
        # 1. 查询项目信息
        stmt = select(Project).where(Project.id == project_id)
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()
        
        if not project:
            raise ValueError(f"项目 #{project_id} 不存在")
        
        # 2. 查询客户信息
        customer = None
        if project.customer_id:
            stmt = select(Customer).where(Customer.id == project.customer_id)
            result = await db.execute(stmt)
            customer = result.scalar_one_or_none()
        
        # 3. 生成安全链接（客户专属，1小时有效）
        secure_link = SecureLinkService.generate_project_detail_link(
            user_id=customer_external_userid,
            project_id=project_id,
            wechat_user_id=customer_external_userid,
            expiry_hours=1  # 客户链接1小时有效
        )
        
        # 4. 构建消息内容
        message_content = await CustomerContactService._build_progress_message(
            project=project,
            customer=customer,
            secure_link=secure_link
        )
        
        # 5. 调用企业微信API发送消息
        if not wechat_api:
            wechat_api = WeChatWorkAPI(
                corp_id=os.getenv("CORP_ID"),
                corp_secret=os.getenv("CORP_SECRET"),
                agent_id=os.getenv("AGENT_ID")
            )
        
        # 发送图文消息
        result = await CustomerContactService._send_external_message(
            wechat_api=wechat_api,
            external_userid=customer_external_userid,
            sender=sender_userid,
            message_type='link',
            content=message_content
        )
        
        return {
            "success": True,
            "project_id": project_id,
            "customer_external_userid": customer_external_userid,
            "secure_link": secure_link,
            "send_result": result
        }
    
    @staticmethod
    async def _build_progress_message(
        project: Project,
        customer: Customer = None,
        secure_link: str = None
    ) -> Dict[str, Any]:
        """
        构建项目进度消息内容
        
        Returns:
            消息内容字典
        """
        
        # 计算进度描述
        progress_status = "准备启动"
        if project.progress >= 90:
            progress_status = "即将完成"
        elif project.progress >= 70:
            progress_status = "进入收尾阶段"
        elif project.progress >= 50:
            progress_status = "稳步推进中"
        elif project.progress >= 30:
            progress_status = "开发进行中"
        elif project.progress > 0:
            progress_status = "已启动开发"
        
        # 状态文本映射
        status_text = {
            'pending': '待启动',
            'assigned': '已分配',
            'processing': '进行中',
            'escalated': '加急处理',
            'resolved': '已完成',
            'closed': '已交付'
        }
        
        return {
            "type": "link",
            "link": {
                "title": f"📊 {project.title} - 项目进度通知",
                "url": secure_link,
                "desc": f"""亲爱的{customer.name if customer else '客户'}，您好！

项目名称：{project.title}
当前进度：已完成 {project.progress}%
最新状态：{status_text.get(project.status, '进行中')} - {progress_status}
负责团队：{', '.join(project.team_members) if project.team_members else '技术团队'}

💡 点击查看详细进度报告
⏰ 页面将每30分钟自动更新最新进展""",
                "picurl": os.getenv("APP_DOMAIN", "http://localhost:8000") + "/static/project-icon.png"  # 可选：项目图标
            }
        }
    
    @staticmethod
    async def _send_external_message(
        wechat_api: WeChatWorkAPI,
        external_userid: str,
        sender: str,
        message_type: str,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送消息给外部联系人（客户）
        
        Args:
            wechat_api: 企业微信API实例
            external_userid: 客户的external_userid
            sender: 发送者的UserID
            message_type: 消息类型（text, link, image等）
            content: 消息内容
            
        Returns:
            发送结果
        """
        
        # 获取access_token
        access_token = await wechat_api.get_access_token()
        
        # 构建API请求
        api_url = f"https://qyapi.weixin.qq.com/cgi-bin/externalcontact/message/send?access_token={access_token}"
        
        # 组装请求体
        request_body = {
            "external_userid": [external_userid],
            "sender": sender,
            "msgtype": message_type
        }
        
        # 根据消息类型添加内容
        if message_type == 'text':
            request_body["text"] = {
                "content": content.get('text', '')
            }
        elif message_type == 'link':
            request_body["link"] = content.get('link', {})
        elif message_type == 'miniprogram':
            request_body["miniprogram"] = content.get('miniprogram', {})
        
        # 发送请求
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=request_body) as response:
                result = await response.json()
                
                if result.get('errcode') == 0:
                    print(f"✅ 消息发送成功：external_userid={external_userid}")
                    return {
                        "success": True,
                        "errcode": 0,
                        "errmsg": "ok"
                    }
                else:
                    print(f"❌ 消息发送失败：{result.get('errmsg')}")
                    return {
                        "success": False,
                        "errcode": result.get('errcode'),
                        "errmsg": result.get('errmsg')
                    }
    
    @staticmethod
    async def auto_notify_on_milestone(
        db: AsyncSession,
        project_id: int,
        milestone: str,
        customer_external_userid: str,
        sender_userid: str
    ) -> Dict[str, Any]:
        """
        当项目到达里程碑时自动通知客户
        
        Args:
            db: 数据库会话
            project_id: 项目ID
            milestone: 里程碑名称（如："需求确认"、"开发完成"、"测试通过"）
            customer_external_userid: 客户external_userid
            sender_userid: 发送者UserID
            
        Returns:
            通知结果
        """
        
        # 查询项目
        stmt = select(Project).where(Project.id == project_id)
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()
        
        if not project:
            raise ValueError(f"项目 #{project_id} 不存在")
        
        # 生成安全链接
        secure_link = SecureLinkService.generate_project_detail_link(
            user_id=customer_external_userid,
            project_id=project_id,
            wechat_user_id=customer_external_userid,
            expiry_hours=2  # 里程碑通知链接2小时有效
        )
        
        # 构建里程碑通知消息
        wechat_api = WeChatWorkAPI(
            corp_id=os.getenv("CORP_ID"),
            corp_secret=os.getenv("CORP_SECRET"),
            agent_id=os.getenv("AGENT_ID")
        )
        
        milestone_emoji = {
            "需求确认": "✅",
            "设计完成": "🎨",
            "开发完成": "💻",
            "测试通过": "✔️",
            "上线部署": "🚀",
            "验收通过": "🎉"
        }
        
        message_content = {
            "type": "link",
            "link": {
                "title": f"{milestone_emoji.get(milestone, '📢')} 【项目里程碑通知】{milestone}",
                "url": secure_link,
                "desc": f"""🎊 好消息！

您的项目【{project.title}】已达成重要里程碑：
✨ {milestone}

当前进度：{project.progress}%
项目状态：进展顺利

点击查看详细报告 →""",
                "picurl": ""
            }
        }
        
        result = await CustomerContactService._send_external_message(
            wechat_api=wechat_api,
            external_userid=customer_external_userid,
            sender=sender_userid,
            message_type='link',
            content=message_content
        )
        
        return {
            "success": result.get('success'),
            "milestone": milestone,
            "project_id": project_id,
            "secure_link": secure_link
        }
    
    @staticmethod
    async def batch_send_progress_updates(
        db: AsyncSession,
        project_ids: List[int],
        sender_userid: str
    ) -> List[Dict[str, Any]]:
        """
        批量发送项目进度给多个客户
        
        用于定期（如每周五）向所有进行中的项目客户发送进度更新
        
        Args:
            db: 数据库会话
            project_ids: 项目ID列表
            sender_userid: 发送者UserID
            
        Returns:
            发送结果列表
        """
        
        results = []
        
        for project_id in project_ids:
            try:
                # 查询项目
                stmt = select(Project).where(Project.id == project_id)
                result = await db.execute(stmt)
                project = result.scalar_one_or_none()
                
                if not project:
                    results.append({
                        "project_id": project_id,
                        "success": False,
                        "error": "项目不存在"
                    })
                    continue
                
                # 查询客户
                if not project.customer_id:
                    results.append({
                        "project_id": project_id,
                        "success": False,
                        "error": "未关联客户"
                    })
                    continue
                
                stmt = select(Customer).where(Customer.id == project.customer_id)
                result = await db.execute(stmt)
                customer = result.scalar_one_or_none()
                
                if not customer or not customer.wechat_openid:
                    results.append({
                        "project_id": project_id,
                        "success": False,
                        "error": "客户无企业微信联系方式"
                    })
                    continue
                
                # 发送进度通知
                send_result = await CustomerContactService.send_progress_to_customer(
                    db=db,
                    project_id=project_id,
                    customer_external_userid=customer.wechat_openid,
                    sender_userid=sender_userid
                )
                
                results.append({
                    "project_id": project_id,
                    "success": send_result.get('success'),
                    "customer_name": customer.name
                })
                
                # 避免频繁发送，间隔1秒
                import asyncio
                await asyncio.sleep(1)
            
            except Exception as e:
                results.append({
                    "project_id": project_id,
                    "success": False,
                    "error": str(e)
                })
        
        return results
