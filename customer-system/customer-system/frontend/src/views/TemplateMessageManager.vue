<template>
  <div class="template-message-manager">
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 模板管理 -->
      <el-tab-pane label="📝 模板管理" name="templates">
        <el-card>
          <div style="margin-bottom: 20px;">
            <el-button type="primary" @click="loadTemplates">刷新</el-button>
          </div>

          <el-table :data="templates" border style="width: 100%">
            <el-table-column prop="id" label="ID" width="60"></el-table-column>
            <el-table-column prop="name" label="模板名称" width="150"></el-table-column>
            <el-table-column prop="channel_type" label="渠道" width="120"></el-table-column>
            <el-table-column prop="send_mode" label="模式" width="100"></el-table-column>
            <el-table-column prop="description" label="描述"></el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="scope">
                <el-button type="primary" size="small" @click="previewTemplate(scope.row)">
                  预览
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- 消息记录 -->
      <el-tab-pane label="📋 消息记录" name="messages">
        <el-card>
          <el-empty description="消息记录功能开发中"></el-empty>
        </el-card>
      </el-tab-pane>

      <!-- 渠道配置 -->
      <el-tab-pane label="⚙️ 渠道配置" name="channels">
        <el-card>
          <el-empty description="渠道配置功能开发中"></el-empty>
        </el-card>
      </el-tab-pane>

      <!-- 统计分析 -->
      <el-tab-pane label="📊 统计分析" name="stats">
        <el-card>
          <el-empty description="统计分析功能开发中"></el-empty>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 预览对话框 -->
    <el-dialog v-model="previewVisible" title="模板预览" width="600px">
      <div v-if="previewContent">
        <pre style="white-space: pre-wrap; background: #f5f5f5; padding: 15px; border-radius: 4px;">{{ previewContent }}</pre>
      </div>
      <div v-else>
        <el-empty description="加载中..."></el-empty>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const API_BASE = 'http://localhost:8001/api/template'

const activeTab = ref('templates')
const templates = ref([])
const previewVisible = ref(false)
const previewContent = ref('')

// 加载模板列表
const loadTemplates = async () => {
  try {
    const response = await axios.get(`${API_BASE}/list`)
    templates.value = response.data.templates || []
    ElMessage.success(`加载成功，共 ${templates.value.length} 个模板`)
  } catch (error) {
    ElMessage.error('加载失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 预览模板
const previewTemplate = async (template) => {
  try {
    const response = await axios.get(`${API_BASE}/preview/${template.id}`)
    previewContent.value = response.data.preview_content
    previewVisible.value = true
  } catch (error) {
    ElMessage.error('预览失败: ' + (error.response?.data?.detail || error.message))
  }
}

onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.template-message-manager {
  padding: 20px;
}
</style>
