"""
数据源管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.database import get_db
from app.models_datasource import DataSource
from pydantic import BaseModel
from typing import Optional, List
import base64


router = APIRouter(prefix="/api/datasources", tags=["数据源管理"])


class DataSourceCreate(BaseModel):
    """创建数据源请求"""
    source_name: str
    source_desc: Optional[str] = None
    db_type: str  # mysql, postgresql, sqlserver
    db_host: str
    db_port: int
    db_name: str
    db_username: str
    db_password: str
    db_charset: Optional[str] = "utf8mb4"
    use_ssl: Optional[bool] = False
    is_active: Optional[bool] = True
    is_default: Optional[bool] = False


class DataSourceUpdate(BaseModel):
    """更新数据源请求"""
    source_name: Optional[str] = None
    source_desc: Optional[str] = None
    db_type: Optional[str] = None
    db_host: Optional[str] = None
    db_port: Optional[int] = None
    db_name: Optional[str] = None
    db_username: Optional[str] = None
    db_password: Optional[str] = None
    db_charset: Optional[str] = None
    use_ssl: Optional[bool] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class DataSourceResponse(BaseModel):
    """数据源响应"""
    id: int
    source_name: str
    source_desc: Optional[str]
    db_type: str
    db_host: str
    db_port: int
    db_name: str
    db_username: str
    db_password: str  # 前端显示时会隐藏
    db_charset: str
    use_ssl: bool
    is_active: bool
    is_default: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


def encode_password(password: str) -> str:
    """简单加密密码(Base64)"""
    return base64.b64encode(password.encode()).decode()


def decode_password(encoded_password: str) -> str:
    """解密密码"""
    try:
        return base64.b64decode(encoded_password.encode()).decode()
    except:
        return encoded_password


@router.get("/", response_model=List[DataSourceResponse])
async def list_datasources(db: AsyncSession = Depends(get_db)):
    """获取所有数据源列表"""
    result = await db.execute(select(DataSource).order_by(DataSource.is_default.desc(), DataSource.created_at))
    datasources = result.scalars().all()
    
    # 转换为响应模型,密码解密后返回(前端会自动隐藏)
    return [
        DataSourceResponse(
            id=ds.id,
            source_name=ds.source_name,
            source_desc=ds.source_desc,
            db_type=ds.db_type,
            db_host=ds.db_host,
            db_port=ds.db_port,
            db_name=ds.db_name,
            db_username=ds.db_username,
            db_password=decode_password(ds.db_password),
            db_charset=ds.db_charset,
            use_ssl=ds.use_ssl,
            is_active=ds.is_active,
            is_default=ds.is_default,
            created_at=ds.created_at.isoformat() if ds.created_at else "",
            updated_at=ds.updated_at.isoformat() if ds.updated_at else ""
        )
        for ds in datasources
    ]


@router.post("/", response_model=DataSourceResponse)
async def create_datasource(data: DataSourceCreate, db: AsyncSession = Depends(get_db)):
    """创建新数据源"""
    # 检查数据源名称是否已存在
    result = await db.execute(select(DataSource).where(DataSource.source_name == data.source_name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"数据源名称 '{data.source_name}' 已存在")
    
    # 如果设置为默认数据源,取消其他数据源的默认状态
    if data.is_default:
        await db.execute(update(DataSource).values(is_default=False))
    
    # 创建数据源(密码加密)
    datasource = DataSource(
        source_name=data.source_name,
        source_desc=data.source_desc,
        db_type=data.db_type,
        db_host=data.db_host,
        db_port=data.db_port,
        db_name=data.db_name,
        db_username=data.db_username,
        db_password=encode_password(data.db_password),
        db_charset=data.db_charset,
        use_ssl=data.use_ssl,
        is_active=data.is_active,
        is_default=data.is_default
    )
    
    db.add(datasource)
    await db.commit()
    await db.refresh(datasource)
    
    return DataSourceResponse(
        id=datasource.id,
        source_name=datasource.source_name,
        source_desc=datasource.source_desc,
        db_type=datasource.db_type,
        db_host=datasource.db_host,
        db_port=datasource.db_port,
        db_name=datasource.db_name,
        db_username=datasource.db_username,
        db_password=decode_password(datasource.db_password),
        db_charset=datasource.db_charset,
        use_ssl=datasource.use_ssl,
        is_active=datasource.is_active,
        is_default=datasource.is_default,
        created_at=datasource.created_at.isoformat() if datasource.created_at else "",
        updated_at=datasource.updated_at.isoformat() if datasource.updated_at else ""
    )


@router.get("/{datasource_id}", response_model=DataSourceResponse)
async def get_datasource(datasource_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个数据源详情"""
    result = await db.execute(select(DataSource).where(DataSource.id == datasource_id))
    datasource = result.scalar_one_or_none()
    
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    return DataSourceResponse(
        id=datasource.id,
        source_name=datasource.source_name,
        source_desc=datasource.source_desc,
        db_type=datasource.db_type,
        db_host=datasource.db_host,
        db_port=datasource.db_port,
        db_name=datasource.db_name,
        db_username=datasource.db_username,
        db_password=decode_password(datasource.db_password),
        db_charset=datasource.db_charset,
        use_ssl=datasource.use_ssl,
        is_active=datasource.is_active,
        is_default=datasource.is_default,
        created_at=datasource.created_at.isoformat() if datasource.created_at else "",
        updated_at=datasource.updated_at.isoformat() if datasource.updated_at else ""
    )


