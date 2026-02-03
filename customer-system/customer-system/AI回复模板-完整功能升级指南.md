# 🎯 AI回复模板 - 完整功能升级指南

## 📋 升级概述

本次升级全面优化了AI回复模板管理系统，解决了以下核心问题：

1. ✅ **触发关键词智能显示** - 只在企业微信官方API时显示，第三方AI模型自动隐藏
2. ✅ **动态变量管理系统** - 支持新增自定义变量，颜色区分系统变量和自定义变量
3. ✅ **工单变量完整支持** - 新增9个工单相关变量
4. ✅ **测试发送功能增强** - 支持多种测试方式和变量预填充
5. ✅ **模板预览实时渲染** - 一键预览最终效果

---

## 🔍 问题1：触发关键词显示逻辑优化

### 问题描述
- ❌ **之前**：无论选择什么AI模型，都显示"触发关键词"字段
- ❌ **问题**：第三方AI模型（如腾讯混元）不需要触发关键词，只有企业微信官方API需要

### ✅ 解决方案

**新增智能判断逻辑**：
```javascript
// 计算属性：是否使用企业微信官方API
const isWeworkOfficialAPI = computed(() => {
  if (activeTab.value !== 'AI' && activeTab.value !== 'WORK_WECHAT') {
    return false
  }
  // 只有选择企业微信官方API时才返回true
  return templateForm.value.ai_model === 'wework-official' || 
         !templateForm.value.ai_model
})
```

**显示条件**：
```vue
<el-form-item 
  label="触发关键词" 
  v-if="templateForm.push_mode === 'realtime' && needsPushMode && isWeworkOfficialAPI"
>
```

### 效果对比

| AI模型 | 触发关键词字段 | 说明 |
|--------|--------------|------|
| 企业微信官方API | ✅ 显示 | 需要配置关键词触发 |
| 腾讯混元 | ❌ 隐藏 | 第三方AI自动处理，不需要关键词 |
| OpenAI | ❌ 隐藏 | 第三方AI自动处理，不需要关键词 |

---

## 🎨 问题2：动态变量管理系统

### 问题描述
- ❌ **之前**：变量列表固定，无法新增
- ❌ **问题**：如果需要新变量，必须修改代码

### ✅ 解决方案

#### 1. 新增"新增自定义变量"按钮

```vue
<el-button 
  type="primary" 
  size="small" 
  @click="showAddVariableDialog = true"
>
  ➕ 新增自定义变量
</el-button>
```

#### 2. 颜色区分系统变量和自定义变量

| 变量类型 | 颜色标签 | 说明 | 可删除 |
|---------|---------|------|--------|
| 系统变量 | 🔵 蓝色 (info) | 内置变量，不可删除 | ❌ |
| 自定义变量 | 🟢 绿色 (success) | 用户新增，可删除 | ✅ |

#### 3. 新增变量对话框

**对话框内容**：
```vue
<el-dialog title="新增自定义变量" width="450px">
  <el-form-item label="变量代码">
    <el-input 
      v-model="newVariableForm.code" 
      placeholder="如：ticket_id（不含大括号）"
    >
      <template #prepend>{</template>
      <template #append>}</template>
    </el-input>
  </el-form-item>
  <el-form-item label="变量名称">
    <el-input 
      v-model="newVariableForm.label" 
      placeholder="如：工单编号"
    ></el-input>
  </el-form-item>
</el-dialog>
```

#### 4. 变量存储逻辑

```javascript
// 系统内置变量（不可删除）
const systemVariables = [
  { code: '{customer_name}', label: '客户姓名', isCustom: false },
  { code: '{phone}', label: '联系电话', isCustom: false },
  // ...
]

// 用户自定义变量（可删除）
const customVariables = ref([])

// 所有变量合并
const allVariables = computed(() => {
  return [...systemVariables, ...customVariables.value]
})

// 新增自定义变量
const addCustomVariable = () => {
  const code = `{${newVariableForm.value.code.replace(/[{}]/g, '')}}`
  customVariables.value.push({
    code: code,
    label: newVariableForm.value.label,
    isCustom: true
  })
}

// 删除自定义变量
const removeCustomVariable = (code) => {
  const index = customVariables.value.findIndex(v => v.code === code)
  customVariables.value.splice(index, 1)
}
```

