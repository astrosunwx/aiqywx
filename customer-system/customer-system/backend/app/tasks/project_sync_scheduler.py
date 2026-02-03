"""
项目同步功能 - 定时任务
文件: app/tasks/project_sync_scheduler.py
说明: 使用APScheduler配置定时同步任务
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import json
import logging
from sqlalchemy import select, and_
from typing import Optional, List, Dict, Any
import httpx

from app.database import AsyncSessionLocal
from app.models import (
    ProjectCache, ProjectSyncHistory, ProjectSyncConfig,
    ProjectStatusNotifications
)

logger = logging.getLogger(__name__)

# 全局调度器实例
scheduler: Optional[AsyncIOScheduler] = None


class ProjectSyncScheduler:
    """项目同步调度器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.job_id = 'project_sync_job'
    
    async def start(self):
        """启动调度器"""
        try:
            # 获取同步配置
            config = await self._get_sync_config()
            
            if not config.get('auto_sync_enabled'):
                logger.info("Auto sync is disabled")
                return
            
            # 解析Cron表达式
            cron_expr = config.get('sync_frequency', '*/15 * * * *')
            cron_parts = cron_expr.split()
            
            if len(cron_parts) != 5:
                logger.error(f"Invalid cron expression: {cron_expr}")
                return
            
            # 创建Cron触发器
            trigger = CronTrigger(
                minute=cron_parts[0],
                hour=cron_parts[1],
                day=cron_parts[2],
                month=cron_parts[3],
                day_of_week=cron_parts[4]
            )
            
            # 添加定时任务
            self.scheduler.add_job(
                self.sync_projects,
                trigger,
                id=self.job_id,
                name='Project Sync Job',
                replace_existing=True,
                misfire_grace_time=30,
                coalesce=True  # 多个错过的执行合并为一次
            )
            
            # 启动调度器
            self.scheduler.start()
            logger.info(f"Project sync scheduler started with cron: {cron_expr}")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
    
    async def stop(self):
        """停止调度器"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Project sync scheduler stopped")
    
    async def sync_projects(self):
        """
        同步所有项目的状态
        这是定时任务的主要执行函数
        """
        start_time = datetime.utcnow()
        logger.info("Starting automatic project sync")
        
        try:
            async with AsyncSessionLocal() as db:
                # 获取配置
                config = await self._get_sync_config()
                
                if not config.get('auto_sync_enabled'):
                    logger.info("Auto sync is disabled, skipping sync")
                    return
                
                # 获取同步的项目类型
                project_types = config.get('sync_types', ['presale', 'aftersales', 'sales'])
                cache_ttl = config.get('cache_ttl', 30)
                notify_on_change = config.get('notify_on_change', True)
                
                # 从远程API获取所有项目
                all_projects = await self._fetch_remote_projects(project_types)
                
                if not all_projects:
                    logger.warning("No projects fetched from remote API")
                    return
                
                # 统计信息
                total = len(all_projects)
                updated = 0
                unchanged = 0
                failed = 0
                changes = []
                
                # 同步每个项目
                for project in all_projects:
                    try:
                        project_id = project.get('id')
                        new_status = project.get('status')
                        
                        # 获取旧的缓存数据
                        old_cache = await self._get_project_cache(project_id, db)
                        old_status = old_cache.get('status') if old_cache else None
                        
                        # 更新缓存
                        cache = await self._update_project_cache(
                            project_id, project, cache_ttl, db
                        )
                        
                        # 检测状态变更
                        if old_cache and old_status != new_status:
                            updated += 1
                            changes.append({
                                'project_id': project_id,
                                'old_status': old_status,
                                'new_status': new_status,
                                'project_title': project.get('title'),
                                'notified': False
                            })
                            
                            # 发送通知
                            if notify_on_change:
                                await self._send_notifications(
                                    project_id, old_status, new_status, project, db
                                )
                                
                                # 标记为已通知
                                if changes:
                                    changes[-1]['notified'] = True
                        else:
                            unchanged += 1
                    
                    except Exception as e:
                        logger.error(f"Failed to sync project {project.get('id')}: {e}")
                        failed += 1
                        continue
                
                # 记录同步历史
                duration = (datetime.utcnow() - start_time).total_seconds()
                status = "success" if failed == 0 else ("partial" if failed < total else "failed")
                
                await self._record_sync_history(
                    db=db,
                    total=total,
                    updated=updated,
                    unchanged=unchanged,
                    failed=failed,
                    duration=duration,
                    status=status,
                    changes=changes
                )
                
                logger.info(
                    f"Project sync completed: total={total}, updated={updated}, "
                    f"unchanged={unchanged}, failed={failed}, duration={duration:.2f}s"
                )
        
        except Exception as e:
            logger.error(f"Project sync failed: {e}", exc_info=True)
    
    async def _get_sync_config(self) -> Dict[str, Any]:
        """获取同步配置"""
        async with AsyncSessionLocal() as db:
            try:
                config_keys = [
                    'auto_sync_enabled',
                    'sync_frequency',
                    'cache_ttl',
                    'sync_types',
                    'notify_on_change',
                    'notify_channels'
                ]
                
                config = {}
                
                for key in config_keys:
                    stmt = select(ProjectSyncConfig).where(
                        ProjectSyncConfig.config_key == key
                    )
                    result = await db.execute(stmt)
                    record = result.scalar_one_or_none()
                    
                    if record:
                        value = json.loads(record.config_value)
                        config[key] = value.get('value', None)
                
                # 设置默认值
                return {
                    'auto_sync_enabled': config.get('auto_sync_enabled', True),
                    'sync_frequency': config.get('sync_frequency', '*/15 * * * *'),
                    'cache_ttl': config.get('cache_ttl', 30),
                    'sync_types': config.get('sync_types', ['presale', 'aftersales', 'sales']),
                    'notify_on_change': config.get('notify_on_change', True),
                    'notify_channels': config.get('notify_channels', ['wechat', 'sms'])
                }
            
            except Exception as e:
                logger.error(f"Failed to get sync config: {e}")
                # 返回默认配置
                return {
                    'auto_sync_enabled': True,
                    'sync_frequency': '*/15 * * * *',
                    'cache_ttl': 30,
                    'sync_types': ['presale', 'aftersales', 'sales'],
                    'notify_on_change': True,
                    'notify_channels': ['wechat', 'sms']
                }
    
    async def _fetch_remote_projects(self, project_types: List[str]) -> List[Dict[str, Any]]:
        """从远程API批量获取所有项目"""
        try:
            REMOTE_API_BASE = "https://remote-api.example.com"  # 需要配置实际地址
            REMOTE_API_KEY = "your-api-key"  # 需要配置实际密钥
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{REMOTE_API_BASE}/projects",
                    params={"types": ",".join(project_types)},
                    headers={"Authorization": f"Bearer {REMOTE_API_KEY}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('projects', [])
                else:
                    logger.error(f"Remote API error: {response.status_code}")
                    return []
        
        except Exception as e:
            logger.error(f"Failed to fetch projects from remote API: {e}")
            return []
    
    async def _get_project_cache(self, project_id: str, db) -> Optional[Dict[str, Any]]:
        """从缓存获取项目数据"""
        try:
            stmt = select(ProjectCache).where(ProjectCache.project_id == project_id)
            result = await db.execute(stmt)
            cache = result.scalar_one_or_none()
            
            if cache:
                return json.loads(cache.data)
            return None
        
        except Exception as e:
            logger.error(f"Failed to get project cache: {e}")
            return None
    
    async def _update_project_cache(self, project_id: str, project_data: Dict[str, Any],
                                   cache_ttl: int, db) -> ProjectCache:
        """更新项目缓存"""
        try:
            stmt = select(ProjectCache).where(ProjectCache.project_id == project_id)
            result = await db.execute(stmt)
            cache = result.scalar_one_or_none()
            
            expires_at = datetime.utcnow() + timedelta(minutes=cache_ttl)
            
            if not cache:
                cache = ProjectCache(
                    project_id=project_id,
                    project_type=project_data.get('type', 'unknown'),
                    title=project_data.get('title'),
                    status=project_data.get('status'),
                    data=json.dumps(project_data, default=str),
                    remote_updated_at=datetime.utcnow(),
                    expires_at=expires_at
                )
                db.add(cache)
            else:
                cache.title = project_data.get('title')
                cache.status = project_data.get('status')
                cache.data = json.dumps(project_data, default=str)
                cache.remote_updated_at = datetime.utcnow()
                cache.expires_at = expires_at
            
            await db.commit()
            return cache
        
        except Exception as e:
            logger.error(f"Failed to update project cache: {e}")
            raise
    
    async def _send_notifications(self, project_id: str, old_status: str, new_status: str,
                                 project: Dict[str, Any], db):
        """发送项目状态变更通知"""
        try:
            # 获取配置
            config = await self._get_sync_config()
            notify_channels = config.get('notify_channels', [])
            
            # 生成通知内容
            project_type = project.get('type', 'unknown')
            project_title = project.get('title', '项目')
            message = f"您的{project_type}项目【{project_title}】状态已更新：{old_status} → {new_status}"
            
            # 获取需要通知的人员
            stakeholders = await self._get_project_stakeholders(project_id)
            
            # 创建通知记录
            for stakeholder in stakeholders:
                for channel in notify_channels:
                    notification = ProjectStatusNotifications(
                        project_id=project_id,
                        old_status=old_status,
                        new_status=new_status,
                        notify_to=stakeholder.get('user_id'),
                        notify_type=channel,
                        notify_content=message,
                        send_status='pending'
                    )
                    db.add(notification)
            
            await db.commit()
            logger.info(f"Notifications created for project {project_id}")
        
        except Exception as e:
            logger.error(f"Failed to send notifications: {e}")
    
    async def _get_project_stakeholders(self, project_id: str) -> List[Dict[str, str]]:
        """
        获取项目相关人员
        包括：客户、工程师、销售
        需要从CRM系统查询
        """
        try:
            # 这里需要根据实际业务逻辑实现
            # 从project_cache中获取相关人员ID，然后查询CRM系统
            async with AsyncSessionLocal() as db:
                stmt = select(ProjectCache).where(ProjectCache.project_id == project_id)
                result = await db.execute(stmt)
                cache = result.scalar_one_or_none()
                
                if not cache:
                    return []
                
                project_data = json.loads(cache.data)
                
                stakeholders = []
                
                # 添加客户
                if project_data.get('customer_id'):
                    stakeholders.append({
                        'user_id': project_data.get('customer_id'),
                        'phone': project_data.get('phone'),
                        'type': 'customer'
                    })
                
                # 添加工程师（售后）
                if project_data.get('engineer_id'):
                    stakeholders.append({
                        'user_id': project_data.get('engineer_id'),
                        'phone': project_data.get('engineer_phone'),
                        'type': 'engineer'
                    })
                
                # 添加销售（售前和销售）
                if project_data.get('salesman_id'):
                    stakeholders.append({
                        'user_id': project_data.get('salesman_id'),
                        'phone': project_data.get('salesman_phone'),
                        'type': 'salesman'
                    })
                
                return stakeholders
        
        except Exception as e:
            logger.error(f"Failed to get project stakeholders: {e}")
            return []
    
    async def _record_sync_history(self, db, total: int, updated: int, unchanged: int,
                                  failed: int, duration: float, status: str,
                                  changes: List[Dict[str, Any]]):
        """记录同步历史"""
        try:
            sync_record = ProjectSyncHistory(
                sync_time=datetime.utcnow(),
                sync_type='auto',
                total_projects=total,
                updated_count=updated,
                unchanged_count=unchanged,
                failed_count=failed,
                duration=duration,
                status=status,
                message=f"自动同步完成：更新{updated}个，未变更{unchanged}个，失败{failed}个",
                changes=json.dumps(changes, default=str),
                triggered_by='system'
            )
            db.add(sync_record)
            await db.commit()
        
        except Exception as e:
            logger.error(f"Failed to record sync history: {e}")


# 全局函数
async def init_project_sync_scheduler():
    """初始化项目同步调度器"""
    global scheduler
    scheduler = ProjectSyncScheduler()
    await scheduler.start()


async def shutdown_project_sync_scheduler():
    """关闭项目同步调度器"""
    global scheduler
    if scheduler:
        await scheduler.stop()
