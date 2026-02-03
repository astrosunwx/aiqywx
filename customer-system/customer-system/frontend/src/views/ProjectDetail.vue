<template>
  <div class="project-detail">
    <!-- 访问验证失败 -->
    <el-result
      v-if="!hasAccess"
      icon="error"
      title="无访问权限"
      sub-title="抱歉，您无权查看此项目详情。项目详情仅限相关人员查看。"
    >
      <template #extra>
        <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
      </template>
    </el-result>

    <!-- 正常显示项目详情 -->
    <div class="detail-container" v-else-if="project">
      <!-- 头部信息 -->
      <el-card class="header-card">
        <div class="project-header">
          <div class="header-left">
            <h2>{{ getTypeIcon(project.type) }} {{ project.title }}</h2>
            <div class="project-meta">
              <el-tag :type="getTypeTagColor(project.type)" size="large">
                {{ getTypeText(project.type) }}
              </el-tag>
              <el-tag :type="getStatusTagColor(project.status)" size="large">
                {{ getStatusText(project.status) }}
              </el-tag>
              <span class="project-id">工单编号: {{ project.id }}</span>
            </div>
          </div>
          <div class="header-right">
            <el-space>
              <el-tag v-if="project.from_cache" type="info" effect="plain">
                <el-icon><Clock /></el-icon>
                缓存数据 {{ project.cache_time }}
              </el-tag>
              <el-button 
                type="primary"
                plain
                size="default"
                @click="refreshStatus"
                :loading="refreshing"
              >
                <el-icon><RefreshRight /></el-icon>
                刷新状态
              </el-button>
              <el-button 
                v-if="project.type === 'aftersales' && project.status !== 'resolved'"
                type="success" 
                size="large"
                @click="markAsResolved"
              >
                ✅ 标记为已解决
              </el-button>
            </el-space>
          </div>
        </div>
      </el-card>

      <!-- 项目状态查询（轻量级） -->
      <div v-if="project.type === 'status'">
        <el-card class="status-query-card">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>📊 项目状态查询</span>
              <el-tag 
                :type="getStatusTagColor(project.status)" 
                size="large"
                effect="dark"
              >
                {{ getStatusText(project.status) }}
              </el-tag>
            </div>
          </template>

          <el-row :gutter="20" style="margin-bottom: 30px;">
            <el-col :span="12">
              <div class="status-item">
                <div class="status-label">项目类型</div>
                <div class="status-value">{{ getTypeText(project.type) }}</div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="status-item">
                <div class="status-label">项目ID</div>
                <div class="status-value">{{ project.id }}</div>
              </div>
            </el-col>
          </el-row>

          <el-row :gutter="20" style="margin-bottom: 30px;">
            <el-col :span="12">
              <div class="status-item">
                <div class="status-label">项目标题</div>
                <div class="status-value">{{ project.title }}</div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="status-item">
                <div class="status-label">最后更新</div>
                <div class="status-value">{{ formatTime(project.updated_at) }}</div>
              </div>
            </el-col>
          </el-row>

          <!-- 快速状态概览 -->
          <el-divider></el-divider>
          
          <div style="text-align: center; padding: 20px 0;">
            <div style="margin-bottom: 20px;">
              <el-statistic 
                title="完成度" 
                :value="project.progress || 0" 
                suffix="%"
                style="font-size: 24px;"
              ></el-statistic>
            </div>
            <el-progress 
              :percentage="project.progress || 0" 
              :status="project.status === 'completed' ? 'success' : 'exception'"
              :color="getProgressColor(project.progress)"
              style="margin-bottom: 20px;"
            ></el-progress>
          </div>

          <!-- 相关人员 -->
          <el-divider v-if="project.customer_name || project.engineer_name || project.salesman_name"></el-divider>

          <div v-if="project.customer_name || project.engineer_name || project.salesman_name" style="margin-top: 20px;">
            <div style="font-size: 14px; color: #666; margin-bottom: 10px;">📞 相关人员</div>
            <el-row :gutter="15">
              <el-col :span="8" v-if="project.customer_name">
                <div style="border-left: 3px solid #409eff; padding-left: 10px;">
                  <div style="font-size: 12px; color: #909399;">客户</div>
                  <div style="font-weight: bold;">{{ project.customer_name }}</div>
                  <div style="font-size: 12px; color: #909399;">{{ project.phone }}</div>
                </div>
              </el-col>
              <el-col :span="8" v-if="project.engineer_name">
                <div style="border-left: 3px solid #67c23a; padding-left: 10px;">
                  <div style="font-size: 12px; color: #909399;">工程师</div>
                  <div style="font-weight: bold;">{{ project.engineer_name }}</div>
                  <div style="font-size: 12px; color: #909399;">{{ project.engineer_phone }}</div>
                </div>
              </el-col>
              <el-col :span="8" v-if="project.salesman_name">
                <div style="border-left: 3px solid #e6a23c; padding-left: 10px;">
                  <div style="font-size: 12px; color: #909399;">销售</div>
                  <div style="font-weight: bold;">{{ project.salesman_name }}</div>
                  <div style="font-size: 12px; color: #909399;">{{ project.salesman_phone }}</div>
                </div>
              </el-col>
            </el-row>
          </div>

          <!-- 轻量级提示 -->
          <el-alert
            type="info"
            :closable="false"
            style="margin-top: 20px;"
          >
            <template #title>
              💡 这是项目状态快速查询页面，支持AI机器人轻量级调用，避免频繁查询完整项目数据
            </template>
          </el-alert>
        </el-card>
      </div>

      <!-- 售前商机详情 -->
      <div v-if="project.type === 'presale'">
        <el-row :gutter="20">
          <el-col :span="16">
            <el-card title="商机详情">
              <template #header>
                <span>💼 商机详情</span>
              </template>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="客户姓名">{{ project.customer_name }}</el-descriptions-item>
                <el-descriptions-item label="联系电话">{{ project.phone }}</el-descriptions-item>
                <el-descriptions-item label="意向产品">{{ project.product }}</el-descriptions-item>
                <el-descriptions-item label="预算金额">{{ project.budget }}元</el-descriptions-item>
                <el-descriptions-item label="紧急程度">
                  <el-rate v-model="project.urgency" disabled show-score></el-rate>
                </el-descriptions-item>
                <el-descriptions-item label="创建时间">{{ project.created_at }}</el-descriptions-item>
                <el-descriptions-item label="客户需求" :span="2">
                  <div class="need-content">{{ project.description }}</div>
                </el-descriptions-item>
              </el-descriptions>
            </el-card>

            <el-card style="margin-top: 20px;">
              <template #header>
                <span>📊 跟进记录</span>
              </template>
              <el-timeline>
                <el-timeline-item 
                  v-for="record in project.follow_records" 
                  :key="record.id"
                  :timestamp="record.time"
                >
                  <el-card>
                    <p><strong>{{ record.salesman }}:</strong> {{ record.content }}</p>
                  </el-card>
                </el-timeline-item>
              </el-timeline>
            </el-card>
          </el-col>

          <el-col :span="8">
            <el-card>
              <template #header>
                <span>👤 负责销售</span>
              </template>
              <div class="sales-info">
                <el-avatar :size="80" :src="project.salesman_avatar"></el-avatar>
                <h3>{{ project.salesman_name }}</h3>
                <p>{{ project.salesman_phone }}</p>
                <el-button type="primary" style="width: 100%; margin-top: 10px;">
                  联系销售
                </el-button>
              </div>
            </el-card>

            <el-card style="margin-top: 20px;">
              <template #header>
                <span>📅 重要时间</span>
              </template>
              <el-descriptions :column="1">
                <el-descriptions-item label="创建时间">{{ project.created_at }}</el-descriptions-item>
                <el-descriptions-item label="最后跟进">{{ project.last_follow }}</el-descriptions-item>
                <el-descriptions-item label="预计成交">{{ project.expected_close }}</el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 售后服务详情 -->
      <div v-if="project.type === 'aftersales'">
        <el-row :gutter="20">
          <el-col :span="16">
            <el-card>
              <template #header>
                <span>🔧 服务工单详情</span>
              </template>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="工单编号">{{ project.id }}</el-descriptions-item>
                <el-descriptions-item label="工单类型">
                  <el-tag>{{ project.service_type }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="客户姓名">{{ project.customer_name }}</el-descriptions-item>
                <el-descriptions-item label="联系电话">{{ project.phone }}</el-descriptions-item>
                <el-descriptions-item label="设备名称">{{ project.equipment }}</el-descriptions-item>
                <el-descriptions-item label="故障描述" :span="2">
                  <div class="issue-content">{{ project.issue_description }}</div>
                </el-descriptions-item>
                <el-descriptions-item label="服务地址" :span="2">
                  {{ project.service_address }}
                </el-descriptions-item>
                <el-descriptions-item label="预约时间">{{ project.appointment_time }}</el-descriptions-item>
                <el-descriptions-item label="创建时间">{{ project.created_at }}</el-descriptions-item>
              </el-descriptions>
            </el-card>

            <!-- 处理进度 -->
            <el-card style="margin-top: 20px;">
              <template #header>
                <span>📈 处理进度</span>
              </template>
              <el-steps :active="getStepActive(project.status)" finish-status="success">
                <el-step title="工单创建" :description="project.created_at"></el-step>
                <el-step title="已分配" :description="project.assigned_at"></el-step>
                <el-step title="处理中" :description="project.processing_at"></el-step>
                <el-step title="已完成" :description="project.completed_at"></el-step>
              </el-steps>

              <el-timeline style="margin-top: 20px;">
                <el-timeline-item 
                  v-for="record in project.service_records" 
                  :key="record.id"
                  :timestamp="record.time"
                  :type="record.type"
                >
                  <el-card>
                    <p><strong>{{ record.engineer }}:</strong> {{ record.content }}</p>
                  </el-card>
                </el-timeline-item>
              </el-timeline>
            </el-card>

            <!-- 客户反馈区域 -->
            <el-card style="margin-top: 20px;" v-if="project.status === 'completed'">
              <template #header>
                <span>💬 客户反馈</span>
              </template>
              <el-form :model="feedbackForm">
                <el-form-item label="问题是否已解决？">
                  <el-radio-group v-model="feedbackForm.resolved">
                    <el-radio :label="true">✅ 已解决</el-radio>
                    <el-radio :label="false">❌ 未解决</el-radio>
                  </el-radio-group>
                </el-form-item>

                <el-form-item label="服务评价" v-if="feedbackForm.resolved">
                  <el-rate v-model="feedbackForm.rating" show-text></el-rate>
                </el-form-item>

                <el-form-item label="补充说明（非必填）">
                  <el-input 
                    v-model="feedbackForm.comment" 
                    type="textarea" 
                    :rows="4"
                    placeholder="请输入您的反馈..."
                  ></el-input>
                </el-form-item>

                <el-form-item v-if="!feedbackForm.resolved">
                  <el-alert 
                    type="warning" 
                    :closable="false"
                    title="问题未解决将转交给工程师进一步处理"
                  ></el-alert>
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="submitFeedback">提交反馈</el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>

          <el-col :span="8">
            <el-card>
              <template #header>
                <span>👨‍🔧 负责工程师</span>
              </template>
              <div class="engineer-info">
                <el-avatar :size="80" :src="project.engineer_avatar"></el-avatar>
                <h3>{{ project.engineer_name }}</h3>
                <p>{{ project.engineer_phone }}</p>
                <el-button type="primary" style="width: 100%; margin-top: 10px;">
                  联系工程师
                </el-button>
              </div>
            </el-card>

            <el-card style="margin-top: 20px;">
              <template #header>
                <span>📋 工单信息</span>
              </template>
              <el-descriptions :column="1">
                <el-descriptions-item label="优先级">
                  <el-tag :type="getPriorityType(project.priority)">
                    {{ project.priority }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="创建时间">{{ project.created_at }}</el-descriptions-item>
                <el-descriptions-item label="预计完成">{{ project.expected_complete }}</el-descriptions-item>
                <el-descriptions-item label="实际完成" v-if="project.completed_at">
                  {{ project.completed_at }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 销售订单详情 -->
      <div v-if="project.type === 'sales'">
        <el-row :gutter="20">
          <el-col :span="16">
            <el-card>
              <template #header>
                <span>📦 订单详情</span>
              </template>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="订单编号">{{ project.order_id }}</el-descriptions-item>
                <el-descriptions-item label="下单时间">{{ project.order_time }}</el-descriptions-item>
                <el-descriptions-item label="客户姓名">{{ project.customer_name }}</el-descriptions-item>
                <el-descriptions-item label="联系电话">{{ project.phone }}</el-descriptions-item>
                <el-descriptions-item label="订单金额">
                  <span class="amount">¥{{ project.amount }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="支付状态">
                  <el-tag :type="project.payment_status === 'paid' ? 'success' : 'warning'">
                    {{ project.payment_status === 'paid' ? '已支付' : '待支付' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="收货地址" :span="2">
                  {{ project.shipping_address }}
                </el-descriptions-item>
              </el-descriptions>

              <el-table :data="project.items" style="margin-top: 20px;" border>
                <el-table-column prop="name" label="产品名称"></el-table-column>
                <el-table-column prop="specs" label="规格"></el-table-column>
                <el-table-column prop="quantity" label="数量"></el-table-column>
                <el-table-column prop="price" label="单价"></el-table-column>
                <el-table-column prop="total" label="小计"></el-table-column>
              </el-table>
            </el-card>

            <el-card style="margin-top: 20px;">
              <template #header>
                <span>🚚 物流信息</span>
              </template>
              <el-timeline v-if="project.logistics">
                <el-timeline-item 
                  v-for="log in project.logistics" 
                  :key="log.id"
                  :timestamp="log.time"
                >
                  {{ log.content }}
                </el-timeline-item>
              </el-timeline>
              <el-empty v-else description="暂无物流信息"></el-empty>
            </el-card>
          </el-col>

          <el-col :span="8">
            <el-card v-if="project.payment_status === 'unpaid'">
              <template #header>
                <span>💰 立即支付</span>
              </template>
              <div class="payment-section">
                <div class="amount-big">¥{{ project.amount }}</div>
                <el-button type="danger" size="large" style="width: 100%; margin-top: 20px;">
                  立即支付
                </el-button>
                <el-divider>支付方式</el-divider>
                <el-radio-group v-model="paymentMethod" style="width: 100%;">
                  <el-radio label="wechat" border>微信支付</el-radio>
                  <el-radio label="alipay" border>支付宝</el-radio>
                </el-radio-group>
              </div>
            </el-card>

            <el-card>
              <template #header>
                <span>📞 联系客服</span>
              </template>
              <div class="contact-info">
                <p>客服电话: 400-XXX-XXXX</p>
                <p>工作时间: 9:00-18:00</p>
                <el-button type="primary" style="width: 100%; margin-top: 10px;">
                  在线客服
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 加载状态 -->
    <el-card v-else-if="loading" class="loading-card">
      <el-skeleton :rows="10" animated></el-skeleton>
    </el-card>

    <!-- 错误状态 -->
    <el-card v-else class="error-card">
      <el-result 
        icon="error" 
        title="工单不存在" 
        sub-title="请检查工单编号是否正确"
      >
        <template #extra>
          <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
        </template>
      </el-result>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Clock, RefreshRight } from '@element-plus/icons-vue'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const project = ref(null)
const loading = ref(true)
const hasAccess = ref(true) // 访问权限
const refreshing = ref(false) // 刷新状态中
const paymentMethod = ref('wechat')

const feedbackForm = ref({
  resolved: true,
  rating: 5,
  comment: ''
})

// 加载项目详情
const loadProjectDetail = async () => {
  loading.value = true
  hasAccess.value = true
  try {
    const projectId = route.params.id
    const token = route.query.token // 获取访问令牌
    const queryType = route.query.type || 'full' // 查询类型：status（轻量级） | full（完整）
    
    // 验证访问权限
    try {
      const accessResponse = await axios.get(`http://localhost:8000/api/projects/${projectId}/verify-access`, {
        params: { token }
      })
      hasAccess.value = accessResponse.data.has_access
      
      if (!hasAccess.value) {
        loading.value = false
        return
      }
    } catch (error) {
      console.log('权限验证失败，使用模拟数据:', error)
      // 开发环境允许访问
      hasAccess.value = true
    }
    
    // 根据查询类型调用不同API
    let response
    if (queryType === 'status') {
      // 调用轻量级状态查询API（为AI机器人优化）
      response = await axios.get(`http://localhost:8000/api/projects/${projectId}/status`, {
        params: { token }
      })
      // 转换响应格式
      const statusData = response.data
      project.value = {
        id: statusData.project_id,
        title: statusData.title,
        type: 'status',
        status: statusData.status,
        progress: statusData.progress || 0,
        updated_at: statusData.updated_at,
        customer_name: statusData.customer_name,
        engineer_name: statusData.engineer_name,
        salesman_name: statusData.salesman_name,
        from_cache: statusData.from_cache,
        cache_time: statusData.from_cache ? `缓存${statusData.cache_ttl || 300}秒` : '实时'
      }
    } else {
      // 调用完整项目详情API
      response = await axios.get(`http://localhost:8000/api/projects/${projectId}`, {
        params: { 
          token,
          use_cache: true // 优先使用缓存数据
        }
      })
      
      if (response.data.project) {
        project.value = response.data.project
        // 添加缓存标识
        if (response.data.from_cache) {
          project.value.from_cache = true
          project.value.cache_time = response.data.cache_time || '刚刚'
        }
      } else {
        project.value = getMockData(projectId)
        project.value.from_cache = true
        project.value.cache_time = '模拟数据'
      }
    }
  } catch (error) {
    console.error('加载失败:', error)
    project.value = getMockData(route.params.id)
    project.value.from_cache = true
    project.value.cache_time = '模拟数据'
  } finally {
    loading.value = false
  }
}

// 刷新项目状态
const refreshStatus = async () => {
  refreshing.value = true
  try {
    const projectId = route.params.id
    const token = route.query.token
    
    // 强制从远程获取最新状态
    const response = await axios.get(`http://localhost:8000/api/projects/${projectId}`, {
      params: { 
        token,
        use_cache: false, // 不使用缓存，强制刷新
        force_sync: true  // 强制同步远程数据
      }
    })
    
    if (response.data.project) {
      project.value = response.data.project
      project.value.from_cache = false
      project.value.cache_time = '刚刚更新'
      ElMessage.success('状态已更新')
    } else {
      ElMessage.warning('暂无更新')
    }
  } catch (error) {
    console.error('刷新失败:', error)
    ElMessage.error('刷新失败，请稍后重试')
  } finally {
    refreshing.value = false
  }
}

// 模拟数据
const getMockData = (id) => {
  const type = route.query.type || 'aftersales'
  
  if (type === 'presale') {
    return {
      id: id,
      type: 'presale',
      title: '空调销售商机',
      status: 'pending',
      customer_name: '张三',
      phone: '138****8888',
      product: '中央空调',
      budget: 50000,
      urgency: 4,
      description: '需要为新办公室安装中央空调，面积约200平米，希望节能环保型号',
      created_at: '2024-02-01 10:00',
      salesman_name: '李销售',
      salesman_phone: '139****9999',
      last_follow: '2024-02-01 14:30',
      expected_close: '2024-02-15',
      follow_records: [
        { id: 1, time: '2024-02-01 14:30', salesman: '李销售', content: '已联系客户，了解详细需求' },
        { id: 2, time: '2024-02-01 10:00', salesman: '系统', content: '商机创建' }
      ]
    }
  } else if (type === 'sales') {
    return {
      id: id,
      type: 'sales',
      title: '空调购买订单',
      status: 'shipped',
      order_id: 'ORD' + id,
      order_time: '2024-02-01 10:00',
      customer_name: '王五',
      phone: '137****7777',
      amount: 8999,
      payment_status: 'paid',
      shipping_address: '北京市朝阳区xxx路xxx号',
      items: [
        { name: '格力空调', specs: '1.5匹', quantity: 2, price: 3999, total: 7998 },
        { name: '安装服务', specs: '-', quantity: 1, price: 1000, total: 1000 }
      ],
      logistics: [
        { id: 1, time: '2024-02-03 10:00', content: '商品已发货' },
        { id: 2, time: '2024-02-02 16:00', content: '订单已打包' }
      ]
    }
  } else {
    return {
      id: id,
      type: 'aftersales',
      title: '空调维修工单',
      status: 'completed',
      service_type: '维修',
      customer_name: '李四',
      phone: '136****6666',
      equipment: '格力空调',
      issue_description: '空调不制冷，噪音大',
      service_address: '北京市海淀区xxx小区xxx号楼xxx室',
      appointment_time: '2024-02-03 14:00',
      created_at: '2024-02-01 09:00',
      assigned_at: '2024-02-01 09:30',
      processing_at: '2024-02-03 14:00',
      completed_at: '2024-02-03 16:00',
      engineer_name: '张工',
      engineer_phone: '135****5555',
      priority: '紧急',
      expected_complete: '2024-02-03',
      service_records: [
        { id: 1, time: '2024-02-03 16:00', engineer: '张工', content: '维修完成，已更换压缩机', type: 'success' },
        { id: 2, time: '2024-02-03 14:00', engineer: '张工', content: '已到达现场，开始检查', type: 'primary' },
        { id: 3, time: '2024-02-01 09:30', engineer: '系统', content: '工单已分配给张工', type: 'info' }
      ]
    }
  }
}

// 辅助函数
const getTypeText = (type) => {
  const texts = {
    'presale': '售前商机',
    'aftersales': '售后服务',
    'sales': '销售订单'
  }
  return texts[type] || type
}

const getTypeIcon = (type) => {
  const icons = {
    'presale': '💼',
    'aftersales': '🔧',
    'sales': '📦'
  }
  return icons[type] || '📋'
}

const getTypeTagColor = (type) => {
  const colors = {
    'presale': 'primary',
    'aftersales': 'warning',
    'sales': 'success'
  }
  return colors[type] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    'pending': '待处理',
    'processing': '处理中',
    'completed': '已完成',
    'resolved': '已解决',
    'shipped': '已发货'
  }
  return texts[status] || status
}

const getStatusTagColor = (status) => {
  const colors = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'resolved': 'success',
    'shipped': 'success'
  }
  return colors[status] || 'info'
}

const getPriorityType = (priority) => {
  if (priority === '紧急') return 'danger'
  if (priority === '高') return 'warning'
  return 'info'
}

const getStepActive = (status) => {
  const steps = {
    'pending': 0,
    'assigned': 1,
    'processing': 2,
    'completed': 3
  }
  return steps[status] || 0
}

const getProgressColor = (progress) => {
  if (progress >= 80) return '#67c23a'  // 绿色
  if (progress >= 60) return '#409eff'  // 蓝色
  if (progress >= 40) return '#e6a23c'  // 橙色
  return '#f56c6c'                      // 红色
}

const formatTime = (time) => {
  if (!time) return '未知'
  try {
    const date = new Date(time)
    return date.toLocaleString('zh-CN')
  } catch {
    return time
  }
}

// 标记为已解决
const markAsResolved = async () => {
  try {
    await axios.post(`http://localhost:8000/api/projects/${project.value.id}/resolve`)
    ElMessage.success('已标记为已解决')
    project.value.status = 'resolved'
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 提交反馈
const submitFeedback = async () => {
  try {
    await axios.post(`http://localhost:8000/api/projects/${project.value.id}/feedback`, feedbackForm.value)
    
    if (feedbackForm.value.resolved) {
      ElMessage.success('感谢您的反馈！')
    } else {
      ElMessage.warning('问题已转交工程师，我们会尽快为您处理')
    }
  } catch (error) {
    ElMessage.error('提交失败')
  }
}

onMounted(() => {
  loadProjectDetail()
})
</script>

<style scoped>
.project-detail {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
}

.detail-container {
  max-width: 1400px;
  margin: 0 auto;
}

.header-card {
  margin-bottom: 20px;
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left h2 {
  margin: 0 0 10px 0;
  font-size: 24px;
}

.project-meta {
  display: flex;
  gap: 10px;
  align-items: center;
}

.project-id {
  color: #909399;
  font-size: 14px;
}

.need-content,
.issue-content {
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  line-height: 1.6;
}

.sales-info,
.engineer-info {
  text-align: center;
}

.sales-info h3,
.engineer-info h3 {
  margin: 10px 0 5px;
}

.sales-info p,
.engineer-info p {
  color: #909399;
  margin: 5px 0;
}

.amount {
  font-size: 20px;
  color: #f56c6c;
  font-weight: bold;
}

.payment-section {
  text-align: center;
}

.amount-big {
  font-size: 36px;
  color: #f56c6c;
  font-weight: bold;
  margin: 20px 0;
}

.contact-info {
  text-align: center;
}

.loading-card,
.error-card {
  max-width: 800px;
  margin: 50px auto;
}

/* 状态查询卡片样式 */
.status-query-card {
  max-width: 600px;
  margin: 20px auto;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.status-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 25px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
}

.status-badge-container {
  flex: 1;
}

.status-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-bottom: 25px;
}

.status-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  line-height: 1.6;
}

.status-item-label {
  color: #909399;
  font-size: 12px;
  display: block;
  margin-bottom: 5px;
}

.status-item-value {
  color: #303133;
  font-weight: 500;
  font-size: 14px;
}

.progress-section {
  margin-bottom: 25px;
}

.progress-section :deep(.el-statistic__content) {
  font-size: 28px;
  font-weight: bold;
}

.progress-bar {
  margin-top: 10px;
}

.people-section {
  margin-bottom: 25px;
}

.people-section-title {
  color: #606266;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 12px;
}

.people-item {
  display: flex;
  align-items: center;
  padding: 10px;
  margin-bottom: 8px;
  background: #f9fafc;
  border-left: 3px solid #409eff;
  border-radius: 2px;
}

.people-item.customer {
  border-left-color: #67c23a;
}

.people-item.engineer {
  border-left-color: #e6a23c;
}

.people-item.salesman {
  border-left-color: #909399;
}

.people-role {
  color: #606266;
  font-size: 12px;
  min-width: 60px;
  margin-right: 10px;
}

.people-name {
  color: #303133;
  font-weight: 500;
  flex: 1;
}

.ai-info-alert {
  margin-top: 20px;
  background: #e6f7ff;
  border-left: 4px solid #409eff;
}

.ai-info-alert :deep(.el-alert__title) {
  font-size: 13px;
  color: #0a5caf;
}

.ai-info-alert :deep(.el-alert__content) {
  font-size: 12px;
  color: #0a5caf;
}
</style>