### 使用示例

**场景：需要新增"发货时间"变量**

1. 点击"➕ 新增自定义变量"
2. 填写：
   - 变量代码：`ship_time`
   - 变量名称：`发货时间`
3. 点击"添加"
4. 变量列表中出现 🟢 **发货时间** （绿色标签）
5. 点击即可插入到模板内容：`{ship_time}`
6. 不需要时可点击 ❌ 删除

---

## 🎫 问题3：工单变量完整支持

### 问题描述
- ❌ **之前**：没有工单相关变量
- ❌ **问题**：无法在模板中引用工单信息

### ✅ 解决方案

**新增9个工单相关变量**：

| 变量代码 | 变量名称 | 示例值 | 使用场景 |
|---------|---------|--------|---------|
| `{ticket_id}` | 工单编号 | #123 | 工单通知、催促提醒 |
| `{ticket_status}` | 工单状态 | 处理中 | 状态更新通知 |
| `{ticket_title}` | 工单标题 | 服务器无法连接 | 工单详情 |
| `{ticket_priority}` | 工单优先级 | 高 | 优先级提醒 |
| `{assigned_to}` | 负责人 | 李四 | 分配通知 |
| `{deadline}` | 处理期限 | 2026-02-04 15:30 | 超时提醒 |
| `{progress}` | 处理进度 | 75% | 进度更新 |
| `{pending_count}` | 待处理数量 | 3 | 每日工作提醒 |
| `{processing_count}` | 进行中数量 | 5 | 工作统计 |
| `{completed_count}` | 已完成数量 | 12 | 工作汇报 |

### 模板示例

#### 1️⃣ 工单分配通知模板

```
📋 工单分配通知

工单编号：{ticket_id}
工单标题：{ticket_title}
优先级：{ticket_priority}

负责人：{assigned_to}
处理期限：{deadline}
当前进度：{progress}

请及时处理！
```

#### 2️⃣ 每日工作提醒模板

```
🌅 今日工作提醒（{date}）

待处理工单：{pending_count} 个 ⚠️
进行中工单：{processing_count} 个 🔄
已完成工单：{completed_count} 个 ✅

请各位同事及时跟进！
```

#### 3️⃣ 工单超时催促模板

```
🚨 工单超时提醒

工单编号：{ticket_id}
问题描述：{ticket_title}
客户信息：{customer_name} ({phone})

处理期限：{deadline}
当前状态：{ticket_status}
负责人：{assigned_to}

请尽快处理！
```

---

## 🧪 问题4：测试发送功能增强

### 问题描述
- ❌ **之前**：测试发送只能填手机号
- ❌ **问题**：不同渠道需要不同的测试方式

### ✅ 解决方案

#### 1. 多种测试方式

| 测试方式 | 适用渠道 | 输入内容 |
|---------|---------|---------|
| 📱 手机号 | 短信、邮件、AI回复 | 13800138000 |
| 💬 微信OpenID | 微信公众号 | oXXXXXXXXXXXXXX |
| 👤 员工UserID | 企业微信 | zhangsan |
| 👥 选择客户 | AI回复 | 从客户列表选择 |
| 📢 选择群聊 | 群机器人 | 从群列表选择 |

#### 2. 变量预填充功能

**新增"变量预填充"区域**：

```vue
<el-divider>变量预填充（可选）</el-divider>
<el-form-item 
  v-for="variable in getTemplateVariables()"
  :label="getVariableName(variable)"
>
  <el-input 
    v-model="testForm.variableValues[variable]"
    :placeholder="'填写' + getVariableName(variable) + '的值'"
  ></el-input>
</el-form-item>
```

**效果**：
- 自动检测模板中使用的变量
- 为每个变量生成输入框
- 支持预填充测试数据
- 发送时自动替换变量

#### 3. 测试发送示例

**场景：测试工单分配通知模板**

