<!-- 消息监控大屏 - ECharts可视化 -->
<template>
  <div class="message-monitor">
    <el-page-header @back="$router.back()" title="返回">
      <template #content>
        <span class="page-title">📊 消息处理监控大屏</span>
      </template>
    </el-page-header>

    <!-- 实时数据概览 -->
    <el-row :gutter="20" class="stats-cards">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon success">📧</div>
          <div class="stat-content">
            <div class="stat-value">{{ overview.total_sent.toLocaleString() }}</div>
            <div class="stat-label">今日发送总数</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon primary">✅</div>
          <div class="stat-content">
            <div class="stat-value">{{ overview.success_rate }}%</div>
            <div class="stat-label">发送成功率</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon warning">⚡</div>
          <div class="stat-content">
            <div class="stat-value">{{ overview.avg_response_time }}ms</div>
            <div class="stat-label">平均响应时间</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon danger">⚠️</div>
          <div class="stat-content">
            <div class="stat-value">{{ overview.total_failed.toLocaleString() }}</div>
            <div class="stat-label">发送失败数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-section">
      <!-- 发送趋势图 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>📈 各时段发送情况</span>
          </template>
          <div ref="trendChart" style="height: 350px;"></div>
        </el-card>
      </el-col>

      <!-- 渠道分布饼图 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>🎯 各渠道发送占比</span>
          </template>
          <div ref="channelChart" style="height: 350px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="charts-section">
      <!-- 成功率对比柱状图 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>📊 各渠道成功率对比</span>
          </template>
          <div ref="successRateChart" style="height: 350px;"></div>
        </el-card>
      </el-col>

      <!-- 线程池状态 -->
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>⚙️ 线程池实时状态</span>
          </template>
          <div ref="threadPoolChart" style="height: 350px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 实时消息流 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <span>🔄 实时消息流（最近50条）</span>
            <el-tag :type="autoRefresh ? 'success' : 'info'" size="small" style="float: right;">
              {{ autoRefresh ? '自动刷新' : '已暂停' }}
            </el-tag>
          </template>

          <el-timeline>
            <el-timeline-item
              v-for="msg in realtimeMessages"
              :key="msg.id"
              :timestamp="msg.timestamp"
              placement="top"
              :color="getStatusColor(msg.status)"
            >
              <el-tag :type="getStatusType(msg.status)" size="small">{{ msg.status }}</el-tag>
              <span style="margin-left: 10px;">{{ msg.channel }}</span>
              <span style="margin-left: 10px; color: #666;">→ {{ msg.recipient }}</span>
              <span style="margin-left: 10px; color: #999;">耗时: {{ msg.duration }}ms</span>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'

// 数据
const overview = reactive({
  total_sent: 0,
  total_success: 0,
  total_failed: 0,
  success_rate: 0,
  avg_response_time: 0
})

const realtimeMessages = ref([])
const autoRefresh = ref(true)

// ECharts实例
let trendChartInstance = null
let channelChartInstance = null
let successRateChartInstance = null
let threadPoolChartInstance = null

// 图表引用
const trendChart = ref(null)
const channelChart = ref(null)
const successRateChart = ref(null)
const threadPoolChart = ref(null)

// 定时器
let refreshTimer = null

onMounted(() => {
  initCharts()
  loadData()
  
  // 自动刷新（每5秒）
  refreshTimer = setInterval(() => {
    if (autoRefresh.value) {
      loadData()
    }
  }, 5000)
})

onBeforeUnmount(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
  
  // 销毁图表
  trendChartInstance?.dispose()
  channelChartInstance?.dispose()
  successRateChartInstance?.dispose()
  threadPoolChartInstance?.dispose()
})

// 初始化图表
function initCharts() {
  // 发送趋势图
  trendChartInstance = echarts.init(trendChart.value)
  trendChartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['发送总数', '成功数', '失败数']
    },
    xAxis: {
      type: 'category',
      data: []
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '发送总数',
        type: 'line',
        data: [],
        smooth: true,
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '成功数',
        type: 'line',
        data: [],
        smooth: true,
        itemStyle: { color: '#67C23A' }
      },
      {
        name: '失败数',
        type: 'line',
        data: [],
        smooth: true,
        itemStyle: { color: '#F56C6C' }
      }
    ]
  })

  // 渠道分布饼图
  channelChartInstance = echarts.init(channelChart.value)
  channelChartInstance.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '渠道分布',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}: {d}%'
        },
        data: []
      }
    ]
  })

  // 成功率对比柱状图
  successRateChartInstance = echarts.init(successRateChart.value)
  successRateChartInstance.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    xAxis: {
      type: 'category',
      data: []
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: '成功率',
        type: 'bar',
        data: [],
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#83bff6' },
            { offset: 0.5, color: '#188df0' },
            { offset: 1, color: '#188df0' }
          ])
        },
        label: {
          show: true,
          position: 'top',
          formatter: '{c}%'
        }
      }
    ]
  })

  // 线程池状态仪表盘
  threadPoolChartInstance = echarts.init(threadPoolChart.value)
  threadPoolChartInstance.setOption({
    tooltip: {
      formatter: '{a} <br/>{b} : {c}%'
    },
    series: [
      {
        name: '线程池使用率',
        type: 'gauge',
        detail: {
          formatter: '{value}%'
        },
        data: [{ value: 0, name: '使用率' }]
      }
    ]
  })
}

