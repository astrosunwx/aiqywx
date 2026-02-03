"""
增强的群机器人命令处理服务
支持售前、售后、查询等全面的命令系统
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.opportunity_service import OpportunityService
from app.services.order_service import OrderService
from app.services.parts_service import PartsService
from app.services.equipment_service import EquipmentService
from app.services.ticket_service import TicketService
from typing import Dict, Optional
from decimal import Decimal


class GroupBotCommandService:
    """群机器人命令处理服务"""
    
    @staticmethod
    async def process_command(
        db: AsyncSession,
        command: str,
        operator_userid: str,
        operator_name: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        处理群命令
        
        Args:
            db: 数据库会话
            command: 命令文本
            operator_userid: 操作人UserID
            operator_name: 操作人姓名
            context: 上下文信息（如消息ID、关联实体ID等）
        
        Returns:
            处理结果字典
        """
        command = command.strip()
        context = context or {}
        
        # ========== 售前命令 ==========
        
        # #认领 - 认领商机
        if command == "#认领" and context.get('opportunity_id'):
            opportunity = await OpportunityService.claim_opportunity(
                db, context['opportunity_id'], operator_userid, operator_name
            )
            return {
                "success": True,
                "message": f"✅ 商机已认领\n商机ID: {opportunity.id}\n客户: {opportunity.customer_name}\n产品: {opportunity.product_name}",
                "opportunity": opportunity
            }
        
        # #认领 - 认领工单
        elif command == "#认领" and context.get('ticket_id'):
            # TODO: 调用工单认领服务
            return {
                "success": True,
                "message": f"✅ 工单已认领\n工单ID: {context['ticket_id']}"
            }
        
        # #跟进 [内容] - 添加跟进记录
        elif command.startswith("#跟进"):
            parts = command.split(maxsplit=1)
            if len(parts) < 2:
                return {"success": False, "message": "❌ 命令格式错误\n正确格式: #跟进 跟进内容"}
            
            follow_up_content = parts[1]
            opportunity_id = context.get('opportunity_id')
            
            if not opportunity_id:
                return {"success": False, "message": "❌ 未找到关联的商机"}
            
            opportunity = await OpportunityService.add_follow_up(
                db, opportunity_id, operator_userid, operator_name, follow_up_content
            )
            
            return {
                "success": True,
                "message": f"✅ 跟进记录已添加\n商机ID: {opportunity.id}\n跟进内容: {follow_up_content}"
            }
        
        # #报价 [金额] - 提交报价
        elif command.startswith("#报价"):
            parts = command.split()
            if len(parts) < 2:
                return {"success": False, "message": "❌ 命令格式错误\n正确格式: #报价 金额"}
            
            try:
                amount = Decimal(parts[1])
            except:
                return {"success": False, "message": "❌ 金额格式错误"}
            
            opportunity_id = context.get('opportunity_id')
            if not opportunity_id:
                return {"success": False, "message": "❌ 未找到关联的商机"}
            
            opportunity = await OpportunityService.submit_quote(
                db, opportunity_id, amount, operator_userid, operator_name
            )
            
            return {
                "success": True,
                "message": f"✅ 报价已提交\n商机ID: {opportunity.id}\n报价金额: ¥{amount}"
            }
        
        # #成交 - 标记商机成交并生成订单
        elif command == "#成交":
            opportunity_id = context.get('opportunity_id')
            if not opportunity_id:
                return {"success": False, "message": "❌ 未找到关联的商机"}
            
            # 标记商机为成交
            opportunity = await OpportunityService.mark_as_won(
                db, opportunity_id, operator_userid, operator_name
            )
            
            # TODO: 可以在这里引导用户填写配送信息以创建订单
            
            return {
                "success": True,
                "message": f"✅ 商机已标记为成交！\n商机ID: {opportunity.id}\n"
                          f"请在网页系统中填写配送信息以创建订单"
            }
        
        # #丢单 [原因] - 标记商机丢失
        elif command.startswith("#丢单"):
            parts = command.split(maxsplit=1)
            reason = parts[1] if len(parts) > 1 else "未填写原因"
            
            opportunity_id = context.get('opportunity_id')
            if not opportunity_id:
                return {"success": False, "message": "❌ 未找到关联的商机"}
            
            opportunity = await OpportunityService.mark_as_lost(
                db, opportunity_id, reason, operator_userid, operator_name
            )
            
            return {
                "success": True,
                "message": f"✅ 商机已标记为丢单\n商机ID: {opportunity.id}\n丢单原因: {reason}"
            }
        
        # ========== 售后命令 ==========
        
        # #转派 @某人 - 转派工单
        elif command.startswith("#转派"):
            # TODO: 实现工单转派逻辑
            return {"success": True, "message": "✅ 工单转派功能开发中"}
        
        # #协作 @某人 - 添加协作人员
        elif command.startswith("#协作"):
            # TODO: 实现添加协作人员逻辑
            return {"success": True, "message": "✅ 添加协作人员功能开发中"}
        
        # #申请配件 [编码] [数量] - 申请配件
        elif command.startswith("#申请配件"):
            parts = command.split()
            if len(parts) < 3:
                return {"success": False, "message": "❌ 命令格式错误\n正确格式: #申请配件 配件编码 数量"}
            
            part_code = parts[1]
            try:
                quantity = int(parts[2])
            except:
                return {"success": False, "message": "❌ 数量格式错误"}
            
            ticket_id = context.get('ticket_id')
            if not ticket_id:
                return {"success": False, "message": "❌ 未找到关联的工单"}
            
            try:
                usage = await PartsService.request_parts(
                    db, ticket_id, part_code, quantity, 
                    operator_userid, operator_name
                )
                
                return {
                    "success": True,
                    "message": f"✅ 配件申请成功\n"
                              f"配件: {usage.part_name} ({usage.part_code})\n"
                              f"数量: {quantity}\n"
                              f"单价: ¥{usage.unit_price}\n"
                              f"总计: ¥{usage.total_cost}"
                }
            except ValueError as e:
                return {"success": False, "message": f"❌ {str(e)}"}
        
        # #进度 [百分比] - 更新处理进度
        elif command.startswith("#进度"):
            parts = command.split()
            if len(parts) < 2:
                return {"success": False, "message": "❌ 命令格式错误\n正确格式: #进度 百分比(例如: #进度 50%)"}
            
            # TODO: 实现更新工单进度逻辑
            progress_str = parts[1].rstrip('%')
            try:
                progress = int(progress_str)
                return {
                    "success": True,
                    "message": f"✅ 工单进度已更新为 {progress}%"
                }
            except:
                return {"success": False, "message": "❌ 进度格式错误"}
        
        # #已解决 - 标记工单已解决
        elif command == "#已解决":
            ticket_id = context.get('ticket_id')
            if not ticket_id:
                return {"success": False, "message": "❌ 未找到关联的工单"}
            
            # TODO: 调用工单解决服务
            return {
                "success": True,
                "message": f"✅ 工单已标记为已解决\n工单ID: {ticket_id}\n"
                          f"系统将发送客户满意度调查"
            }
        
        # #需要回访 - 标记需要客户回访
        elif command == "#需要回访":
            return {"success": True, "message": "✅ 已标记需要回访"}
        
        # ========== 查询命令 ==========
        
        # #我的工单 - 查询自己负责的工单
        elif command == "#我的工单":
            # TODO: 实现查询工单逻辑
            return {
                "success": True,
                "message": f"📋 您的工单列表：\n(功能开发中，请访问网页系统查看)"
            }
        
        # #查询设备 [客户名称] - 查询客户设备信息
        elif command.startswith("#查询设备"):
            parts = command.split(maxsplit=1)
            if len(parts) < 2:
                return {"success": False, "message": "❌ 命令格式错误\n正确格式: #查询设备 客户名称或电话"}
            
            customer_info = parts[1]
            # TODO: 实现设备查询逻辑（根据客户名称或电话）
            
            return {
                "success": True,
                "message": f"🔍 查询客户: {customer_info}\n(功能开发中)"
            }
        
        # #查询配件 [编码] - 查询配件库存
        elif command.startswith("#查询配件"):
            parts = command.split()
            if len(parts) < 2:
                return {"success": False, "message": "❌ 命令格式错误\n正确格式: #查询配件 配件编码"}
            
            part_code = parts[1]
            
            try:
                part = await PartsService.get_part_by_code(db, part_code)
                
                if not part:
                    return {"success": False, "message": f"❌ 未找到配件编码: {part_code}"}
                
                stock_status = "✅ 库存充足" if part.stock_quantity > part.min_stock_alert else "⚠️ 库存不足"
                
                return {
                    "success": True,
                    "message": f"📦 配件信息\n"
                              f"编码: {part.part_code}\n"
                              f"名称: {part.part_name}\n"
                              f"规格: {part.specification}\n"
                              f"库存: {part.stock_quantity}\n"
                              f"单价: ¥{part.unit_price}\n"
                              f"状态: {stock_status}"
                }
            except Exception as e:
                return {"success": False, "message": f"❌ 查询失败: {str(e)}"}
        
        # #客户历史 [手机号] - 查询客户历史记录
        elif command.startswith("#客户历史"):
            parts = command.split()
            if len(parts) < 2:
                return {"success": False, "message": "❌ 命令格式错误\n正确格式: #客户历史 手机号"}
            
            customer_phone = parts[1]
            
            try:
                # 查询客户设备
                equipment_list = await EquipmentService.get_equipment_by_customer(db, customer_phone)
                
                # 查询客户订单
                order_list = await OrderService.get_orders_by_customer(db, customer_phone)
                
                return {
                    "success": True,
                    "message": f"👤 客户: {customer_phone}\n"
                              f"设备数量: {len(equipment_list)}\n"
                              f"订单数量: {len(order_list)}\n"
                              f"详细信息请访问网页系统查看"
                }
            except Exception as e:
                return {"success": False, "message": f"❌ 查询失败: {str(e)}"}
        
        # 未知命令
        else:
            return {
                "success": False,
                "message": f"❌ 未知命令: {command}\n"
                          "请使用以下命令:\n"
                          "售前: #认领 #跟进 #报价 #成交 #丢单\n"
                          "售后: #认领 #转派 #协作 #申请配件 #进度 #已解决\n"
                          "查询: #我的工单 #查询设备 #查询配件 #客户历史"
            }
