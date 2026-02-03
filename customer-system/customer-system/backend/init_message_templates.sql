-- =====================================================
-- 消息模板管理 - 预留模板初始化脚本
-- =====================================================
-- 说明：
-- 1. 本脚本创建所有预留模板（涵盖工单、项目、售后、售前等场景）
-- 2. 预留模板标记为 is_system=1（不可删除，只能禁用）
-- 3. 短信模板较少（用户说不重要）
-- 4. AI回复模板、企业微信、微信公众号模板较多
-- 5. 所有模板包含安全链接变量
-- =====================================================

-- 清空旧数据（可选，首次导入时注释掉）
-- DELETE FROM message_templates WHERE is_system = 1;

-- =====================================================
-- 1. 短信模板（少量，因为不重要）
-- =====================================================

-- 短信模板1：订单确认
INSERT INTO message_templates (
    name, channel, category, type, content, 
    status, is_system, push_mode, created_at, updated_at
) VALUES (
    '订单确认短信', 'SMS', '订单提醒', 'text',
    '【公司名】您的订单{order_no}已确认，金额{amount}元。查看详情：{detail_link}',
    1, 1, NULL, datetime('now'), datetime('now')
);

-- 短信模板2：物流通知
INSERT INTO message_templates (
    name, channel, category, type, content, 
    status, is_system, push_mode, created_at, updated_at
) VALUES (
    '物流发货短信', 'SMS', '物流通知', 'text',
    '【公司名】您的订单{order_no}已发货，快递单号{tracking_no}。查询物流：{detail_link}',
    1, 1, NULL, datetime('now'), datetime('now')
);

-- =====================================================
-- 2. AI回复模板（丰富，涵盖所有场景）
-- =====================================================

-- AI模板1：价格咨询
INSERT INTO message_templates (
    name, channel, category, type, content, ai_model, push_mode, keywords,
    status, is_system, created_at, updated_at
) VALUES (
    '💰 价格咨询AI回复', 'AI', 'AI回复模板', 'text',
    '您好！{customer_name}，感谢关注我们的{product}！

我们为您准备了三个价格方案：

🔷 基础版 - ￥3,999元
   适合个人用户和小企业
   包含：基础功能、免费更新

🔶 标准版 - ￥9,999元（推荐⭐⭐⭐）
   适合中小企业
   包含：完整功能、优先支持、定制化

🔴 旗舰版 - ￥29,999元
   适合大企业和定制需求
   包含：全部功能、24小时客服、专属账户管理

需要帮助选择？请联系{staff_name}：{staff_phone}
或点击了解详情：{detail_link}',
    'wework-official', 'realtime', '价格,报价,多少钱,费用,成本',
    1, 1, datetime('now'), datetime('now')
);

-- AI模板2：售后维修
INSERT INTO message_templates (
    name, channel, category, type, content, ai_model, push_mode, keywords,
    status, is_system, created_at, updated_at
) VALUES (
    '🔧 售后维修AI回复', 'AI', 'AI回复模板', 'text',
    '您好！我们已收到您的报修请求。

📋 工单信息：
工单编号：{ticket_id}
问题描述：{ticket_title}
优先级：{ticket_priority}

👨‍🔧 技术员信息：
负责人：{assigned_to}
预约时间：{deadline}

我们承诺：
✅ 2小时内响应
✅ 24小时内上门
✅ 修好为止

查看工单详情：{ticket_link}
如有疑问请联系：{staff_phone}',
    'wework-official', 'realtime', '维修,报修,坏了,故障,修理',
    1, 1, datetime('now'), datetime('now')
);

-- AI模板3：项目进度查询
INSERT INTO message_templates (
    name, channel, category, type, content, ai_model, push_mode, keywords,
    status, is_system, created_at, updated_at
) VALUES (
    '📊 项目进度查询', 'AI', 'AI回复模板', 'text',
    '您好！为您查询项目进度：

📌 项目名称：{project_name}
📋 项目编号：{project_id}
📈 当前状态：{project_status}
🎯 完成进度：{project_progress}
🏆 当前里程碑：{milestone}

查看详细进度：{project_link}
负责人：{staff_name}（{staff_phone}）

如需沟通项目细节，请点击联系我们：{feedback_link}',
    'wework-official', 'realtime', '项目,进度,状态,完成情况',
    1, 1, datetime('now'), datetime('now')
);

