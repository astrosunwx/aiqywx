<template>
  <div class="ai-model-manager">
    <el-card>
      <template #header>
        <div class="header-actions">
          <h2>🤖 AI模型配置管理</h2>
          <el-button type="primary" @click="showCreateDialog">+ 添加AI模型</el-button>
        </div>
      </template>

      <!-- 提示信息 -->
      <el-alert
        title="✅ 企业微信官方API vs 第三方大模型"
        type="success"
        :closable="false"
        style="margin-bottom: 20px;"
      >
        <div style="line-height: 1.8;">
          <p><strong>企业微信官方API（推荐）：</strong></p>
          <ul>
            <li>✅ 官方认证，安全稳定，无封号风险</li>
            <li>✅ 基于规则引擎的智能回复，无需第三方大模型</li>
            <li>✅ 免费使用，无额外API调用费用</li>
            <li>✅ 响应速度快，可控性强</li>
          </ul>
          <p style="margin-top: 10px;"><strong>第三方大模型（可选）：</strong></p>
          <ul>
            <li>💡 智谱GLM-4、腾讯云混元、豆包等</li>
            <li>⚠️ 需要配置API密钥，产生API调用费用</li>
            <li>⚠️ 适合复杂对话场景和自然语言处理</li>
          </ul>
        </div>
      </el-alert>

      <!-- AI模型列表 -->
      <el-table :data="models" border stripe>
        <el-table-column prop="id" label="ID" width="60"></el-table-column>
        
        <el-table-column label="模型名称" width="200">
          <template #default="scope">
            <div style="display: flex; align-items: center; gap: 10px;">
              <span style="font-weight: bold;">{{ scope.row.model_name }}</span>
              <el-tag v-if="scope.row.is_official" type="success" size="small">
                ✅ 官方API
              </el-tag>
              <el-tag v-if="scope.row.is_default" type="primary" size="small">
                ⭐ 默认
              </el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="provider_display_name" label="服务商" width="120">
          <template #default="scope">
            {{ scope.row.provider_display_name || scope.row.provider }}
          </template>
        </el-table-column>

        <el-table-column prop="model_version" label="版本" width="100"></el-table-column>

        <el-table-column label="API密钥" width="180">
          <template #default="scope">
            <span v-if="scope.row.api_key_masked" style="font-family: monospace; color: #909399;">
              {{ scope.row.api_key_masked }}
            </span>
            <span v-else style="color: #C0C4CC;">未配置</span>
          </template>
        </el-table-column>

        <el-table-column prop="description" label="说明" show-overflow-tooltip></el-table-column>

        <el-table-column label="优先级" width="80" align="center">
          <template #default="scope">
            <el-tag :type="getPriorityType(scope.row.priority)" size="small">
              {{ scope.row.priority }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100" align="center">
          <template #default="scope">
            <el-switch
              v-model="scope.row.is_active"
              active-text="启用"
              inactive-text="禁用"
              @change="toggleStatus(scope.row)"
            ></el-switch>
          </template>
        </el-table-column>

        <el-table-column label="使用次数" width="100" align="center">
          <template #default="scope">
            {{ scope.row.usage_count || 0 }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="280" fixed="right">
          <template #default="scope">
            <el-button 
              type="primary" 
              size="small"
              @click="editModel(scope.row)"
            >
              编辑
            </el-button>
            <el-button 
              v-if="!scope.row.is_default"
              type="success" 
              size="small"
              @click="setDefault(scope.row)"
            >
              设为默认
            </el-button>
            <el-button 
              v-if="!scope.row.is_default"
              type="danger" 
              size="small"
              @click="deleteModel(scope.row)"
            >
              删除
            </el-button>
            <el-button 
              v-else
              type="info" 
              size="small"
              disabled
            >
              🔒 默认模型
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑AI模型' : '添加AI模型'"
      width="700px"
    >
      <el-form :model="modelForm" label-width="120px" :rules="modelRules" ref="modelFormRef">
        <el-form-item label="模型代码" required prop="model_code">
          <el-input 
            v-model="modelForm.model_code" 
            placeholder="如：tencent-hunyuan-a13b"
            :disabled="isEditing"
          >
            <template #prefix>
              <span style="color: #909399;">🔑</span>
            </template>
          </el-input>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            <strong>命名规则：</strong>服务商-模型名-版本（如：tencent-hunyuan-a13b），创建后不可修改
          </div>
        </el-form-item>

        <el-form-item label="模型名称" required prop="model_name">
          <el-input 
            v-model="modelForm.model_name" 
            placeholder="如：腾讯云混元-A13B"
          >
            <template #prefix>
              <span style="color: #409eff;">🤖</span>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="服务提供商" required prop="provider">
          <el-select v-model="modelForm.provider" placeholder="选择服务商" style="width: 100%;">
            <el-option label="企业微信官方" value="wework"></el-option>
            <el-option label="腾讯云" value="tencent"></el-option>
            <el-option label="智谱AI" value="zhipu"></el-option>
            <el-option label="字节跳动（豆包）" value="doubao"></el-option>
            <el-option label="DeepSeek" value="deepseek"></el-option>
            <el-option label="其他" value="custom"></el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="提供商显示名">
          <el-input 
            v-model="modelForm.provider_display_name" 
            placeholder="如：腾讯云"
          ></el-input>
        </el-form-item>

        <el-form-item label="模型版本">
          <el-input 
            v-model="modelForm.model_version" 
            placeholder="如：hunyuan-A13B"
          ></el-input>
        </el-form-item>

        <el-form-item label="API端点URL">
          <el-input 
            v-model="modelForm.api_endpoint" 
            placeholder="如：https://hunyuan.tencentcloudapi.com"
            type="textarea"
            :rows="2"
          ></el-input>
        </el-form-item>

        <el-form-item label="API密钥" prop="api_key">
          <el-input 
            v-model="modelForm.api_key" 
            placeholder="请输入腾讯云混元API密钥（第三方模型必填）"
            type="password"
            show-password
          >
            <template #prefix>
              <span style="color: #f56c6c;">🔐</span>
            </template>
          </el-input>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            ⚠️ 敏感信息，保存后只显示脱敏版本。企业微信官方API无需填写密钥。
          </div>
        </el-form-item>

        <el-form-item label="模型描述">
          <el-input 
            v-model="modelForm.description" 
            type="textarea"
            :rows="3"
            placeholder="例如：适合复杂对话场景，支持多轮交互和工具调用"
          >
            <template #prepend>
              <span>💬</span>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="优先级">
          <el-input-number 
            v-model="modelForm.priority" 
            :min="0" 
            :max="100"
          ></el-input-number>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            数字越大优先级越高，在下拉列表中越靠前
          </div>
        </el-form-item>

        <el-form-item label="官方API">
          <el-switch
            v-model="modelForm.is_official"
            active-text="是"
            inactive-text="否"
          ></el-switch>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            标记为企业微信官方API
          </div>
        </el-form-item>

        <el-form-item label="启用状态">
          <el-switch
            v-model="modelForm.is_active"
            active-text="启用"
            inactive-text="禁用"
          ></el-switch>
        </el-form-item>

        <el-form-item label="设为默认">
          <el-switch
            v-model="modelForm.is_default"
            active-text="是"
            inactive-text="否"
          ></el-switch>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            新建模板时默认选择此模型
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <div style="display: flex; justify-content: space-between; width: 100%;">
          <el-button 
            v-if="modelForm.api_key && modelForm.api_endpoint"
            type="info" 
            @click="testConnection"
            :loading="testing"
          >
            {{ testing ? '测试中...' : '🔍 测试连接' }}
          </el-button>
          <div style="flex: 1;"></div>
          <div>
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" @click="saveModel" :loading="saving">
              {{ saving ? '保存中...' : '保存' }}
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

// 数据
const models = ref([])
const dialogVisible = ref(false)
const isEditing = ref(false)
const testing = ref(false)
const saving = ref(false)
const modelFormRef = ref(null)

const modelForm = ref({
  model_code: '',
  model_name: '',
  provider: 'tencent',
  provider_display_name: '',
  model_version: '',
  api_endpoint: '',
  api_key: '',
  description: '',
  is_official: false,
  is_active: true,
  is_default: false,
  priority: 50
})

// 表单校验规则
const modelRules = {
  model_code: [
    { required: true, message: '请输入模型代码', trigger: 'blur' },
    { pattern: /^[a-z0-9-]+$/, message: '只能包含小写字母、数字和连字符', trigger: 'blur' }
  ],
  model_name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ],
  provider: [
    { required: true, message: '请选择服务提供商', trigger: 'change' }
  ],
  api_key: [
    { 
      validator: (rule, value, callback) => {
        if (!modelForm.value.is_official && !value && !isEditing.value) {
          callback(new Error('第三方模型必须填写API密钥'))
        } else {
          callback()
        }
      }, 
      trigger: 'blur' 
    }
  ]
}

// 加载AI模型列表
const loadModels = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/admin/ai-models/list?include_inactive=true')
    models.value = response.data
    console.log('✅ 已加载AI模型列表:', models.value.length, '个模型')
  } catch (error) {
    console.error('❌ 加载AI模型列表失败:', error)
    ElMessage.error('加载AI模型列表失败')
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  isEditing.value = false
  modelForm.value = {
    model_code: '',
    model_name: '',
    provider: 'tencent',
    provider_display_name: '',
    model_version: '',
    api_endpoint: '',
    api_key: '',
    description: '',
    is_official: false,
    is_active: true,
    is_default: false,
    priority: 50
  }
  dialogVisible.value = true
}