// 加载数据
async function loadData() {
  try {
    // 加载概览数据
    const overviewRes = await axios.get('/api/messages/statistics/overview')
    if (overviewRes.data.code === 0) {
      const data = overviewRes.data.data.overview
      overview.total_sent = data.total_sent
      overview.total_success = data.total_success
      overview.total_failed = data.total_failed
      overview.success_rate = data.success_rate
      overview.avg_response_time = Math.round(data.avg_response_time)

      // 更新趋势图
      const dailyStats = overviewRes.data.data.daily_stats
      const dates = [...new Set(dailyStats.map(s => s.date))]
      const sentData = dates.map(date => {
        return dailyStats.filter(s => s.date === date).reduce((sum, s) => sum + s.sent, 0)
      })
      const successData = dates.map(date => {
        return dailyStats.filter(s => s.date === date).reduce((sum, s) => sum + s.success, 0)
      })
      const failedData = dates.map(date => {
        return dailyStats.filter(s => s.date === date).reduce((sum, s) => sum + s.failed, 0)
      })

      trendChartInstance.setOption({
        xAxis: { data: dates },
        series: [
          { data: sentData },
          { data: successData },
          { data: failedData }
        ]
      })

      // 更新渠道饼图
      const channelData = Object.entries(overviewRes.data.data.by_channel).map(([channel, stats]) => ({
        name: getChannelName(channel),
        value: stats.sent
      }))

      channelChartInstance.setOption({
        series: [{ data: channelData }]
      })

      // 更新成功率柱状图
      const successRateData = Object.entries(overviewRes.data.data.by_channel).map(([channel, stats]) => ({
        channel: getChannelName(channel),
        rate: stats.sent > 0 ? Math.round(stats.success / stats.sent * 100) : 0
      }))

      successRateChartInstance.setOption({
        xAxis: { data: successRateData.map(d => d.channel) },
        series: [{ data: successRateData.map(d => d.rate) }]
      })
    }

    // 加载实时数据
    const realtimeRes = await axios.get('/api/messages/statistics/realtime')
    if (realtimeRes.data.code === 0) {
      // 更新线程池状态
      const poolStats = realtimeRes.data.data.thread_pool_stats
      if (poolStats.message_sender) {
        const usage = Math.round(poolStats.message_sender.queue_usage_percent)
        threadPoolChartInstance.setOption({
          series: [{
            data: [{ value: usage, name: '使用率' }]
          }]
        })
      }

      // 模拟实时消息流（实际应该用WebSocket）
      updateRealtimeMessages()
    }
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

// 更新实时消息流
function updateRealtimeMessages() {
  // 这里模拟数据，实际应该从WebSocket获取
  const newMsg = {
    id: Date.now(),
    timestamp: new Date().toLocaleTimeString(),
    status: ['发送成功', '发送中', '发送失败'][Math.floor(Math.random() * 3)],
    channel: ['短信', '邮箱', 'APP通知', '微信公众号'][Math.floor(Math.random() * 4)],
    recipient: `用户${Math.floor(Math.random() * 10000)}`,
    duration: Math.floor(Math.random() * 500) + 50
  }

  realtimeMessages.value.unshift(newMsg)
  if (realtimeMessages.value.length > 50) {
    realtimeMessages.value.pop()
  }
}

// 工具函数
function getChannelName(channel) {
  const names = {
    'sms': '短信',
    'email': '邮箱',
    'app': 'APP通知',
    'wechat': '微信公众号',
    'feishu': '飞书机器人'
  }
  return names[channel] || channel
}

function getStatusColor(status) {
  const colors = {
    '发送成功': '#67C23A',
    '发送中': '#E6A23C',
    '发送失败': '#F56C6C'
  }
  return colors[status] || '#909399'
}

function getStatusType(status) {
  const types = {
    '发送成功': 'success',
    '发送中': 'warning',
    '发送失败': 'danger'
  }
  return types[status] || 'info'
}
</script>

<style scoped>
.message-monitor {
  padding: 20px;
  background: #f0f2f5;
  min-height: 100vh;
}

.page-title {
  font-size: 20px;
  font-weight: bold;
}

.stats-cards {
  margin: 20px 0;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 10px;
}

.stat-icon {
  font-size: 48px;
  margin-right: 15px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.charts-section {
  margin: 20px 0;
}

.el-timeline {
  max-height: 500px;
  overflow-y: auto;
}
</style>