-- AI模板4：订单确认
INSERT INTO message_templates (
    name, channel, category, type, content, ai_model, push_mode, keywords,
    status, is_system, created_at, updated_at
) VALUES (
    '📦 订单确认AI回复', 'AI', 'AI回复模板', 'text',
    '您好！{customer_name}，您的订单已确认！

📋 订单详情：
订单号：{order_no}
产品：{product}
金额：￥{amount}
下单时间：{date} {time}

💳 支付方式：
请点击完成支付：{payment_link}

📦 配送信息：
预计3-5个工作日送达
查看物流：{detail_link}

感谢您的订购！有任何问题请联系客服：{staff_phone}',
    'wework-official', 'realtime', '订单,下单,购买,支付',
    1, 1, datetime('now'), datetime('now')
);

-- AI模板5：常见问题
INSERT INTO message_templates (
    name, channel, category, type, content, ai_model, push_mode, keywords,
    status, is_system, created_at, updated_at
) VALUES (
    '❓ 常见问题AI回复', 'AI', 'AI回复模板', 'text',
    '您好！关于{product}的问题，以下是常见解答：

1️⃣ 如何使用？
   详细使用文档：{detail_link}

2️⃣ 如何付费？
   支付流程：{payment_link}

3️⃣ 遇到问题怎么办？
   提交反馈：{feedback_link}
   联系客服：{staff_phone}

4️⃣ 售后支持：
   工单系统：{ticket_link}
   负责人：{staff_name}

需要人工帮助？请直接联系：{staff_phone}',
    'wework-official', 'realtime', '怎么样,如何,使用,功能,问题',
    1, 1, datetime('now'), datetime('now')
);

-- AI模板6：工单统计
INSERT INTO message_templates (
    name, channel, category, type, content, ai_model, push_mode, keywords,
    status, is_system, created_at, updated_at
) VALUES (
    '📊 工单数据统计', 'AI', 'AI回复模板', 'text',
    '您好！为您查询工单统计数据：

📅 查询日期：{date}

📊 工单概况：
待处理：{pending_count} 个 ⚠️
处理中：{processing_count} 个 🔄
已完成：{completed_count} 个 ✅

🔥 您的待办工单：
- 工单 {ticket_id}：{ticket_title}
  状态：{ticket_status}
  进度：{progress}
  期限：{deadline}

查看所有工单：{ticket_link}
需要帮助请联系：{staff_name}（{staff_phone}）',
    'wework-official', 'realtime', '统计,数据,报表,工单数量',
    1, 1, datetime('now'), datetime('now')
);

-- AI模板7：预约提醒
INSERT INTO message_templates (
    name, channel, category, type, content, ai_model, push_mode, keywords,
    status, is_system, created_at, updated_at
) VALUES (
    '⏰ 预约提醒AI回复', 'AI', 'AI回复模板', 'text',
    '您好！{customer_name}，您有一个预约即将到期：

⏰ 预约时间：{deadline}
👨‍🔧 技术员：{assigned_to}
📋 服务内容：{ticket_title}
🏢 服务地址：{company}

📞 联系方式：
技术员电话：{staff_phone}
客服热线：{phone}

❗ 如需改约请提前联系我们
查看详情：{ticket_link}
提交反馈：{feedback_link}',
    'wework-official', 'realtime', '预约,时间,什么时候,排期',
    1, 1, datetime('now'), datetime('now')
);

-- AI模板8：咨询转接
INSERT INTO message_templates (
    name, channel, category, type, content, ai_model, push_mode, keywords,
    status, is_system, created_at, updated_at
) VALUES (
    '💬 咨询转接AI回复', 'AI', 'AI回复模板', 'text',
    '您好！我是AI客服助手，很高兴为您服务。

由于您的问题需要人工处理，已为您安排专属客服：

👤 负责人：{staff_name}
📞 联系电话：{staff_phone}
🏢 所属部门：{department}

您也可以：
📋 创建工单：{ticket_link}
💬 在线反馈：{feedback_link}
📊 查看项目：{project_link}

我们将在1小时内回复您，请保持电话畅通！',
    'wework-official', 'realtime', '转接,人工,客服,销售代表',
    1, 1, datetime('now'), datetime('now')
);

