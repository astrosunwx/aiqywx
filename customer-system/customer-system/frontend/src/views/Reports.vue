<template>
  <div class="reports">
    <el-row :gutter="20">
      <el-col :span="24">
        <h2>销售报表</h2>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>客户来源分析</span>
          </template>
          <el-table :data="sourceData" style="width: 100%">
            <el-table-column prop="source" label="来源渠道" />
            <el-table-column prop="count" label="客户数量" />
            <el-table-column prop="percentage" label="占比" />
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <span>项目类型分布</span>
          </template>
          <el-table :data="typeData" style="width: 100%">
            <el-table-column prop="type" label="项目类型" />
            <el-table-column prop="count" label="数量" />
            <el-table-column prop="percentage" label="占比" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row style="margin-top: 30px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>项目状态统计</span>
          </template>
          <el-table :data="statusData" style="width: 100%">
            <el-table-column prop="status" label="状态" />
            <el-table-column prop="count" label="数量" />
            <el-table-column prop="percentage" label="占比" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'Reports',
  setup() {
    const sourceData = ref([])
    const typeData = ref([])
    const statusData = ref([])

    const loadReports = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/admin/reports/sales')
        const data = response.data

        // 客户来源数据
        const totalSource = data.by_source.wechat_official + data.by_source.wechat_work
        sourceData.value = [
          {
            source: '微信公众号',
            count: data.by_source.wechat_official,
            percentage: `${((data.by_source.wechat_official / totalSource) * 100).toFixed(1)}%`
          },
          {
            source: '企业微信',
            count: data.by_source.wechat_work,
            percentage: `${((data.by_source.wechat_work / totalSource) * 100).toFixed(1)}%`
          }
        ]

        // 项目类型数据
        const totalType = data.by_type.presale + data.by_type.installation + data.by_type.aftersale
        typeData.value = [
          {
            type: '售前咨询',
            count: data.by_type.presale,
            percentage: `${((data.by_type.presale / totalType) * 100).toFixed(1)}%`
          },
          {
            type: '安装服务',
            count: data.by_type.installation,
            percentage: `${((data.by_type.installation / totalType) * 100).toFixed(1)}%`
          },
          {
            type: '售后服务',
            count: data.by_type.aftersale,
            percentage: `${((data.by_type.aftersale / totalType) * 100).toFixed(1)}%`
          }
        ]

        // 项目状态数据
        const totalStatus = Object.values(data.by_status).reduce((a, b) => a + b, 0)
        statusData.value = [
          {
            status: '待处理',
            count: data.by_status.pending,
            percentage: `${((data.by_status.pending / totalStatus) * 100).toFixed(1)}%`
          },
          {
            status: '已联系',
            count: data.by_status.contacted,
            percentage: `${((data.by_status.contacted / totalStatus) * 100).toFixed(1)}%`
          },
          {
            status: '处理中',
            count: data.by_status.processing,
            percentage: `${((data.by_status.processing / totalStatus) * 100).toFixed(1)}%`
          },
          {
            status: '已完成',
            count: data.by_status.completed,
            percentage: `${((data.by_status.completed / totalStatus) * 100).toFixed(1)}%`
          },
          {
            status: '已取消',
            count: data.by_status.cancelled,
            percentage: `${((data.by_status.cancelled / totalStatus) * 100).toFixed(1)}%`
          }
        ]
      } catch (error) {
        console.error('加载报表失败:', error)
      }
    }

    onMounted(() => {
      loadReports()
    })

    return {
      sourceData,
      typeData,
      statusData
    }
  }
}
</script>

<style scoped>
.reports {
  padding: 20px;
}
</style>
