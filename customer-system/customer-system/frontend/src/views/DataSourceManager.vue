<template>
  <div class="datasource-manager">
    <el-card class="header-card">
      <div class="header-content">
        <div>
          <h3><el-icon><Connection /></el-icon> 数据源管理</h3>
          <p class="desc">管理多个远程数据库连接,用于项目同步</p>
        </div>
        <el-button type="primary" @click="showAddDialog" :icon="Plus">添加数据源</el-button>
      </div>
    </el-card>

    <!-- 数据源列表 -->
    <el-table :data="datasources" stripe style="width: 100%">
      <el-table-column type="expand">
        <template #default="{ row }">
          <div class="expand-detail">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="数据库类型">
                <el-tag :type="getDbTypeTag(row.db_type)">{{ getDbTypeName(row.db_type) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="主机地址">{{ row.db_host }}:{{ row.db_port }}</el-descriptions-item>
              <el-descriptions-item label="数据库名">{{ row.db_name }}</el-descriptions-item>
              <el-descriptions-item label="用户名">{{ row.db_username }}</el-descriptions-item>
              <el-descriptions-item label="字符集">{{ row.db_charset }}</el-descriptions-item>
              <el-descriptions-item label="SSL连接">
                <el-tag :type="row.use_ssl ? 'success' : 'info'" size="small">
                  {{ row.use_ssl ? '已启用' : '未启用' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ formatTime(row.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="更新时间">{{ formatTime(row.updated_at) }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="数据源名称" prop="source_name" min-width="150">
        <template #default="{ row }">
          <strong>{{ row.source_name }}</strong>
          <el-tag v-if="row.is_default" type="success" size="small" style="margin-left: 8px">默认</el-tag>
        </template>
      </el-table-column>

      <el-table-column label="描述" prop="source_desc" min-width="200" show-overflow-tooltip />

      <el-table-column label="数据库类型" width="120">
        <template #default="{ row }">
          <el-tag :type="getDbTypeTag(row.db_type)">{{ getDbTypeName(row.db_type) }}</el-tag>
        </template>
      </el-table-column>

      <el-table-column label="连接地址" min-width="200">
        <template #default="{ row }">
          <code class="connection-info">{{ row.db_host }}:{{ row.db_port }}/{{ row.db_name }}</code>
        </template>
      </el-table-column>

      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button-group size="small">
            <el-button @click="testConnection(row)" :icon="Connection" :loading="testing === row.id">
              测试连接
            </el-button>
            <el-button v-if="!row.is_default" @click="setDefault(row)" :icon="Star">设为默认</el-button>
            <el-button @click="editDatasource(row)" :icon="Edit">编辑</el-button>
            <el-button type="danger" @click="deleteDatasource(row)" :icon="Delete">删除</el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <!-- 添加/编辑数据源对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'add' ? '添加数据源' : '编辑数据源'"
      width="600px"
      @close="resetForm"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="120px">
        <el-form-item label="数据源名称" prop="source_name">
          <el-input v-model="formData.source_name" placeholder="例如: 客户A项目库" />
          <span class="hint">建议使用有意义的名称,方便区分不同数据源</span>
        </el-form-item>

        <el-form-item label="描述" prop="source_desc">
          <el-input v-model="formData.source_desc" type="textarea" :rows="2" placeholder="可选,描述这个数据源的用途" />
        </el-form-item>

        <el-form-item label="数据库类型" prop="db_type">
          <el-select v-model="formData.db_type" placeholder="选择数据库类型" @change="onDbTypeChange">
            <el-option label="MySQL" value="mysql" />
            <el-option label="PostgreSQL" value="postgresql" />
            <el-option label="SQL Server" value="sqlserver" />
          </el-select>
          <span class="hint">SQL Server连接需要额外安装pyodbc驱动</span>
        </el-form-item>

        <el-form-item label="主机地址" prop="db_host">
          <el-input v-model="formData.db_host" placeholder="IP地址或域名,例如: 192.168.1.100" />
        </el-form-item>

        <el-form-item label="端口号" prop="db_port">
          <el-input-number v-model="formData.db_port" :min="1" :max="65535" style="width: 100%" />
        </el-form-item>

        <el-form-item label="数据库名" prop="db_name">
          <el-input v-model="formData.db_name" placeholder="要连接的数据库名称" />
        </el-form-item>

        <el-form-item label="用户名" prop="db_username">
          <el-input v-model="formData.db_username" placeholder="数据库登录用户名" />
        </el-form-item>

        <el-form-item label="密码" prop="db_password">
          <el-input v-model="formData.db_password" type="password" show-password placeholder="数据库登录密码" />
        </el-form-item>

        <el-form-item label="字符集">
          <el-input v-model="formData.db_charset" placeholder="默认: utf8mb4" />
        </el-form-item>

        <el-form-item label="启用SSL">
          <el-switch v-model="formData.use_ssl" />
          <span class="hint" style="margin-left: 12px">使用SSL加密连接(需要数据库支持)</span>
        </el-form-item>

        <el-form-item label="启用状态">
          <el-switch v-model="formData.is_active" />
        </el-form-item>

        <el-form-item label="设为默认">
          <el-switch v-model="formData.is_default" />
          <span class="hint" style="margin-left: 12px">默认数据源将用于自动同步</span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Connection, Plus, Edit, Delete, Star } from '@element-plus/icons-vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001'

// 数据源列表
const datasources = ref([])
const testing = ref(null)
const saving = ref(false)

// 对话框
const dialogVisible = ref(false)
const dialogMode = ref('add') // 'add' or 'edit'
const formRef = ref(null)

// 表单数据
const formData = reactive({
  id: null,
  source_name: '',
  source_desc: '',
  db_type: 'mysql',
  db_host: '',
  db_port: 3306,
  db_name: '',
  db_username: '',
  db_password: '',
  db_charset: 'utf8mb4',
  use_ssl: false,
  is_active: true,
  is_default: false
})

// 表单验证规则
const formRules = {
  source_name: [{ required: true, message: '请输入数据源名称', trigger: 'blur' }],
  db_type: [{ required: true, message: '请选择数据库类型', trigger: 'change' }],
  db_host: [{ required: true, message: '请输入主机地址', trigger: 'blur' }],
  db_port: [{ required: true, message: '请输入端口号', trigger: 'blur' }],
  db_name: [{ required: true, message: '请输入数据库名', trigger: 'blur' }],
  db_username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  db_password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 加载数据源列表
const loadDatasources = async () => {
  try {
    const response = await axios.get(`${API_BASE}/api/datasources/`)
    datasources.value = response.data
  } catch (error) {
    console.error('加载数据源失败:', error)
    ElMessage.error('加载数据源失败')
  }
}

// 显示添加对话框
const showAddDialog = () => {
  dialogMode.value = 'add'
  resetForm()
  dialogVisible.value = true
}

// 编辑数据源
const editDatasource = (row) => {
  dialogMode.value = 'edit'
  Object.assign(formData, {
    id: row.id,
    source_name: row.source_name,
    source_desc: row.source_desc,
    db_type: row.db_type,
    db_host: row.db_host,
    db_port: row.db_port,
    db_name: row.db_name,
    db_username: row.db_username,
    db_password: row.db_password,
    db_charset: row.db_charset,
    use_ssl: row.use_ssl,
    is_active: row.is_active,
    is_default: row.is_default
  })
  dialogVisible.value = true
}

// 删除数据源
const deleteDatasource = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除数据源 "${row.source_name}" 吗?此操作无法撤销。`,
      '确认删除',
      { type: 'warning' }
    )
    
    await axios.delete(`${API_BASE}/api/datasources/${row.id}`)
    ElMessage.success('删除成功')
    loadDatasources()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 测试连接
const testConnection = async (row) => {
  testing.value = row.id
  try {
    const response = await axios.post(`${API_BASE}/api/datasources/${row.id}/test`)
    if (response.data.status === 'success') {
      ElMessage.success(response.data.message)
    } else {
      ElMessage.error(response.data.message)
    }
  } catch (error) {
    console.error('测试连接失败:', error)
    ElMessage.error('测试连接失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    testing.value = null
  }
}

// 设为默认
const setDefault = async (row) => {
  try {
    await axios.post(`${API_BASE}/api/datasources/${row.id}/set-default`)
    ElMessage.success(`"${row.source_name}" 已设为默认数据源`)
    loadDatasources()
  } catch (error) {
    console.error('设置失败:', error)
    ElMessage.error('设置失败')
  }
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    saving.value = true
    try {
      if (dialogMode.value === 'add') {
        await axios.post(`${API_BASE}/api/datasources/`, formData)
        ElMessage.success('添加成功')
      } else {
        await axios.put(`${API_BASE}/api/datasources/${formData.id}`, formData)
        ElMessage.success('更新成功')
      }
      
      dialogVisible.value = false
      loadDatasources()
    } catch (error) {
      console.error('保存失败:', error)
      ElMessage.error(error.response?.data?.detail || '保存失败')
    } finally {
      saving.value = false
    }
  })
}

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    id: null,
    source_name: '',
    source_desc: '',
    db_type: 'mysql',
    db_host: '',
    db_port: 3306,
    db_name: '',
    db_username: '',
    db_password: '',
    db_charset: 'utf8mb4',
    use_ssl: false,
    is_active: true,
    is_default: false
  })
  formRef.value?.clearValidate()
}

// 数据库类型改变
const onDbTypeChange = (type) => {
  const portMap = {
    mysql: 3306,
    postgresql: 5432,
    sqlserver: 1433
  }
  formData.db_port = portMap[type] || 3306
}

// 工具函数
const getDbTypeName = (type) => {
  const names = {
    mysql: 'MySQL',
    postgresql: 'PostgreSQL',
    sqlserver: 'SQL Server'
  }
  return names[type] || type
}

const getDbTypeTag = (type) => {
  const tags = {
    mysql: 'primary',
    postgresql: 'success',
    sqlserver: 'warning'
  }
  return tags[type] || ''
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

// 初始化
onMounted(() => {
  loadDatasources()
})
</script>

<style scoped>
.datasource-manager {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h3 {
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 20px;
  color: #333;
}

.header-content .desc {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.connection-info {
  background-color: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #606266;
}

.expand-detail {
  padding: 20px;
}

.hint {
  font-size: 12px;
  color: #909399;
  display: block;
  margin-top: 4px;
}

:deep(.el-button-group) {
  display: flex;
  gap: 4px;
}
</style>