-- AI模板9：活动推广
INSERT INTO message_templates (
    name, channel, category, type, content, ai_model, push_mode, keywords,
    status, is_system, created_at, updated_at
) VALUES (
    '🎁 活动推广AI回复', 'AI', 'AI回复模板', 'text',
    '🎉 限时优惠活动来啦！

📣 活动主题：新年大促
💰 优惠力度：全场8折
🎫 优惠券码：NEWYEAR2026
⏰ 活动时间：{date}截止

🔥 热销产品推荐：
1. {product} - 原价￥{amount}
2. 智能客服系统 - 限时特惠
3. 售后管理平台 - 买一送一

💳 立即购买：{payment_link}
📖 活动详情：{detail_link}

分享好友赚奖励：{feedback_link}
客服咨询：{staff_phone}',
    'wework-official', 'realtime', '活动,促销,优惠,打折,特价',
    1, 1, datetime('now'), datetime('now')
);

-- AI模板10：售前咨询
INSERT INTO message_templates (
    name, channel, category, type, content, ai_model, push_mode, keywords,
    status, is_system, created_at, updated_at
) VALUES (
    '📞 售前咨询AI回复', 'AI', 'AI回复模板', 'text',
    '您好！{customer_name}，感谢咨询{product}！

我是您的专属顾问{staff_name}，很高兴为您服务。

📋 产品介绍：
{product} - 企业级智能解决方案
✅ 功能全面，简单易用
✅ 7×24小时技术支持
✅ 按需定制，灵活部署

💰 价格方案：
基础版：￥3,999起
企业版：￥9,999起
旗舰版：按需报价

📖 了解详情：{detail_link}
📞 电话咨询：{staff_phone}
💬 在线沟通：{feedback_link}

立即购买享8折优惠：{payment_link}',
    'wework-official', 'realtime', '咨询,了解,介绍,推荐',
    1, 1, datetime('now'), datetime('now')
);

-- =====================================================
-- 3. 企业微信模板（工单、项目、内部通知）
-- =====================================================

-- 企业微信模板1：工单创建通知
INSERT INTO message_templates (
    name, channel, category, type, content, 
    push_mode, targets, status, is_system, created_at, updated_at
) VALUES (
    '🟡 工单创建通知', 'WORK_WECHAT', '售后工单', 'text',
    '🟡 【新工单提醒】{ticket_id}

**客户信息**
> 客户：{customer_name}
> 公司：{company}
> 联系：{phone}

**工单详情**
> 产品/项目：{product}
> 问题描述：{ticket_title}
> 优先级：{ticket_priority}
> 提交时间：{date} {time}

**处理状态**
> 当前状态：待分配
> 负责人：{assigned_to}
> 处理进度：{progress}
> 处理期限：⏰ {deadline}

---
💬 请负责人在本消息下回复处理进度
✅ 回复"已解决"可自动关闭工单
📋 回复"分配给@某人"可转交工单
📊 查看详情：{ticket_link}

🆘 请在{deadline}前处理',
    'realtime', '["all_members"]', 1, 1, datetime('now'), datetime('now')
);

-- 企业微信模板2：工单超时提醒
INSERT INTO message_templates (
    name, channel, category, type, content, 
    push_mode, targets, status, is_system, created_at, updated_at
) VALUES (
    '🚨 工单超时提醒', 'WORK_WECHAT', '售后工单', 'text',
    '🚨 【工单超时提醒】

工单编号：{ticket_id}
客户：{customer_name} ({phone})
问题：{ticket_title}

当前状态：{ticket_status}
负责人：{assigned_to}
处理进度：{progress}

⏰ 处理期限：{deadline}
⏱️  已超时：12 小时
🔔 催促次数：第 1 次

@{assigned_to} 请尽快处理！

---
💡 回复 "#{ticket_id} 已解决" 可关闭工单
💡 回复 "#{ticket_id} 升级处理" 可升级工单
📊 查看详情：{ticket_link}',
    'realtime', '["all_members"]', 1, 1, datetime('now'), datetime('now')
);

