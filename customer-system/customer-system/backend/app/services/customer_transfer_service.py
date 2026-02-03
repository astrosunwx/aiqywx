"""
客户关系转接服务
实现企业微信客户无感转接：销售 → 工程师 → 销售
核心功能：调用企业微信「分配客户」API，实现权限静默切换
"""
from typing import Dict, Any, Optional
from ..utils.wechat_work_api import WeChatWorkAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ..models import Project, Customer, WeChatSession
import os
import logging

logger = logging.getLogger(__name__)


class CustomerTransferService:
    """客户关系转接服务 - 无感切换联系人"""
    
    @staticmethod
    async def transfer_customer_to_engineer(
        db: AsyncSession,
        project_id: int,
        engineer_userid: str,
        engineer_name: str,
        wechat_api: WeChatWorkAPI = None
    ) -> Dict[str, Any]:
        """
        将客户关系转接给工程师
        
        场景：售后工单分配给工程师时，自动将客户联系权限转移
        
        Args:
            db: 数据库会话
            project_id: 项目/工单ID
            engineer_userid: 工程师的UserID
            engineer_name: 工程师姓名
            wechat_api: 企业微信API实例
            
        Returns:
            转接结果
        """
        
        # 1. 查询项目和客户信息
        stmt = select(Project).where(Project.id == project_id)
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()
        
        if not project:
            raise ValueError(f"项目 #{project_id} 不存在")
        
        if not project.customer_id:
            raise ValueError(f"项目 #{project_id} 未关联客户")
        
        stmt = select(Customer).where(Customer.id == project.customer_id)
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise ValueError(f"客户不存在")
        
        if not customer.wechat_openid:
            raise ValueError(f"客户无企业微信联系方式")
        
        # 2. 获取当前负责的销售UserID
        original_sales_userid = project.assigned_to or customer.sales_representative
        
        if not original_sales_userid:
            raise ValueError(f"无法确定原销售负责人")
        
        # 3. 记录原销售信息（用于后续转回）
        project.original_sales_userid = original_sales_userid
        project.transfer_timestamp = None  # 记录转接时间
        await db.commit()
        
        # 4. 调用企业微信API转接客户
        if not wechat_api:
            wechat_api = WeChatWorkAPI(
                corp_id=os.getenv("CORP_ID"),
                corp_secret=os.getenv("CORP_SECRET"),
                agent_id=os.getenv("AGENT_ID")
            )
        
        transfer_result = await CustomerTransferService._call_transfer_customer_api(
            wechat_api=wechat_api,
            external_userid=customer.wechat_openid,
            handover_userid=original_sales_userid,  # 原负责人（销售）
            takeover_userid=engineer_userid,        # 新负责人（工程师）
            transfer_success_msg="您好，我是负责技术支持的工程师，接下来由我为您服务。"
        )
        
        # 5. 更新项目负责人
        project.assigned_to = engineer_userid
        project.assigned_to_name = engineer_name
        await db.commit()
        
        logger.info(
            f"✅ 客户关系转接成功：客户={customer.name}, "
            f"原销售={original_sales_userid} → 工程师={engineer_userid}"
        )
        
        return {
            "success": True,
            "project_id": project_id,
            "customer_name": customer.name,
            "customer_external_userid": customer.wechat_openid,
            "from_userid": original_sales_userid,
            "to_userid": engineer_userid,
            "to_name": engineer_name,
            "transfer_result": transfer_result,
            "message": f"客户已转接给工程师 {engineer_name}"
        }
    
    @staticmethod
    async def transfer_customer_back_to_sales(
        db: AsyncSession,
        project_id: int,
        wechat_api: WeChatWorkAPI = None
    ) -> Dict[str, Any]:
        """
        将客户关系转回原销售
        
        场景：工单解决后，自动将客户联系权限归还给原销售
        
        Args:
            db: 数据库会话
            project_id: 项目/工单ID
            wechat_api: 企业微信API实例
            
        Returns:
            转接结果
        """
        
        # 1. 查询项目和客户信息
        stmt = select(Project).where(Project.id == project_id)
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()
        
        if not project:
            raise ValueError(f"项目 #{project_id} 不存在")
        
        # 2. 获取原销售UserID
        original_sales_userid = project.original_sales_userid
        
        if not original_sales_userid:
            raise ValueError(f"未找到原销售负责人信息，无法转回")
        
        # 3. 获取当前工程师UserID
        current_engineer_userid = project.assigned_to
        
        if not current_engineer_userid:
            raise ValueError(f"未找到当前负责人信息")
        
        # 4. 查询客户
        stmt = select(Customer).where(Customer.id == project.customer_id)
        result = await db.execute(stmt)
        customer = result.scalar_one_or_none()
        
        if not customer or not customer.wechat_openid:
            raise ValueError(f"客户信息不完整")
        
        # 5. 调用企业微信API转回客户
        if not wechat_api:
            wechat_api = WeChatWorkAPI(
                corp_id=os.getenv("CORP_ID"),
                corp_secret=os.getenv("CORP_SECRET"),
                agent_id=os.getenv("AGENT_ID")
            )
        
        transfer_result = await CustomerTransferService._call_transfer_customer_api(
            wechat_api=wechat_api,
            external_userid=customer.wechat_openid,
            handover_userid=current_engineer_userid,  # 原负责人（工程师）
            takeover_userid=original_sales_userid,    # 新负责人（销售）
            transfer_success_msg="问题已解决，后续我继续为您服务。"
        )
        
        # 6. 更新项目负责人（恢复为原销售）
        project.assigned_to = original_sales_userid
        project.assigned_to_name = customer.sales_representative  # 恢复销售姓名
        project.original_sales_userid = None  # 清空转接记录
        await db.commit()
        
        logger.info(
            f"✅ 客户关系转回成功：客户={customer.name}, "
            f"工程师={current_engineer_userid} → 原销售={original_sales_userid}"
        )
        
        return {
            "success": True,
            "project_id": project_id,
            "customer_name": customer.name,
            "customer_external_userid": customer.wechat_openid,
            "from_userid": current_engineer_userid,
            "to_userid": original_sales_userid,
            "transfer_result": transfer_result,
            "message": f"客户已转回原销售"
        }
    
    @staticmethod
    async def _call_transfer_customer_api(
        wechat_api: WeChatWorkAPI,
        external_userid: str,
        handover_userid: str,
        takeover_userid: str,
        transfer_success_msg: str = ""
    ) -> Dict[str, Any]:
        """
        调用企业微信「分配客户」API
        
        文档：https://developer.work.weixin.qq.com/document/path/92125
        
        Args:
            wechat_api: 企业微信API实例
            external_userid: 客户的external_userid
            handover_userid: 原负责人UserID（移交方）
            takeover_userid: 新负责人UserID（接收方）
            transfer_success_msg: 转接成功后发送给客户的消息
            
        Returns:
            API调用结果
        """
        
        # 获取access_token
        access_token = await wechat_api.get_access_token()
        
        # 构建API请求URL
        api_url = f"https://qyapi.weixin.qq.com/cgi-bin/externalcontact/transfer_customer?access_token={access_token}"
        
        # 构建请求体
        request_body = {
            "handover_userid": handover_userid,
            "takeover_userid": takeover_userid,
            "external_userid": [external_userid]
        }
        
        # 可选：转接成功后的提示消息
        if transfer_success_msg:
            request_body["transfer_success_msg"] = transfer_success_msg
        
        # 发送请求
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=request_body) as response:
                result = await response.json()
                
                if result.get('errcode') == 0:
                    logger.info(
                        f"✅ 企业微信API调用成功：客户={external_userid}, "
                        f"{handover_userid} → {takeover_userid}"
                    )
                    return {
                        "success": True,
                        "errcode": 0,
                        "errmsg": "ok",
                        "customer": result.get('customer', [])
                    }
                else:
                    logger.error(
                        f"❌ 企业微信API调用失败：{result.get('errmsg')}, "
                        f"errcode={result.get('errcode')}"
                    )
                    return {
                        "success": False,
                        "errcode": result.get('errcode'),
                        "errmsg": result.get('errmsg')
                    }
    
    @staticmethod
    async def batch_transfer_customers(
        db: AsyncSession,
        project_ids: list[int],
        engineer_userid: str,
        engineer_name: str
    ) -> list[Dict[str, Any]]:
        """
        批量转接客户（用于批量分配工单）
        
        Args:
            db: 数据库会话
            project_ids: 项目ID列表
            engineer_userid: 工程师UserID
            engineer_name: 工程师姓名
            
        Returns:
            转接结果列表
        """
        
        results = []
        
        for project_id in project_ids:
            try:
                result = await CustomerTransferService.transfer_customer_to_engineer(
                    db=db,
                    project_id=project_id,
                    engineer_userid=engineer_userid,
                    engineer_name=engineer_name
                )
                results.append({
                    "project_id": project_id,
                    "success": True,
                    "result": result
                })
                
                # 避免频繁调用API，间隔1秒
                import asyncio
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ 项目 #{project_id} 转接失败：{str(e)}")
                results.append({
                    "project_id": project_id,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    @staticmethod
    async def get_customer_current_owner(
        db: AsyncSession,
        customer_external_userid: str,
        wechat_api: WeChatWorkAPI = None
    ) -> Dict[str, Any]:
        """
        查询客户当前的负责人
        
        调用企业微信API获取客户的最新归属信息
        
        Args:
            db: 数据库会话
            customer_external_userid: 客户的external_userid
            wechat_api: 企业微信API实例
            
        Returns:
            当前负责人信息
        """
        
        if not wechat_api:
            wechat_api = WeChatWorkAPI(
                corp_id=os.getenv("CORP_ID"),
                corp_secret=os.getenv("CORP_SECRET"),
                agent_id=os.getenv("AGENT_ID")
            )
        
        # 获取access_token
        access_token = await wechat_api.get_access_token()
        
        # 调用获取客户详情API
        api_url = f"https://qyapi.weixin.qq.com/cgi-bin/externalcontact/get?access_token={access_token}&external_userid={customer_external_userid}"
        
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                result = await response.json()
                
                if result.get('errcode') == 0:
                    external_contact = result.get('external_contact', {})
                    follow_users = result.get('follow_user', [])
                    
                    # 获取第一个跟进人（通常是当前负责人）
                    current_owner = follow_users[0] if follow_users else None
                    
                    return {
                        "success": True,
                        "customer_name": external_contact.get('name'),
                        "current_owner_userid": current_owner.get('userid') if current_owner else None,
                        "current_owner_remark": current_owner.get('remark') if current_owner else None,
                        "follow_users": follow_users
                    }
                else:
                    return {
                        "success": False,
                        "errcode": result.get('errcode'),
                        "errmsg": result.get('errmsg')
                    }