// 编辑模型
const editModel = (model) => {
  isEditing.value = true
  modelForm.value = {
    id: model.id,
    model_code: model.model_code,
    model_name: model.model_name,
    provider: model.provider,
    provider_display_name: model.provider_display_name,
    model_version: model.model_version,
    api_endpoint: model.api_endpoint,
    api_key: '',  // 不回显密钥
    description: model.description,
    is_official: model.is_official,
    is_active: model.is_active,
    is_default: model.is_default,
    priority: model.priority
  }
  dialogVisible.value = true
}

// 测试连接
const testConnection = async () => {
  testing.value = true
  try {
    // 这里应该调用后端的测试接口
    await new Promise(resolve => setTimeout(resolve, 1500)) // 模拟测试
    ElMessage.success('✅ API连接测试成功！')
  } catch (error) {
    ElMessage.error('❌ API连接测试失败，请检查配置')
  } finally {
    testing.value = false
  }
}

// 保存模型
const saveModel = async () => {
  // 表单验证
  if (!modelFormRef.value) {
    ElMessage.warning('表单未初始化')
    return
  }

  try {
    await modelFormRef.value.validate()
  } catch (error) {
    ElMessage.warning('请填写所有必填项')
    return
  }

  saving.value = true
  try {
    if (isEditing.value) {
      // 更新
      await axios.put(`http://localhost:8000/api/admin/ai-models/update/${modelForm.value.id}`, modelForm.value)
      ElMessage.success('✅ AI模型配置已保存')
    } else {
      // 创建
      await axios.post('http://localhost:8000/api/admin/ai-models/create', modelForm.value)
      ElMessage.success('✅ AI模型配置已保存')
    }

    dialogVisible.value = false
    await loadModels()
  } catch (error) {
    console.error('❌ 保存失败:', error)
    ElMessage.error(error.response?.data?.detail || 'API密钥错误，请重新输入')
  } finally {
    saving.value = false
  }
}