-- 企业微信模板3：项目进度更新
INSERT INTO message_templates (
    name, channel, category, type, content, 
    push_mode, targets, status, is_system, created_at, updated_at
) VALUES (
    '📈 项目进度更新通知', 'WORK_WECHAT', '项目管理', 'text',
    '📈 【项目进度更新】

项目名称：{project_name}
项目编号：{project_id}

📊 进度情况：
当前状态：{project_status}
完成进度：{project_progress}
当前里程碑：{milestone}

👥 项目团队：
负责人：{staff_name}
部门：{department}
联系方式：{staff_phone}

📅 时间节点：
更新时间：{date} {time}

---
📖 查看项目详情：{project_link}
💬 项目讨论：{feedback_link}

请各位同事知悉！',
    'realtime', '["all_members"]', 1, 1, datetime('now'), datetime('now')
);

-- 企业微信模板4：每日工作汇报
INSERT INTO message_templates (
    name, channel, category, type, content, 
    push_mode, schedule_time, repeat_type, targets,
    status, is_system, created_at, updated_at
) VALUES (
    '📊 每日工作数据汇报', 'WORK_WECHAT', '数据统计', 'text',
    '📊 【每日工作汇报】{date}

🎯 工单数据：
待处理工单：{pending_count} 个 ⚠️
进行中工单：{processing_count} 个 🔄
已完成工单：{completed_count} 个 ✅

📈 项目数据：
进行中项目：5 个
本周完成：2 个
整体进度：{project_progress}

👥 团队协作：
部门：{department}
负责人：{staff_name}

---
📋 查看详细数据：{detail_link}
📊 工单管理：{ticket_link}
📈 项目看板：{project_link}

各位同事请及时跟进！',
    'scheduled', '2026-02-03 09:00:00', 'daily', '["all_members"]',
    1, 1, datetime('now'), datetime('now')
);

-- 企业微信模板5：客户反馈通知
INSERT INTO message_templates (
    name, channel, category, type, content, 
    push_mode, targets, status, is_system, created_at, updated_at
) VALUES (
    '💬 客户反馈通知', 'WORK_WECHAT', '客户服务', 'text',
    '💬 【新客户反馈】

客户信息：
姓名：{customer_name}
公司：{company}
电话：{phone}

反馈内容：
{ticket_title}

反馈时间：{date} {time}
反馈渠道：企业微信

---
📋 创建工单跟进：{ticket_link}
💬 查看反馈详情：{feedback_link}

@{staff_name} 请及时回复客户',
    'realtime', '["dept_service"]', 1, 1, datetime('now'), datetime('now')
);

-- =====================================================
-- 4. 微信公众号模板（客户通知、营销推广）
-- =====================================================

-- 公众号模板1：订单确认
INSERT INTO message_templates (
    name, channel, category, type, content, 
    push_mode, targets, status, is_system, created_at, updated_at
) VALUES (
    '📦 订单确认通知', 'WECHAT', '订单提醒', 'text',
    '您好！{customer_name}

您的订单已确认成功！

📋 订单信息：
订单号：{order_no}
产品：{product}
金额：￥{amount}
下单时间：{date} {time}

💳 支付状态：待支付
点击完成支付：{payment_link}

📦 物流信息：
预计3-5个工作日送达
查看物流：{detail_link}

感谢您的支持！有问题请联系客服：{staff_phone}',
    'realtime', '["all_fans"]', 1, 1, datetime('now'), datetime('now')
);

-- 公众号模板2：售后服务
INSERT INTO message_templates (
    name, channel, category, type, content, 
    push_mode, targets, status, is_system, created_at, updated_at
) VALUES (
    '🔧 售后服务通知', 'WECHAT', '售后工单', 'text',
    '您好！{customer_name}

您的售后服务已安排：

📋 工单编号：{ticket_id}
问题描述：{ticket_title}
优先级：{ticket_priority}

👨‍🔧 服务人员：
姓名：{assigned_to}
电话：{staff_phone}
预约时间：{deadline}

我们承诺：
✅ 准时上门服务
✅ 问题一次解决
✅ 服务满意为止

查看工单详情：{ticket_link}
服务评价：{feedback_link}

感谢您的信任！',
    'realtime', '["purchased"]', 1, 1, datetime('now'), datetime('now')
);

