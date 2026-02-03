<template>
  <div class="message-manager">
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 1. 发送消息 -->
      <el-tab-pane label="📤 发送消息" name="send">
        <el-card>
          <el-form :model="sendForm" label-width="120px">
            <el-form-item label="消息标题">
              <el-input v-model="sendForm.title" placeholder="请输入消息标题"></el-input>
            </el-form-item>

            <el-form-item label="发送渠道">
              <el-radio-group v-model="sendForm.channel">
                <el-radio label="SMS">短信</el-radio>
                <el-radio label="EMAIL">邮箱</el-radio>
                <el-radio label="APP">APP推送</el-radio>
                <el-radio label="WECHAT">微信公众号</el-radio>
                <el-radio label="FEISHU">飞书</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="接收者">
              <el-input 
                v-model="sendForm.receiver" 
                placeholder="手机号/邮箱/UserID（多个用逗号分隔）"
                type="textarea"
                :rows="2"
              ></el-input>
            </el-form-item>

            <el-form-item label="消息内容">
              <el-input 
                v-model="sendForm.content" 
                type="textarea" 
                :rows="5"
                placeholder="请输入消息内容"
              ></el-input>
            </el-form-item>

            <el-form-item label="优先级">
              <el-select v-model="sendForm.priority">
                <el-option label="低优先级 (0-3)" :value="2"></el-option>
                <el-option label="普通优先级 (4-6)" :value="5"></el-option>
                <el-option label="高优先级 (7-10)" :value="8"></el-option>
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="sendMessage" :loading="sending">
                立即发送
              </el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 2. 消息列表 -->
      <el-tab-pane label="📋 消息列表" name="list">
        <el-card>
          <div style="margin-bottom: 20px;">
            <el-button type="primary" @click="loadMessages" :icon="Refresh">刷新</el-button>
            <el-select v-model="filterStatus" placeholder="筛选状态" style="margin-left: 10px; width: 150px;">
              <el-option label="全部" value=""></el-option>
              <el-option label="待发送" value="PENDING"></el-option>
              <el-option label="发送中" value="SENDING"></el-option>
              <el-option label="已发送" value="SENT"></el-option>
              <el-option label="失败" value="FAILED"></el-option>
            </el-select>
            <el-select v-model="filterChannel" placeholder="筛选渠道" style="margin-left: 10px; width: 150px;">
              <el-option label="全部渠道" value=""></el-option>
              <el-option label="短信" value="SMS"></el-option>
              <el-option label="邮箱" value="EMAIL"></el-option>
              <el-option label="APP" value="APP"></el-option>
              <el-option label="微信" value="WECHAT"></el-option>
              <el-option label="飞书" value="FEISHU"></el-option>
            </el-select>
          </div>

          <el-table :data="filteredMessages" border style="width: 100%">
            <el-table-column prop="id" label="消息ID" width="80"></el-table-column>
            <el-table-column prop="title" label="标题" width="150"></el-table-column>
            <el-table-column prop="channel" label="渠道" width="100">
              <template #default="scope">
                <el-tag :type="getChannelType(scope.row.channel)">
                  {{ scope.row.channel }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="receiver" label="接收者" width="150"></el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">
                  {{ getStatusText(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="priority" label="优先级" width="80"></el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180"></el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="scope">
                <el-button type="primary" size="small" @click="viewTrace(scope.row)">
                  查看追踪
                </el-button>
                <el-button type="info" size="small" @click="viewDetail(scope.row)">
                  详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 3. 链路追踪 -->
      <el-tab-pane label="🔍 链路追踪" name="trace">
        <el-card>
          <div style="margin-bottom: 20px;">
            <el-input 
              v-model="traceId" 
              placeholder="输入消息ID查询追踪信息"
              style="width: 300px;"
            >
              <template #append>
                <el-button @click="searchTrace" :icon="Search">查询</el-button>
              </template>
            </el-input>
          </div>

          <el-timeline v-if="traceData.length > 0">
            <el-timeline-item
              v-for="(item, index) in traceData"
              :key="index"
              :timestamp="item.timestamp"
              :type="getTraceType(item.status)"
              placement="top"
            >
              <el-card>
                <h4>{{ item.stage }}</h4>
                <p>状态: <el-tag :type="getStatusType(item.status)">{{ item.status }}</el-tag></p>
                <p v-if="item.message">{{ item.message }}</p>
                <p v-if="item.details">详情: {{ item.details }}</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>

          <el-empty v-else description="暂无追踪数据，请先查询消息ID"></el-empty>
        </el-card>
      </el-tab-pane>

      <!-- 4. 统计分析 -->
      <el-tab-pane label="📊 统计分析" name="stats">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card>
              <div class="stat-card">
                <div class="stat-title">今日发送</div>
                <div class="stat-value">{{ stats.today_sent }}</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card>
              <div class="stat-card">
                <div class="stat-title">成功率</div>
                <div class="stat-value success">{{ stats.success_rate }}%</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card>
              <div class="stat-card">
                <div class="stat-title">失败数</div>
                <div class="stat-value error">{{ stats.failed_count }}</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card>
              <div class="stat-card">
                <div class="stat-title">平均耗时</div>
                <div class="stat-value">{{ stats.avg_time }}ms</div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-card style="margin-top: 20px;">
          <h3>渠道分布</h3>
          <el-table :data="stats.channel_stats" border>
            <el-table-column prop="channel" label="渠道"></el-table-column>
            <el-table-column prop="total" label="总数"></el-table-column>
            <el-table-column prop="success" label="成功"></el-table-column>
            <el-table-column prop="failed" label="失败"></el-table-column>
            <el-table-column prop="success_rate" label="成功率"></el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="消息详情" width="600px">
      <el-descriptions :column="1" border v-if="currentMessage">
        <el-descriptions-item label="消息ID">{{ currentMessage.id }}</el-descriptions-item>
        <el-descriptions-item label="标题">{{ currentMessage.title }}</el-descriptions-item>
        <el-descriptions-item label="渠道">{{ currentMessage.channel }}</el-descriptions-item>
        <el-descriptions-item label="接收者">{{ currentMessage.receiver }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentMessage.status)">
            {{ getStatusText(currentMessage.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="优先级">{{ currentMessage.priority }}</el-descriptions-item>
        <el-descriptions-item label="内容">{{ currentMessage.content }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentMessage.created_at }}</el-descriptions-item>
        <el-descriptions-item label="发送时间" v-if="currentMessage.sent_at">
          {{ currentMessage.sent_at }}
        </el-descriptions-item>
        <el-descriptions-item label="错误信息" v-if="currentMessage.error_message">
          <el-text type="danger">{{ currentMessage.error_message }}</el-text>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import axios from 'axios'

const activeTab = ref('send')
const sending = ref(false)
const detailDialogVisible = ref(false)
const currentMessage = ref(null)

// 发送表单
const sendForm = ref({
  title: '',
  channel: 'SMS',
  receiver: '',
  content: '',
  priority: 5
})

// 消息列表
const messages = ref([])
const filterStatus = ref('')
const filterChannel = ref('')

// 追踪数据
const traceId = ref('')
const traceData = ref([])

// 统计数据
const stats = ref({
  today_sent: 0,
  success_rate: 0,
  failed_count: 0,
  avg_time: 0,
  channel_stats: []
})

// 过滤后的消息列表
const filteredMessages = computed(() => {
  return messages.value.filter(msg => {
    if (filterStatus.value && msg.status !== filterStatus.value) return false
    if (filterChannel.value && msg.channel !== filterChannel.value) return false
    return true
  })
})

// 发送消息
const sendMessage = async () => {
  if (!sendForm.value.title || !sendForm.value.receiver || !sendForm.value.content) {
    ElMessage.warning('请填写完整信息')
    return
  }

  sending.value = true
  try {
    const response = await axios.post('http://localhost:8000/api/messages/send', {
      title: sendForm.value.title,
      channel: sendForm.value.channel,
      receivers: sendForm.value.receiver.split(',').map(r => r.trim()),
      content: sendForm.value.content,
      priority: sendForm.value.priority
    })

    ElMessage.success('消息发送成功！消息ID: ' + response.data.message_id)
    resetForm()
    loadMessages()
    activeTab.value = 'list'
  } catch (error) {
    ElMessage.error('发送失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    sending.value = false
  }
}

// 重置表单
const resetForm = () => {
  sendForm.value = {
    title: '',
    channel: 'SMS',
    receiver: '',
    content: '',
    priority: 5
  }
}

// 加载消息列表
const loadMessages = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/messages/list', {
      params: {
        limit: 50
      }
    })
    messages.value = response.data.messages || []
  } catch (error) {
    ElMessage.error('加载消息列表失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 查看追踪
const viewTrace = async (message) => {
  traceId.value = message.id.toString()
  await searchTrace()
  activeTab.value = 'trace'
}

// 搜索追踪
const searchTrace = async () => {
  if (!traceId.value) {
    ElMessage.warning('请输入消息ID')
    return
  }

  try {
    const response = await axios.get(`http://localhost:8000/api/messages/trace/${traceId.value}`)
    traceData.value = response.data.trace || []
    
    if (traceData.value.length === 0) {
      ElMessage.info('暂无追踪数据')
    }
  } catch (error) {
    ElMessage.error('查询追踪失败: ' + (error.response?.data?.detail || error.message))
    traceData.value = []
  }
}

// 查看详情
const viewDetail = (message) => {
  currentMessage.value = message
  detailDialogVisible.value = true
}

// 加载统计数据
const loadStats = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/messages/stats')
    stats.value = response.data
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

// 辅助函数
const getChannelType = (channel) => {
  const types = {
    'SMS': 'success',
    'EMAIL': 'primary',
    'APP': 'warning',
    'WECHAT': 'success',
    'FEISHU': 'info'
  }
  return types[channel] || 'info'
}

const getStatusType = (status) => {
  const types = {
    'PENDING': 'info',
    'SENDING': 'warning',
    'SENT': 'success',
    'FAILED': 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    'PENDING': '待发送',
    'SENDING': '发送中',
    'SENT': '已发送',
    'FAILED': '失败'
  }
  return texts[status] || status
}

const getTraceType = (status) => {
  if (status.includes('成功') || status.includes('SENT')) return 'success'
  if (status.includes('失败') || status.includes('FAILED')) return 'danger'
  if (status.includes('发送中') || status.includes('SENDING')) return 'warning'
  return 'primary'
}

// 组件挂载时加载数据
onMounted(() => {
  loadMessages()
  loadStats()
})
</script>

<style scoped>
.message-manager {
  padding: 20px;
}

.stat-card {
  text-align: center;
  padding: 20px;
}

.stat-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
}

.stat-value.success {
  color: #67C23A;
}

.stat-value.error {
  color: #F56C6C;
}

:deep(.el-timeline-item__timestamp) {
  color: #909399;
  font-size: 12px;
}

:deep(.el-card__body) {
  padding: 15px;
}
</style>