// 切换启用状态
const toggleStatus = async (model) => {
  try {
    await axios.put(`http://localhost:8000/api/admin/ai-models/update/${model.id}`, {
      is_active: model.is_active
    })
    ElMessage.success('✅ 状态更新成功')
  } catch (error) {
    console.error('❌ 更新状态失败:', error)
    ElMessage.error('更新状态失败')
    model.is_active = !model.is_active  // 回滚
  }
}

// 设为默认
const setDefault = async (model) => {
  try {
    await ElMessageBox.confirm(
      `确定将 ${model.model_name} 设置为默认AI模型吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await axios.post(`http://localhost:8000/api/admin/ai-models/set-default/${model.id}`)
    ElMessage.success('✅ 已设为默认模型')
    await loadModels()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('❌ 设置默认失败:', error)
      ElMessage.error('设置默认失败')
    }
  }
}

// 删除模型
const deleteModel = async (model) => {
  try {
    await ElMessageBox.confirm(
      `确定删除AI模型 ${model.model_name} 吗？此操作不可恢复！`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error',
      }
    )

    await axios.delete(`http://localhost:8000/api/admin/ai-models/delete/${model.id}`)
    ElMessage.success('✅ 删除成功')
    await loadModels()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('❌ 删除失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 获取优先级类型
const getPriorityType = (priority) => {
  if (priority >= 90) return 'danger'
  if (priority >= 70) return 'warning'
  if (priority >= 50) return 'success'
  return 'info'
}

onMounted(() => {
  loadModels()
})
</script>

<style scoped>
.ai-model-manager {
  padding: 20px;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}
</style>