1. 点击"测试发送"
2. 选择测试方式：📱 手机号
3. 输入测试手机号：`13800138000`
4. 填充变量：
   - 工单编号：`#123`
   - 工单标题：`服务器无法连接`
   - 负责人：`李四`
   - 处理期限：`2026-02-04 15:30`
5. 点击"确认发送"
6. ✅ 收到测试消息（变量已替换）

---

## 👁️ 问题5：模板预览功能

### 问题描述
- ❌ **之前**：只能保存后才能看到效果
- ❌ **问题**：需要反复修改调试

### ✅ 解决方案

#### 1. 模板预览按钮

**位置**：对话框底部左侧

```vue
<el-button 
  type="success" 
  @click="showTemplatePreview = true"
  :disabled="!templateForm.content"
>
  👁️ 模板预览
</el-button>
```

#### 2. 预览对话框

**展示效果**：
- 📱 手机界面风格
- 自动替换所有变量为示例数据
- 支持Markdown/HTML渲染
- 实时预览最终效果

#### 3. 变量示例数据

```javascript
const sampleData = {
  '{customer_name}': '张三',
  '{phone}': '13800138000',
  '{company}': 'XX科技有限公司',
  '{ticket_id}': '#123',
  '{ticket_status}': '处理中',
  '{ticket_title}': '服务器无法连接',
  '{assigned_to}': '李四',
  '{deadline}': '2026-02-04 15:30',
  '{progress}': '75%',
  // ...
}
```

#### 4. 预览效果

**原始模板**：
```
📋 工单分配通知

工单编号：{ticket_id}
客户：{customer_name}
问题：{ticket_title}
负责人：{assigned_to}
期限：{deadline}
```

**预览效果**：
```
📋 工单分配通知

工单编号：#123
客户：张三
问题：服务器无法连接
负责人：李四
期限：2026-02-04 15:30
```

---

## 🎯 完整使用流程

### 场景：创建工单超时提醒模板

#### 步骤1：新建模板

1. 进入"AI回复模板"标签页
2. 点击"+ 新建模板"
3. 填写基本信息：
   - 模板名称：`工单超时提醒`
   - 分类：`售后工单`
   - 模板类型：`纯文本`

#### 步骤2：选择AI模型

**选择：腾讯混元**
- ✅ "触发关键词"字段自动隐藏（第三方AI不需要）

**选择：企业微信官方API**
- ✅ "触发关键词"字段显示
- 填写：`超时,催促,提醒`

#### 步骤3：编写模板内容

1. 点击工单相关变量快速插入：
   - `{ticket_id}`
   - `{ticket_title}`
   - `{customer_name}`
   - `{assigned_to}`
   - `{deadline}`

2. 编写模板：
```
🚨 工单超时提醒

工单编号：{ticket_id}
问题描述：{ticket_title}
客户信息：{customer_name} ({phone})

处理期限：{deadline}
负责人：@{assigned_to}

请尽快处理！
```

#### 步骤4：新增自定义变量（可选）

**需求**：添加"超时时长"变量

1. 点击"➕ 新增自定义变量"
2. 填写：
   - 变量代码：`overdue_hours`
   - 变量名称：`超时时长`
3. 点击"添加"
4. 变量列表出现 🟢 **超时时长**
5. 点击插入到模板：
```
已超时：{overdue_hours} 小时
```

#### 步骤5：模板预览

1. 点击"👁️ 模板预览"
2. 查看最终效果（变量已替换）：

```
🚨 工单超时提醒

工单编号：#123
问题描述：服务器无法连接
客户信息：张三 (13800138000)

处理期限：2026-02-04 15:30
负责人：@李四
已超时：12 小时

请尽快处理！
```

3. 确认无误，关闭预览

#### 步骤6：测试发送

1. 点击"保存"
2. 在模板列表找到刚创建的模板
3. 点击"测试发送"
4. 选择测试方式：`👥 选择客户`
5. 选择测试客户：`张三 - 13800138000`
6. 填充变量（可选）：
   - 工单编号：`#123`
   - 超时时长：`12`
