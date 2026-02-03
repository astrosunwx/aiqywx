"""
客户关系转接路由
实现客户无感知的联系人切换
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..services.customer_transfer_service import CustomerTransferService
from pydantic import BaseModel

router = APIRouter(prefix="/customer-transfer", tags=["客户关系转接"])


class TransferToEngineerRequest(BaseModel):
    """转接给工程师请求"""
    project_id: int
    engineer_userid: str
    engineer_name: str


class TransferBackRequest(BaseModel):
    """转回原销售请求"""
    project_id: int


@router.post("/to-engineer")
async def transfer_to_engineer(
    request: TransferToEngineerRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    将客户关系转接给工程师
    
    场景：售后工单分配给工程师时，自动转接客户联系权限
    客户视角：无感知，仍在原聊天窗口对话
    内部实现：调用企业微信API，静默切换负责人
    
    Args:
        project_id: 项目/工单ID
        engineer_userid: 工程师UserID（如：lisi）
        engineer_name: 工程师姓名（如：李四）
    
    Returns:
        转接结果
    
    Example:
        ```
        POST /customer-transfer/to-engineer
        {
            "project_id": 123,
            "engineer_userid": "lisi",
            "engineer_name": "李四"
        }
        ```
    """
    
    try:
        result = await CustomerTransferService.transfer_customer_to_engineer(
            db=db,
            project_id=request.project_id,
            engineer_userid=request.engineer_userid,
            engineer_name=request.engineer_name
        )
        
        return {
            "success": True,
            "message": f"客户已转接给工程师 {request.engineer_name}",
            "result": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转接失败：{str(e)}")


@router.post("/back-to-sales")
async def transfer_back_to_sales(
    request: TransferBackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    将客户关系转回原销售
    
    场景：工单解决后，自动将客户联系权限归还给原销售
    客户视角：无感知，继续在原聊天窗口对话
    内部实现：调用企业微信API，恢复原负责人
    
    Args:
        project_id: 项目/工单ID
    
    Returns:
        转接结果
    
    Example:
        ```
        POST /customer-transfer/back-to-sales
        {
            "project_id": 123
        }
        ```
    """
    
    try:
        result = await CustomerTransferService.transfer_customer_back_to_sales(
            db=db,
            project_id=request.project_id
        )
        
        return {
            "success": True,
            "message": "客户已转回原销售",
            "result": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转回失败：{str(e)}")


@router.get("/current-owner/{external_userid}")
async def get_current_owner(
    external_userid: str,
    db: AsyncSession = Depends(get_db)
):
    """
    查询客户当前的负责人
    
    调用企业微信API获取客户的最新归属信息
    
    Args:
        external_userid: 客户的external_userid
    
    Returns:
        当前负责人信息
    
    Example:
        ```
        GET /customer-transfer/current-owner/wmABCDEFGHIJKLMNOPQ
        ```
    """
    
    try:
        result = await CustomerTransferService.get_customer_current_owner(
            db=db,
            customer_external_userid=external_userid
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.post("/batch-transfer")
async def batch_transfer_customers(
    project_ids: list[int],
    engineer_userid: str,
    engineer_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    批量转接客户（用于批量分配工单）
    
    Args:
        project_ids: 项目ID列表
        engineer_userid: 工程师UserID
        engineer_name: 工程师姓名
    
    Returns:
        批量转接结果
    
    Example:
        ```
        POST /customer-transfer/batch-transfer
        {
            "project_ids": [1, 2, 3],
            "engineer_userid": "lisi",
            "engineer_name": "李四"
        }
        ```
    """
    
    try:
        results = await CustomerTransferService.batch_transfer_customers(
            db=db,
            project_ids=project_ids,
            engineer_userid=engineer_userid,
            engineer_name=engineer_name
        )
        
        success_count = sum(1 for r in results if r.get('success'))
        
        return {
            "success": True,
            "total": len(results),
            "success_count": success_count,
            "failed_count": len(results) - success_count,
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量转接失败：{str(e)}")