-- 公众号模板3：活动推广
INSERT INTO message_templates (
    name, channel, category, type, content, 
    push_mode, schedule_time, targets, status, is_system, created_at, updated_at
) VALUES (
    '🎁 限时活动推广', 'WECHAT', '营销推广', 'text',
    '🎉 {customer_name}，好消息来啦！

📣 限时优惠活动：
{product} 新年大促

💰 优惠内容：
全场8折优惠
额外赠送3个月VIP
前100名送精美礼品

🎫 专属优惠码：
NEWYEAR2026（限时有效）

⏰ 活动时间：
截止日期：{date}

💳 立即抢购：{payment_link}
📖 活动详情：{detail_link}

分享好友各得50元红包：{feedback_link}

数量有限，先到先得！',
    'scheduled', '2026-02-03 10:00:00', '["all_fans","vip"]', 1, 1, datetime('now'), datetime('now')
);

-- 公众号模板4：会员福利
INSERT INTO message_templates (
    name, channel, category, type, content, 
    push_mode, targets, status, is_system, created_at, updated_at
) VALUES (
    '⭐ VIP会员专享福利', 'WECHAT', '会员服务', 'text',
    '⭐ 尊贵的{customer_name}会员，您好！

🎁 本月专属福利已到账：

1️⃣ 消费积分 +1000 分
2️⃣ 优惠券包（价值￥200）
3️⃣ 专属客服通道
4️⃣ 生日礼物定制

💳 会员权益：
当前等级：VIP黄金会员
累计消费：￥{amount}
剩余积分：5000 分

📖 查看权益详情：{detail_link}
🎁 兑换积分礼品：{payment_link}

💬 专属客服：{staff_name}（{staff_phone}）

感谢您的长期支持！',
    'realtime', '["vip"]', 1, 1, datetime('now'), datetime('now')
);

-- =====================================================
-- 5. 群机器人模板（内部协作）
-- =====================================================

-- 群机器人模板1：工单提醒
INSERT INTO message_templates (
    name, channel, category, type, content, 
    push_mode, targets, status, is_system, created_at, updated_at
) VALUES (
    '📢 群机器人-工单提醒', 'GROUP_BOT', '售后工单', 'text',
    '📢 【工单催办提醒】

@{assigned_to} 您有工单待处理！

工单编号：{ticket_id}
客户：{customer_name}（{phone}）
问题：{ticket_title}
期限：{deadline}
当前进度：{progress}

请尽快处理，点击查看：{ticket_link}',
    'realtime', '["internal_work","tech_support"]', 1, 1, datetime('now'), datetime('now')
);

-- 群机器人模板2：每日数据
INSERT INTO message_templates (
    name, channel, category, type, content, 
    push_mode, schedule_time, repeat_type, targets,
    status, is_system, created_at, updated_at
) VALUES (
    '📊 群机器人-每日数据播报', 'GROUP_BOT', '数据统计', 'text',
    '📊 【每日数据播报】{date}

工单统计：
待处理：{pending_count} 个
处理中：{processing_count} 个
已完成：{completed_count} 个

查看详情：{ticket_link}

各位同事辛苦了！💪',
    'scheduled', '2026-02-03 18:00:00', 'daily', '["internal_work"]',
    1, 1, datetime('now'), datetime('now')
);

-- =====================================================
-- 统计信息
-- =====================================================
-- 短信模板：2个
-- AI回复模板：10个（价格、售后、项目、订单、常见问题、工单统计、预约、转接、活动、售前）
-- 企业微信模板：5个（工单创建、工单超时、项目进度、每日汇报、客户反馈）
-- 微信公众号模板：4个（订单确认、售后服务、活动推广、会员福利）
-- 群机器人模板：2个（工单提醒、每日数据）
-- 总计：23个预留模板
-- =====================================================

-- 验证导入
SELECT 
    channel as '渠道',
    COUNT(*) as '模板数量'
FROM message_templates 
WHERE is_system = 1
GROUP BY channel
ORDER BY COUNT(*) DESC;