7. 点击"确认发送"
8. ✅ 测试成功

#### 步骤7：启用模板

1. 在模板列表中开启状态开关
2. ✅ 模板已启用，实时生效

---

## 📊 功能对比表

| 功能 | 升级前 | 升级后 |
|------|-------|-------|
| 触发关键词显示 | ❌ 所有AI模型都显示 | ✅ 只在企业微信API显示 |
| 变量管理 | ❌ 固定10个变量 | ✅ 19个系统变量 + 无限自定义 |
| 工单变量 | ❌ 无 | ✅ 9个工单变量 |
| 测试发送方式 | ❌ 只有手机号 | ✅ 5种测试方式 |
| 变量预填充 | ❌ 无 | ✅ 自动检测并生成输入框 |
| 模板预览 | ❌ 无 | ✅ 实时预览最终效果 |
| 变量删除 | ❌ 不可删除 | ✅ 自定义变量可删除 |
| 颜色区分 | ❌ 无 | ✅ 蓝色系统变量 / 绿色自定义变量 |

---

## 🚀 快速上手指南

### 1. 系统变量速查表

#### 基础客户信息
- `{customer_name}` - 客户姓名
- `{phone}` - 联系电话
- `{company}` - 公司名称

#### 订单信息
- `{order_no}` - 订单号
- `{product}` - 产品名称
- `{amount}` - 金额

#### 时间信息
- `{date}` - 日期
- `{time}` - 时间

#### 工单信息（新增）
- `{ticket_id}` - 工单编号
- `{ticket_status}` - 工单状态
- `{ticket_title}` - 工单标题
- `{ticket_priority}` - 工单优先级
- `{assigned_to}` - 负责人
- `{deadline}` - 处理期限
- `{progress}` - 处理进度
- `{pending_count}` - 待处理数量
- `{processing_count}` - 进行中数量
- `{completed_count}` - 已完成数量

### 2. 常用模板示例

#### 📋 工单创建通知
```
📋 新工单提醒

工单编号：{ticket_id}
客户：{customer_name} ({company})
联系方式：{phone}
问题描述：{ticket_title}

请及时处理！
```

#### ⚠️ 工单超时催促
```
🚨 超时提醒

工单 {ticket_id} 已超时
客户：{customer_name}
负责人：@{assigned_to}
期限：{deadline}

请尽快处理！
```

#### 📊 每日工作统计
```
📊 工作统计（{date}）

待处理：{pending_count} 个
进行中：{processing_count} 个
已完成：{completed_count} 个

继续加油！
```

---

## 🎓 最佳实践

### ✅ 推荐做法

1. **合理使用系统变量**
   - 优先使用系统变量（稳定可靠）
   - 只在系统变量不满足时新增自定义变量

2. **命名规范**
   - 变量代码使用英文下划线：`ticket_id`
   - 变量名称使用中文：`工单编号`

3. **模板编写**
   - 使用模板预览功能实时查看效果
   - 测试发送验证变量是否正确

4. **AI模型选择**
   - 企业微信官方API：需要配置触发关键词
   - 第三方AI（腾讯混元等）：无需触发关键词

### ❌ 避免做法

1. ❌ 重复创建相同的自定义变量
2. ❌ 使用中文作为变量代码
3. ❌ 不测试直接启用模板
4. ❌ 删除正在使用的自定义变量

---

## 📞 技术支持

**遇到问题？**

1. 查看本文档相关章节
2. 使用模板预览验证效果
3. 使用测试发送功能调试
4. 联系技术支持：XXX（企业微信：@管理员）

---

## 🎉 总结

本次升级实现了5大核心功能：

✅ **智能显示** - 触发关键词只在需要时显示  
✅ **动态管理** - 支持无限新增自定义变量  
✅ **工单支持** - 9个工单变量开箱即用  
✅ **测试增强** - 5种测试方式随心选择  
✅ **实时预览** - 一键预览最终效果

**现在开始使用，打造您的专属消息模板！** 🚀

---

**版本**：v2.0  
**更新日期**：2026-02-03  
**文档维护**：智能售后助手技术团队
