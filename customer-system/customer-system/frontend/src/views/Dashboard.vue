<template>
  <div class="dashboard">
    <!-- 欢迎区域 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="welcome-card">
          <h1>👋 欢迎使用智能售前售后系统</h1>
          <p style="color: #909399; margin-top: 10px;">
            当前用户: <el-tag type="success">{{ currentUser.name }}</el-tag> 
            角色: <el-tag type="primary">{{ currentUser.role }}</el-tag>
          </p>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷入口 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <h2 style="margin-bottom: 15px;">📌 快捷入口</h2>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <!-- 配置中心 -->
      <el-col :span="6" v-if="hasPermission('config_view')">
        <el-card class="nav-card" shadow="hover" @click="navigateTo('/config')">
          <div class="nav-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <i class="el-icon-setting" style="font-size: 40px;"></i>
          </div>
          <h3>⚙️ 配置中心</h3>
          <p>零代码配置所有参数</p>
          <ul class="feature-list">
            <li>企业微信配置</li>
            <li>AI服务配置</li>
            <li>数据库配置</li>
            <li>权限管理</li>
          </ul>
          <el-button type="primary" style="width: 100%; margin-top: 10px;">
            进入配置
          </el-button>
        </el-card>
      </el-col>

      <!-- 消息管理 -->
      <el-col :span="6" v-if="hasPermission('message_send')">
        <el-card class="nav-card" shadow="hover" @click="navigateTo('/template-messages')">
          <div class="nav-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <i class="el-icon-message" style="font-size: 40px;"></i>
          </div>
          <h3>📨 消息系统（模板版）</h3>
          <p>统一消息模板管理</p>
          <ul class="feature-list">
            <li>📝 模板管理</li>
            <li>📋 消息记录</li>
            <li>⚙️ 渠道配置</li>
            <li>📊 统计分析</li>
          </ul>
          <el-button type="danger" style="width: 100%; margin-top: 10px;">
            进入消息系统
          </el-button>
        </el-card>
      </el-col>

      <!-- 监控大屏 -->
      <el-col :span="6" v-if="hasPermission('monitor_view')">
        <el-card class="nav-card" shadow="hover" @click="navigateTo('/monitor')">
          <div class="nav-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <i class="el-icon-data-analysis" style="font-size: 40px;"></i>
          </div>
          <h3>📊 监控大屏</h3>
          <p>实时数据可视化</p>
          <ul class="feature-list">
            <li>消息发送统计</li>
            <li>成功率分析</li>
            <li>渠道分布</li>
            <li>实时图表</li>
          </ul>
          <el-button type="info" style="width: 100%; margin-top: 10px;">
            查看监控
          </el-button>
        </el-card>
      </el-col>

      <!-- 报表分析 -->
      <el-col :span="6" v-if="hasPermission('report_view')">
        <el-card class="nav-card" shadow="hover" @click="navigateTo('/reports')">
          <div class="nav-icon" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
            <i class="el-icon-document" style="font-size: 40px;"></i>
          </div>
          <h3>📈 报表分析</h3>
          <p>数据统计与分析</p>
          <ul class="feature-list">
            <li>销售报表</li>
            <li>售后统计</li>
            <li>客户分析</li>
            <li>导出数据</li>
          </ul>
          <el-button type="warning" style="width: 100%; margin-top: 10px;">
            查看报表
          </el-button>
        </el-card>
      </el-col>

      <!-- 模板管理 -->
      <el-col :span="6" v-if="hasPermission('template_manage')">
        <el-card class="nav-card" shadow="hover" @click="navigateTo('/templates')">
          <div class="nav-icon" style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);">
            <i class="el-icon-document-copy" style="font-size: 40px;"></i>
          </div>
          <h3>📝 模板管理</h3>
          <p>预制消息和AI模板</p>
          <ul class="feature-list">
            <li>短信/邮件模板</li>
            <li>微信公众号模板</li>
            <li>AI回复关键词</li>
            <li>群机器人消息</li>
          </ul>
          <el-button type="success" style="width: 100%; margin-top: 10px;">
            管理模板
          </el-button>
        </el-card>
      </el-col>

      <!-- AI模型管理 -->
      <el-col :span="6" v-if="hasPermission('config_view')">
        <el-card class="nav-card" shadow="hover" @click="navigateTo('/ai-models')">
          <div class="nav-icon" style="background: linear-gradient(135deg, #fccb90 0%, #d57eeb 100%);">
            <i class="el-icon-cpu" style="font-size: 40px;"></i>
          </div>
          <h3>🤖 AI模型管理</h3>
          <p>配置和管理AI模型</p>
          <ul class="feature-list">
            <li>企业微信官方API</li>
            <li>腾讯云混元模型</li>
            <li>第三方大模型</li>
            <li>使用统计</li>
          </ul>
          <el-button type="primary" style="width: 100%; margin-top: 10px;">
            配置模型
          </el-button>
        </el-card>
      </el-col>
    </el-row>

    <!-- 统计数据 -->
    <el-row :gutter="20" style="margin-top: 30px;">
      <el-col :span="24">
        <h2 style="margin-bottom: 15px;">📊 今日数据</h2>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="6">
        <el-card>
          <template #header>
            <span>待处理项目</span>
          </template>
          <div class="stat-number">{{ stats.pending }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <template #header>
            <span>处理中项目</span>
          </template>
          <div class="stat-number">{{ stats.processing }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <template #header>
            <span>已完成项目</span>
          </template>
          <div class="stat-number">{{ stats.completed }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <template #header>
            <span>总项目数</span>
          </template>
          <div class="stat-number">{{ stats.total }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row style="margin-top: 30px;">
      <el-col :span="24">
        <el-table :data="projects" style="width: 100%" stripe>
          <el-table-column prop="id" label="项目ID" width="100" />
          <el-table-column prop="title" label="项目标题" />
          <el-table-column prop="type" label="类型" width="120">
            <template #default="scope">
              <el-tag v-if="scope.row.type === 'presale'" type="info">售前</el-tag>
              <el-tag v-else-if="scope.row.type === 'installation'" type="warning">安装</el-tag>
              <el-tag v-else type="danger">售后</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="120">
            <template #default="scope">
              <el-tag v-if="scope.row.status === 'pending'" type="info">待处理</el-tag>
              <el-tag v-else-if="scope.row.status === 'processing'" type="warning">处理中</el-tag>
              <el-tag v-else-if="scope.row.status === 'completed'" type="success">已完成</el-tag>
              <el-tag v-else>{{ scope.row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="customer_phone" label="客户手机" width="140" />
          <el-table-column label="操作" width="150">
            <template #default="scope">
              <el-button size="small" @click="viewProject(scope.row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

// 当前用户信息（模拟）
const currentUser = ref({
  name: 'Admin',
  role: '超级管理员',
  permissions: [
    'config_view',
    'config_edit',
    'message_send',
    'message_view',
    'monitor_view',
    'report_view',
    'template_manage',
    'user_manage'
  ]
})

const projects = ref([])
const stats = ref({
  pending: 0,
  processing: 0,
  completed: 0,
  total: 0
})

// 权限检查
const hasPermission = (permission) => {
  return currentUser.value.permissions.includes(permission)
}

// 导航到页面
const navigateTo = (path) => {
  router.push(path)
}

const loadProjects = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/projects')
    projects.value = response.data.projects
    
    // 计算统计数据
    stats.value.total = projects.value.length
    stats.value.pending = projects.value.filter(p => p.status === 'pending').length
    stats.value.processing = projects.value.filter(p => p.status === 'processing').length
    stats.value.completed = projects.value.filter(p => p.status === 'completed').length
  } catch (error) {
    console.error('加载项目失败:', error)
  }
}

const viewProject = (project) => {
  console.log('查看项目:', project)
  // TODO: 实现项目详情查看
}

onMounted(() => {
  loadProjects()
  // 自动刷新（每30秒）
  setInterval(loadProjects, 30000)
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.welcome-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
}

.welcome-card h1 {
  margin: 0;
  font-size: 28px;
}

.nav-card {
  cursor: pointer;
  transition: all 0.3s ease;
  height: 100%;
  min-height: 320px;
}

.nav-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.2) !important;
}

.nav-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 15px;
  color: white;
}

.nav-card h3 {
  text-align: center;
  margin: 10px 0;
  font-size: 18px;
  color: #303133;
}

.nav-card p {
  text-align: center;
  color: #909399;
  font-size: 14px;
  margin: 5px 0 15px;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 10px 0;
}

.feature-list li {
  padding: 5px 0;
  color: #606266;
  font-size: 13px;
}

.feature-list li:before {
  content: "✓ ";
  color: #67c23a;
  font-weight: bold;
  margin-right: 5px;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
  text-align: center;
  padding: 20px 0;
}
</style>
