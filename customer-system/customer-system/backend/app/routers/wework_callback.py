"""
企业微信回调处理路由
处理企业微信的各类回调事件，包括客户添加/删除等
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auto_binding_service import AutoBindingService
from pydantic import BaseModel
from typing import Dict, Optional
import hashlib
import xml.etree.ElementTree as ET
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class WeChatCallbackResponse(BaseModel):
    """企业微信回调响应"""
    errcode: int = 0
    errmsg: str = "ok"


@router.get("/api/wework/callback")
async def wework_callback_verify(
    msg_signature: str,
    timestamp: str,
    nonce: str,
    echostr: str
):
    """
    企业微信回调URL验证
    
    企业微信会发送GET请求验证回调URL
    需要按照企业微信的加密方式解密echostr并返回
    
    Args:
        msg_signature: 企业微信加密签名
        timestamp: 时间戳
        nonce: 随机数
        echostr: 加密的随机字符串
    
    Returns:
        解密后的echostr
    """
    # TODO: 实现企业微信的消息解密逻辑
    # from wechatpy.enterprise.crypto import WeChatCrypto
    # crypto = WeChatCrypto(token, encoding_aes_key, corp_id)
    # echo_str = crypto.decrypt_message(echostr, msg_signature, timestamp, nonce)
    # return echo_str
    
    logger.info(f"企业微信回调验证: timestamp={timestamp}, nonce={nonce}")
    return echostr  # 临时直接返回，生产环境需要解密


@router.post("/api/wework/callback")
async def wework_callback_handler(
    request: Request,
    msg_signature: Optional[str] = None,
    timestamp: Optional[str] = None,
    nonce: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    企业微信事件回调处理
    
    处理各类企业微信事件：
    - add_external_contact: 添加客户
    - del_external_contact: 删除客户
    - edit_external_contact: 编辑客户
    
    Args:
        request: FastAPI请求对象
        msg_signature: 企业微信加密签名
        timestamp: 时间戳
        nonce: 随机数
        db: 数据库会话
    
    Returns:
        处理结果
    """
    try:
        # 获取POST数据
        body = await request.body()
        
        # TODO: 解密企业微信消息
        # from wechatpy.enterprise.crypto import WeChatCrypto
        # crypto = WeChatCrypto(token, encoding_aes_key, corp_id)
        # decrypted_xml = crypto.decrypt_message(body, msg_signature, timestamp, nonce)
        
        # 临时处理：直接解析XML（生产环境需要先解密）
        decrypted_xml = body.decode('utf-8')
        
        # 解析XML
        root = ET.fromstring(decrypted_xml)
        
        # 提取事件信息
        event_data = {
            'ToUserName': root.find('ToUserName').text if root.find('ToUserName') is not None else None,
            'FromUserName': root.find('FromUserName').text if root.find('FromUserName') is not None else None,
            'CreateTime': root.find('CreateTime').text if root.find('CreateTime') is not None else None,
            'MsgType': root.find('MsgType').text if root.find('MsgType') is not None else None,
            'Event': root.find('Event').text if root.find('Event') is not None else None,
            'ChangeType': root.find('ChangeType').text if root.find('ChangeType') is not None else None,
            'UserID': root.find('UserID').text if root.find('UserID') is not None else None,
            'ExternalUserID': root.find('ExternalUserID').text if root.find('ExternalUserID') is not None else None,
            'State': root.find('State').text if root.find('State') is not None else '',
            'WelcomeCode': root.find('WelcomeCode').text if root.find('WelcomeCode') is not None else None,
        }
        
        logger.info(f"收到企业微信回调: Event={event_data.get('Event')}, ChangeType={event_data.get('ChangeType')}")
        
        # 处理不同类型的事件
        msg_type = event_data.get('MsgType')
        event_type = event_data.get('Event')
        change_type = event_data.get('ChangeType')
        
        if msg_type == 'event' and event_type == 'change_external_contact':
            if change_type == 'add_external_contact':
                # 处理添加客户事件
                result = await AutoBindingService.handle_wework_add_customer_event(db, event_data)
                logger.info(f"添加客户事件处理结果: {result}")
            
            elif change_type == 'del_external_contact':
                # 处理删除客户事件
                logger.info(f"客户删除事件: UserID={event_data.get('UserID')}, ExternalUserID={event_data.get('ExternalUserID')}")
                # TODO: 实现客户删除处理逻辑
            
            elif change_type == 'edit_external_contact':
                # 处理编辑客户事件
                logger.info(f"客户编辑事件: ExternalUserID={event_data.get('ExternalUserID')}")
                # TODO: 实现客户编辑处理逻辑
        
        # 返回成功响应给企业微信
        return "success"
        
    except Exception as e:
        logger.error(f"处理企业微信回调失败: {str(e)}", exc_info=True)
        # 即使失败也返回success，避免企业微信重复推送
        return "success"


@router.post("/api/wework/manual-bind")
async def manual_bind_customer(
    request: Dict,
    db: AsyncSession = Depends(get_db)
):
    """
    手动绑定客户（用于补救场景）
    
    适用场景：
    - 临时绑定已过期
    - 企业微信事件未正常触发
    - 需要管理员手动关联
    
    请求体:
    {
        "customer_phone": "13800138000",
        "wechat_openid": "oABC123...",
        "wework_userid": "wmXXX...",
        "operator_userid": "admin"
    }
    """
    customer_phone = request.get('customer_phone')
    wechat_openid = request.get('wechat_openid')
    wework_userid = request.get('wework_userid')
    operator_userid = request.get('operator_userid')
    
    if not all([customer_phone, operator_userid]):
        raise HTTPException(status_code=400, detail="缺少必要参数")
    
    # 执行手动绑定
    result = await AutoBindingService.auto_bind_customer(
        db, customer_phone, wework_userid or '', operator_userid
    )
    
    return result


@router.get("/api/customer/binding-status/{phone}")
async def get_binding_status(
    phone: str,
    db: AsyncSession = Depends(get_db)
):
    """
    查询客户绑定状态
    
    用于客户在公众号查询绑定进度
    
    Args:
        phone: 客户手机号
    
    Returns:
        绑定状态信息
    """
    result = await AutoBindingService.check_binding_status(db, phone)
    return result


@router.get("/api/customer/can-query/{phone}")
async def check_customer_can_query(
    phone: str,
    db: AsyncSession = Depends(get_db)
):
    """
    检查客户是否有权限查询项目
    
    只有通过企业微信搜索手机号添加的客户才能查询
    
    Args:
        phone: 客户手机号
    
    Returns:
        是否有查询权限
    """
    can_query = await AutoBindingService.check_customer_can_query(db, phone)
    
    return {
        "can_query": can_query,
        "message": "有查询权限" if can_query else "需要先通过企业微信员工添加"
    }
