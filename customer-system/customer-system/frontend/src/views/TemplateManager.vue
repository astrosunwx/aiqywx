<template>
  <div class="template-manager">
    <el-card>
      <template #header>
        <div class="header-actions">
          <h2>📝 消息模板管理</h2>
          <el-button type="primary" @click="showCreateDialog">+ 新建模板</el-button>
        </div>
      </template>

      <!-- 模板分类标签页 -->
      <el-tabs v-model="activeTab">
        <el-tab-pane label="📱 短信模板" name="SMS"></el-tab-pane>
        <el-tab-pane label="📧 邮件模板" name="EMAIL"></el-tab-pane>
        <el-tab-pane label="💬 微信公众号" name="WECHAT"></el-tab-pane>
        <el-tab-pane label="🏢 企业微信" name="WORK_WECHAT"></el-tab-pane>
        <el-tab-pane label="🤖 AI回复模板" name="AI"></el-tab-pane>
        <el-tab-pane label="📢 群机器人" name="GROUP_BOT"></el-tab-pane>
      </el-tabs>

      <!-- 模板列表 -->
      <el-table :data="filteredTemplates" border style="margin-top: 20px;">
        <el-table-column prop="id" label="模板ID" width="80"></el-table-column>
        <el-table-column prop="name" label="模板名称"></el-table-column>
        <el-table-column prop="category" label="分类" width="120"></el-table-column>
        <el-table-column prop="type" label="类型" width="100"></el-table-column>
        <el-table-column label="推送模式" width="120" v-if="needsPushMode">
          <template #default="scope">
            <el-tag v-if="scope.row.push_mode === 'realtime'" type="success" size="small">⚡ 实时</el-tag>
            <el-tag v-else-if="scope.row.push_mode === 'scheduled'" type="warning" size="small">⏰ 定时</el-tag>
            <el-tag v-else type="info" size="small">-</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-switch v-model="scope.row.status" @change="toggleStatus(scope.row)"></el-switch>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250">
          <template #default="scope">
            <el-button size="small" @click="editTemplate(scope.row)">编辑</el-button>
            <el-button 
              v-if="canTestSend" 
              size="small" 
              type="primary"
              @click="testSend(scope.row)"
            >
              测试发送
            </el-button>
            <el-button 
              size="small" 
              type="danger"
              @click="deleteTemplate(scope.row)"
              :disabled="scope.row.is_system"
            >
              {{ scope.row.is_system ? '🔒 禁用' : '删除' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑模板对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑模板' : '新建模板'"
      width="600px"
    >
      <el-form :model="templateForm" label-width="100px" :rules="templateRules" ref="templateFormRef">
        <el-form-item label="模板名称" required prop="name">
          <el-input v-model="templateForm.name" placeholder="请输入模板名称">
            <template #prefix>
              <span style="color: #409eff;">📝</span>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="分类" required prop="category">
          <el-select v-model="templateForm.category" placeholder="选择或输入分类" filterable allow-create style="width: 100%;">
            <el-option label="📱 客户通知" value="客户通知"></el-option>
            <el-option label="📦 订单提醒" value="订单提醒"></el-option>
            <el-option label="🔧 售后工单" value="售后工单"></el-option>
            <el-option label="💰 支付提醒" value="支付提醒"></el-option>
            <el-option label="🚚 物流通知" value="物流通知"></el-option>
            <el-option label="🤖 AI智能回复" value="AI回复模板"></el-option>
            <el-option label="📢 营销推广" value="营销推广"></el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="模板类型">
          <el-radio-group v-model="templateForm.type">
            <el-radio label="text">纯文本</el-radio>
            <el-radio label="markdown">Markdown</el-radio>
            <el-radio label="html">HTML</el-radio>
          </el-radio-group>
          <el-button 
            v-if="templateForm.type !== 'text' && templateForm.content" 
            type="text" 
            size="small" 
            @click="showPreview = !showPreview"
            style="margin-left: 10px;"
          >
            {{ showPreview ? '隐藏预览' : '👁️ 实时预览' }}
          </el-button>
        </el-form-item>

        <el-form-item label="模板内容" required prop="content">
          <div style="width: 100%;">
            <el-input 
              v-model="templateForm.content" 
              type="textarea" 
              :rows="8"
              placeholder="请输入模板内容，支持变量 {customer_name}、{phone} 等"
            ></el-input>
            <div style="background: #f5f7fa; padding: 10px; margin-top: 5px; border-radius: 4px; font-size: 12px;">
              <div style="color: #606266; margin-bottom: 5px;"><strong>💡 支持的变量：</strong></div>
              <div style="color: #909399; line-height: 1.8;">
                <code>{customer_name}</code> - 客户姓名 |
                <code>{phone}</code> - 联系电话 |
                <code>{order_no}</code> - 订单号 |
                <code>{product}</code> - 产品名称 |
                <code>{date}</code> - 日期 |
                <code>{amount}</code> - 金额
              </div>
            </div>
            <!-- 预览区域 -->
            <div v-if="showPreview && templateForm.type !== 'text'" style="margin-top: 10px; padding: 10px; border: 1px solid #dcdfe6; border-radius: 4px; background: white;">
              <div style="color: #909399; font-size: 12px; margin-bottom: 5px;">预览效果：</div>
              <div 
                v-if="templateForm.type === 'markdown'" 
                v-html="renderMarkdown(templateForm.content)"
                style="padding: 10px; background: #fafafa;"
              ></div>
              <div 
                v-if="templateForm.type === 'html'" 
                v-html="templateForm.content"
                style="padding: 10px; background: #fafafa;"
              ></div>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="AI模型" v-if="activeTab === 'AI'">
          <el-select v-model="templateForm.ai_model" placeholder="腾讯云混元A13B" style="width: 100%;">
            <el-option 
              v-for="model in aiModels" 
              :key="model.value"
              :label="model.label"
              :value="model.value"
            >
              <span>{{ model.label }}</span>
              <el-tag 
                v-if="model.is_official" 
                type="success" 
                size="small" 
                style="margin-left: 10px;"
              >
                ✅官方API
              </el-tag>
              <el-tag 
                v-if="model.is_default" 
                type="primary" 
                size="small" 
                style="margin-left: 5px;"
              >
                ⭐默认
              </el-tag>
            </el-option>
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            默认使用最近配置的AI模型
          </div>
        </el-form-item>

        <!-- 推送模式（群机器人/AI回复/企业微信/微信公众号显示） -->
        <el-form-item label="推送模式" v-if="needsPushMode" required prop="push_mode">
          <el-radio-group v-model="templateForm.push_mode" @change="onPushModeChange">
            <el-radio label="realtime" v-if="supportsRealtime">
              <span>⚡ 实时推送</span>
              <el-tooltip content="关键词触发立即响应，适合客服对话" placement="top">
                <el-icon style="margin-left: 5px; color: #909399;"><QuestionFilled /></el-icon>
              </el-tooltip>
            </el-radio>
            <el-radio label="scheduled" v-if="supportsScheduled">
              <span>⏰ 定时推送</span>
              <el-tooltip content="按计划时间发送，适合通知/日报" placement="top">
                <el-icon style="margin-left: 5px; color: #909399;"><QuestionFilled /></el-icon>
              </el-tooltip>
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 触发关键词（实时推送时显示） -->
        <el-form-item 
          label="触发关键词" 
          v-if="templateForm.push_mode === 'realtime' && needsPushMode"
          required
          prop="keywords"
        >
          <el-input 
            v-model="templateForm.keywords" 
            placeholder="多个关键词用逗号分隔，如：价格,报价,咨询"
          >
            <template #prefix>
              <span style="color: #409eff;">🔑</span>
            </template>
          </el-input>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            💡 客户消息包含任一关键词时触发自动回复
          </div>
        </el-form-item>

        <!-- 目标选择（根据不同模板类型显示） -->
        <el-form-item 
          label="发送对象" 
          v-if="needsTargetSelection"
          required
          prop="targets"
        >
          <!-- 群机器人 -->
          <el-select 
            v-if="activeTab === 'GROUP_BOT'"
            v-model="templateForm.targets" 
            placeholder="选择目标群聊"
            multiple
            collapse-tags
            style="width: 100%;"
          >
            <el-option label="📢 内部工作群" value="internal_work"></el-option>
            <el-option label="📢 技术支持群" value="tech_support"></el-option>
            <el-option label="📢 销售团队群" value="sales_team"></el-option>
            <el-option label="📢 客户服务群" value="customer_service"></el-option>
          </el-select>
          
          <!-- 企业微信 -->
          <el-select 
            v-else-if="activeTab === 'WORK_WECHAT'"
            v-model="templateForm.targets" 
            placeholder="选择发送对象"
            multiple
            collapse-tags
            style="width: 100%;"
          >
            <el-option label="👥 全体成员" value="all_members"></el-option>
            <el-option label="👔 销售部门" value="dept_sales"></el-option>
            <el-option label="🔧 技术部门" value="dept_tech"></el-option>
            <el-option label="📞 客服部门" value="dept_service"></el-option>
            <el-option label="🏷️ 客户标签" value="customer_tags"></el-option>
          </el-select>
          
          <!-- 微信公众号 -->
          <el-select 
            v-else-if="activeTab === 'WECHAT'"
            v-model="templateForm.targets" 
            placeholder="选择发送对象"
            multiple
            collapse-tags
            style="width: 100%;"
          >
            <el-option label="📱 全部粉丝" value="all_fans"></el-option>
            <el-option label="🏷️ 已购买客户" value="purchased"></el-option>
            <el-option label="🏷️ VIP会员" value="vip"></el-option>
            <el-option label="🏷️ 活跃粉丝" value="active"></el-option>
          </el-select>
          
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            {{ getTargetTip() }}
          </div>
        </el-form-item>

        <!-- 定时配置（定时推送时显示） -->
        <div v-if="templateForm.push_mode === 'scheduled' && needsPushMode">
          <el-form-item label="发送时间" required prop="schedule_time">
            <el-date-picker
              v-model="templateForm.schedule_time"
              type="datetime"
              placeholder="选择发送时间"
              :disabled-date="disabledDate"
              :disabled-hours="() => disabledHours"
              style="width: 100%;"
            >
            </el-date-picker>
            <div style="color: #909399; font-size: 12px; margin-top: 5px;">
              {{ getScheduleTimeTip() }}
            </div>
          </el-form-item>

          <el-form-item label="重复周期">
            <el-select v-model="templateForm.repeat_type" placeholder="选择重复周期" style="width: 100%;">
              <el-option label="🔄 一次性" value="once"></el-option>
              <el-option label="📆 每天" value="daily"></el-option>
              <el-option label="📅 每周" value="weekly"></el-option>
              <el-option label="🗓️ 每月" value="monthly"></el-option>
            </el-select>
            <div style="color: #909399; font-size: 12px; margin-top: 5px;">
              💡 选择重复周期后，将按设定时间定期发送
            </div>
          </el-form-item>

          <!-- 每周重复时选择星期 -->
          <el-form-item label="选择星期" v-if="templateForm.repeat_type === 'weekly'">
            <el-checkbox-group v-model="templateForm.repeat_days">
              <el-checkbox label="1">周一</el-checkbox>
              <el-checkbox label="2">周二</el-checkbox>
              <el-checkbox label="3">周三</el-checkbox>
              <el-checkbox label="4">周四</el-checkbox>
              <el-checkbox label="5">周五</el-checkbox>
              <el-checkbox label="6">周六</el-checkbox>
              <el-checkbox label="0">周日</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </div>

        <!-- 快速插入变量 -->
        <el-form-item label="快速插入">
          <div style="display: flex; flex-wrap: wrap; gap: 8px;">
            <el-tag 
              v-for="variable in commonVariables" 
              :key="variable.code"
              style="cursor: pointer;"
              @click="insertVariable(variable.code)"
            >
              {{ variable.label }}
            </el-tag>
          </div>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            💡 点击变量快速插入到模板内容中
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <div style="display: flex; justify-content: flex-end; width: 100%; gap: 10px;">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveTemplate" :loading="saving">
            {{ saving ? '保存中...' : '保存' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 测试发送对话框 -->
    <el-dialog
      v-model="testDialogVisible"
      title="测试发送"
      width="500px"
    >
      <el-form :model="testForm" label-width="100px">
        <el-form-item label="模板名称">
          <el-input v-model="testForm.templateName" disabled></el-input>
        </el-form-item>
        
        <el-form-item label="测试对象" v-if="activeTab === 'GROUP_BOT'">
          <el-select v-model="testForm.testTarget" placeholder="选择测试群聊" style="width: 100%;">
            <el-option label="📢 内部工作群" value="internal_work"></el-option>
            <el-option label="📢 技术支持群" value="tech_support"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="测试手机号" v-else>
          <el-input v-model="testForm.testPhone" placeholder="输入测试手机号"></el-input>
        </el-form-item>
        
        <el-alert
          title="测试消息将立即发送到指定对象"
          type="warning"
          :closable="false"
          style="margin-top: 10px;"
        >
        </el-alert>
      </el-form>
      
      <template #footer>
        <div style="display: flex; justify-content: flex-end; gap: 10px;">
          <el-button @click="testDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmTestSend" :loading="testSending">
            {{ testSending ? '发送中...' : '确认发送' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { QuestionFilled } from '@element-plus/icons-vue'
import axios from 'axios'

const activeTab = ref('SMS')
const dialogVisible = ref(false)
const isEdit = ref(false)
const templates = ref([])
const aiModels = ref([])
const showPreview = ref(false)
const saving = ref(false)
const templateFormRef = ref(null)
const testDialogVisible = ref(false)
const testSending = ref(false)

const templateForm = ref({
  id: null,
  name: '',
  category: '',
  type: 'text',
  content: '',
  ai_model: 'wework-official',
  push_mode: 'realtime',
  keywords: '',
  targets: [],
  schedule_time: null,
  repeat_type: 'once',
  repeat_days: [],
  status: true,
  variables: []
})

const testForm = ref({
  templateName: '',
  testTarget: '',
  testPhone: ''
})

// 常用变量列表
const commonVariables = [
  { code: '{customer_name}', label: '客户姓名' },
  { code: '{phone}', label: '联系电话' },
  { code: '{order_no}', label: '订单号' },
  { code: '{product}', label: '产品名称' },
  { code: '{date}', label: '日期' },
  { code: '{time}', label: '时间' },
  { code: '{amount}', label: '金额' },
  { code: '{company}', label: '公司名称' },
  { code: '{contact}', label: '联系人' },
  { code: '{address}', label: '地址' }
]

// 计算属性：是否需要推送模式选择
const needsPushMode = computed(() => {
  return ['GROUP_BOT', 'AI', 'WORK_WECHAT', 'WECHAT'].includes(activeTab.value)
})

// 计算属性：是否支持实时推送
const supportsRealtime = computed(() => {
  return ['GROUP_BOT', 'AI', 'WORK_WECHAT', 'WECHAT'].includes(activeTab.value)
})

// 计算属性：是否支持定时推送
const supportsScheduled = computed(() => {
  return ['GROUP_BOT', 'AI', 'WORK_WECHAT', 'WECHAT'].includes(activeTab.value)
})

// 计算属性：是否需要目标选择
const needsTargetSelection = computed(() => {
  return ['GROUP_BOT', 'WORK_WECHAT', 'WECHAT'].includes(activeTab.value)
})

// 计算属性：是否可以测试发送
const canTestSend = computed(() => {
  return ['GROUP_BOT', 'AI', 'WORK_WECHAT', 'WECHAT'].includes(activeTab.value)
})

// 表单校验规则
const templateRules = {
  name: [
    { required: true, message: '请输入模板名称', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择或输入分类', trigger: 'change' }
  ],
  content: [
    { required: true, message: '请输入模板内容', trigger: 'blur' }
  ],
  push_mode: [
    { required: true, message: '请选择推送模式', trigger: 'change' }
  ],
  keywords: [
    { 
      validator: (rule, value, callback) => {
        if (templateForm.value.push_mode === 'realtime' && needsPushMode.value && !value) {
          callback(new Error('实时推送必须填写触发关键词'))
        } else {
          callback()
        }
      }, 
      trigger: 'blur' 
    }
  ],
  targets: [
    { 
      validator: (rule, value, callback) => {
        if (needsTargetSelection.value && (!value || value.length === 0)) {
          callback(new Error('请选择发送对象'))
        } else {
          callback()
        }
      }, 
      trigger: 'change' 
    }
  ],
  schedule_time: [
    { 
      validator: (rule, value, callback) => {
        if (templateForm.value.push_mode === 'scheduled' && !value) {
          callback(new Error('定时推送必须选择发送时间'))
        } else if (value && new Date(value) <= new Date()) {
          callback(new Error('发送时间必须大于当前时间'))
        } else {
          callback()
        }
      }, 
      trigger: 'change' 
    }
  ]
}

// 简单的Markdown渲染（仅用于预览）
const renderMarkdown = (text) => {
  if (!text) return ''
  return text
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/\n/gim, '<br>')
}

// 禁用过去的日期
const disabledDate = (time) => {
  return time.getTime() < Date.now() - 8.64e7
}

// 禁用过去的小时
const disabledHours = []

// 推送模式变化时的处理
const onPushModeChange = (mode) => {
  if (mode === 'realtime') {
    templateForm.value.schedule_time = null
    templateForm.value.repeat_type = 'once'
  } else if (mode === 'scheduled') {
    templateForm.value.keywords = ''
  }
}

// 获取目标选择提示
const getTargetTip = () => {
  if (activeTab.value === 'GROUP_BOT') {
    return '💡 可选择多个群聊同时发送'
  } else if (activeTab.value === 'WORK_WECHAT') {
    return '💡 支持按部门、标签筛选成员'
  } else if (activeTab.value === 'WECHAT') {
    return '⚠️ 公众号群发每天限制1次'
  }
  return ''
}

// 获取定时时间提示
const getScheduleTimeTip = () => {
  if (activeTab.value === 'WECHAT') {
    return '⚠️ 微信公众号定时时间不得超过7天'
  }
  return '💡 发送时间必须大于当前时间'
}

// 插入变量到模板内容
const insertVariable = (variableCode) => {
  if (!templateForm.value.content) {
    templateForm.value.content = variableCode
  } else {
    templateForm.value.content += ' ' + variableCode
  }
  ElMessage.success(`已插入变量 ${variableCode}`)
}

// 测试发送
const testSend = (row) => {
  testForm.value.templateName = row.name
  testForm.value.testTarget = ''
  testForm.value.testPhone = ''
  testDialogVisible.value = true
}

// 确认测试发送
const confirmTestSend = async () => {
  if (activeTab.value === 'GROUP_BOT' && !testForm.value.testTarget) {
    ElMessage.warning('请选择测试群聊')
    return
  }
  if (activeTab.value !== 'GROUP_BOT' && !testForm.value.testPhone) {
    ElMessage.warning('请输入测试手机号')
    return
  }
  
  testSending.value = true
  try {
    // 模拟发送延迟
    await new Promise(resolve => setTimeout(resolve, 1500))
    ElMessage.success('✅ 测试消息已发送成功')
    testDialogVisible.value = false
  } catch (error) {
    ElMessage.error('❌ 测试发送失败')
  } finally {
    testSending.value = false
  }
}

// 加载AI模型列表
const loadAIModels = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/admin/ai-models/active')
    aiModels.value = response.data.map(model => ({
      value: model.model_code,
      label: model.model_name,
      is_official: model.is_official,
      is_default: model.is_default
    }))
  } catch (error) {
    console.error('加载AI模型失败:', error)
    // 使用默认值
    aiModels.value = [
      { 
        value: 'wework-official', 
        label: '企业微信官方API', 
        is_official: true, 
        is_default: true 
      }
    ]
  }
}

const filteredTemplates = computed(() => {
  return templates.value.filter(t => {
    if (activeTab.value === 'SMS') return ['订单通知', '发货通知', '退款通知'].includes(t.category)
    if (activeTab.value === 'EMAIL') return ['邮件营销', '邮件通知'].includes(t.category)
    if (activeTab.value === 'WECHAT') return t.category.includes('公众号')
    if (activeTab.value === 'WORK_WECHAT') return t.category.includes('企业微信')
    if (activeTab.value === 'AI') return t.category.includes('AI回复')
    if (activeTab.value === 'GROUP_BOT') return t.category.includes('群机器人')
    return true
  })
})

const showCreateDialog = () => {
  isEdit.value = false
  showPreview.value = false
  // 设置默认AI模型为最新配置的模型
  const defaultModel = aiModels.value.find(m => m.is_default) || aiModels.value[0]
  
  // 根据当前标签页设置默认推送模式
  let defaultPushMode = 'realtime'
  if (activeTab.value === 'SMS' || activeTab.value === 'EMAIL') {
    defaultPushMode = null // 短信/邮件不需要推送模式
  }
  
  templateForm.value = {
    id: null,
    name: '',
    category: '',
    type: 'text',
    content: '',
    ai_model: defaultModel ? defaultModel.value : 'wework-official',
    push_mode: defaultPushMode,
    keywords: '',
    targets: [],
    schedule_time: null,
    repeat_type: 'once',
    repeat_days: [],
    status: true,
    variables: []
  }
  dialogVisible.value = true
}

const editTemplate = (row) => {
  isEdit.value = true
  templateForm.value = { ...row }
  dialogVisible.value = true
}

const saveTemplate = async () => {
  // 表单验证
  if (!templateFormRef.value) {
    ElMessage.warning('表单未初始化')
    return
  }

  try {
    await templateFormRef.value.validate()
  } catch (error) {
    ElMessage.warning('请填写所有必填项（带 * 号）')
    return
  }

  saving.value = true
  try {
    // 模拟保存延迟
    await new Promise(resolve => setTimeout(resolve, 500))
    
    if (isEdit.value) {
      const index = templates.value.findIndex(t => t.id === templateForm.value.id)
      if (index !== -1) {
        templates.value[index] = { ...templateForm.value }
      }
      ElMessage.success('✅ 模板配置已保存')
    } else {
      templateForm.value.id = Date.now()
      templates.value.push({ ...templateForm.value })
      ElMessage.success('✅ 模板配置已保存')
    }

    dialogVisible.value = false
    showPreview.value = false
  } catch (error) {
    ElMessage.error('❌ 保存失败，请重试')
  } finally {
    saving.value = false
  }
}

const deleteTemplate = async (row) => {
  if (row.is_system) {
    ElMessage.warning('系统模板禁止删除')
    return
  }

  try {
    await ElMessageBox.confirm('确定要删除这个模板吗？', '确认删除', {
      type: 'warning'
    })
    
    const index = templates.value.findIndex(t => t.id === row.id)
    if (index !== -1) {
      templates.value.splice(index, 1)
    }
    ElMessage.success('模板已删除')
  } catch {
    // 用户取消
  }
}

const toggleStatus = (row) => {
  ElMessage.success(row.status ? '模板已启用' : '模板已禁用')
}

onMounted(() => {
  loadAIModels()
  
  // 初始化示例模板
  templates.value = [
    {
      id: 1,
      name: '订单确认短信',
      category: '订单通知',
      type: 'text',
      content: '尊敬的{customer_name}，您的订单{order_id}已确认，预计{date}送达。',
      status: true,
      is_system: false
    },
    {
      id: 2,
      name: 'AI价格咨询回复',
      category: 'AI回复模板',
      type: 'text',
      content: '您好{customer_name}，关于{product}的价格咨询，我们会尽快为您报价。',
      ai_model: 'wework-official',
      status: true,
      is_system: true
    }
  ]
})
</script>

<style scoped>
.template-manager {
  padding: 20px;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions h2 {
  margin: 0;
}
</style>

