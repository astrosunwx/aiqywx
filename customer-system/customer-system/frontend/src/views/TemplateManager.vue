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
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-switch v-model="scope.row.status" @change="toggleStatus(scope.row)"></el-switch>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="scope">
            <el-button size="small" @click="editTemplate(scope.row)">编辑</el-button>
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
      <el-form :model="templateForm" label-width="100px">
        <el-form-item label="模板名称">
          <el-input v-model="templateForm.name" placeholder="请输入模板名称"></el-input>
        </el-form-item>

        <el-form-item label="分类">
          <el-input v-model="templateForm.category"></el-input>
        </el-form-item>

        <el-form-item label="模板类型">
          <el-radio-group v-model="templateForm.type">
            <el-radio label="text">纯文本</el-radio>
            <el-radio label="markdown">Markdown</el-radio>
            <el-radio label="html">HTML</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="模板内容">
          <el-input 
            v-model="templateForm.content" 
            type="textarea" 
            :rows="8"
            placeholder="请输入模板内容，支持变量 {customer_name}、{phone} 等"
          ></el-input>
        </el-form-item>

        <el-form-item label="AI模型" v-if="activeTab === 'AI'">
          <el-select v-model="templateForm.ai_model" placeholder="选择AI模型">
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
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTemplate">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const activeTab = ref('SMS')
const dialogVisible = ref(false)
const isEdit = ref(false)
const templates = ref([])
const aiModels = ref([])

const templateForm = ref({
  id: null,
  name: '',
  category: '',
  type: 'text',
  content: '',
  ai_model: 'wework-official',
  status: true,
  variables: []
})

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
  templateForm.value = {
    id: null,
    name: '',
    category: '',
    type: 'text',
    content: '',
    ai_model: 'wework-official',
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

const saveTemplate = () => {
  if (!templateForm.value.name || !templateForm.value.content) {
    ElMessage.warning('请填写模板名称和内容')
    return
  }

  if (isEdit.value) {
    const index = templates.value.findIndex(t => t.id === templateForm.value.id)
    if (index !== -1) {
      templates.value[index] = { ...templateForm.value }
    }
    ElMessage.success('模板已更新')
  } else {
    templateForm.value.id = Date.now()
    templates.value.push({ ...templateForm.value })
    ElMessage.success('模板已创建')
  }

  dialogVisible.value = false
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