@router.put("/{datasource_id}", response_model=DataSourceResponse)
async def update_datasource(datasource_id: int, data: DataSourceUpdate, db: AsyncSession = Depends(get_db)):
    """更新数据源"""
    result = await db.execute(select(DataSource).where(DataSource.id == datasource_id))
    datasource = result.scalar_one_or_none()
    
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    # 检查数据源名称是否与其他数据源冲突
    if data.source_name and data.source_name != datasource.source_name:
        result = await db.execute(select(DataSource).where(DataSource.source_name == data.source_name))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"数据源名称 '{data.source_name}' 已存在")
    
    # 如果设置为默认数据源,取消其他数据源的默认状态
    if data.is_default:
        await db.execute(update(DataSource).where(DataSource.id != datasource_id).values(is_default=False))
    
    # 更新字段
    update_data = data.model_dump(exclude_unset=True)
    if 'db_password' in update_data and update_data['db_password']:
        update_data['db_password'] = encode_password(update_data['db_password'])
    
    for key, value in update_data.items():
        setattr(datasource, key, value)
    
    await db.commit()
    await db.refresh(datasource)
    
    return DataSourceResponse(
        id=datasource.id,
        source_name=datasource.source_name,
        source_desc=datasource.source_desc,
        db_type=datasource.db_type,
        db_host=datasource.db_host,
        db_port=datasource.db_port,
        db_name=datasource.db_name,
        db_username=datasource.db_username,
        db_password=decode_password(datasource.db_password),
        db_charset=datasource.db_charset,
        use_ssl=datasource.use_ssl,
        is_active=datasource.is_active,
        is_default=datasource.is_default,
        created_at=datasource.created_at.isoformat() if datasource.created_at else "",
        updated_at=datasource.updated_at.isoformat() if datasource.updated_at else ""
    )


@router.delete("/{datasource_id}")
async def delete_datasource(datasource_id: int, db: AsyncSession = Depends(get_db)):
    """删除数据源"""
    result = await db.execute(select(DataSource).where(DataSource.id == datasource_id))
    datasource = result.scalar_one_or_none()
    
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    await db.execute(delete(DataSource).where(DataSource.id == datasource_id))
    await db.commit()
    
    return {"message": f"数据源 '{datasource.source_name}' 已删除"}


@router.post("/{datasource_id}/test")
async def test_datasource(datasource_id: int, db: AsyncSession = Depends(get_db)):
    """测试数据源连接"""
    result = await db.execute(select(DataSource).where(DataSource.id == datasource_id))
    datasource = result.scalar_one_or_none()
    
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    # 根据数据库类型测试连接
    try:
        password = decode_password(datasource.db_password)
        
        if datasource.db_type == "mysql":
            import aiomysql
            conn = await aiomysql.connect(
                host=datasource.db_host,
                port=datasource.db_port,
                user=datasource.db_username,
                password=password,
                db=datasource.db_name,
                charset=datasource.db_charset
            )
            await conn.close()
            
        elif datasource.db_type == "postgresql":
            import asyncpg
            conn = await asyncpg.connect(
                host=datasource.db_host,
                port=datasource.db_port,
                user=datasource.db_username,
                password=password,
                database=datasource.db_name
            )
            await conn.close()
            
        elif datasource.db_type == "sqlserver":
            # SQL Server连接测试(需要安装pyodbc)
            try:
                import pyodbc
                conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={datasource.db_host},{datasource.db_port};DATABASE={datasource.db_name};UID={datasource.db_username};PWD={password}'
                if datasource.use_ssl:
                    conn_str += ';Encrypt=yes;TrustServerCertificate=no'
                conn = pyodbc.connect(conn_str, timeout=5)
                conn.close()
            except ImportError:
                raise HTTPException(status_code=500, detail="未安装pyodbc驱动，请运行: pip install pyodbc")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"连接失败: {str(e)}")
        
        return {"status": "success", "message": f"连接 {datasource.source_name} 成功!"}
        
    except Exception as e:
        return {"status": "error", "message": f"连接失败: {str(e)}"}


@router.post("/{datasource_id}/set-default")
async def set_default_datasource(datasource_id: int, db: AsyncSession = Depends(get_db)):
    """设置默认数据源"""
    result = await db.execute(select(DataSource).where(DataSource.id == datasource_id))
    datasource = result.scalar_one_or_none()
    
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    # 取消其他数据源的默认状态
    await db.execute(update(DataSource).values(is_default=False))
    
    # 设置当前数据源为默认
    datasource.is_default = True
    await db.commit()
    
    return {"message": f"'{datasource.source_name}' 已设为默认数据源"}
