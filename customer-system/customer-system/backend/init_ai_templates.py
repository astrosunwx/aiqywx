"""
初始化AI回复模板 - 8个预留模块
这些是系统预留模块，用户只能编辑内容和关闭，不能删除
"""
import sys
sys.path.insert(0, '/root/app')

# 预留的8个AI模板
PRESET_AI_TEMPLATES = [
    {
        'id': 5,
        'name': '💰 价格咨询AI回复',
        'category': '售前咨询',
        'type': 'text',
        'keywords': '价格,报价,多少钱,费用,成本',
        'ai_model': 'zhipu-glm4',
        'is_system': True,  # 标记为系统模块，不可删除
        'is_enabled': True,
        'content': '''您好！关于{product}的价格，我们提供以下方案：

📊 **价格体系**
• 基础版：{price_basic}元
• 标准版：{price_standard}元  
• 旗舰版：{price_premium}元

💡 **如何选择？**
- 小规模使用 → 基础版
- 中等规模 → 标准版（性价比最佳）
- 大规模企业 → 旗舰版（功能全面）

具体价格会根据您的需求有所调整。我是{sales_representative_name}，很高兴为您服务！

📞 需要详细咨询？点击链接了解更多：
{baseUrl}/project/{order_id}?type=presale

请问您更倾向于哪个版本呢？''',
        'variables': ['{product}', '{price_basic}', '{price_standard}', '{price_premium}', '{sales_representative_name}', '{baseUrl}', '{order_id}'],
        'description': '用于回复客户的价格咨询问题'
    },
    {
        'id': 6,
        'name': '🔧 售后维修AI回复',
        'category': '售后服务',
        'type': 'text',
        'keywords': '维修,报修,坏了,不能用,故障,坏掉,修理',
        'ai_model': 'zhipu-glm4',
        'is_system': True,
        'is_enabled': True,
        'content': '''非常抱歉给您带来不便！😟

我已为您记录报修信息：

🛠️ **维修工单**
• 产品：{product}
• 问题：{issue}
• 预约时间：{appointment_time}
• 工单号：{ticket_id}

✅ **我们承诺**
我们的技术员{technician}（电话：{technician_phone}）将准时上门服务，预计{expected_visit_date} {expected_visit_time}到达。

请保持电话畅通，以便我们及时联系您。

📋 查看维修详情和进度：
{baseUrl}/project/{ticket_id}?type=aftersales

感谢您的耐心等待！''',
        'variables': ['{product}', '{issue}', '{appointment_time}', '{ticket_id}', '{technician}', '{technician_phone}', '{expected_visit_date}', '{expected_visit_time}', '{baseUrl}'],
        'description': '用于回复售后维修相关问题'
    },
    {
        'id': 7,
        'name': '📦 订单确认AI回复',
        'category': '订单通知',
        'type': 'text',
        'keywords': '订单,确认,已下单,收到订单,订单号',
        'ai_model': 'zhipu-glm4',
        'is_system': True,
        'is_enabled': True,
        'content': '''订单确认成功！🎉

感谢{customer_name}的订单，我们已收到您的购买申请。

📋 **订单信息**
• 订单号：{order_id}
• 产品：{product}
• 金额：{amount}元
• 订单时间：{order_date}
• 预期交付：{expected_delivery_date}

💰 **支付方式**
点击链接完成支付：
{baseUrl}/pay/{order_id}

需要发票吗？我们的客服会为您开具正式发票。

📞 后续流程
1. 💳 完成支付
2. 📦 我们为您准备商品
3. 🚚 发货并推送物流信息  
4. ✅ 确认收货

有任何问题，请随时联系我。祝您购物愉快！''',
        'variables': ['{customer_name}', '{order_id}', '{product}', '{amount}', '{order_date}', '{expected_delivery_date}', '{baseUrl}'],
        'description': '用于订单确认通知'
    },
    {
        'id': 8,
        'name': '❓ 常见问题AI回复',
        'category': '售前咨询',
        'type': 'text',
        'keywords': '怎么样,如何,怎么,什么,哪个,如何使用,使用方法',
        'ai_model': 'zhipu-glm4',
        'is_system': True,
        'is_enabled': True,
        'content': '''很高兴您对我们的产品感兴趣！😊

关于您提出的问题，以下是常见解答：

❓ **常见问题**

**Q1：产品使用难度高吗？**
A：非常简单！我们的产品设计遵循"傻瓜式操作"原则，即使是新手也能5分钟上手。

**Q2：有售后保障吗？**
A：当然有！我们提供：
  ✅ 1年免费保修
  ✅ 7×24小时技术支持
  ✅ 30天无理由退换货

**Q3：能定制化吗？**
A：可以的！我们支持：
  • 功能定制
  • 界面定制  
  • 集成定制

**Q4：购买后如何得到技术支持？**
A：多种方式任选：
  📞 电话：{sales_representative_phone}
  💬 微信：搜索"{sales_representative_name}"
  📧 邮件：support@company.com
  💻 在线：{baseUrl}/support

如果您的问题不在以上列表，请告诉我具体是什么，我会为您详细解答！

点击了解更多：{baseUrl}/product/{product}''',
        'variables': ['{product}', '{sales_representative_name}', '{sales_representative_phone}', '{baseUrl}'],
        'description': '用于回答常见问题'
    },
    {
        'id': 9,
        'name': '📊 数据统计AI回复',
        'category': '查询统计',
        'type': 'text',
        'keywords': '统计,数据,报表,分析,有多少,总共,一共',
        'ai_model': 'zhipu-glm4',
        'is_system': True,
        'is_enabled': True,
        'content': '''您好！以下是最新的数据统计：

📈 **业绩统计**（{query_date}）

**销售数据**
• 今日订单：{today_orders}个
• 本月订单：{month_orders}个
• 本月金额：{month_amount}元
• 同比增长：{growth_rate}%

**服务数据**
• 待处理工单：{pending_tickets}个
• 平均处理时间：{avg_processing_time}小时
• 客户满意度：{satisfaction_rate}%

**库存数据**
• 库存总数：{total_inventory}件
• 本周进货：{weekly_restock}件
• 预警商品：{low_stock_items}件

📊 详细报表：
{baseUrl}/analytics/{customer_id}?date={query_date}

💡 **建议**
根据数据分析，{suggestion_text}。

需要更详细的数据吗？我为您准备了完整的Excel报表，请告诉我您的邮箱！''',
        'variables': ['{query_date}', '{today_orders}', '{month_orders}', '{month_amount}', '{growth_rate}', '{pending_tickets}', '{avg_processing_time}', '{satisfaction_rate}', '{total_inventory}', '{weekly_restock}', '{low_stock_items}', '{baseUrl}', '{customer_id}', '{suggestion_text}'],
        'description': '用于提供数据统计信息'
    },
    {
        'id': 10,
        'name': '⏰ 预约提醒AI回复',
        'category': '预约提醒',
        'type': 'text',
        'keywords': '预约,时间,什么时候,什么时间,排期',
        'ai_model': 'zhipu-glm4',
        'is_system': True,
        'is_enabled': True,
        'content': '''预约成功！我们已为您安排上门服务。✨

📅 **服务预约信息**
• 预约日期：{appointment_date}
• 预约时间：{appointment_time}（请提前10分钟在家等候）
• 服务类型：{service_type}
• 技术员：{technician}
• 联系电话：{technician_phone}

📍 **服务地址**
{appointment_address}

⚠️ **温馨提示**
1. 请保持电话畅通
2. 家里要有人接待（需要原业主或授权人在场）
3. 如需更改时间，请提前24小时通知
4. 我们会在出发前30分钟短信通知您

🚫 **临时取消**
如必须取消或延期，请点击：
{baseUrl}/appointment/{appointment_id}/cancel

感谢您的配合！如有问题可随时致电{technician_phone}。''',
        'variables': ['{appointment_date}', '{appointment_time}', '{service_type}', '{technician}', '{technician_phone}', '{appointment_address}', '{appointment_id}', '{baseUrl}'],
        'description': '用于服务预约提醒'
    },
    {
        'id': 11,
        'name': '💬 咨询转接AI回复',
        'category': '转接处理',
        'type': 'text',
        'keywords': '转接,人工,客服,销售代表,我要',
        'ai_model': 'zhipu-glm4',
        'is_system': True,
        'is_enabled': True,
        'content': '''感谢您的耐心！我已为您转接到专业团队。🎯

👤 **负责人信息**
• 姓名：{assigned_person_name}
• 职位：{assigned_person_title}
• 电话：{assigned_person_phone}  
• 微信：{assigned_person_wechat}
• 邮箱：{assigned_person_email}

⏱️ **预期响应时间**
• 工作时间（9:00-18:00）：5分钟内回复
• 非工作时间：下个工作日09:00回复

📝 **您的咨询信息**
我已记录了您的咨询需求，{assigned_person_name}会立即为您处理。

💡 **更快获得帮助**
如果想加速处理，可以：
1. 直接拨打电话：{assigned_person_phone}
2. 添加微信快速沟通：{assigned_person_wechat}
3. 发邮件详细说明：{assigned_person_email}

查看转接详情：{baseUrl}/ticket/{transfer_id}

感谢您选择我们的服务！''',
        'variables': ['{assigned_person_name}', '{assigned_person_title}', '{assigned_person_phone}', '{assigned_person_wechat}', '{assigned_person_email}', '{transfer_id}', '{baseUrl}'],
        'description': '用于转接到人工客服'
    },
    {
        'id': 12,
        'name': '🎁 活动推广AI回复',
        'category': '营销推广',
        'type': 'text',
        'keywords': '活动,促销,优惠,打折,特价,限时',
        'ai_model': 'zhipu-glm4',
        'is_system': True,
        'is_enabled': True,
        'content': '''🎉 **重大活动通知** - {activity_name}

为感谢{customer_name}的持续支持，我们特别为您准备了专属优惠！

💝 **您的专属优惠**
• 优惠力度：{discount_percentage}% 折扣
• 优惠券码：{coupon_code}
• 使用条件：满{min_amount}元可用
• 有效期：{activity_start_date} - {activity_end_date}

🎁 **活动商品**
• {product_1}：{product_1_discount}
• {product_2}：{product_2_discount}  
• {product_3}：{product_3_discount}

⏰ **倒计时**
优惠仅剩：{remaining_days}天
赶快下单吧，错过就没有了！

🛒 **快速购买链接**
{baseUrl}/activity/{activity_id}?coupon={coupon_code}

📱 **分享赚现金**
将此活动分享给朋友，每成功转介绍1人，您就能获得{referral_bonus}元奖励！
分享链接：{baseUrl}/referral/{referral_code}

还有问题？我随时为您解答！''',
        'variables': ['{activity_name}', '{customer_name}', '{discount_percentage}', '{coupon_code}', '{min_amount}', '{activity_start_date}', '{activity_end_date}', '{product_1}', '{product_1_discount}', '{product_2}', '{product_2_discount}', '{product_3}', '{product_3_discount}', '{remaining_days}', '{activity_id}', '{referral_bonus}', '{referral_code}', '{baseUrl}'],
        'description': '用于活动推广和营销'
    }
]

print(f"✅ 已准备 {len(PRESET_AI_TEMPLATES)} 个系统预留模块")
for template in PRESET_AI_TEMPLATES:
    print(f"   - ID {template['id']}: {template['name']} (是否系统预留: {template['is_system']})")

print("\n💡 这些模块的特点：")
print("   ✅ 不可删除（is_system=True）")
print("   ✅ 可编辑内容和变量")
print("   ✅ 可启用/禁用（is_enabled字段）")
print("   ✅ 预设了完整的模板内容")
print("   ✅ 支持所有常见变量")
