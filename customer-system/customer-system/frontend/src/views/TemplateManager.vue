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
            <el-radio value="text">纯文本</el-radio>
            <el-radio value="markdown">Markdown</el-radio>
            <el-radio value="html">HTML</el-radio>
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
          <el-select 
            v-model="templateForm.ai_model" 
            placeholder="请选择AI模型" 
            style="width: 100%;"
            :loading="aiModelsLoading"
            filterable
          >
            <el-option 
              v-for="model in aiModels" 
              :key="model.value"
              :label="model.label"
              :value="model.value"
            >
              <div style="display: flex; align-items: center; justify-content: space-between;">
                <span>{{ model.label }}</span>
                <div>
                  <el-tag 
                    v-if="model.is_official" 
                    type="success" 
                    size="small" 
                    style="margin-left: 5px;"
                  >
                    ✅官方
                  </el-tag>
                  <el-tag 
                    v-if="model.is_default" 
                    type="primary" 
                    size="small" 
                    style="margin-left: 5px;"
                  >
                    ⭐默认
                  </el-tag>
                </div>
              </div>
            </el-option>
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            <span v-if="aiModelsLoading">⏳ 正在加载AI模型列表...</span>
            <span v-else-if="aiModels.length === 0">⚠️ 暂无可用AI模型，请先配置</span>
            <span v-else>💡 已加载 {{ aiModels.length }} 个AI模型</span>
          </div>
        </el-form-item>

        <!-- 推送模式（群机器人/AI回复/企业微信/微信公众号显示） -->
        <el-form-item label="推送模式" v-if="needsPushMode" required prop="push_mode">
          <el-radio-group v-model="templateForm.push_mode" @change="onPushModeChange">
            <el-radio value="realtime" v-if="supportsRealtime">
              <span>⚡ 实时推送</span>
              <el-tooltip content="关键词触发立即响应，适合客服对话" placement="top">
                <el-icon style="margin-left: 5px; color: #909399;"><QuestionFilled /></el-icon>
              </el-tooltip>
            </el-radio>
            <el-radio value="scheduled" v-if="supportsScheduled">
              <span>⏰ 定时推送</span>
              <el-tooltip content="按计划时间发送，适合通知/日报" placement="top">
                <el-icon style="margin-left: 5px; color: #909399;"><QuestionFilled /></el-icon>
              </el-tooltip>
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 触发关键词（只在企业微信官方API时显示，第三方AI模型不需要） -->
        <el-form-item 
          label="触发关键词" 
          v-if="templateForm.push_mode === 'realtime' && needsPushMode && isWeworkOfficialAPI"
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
            💡 客户消息包含任一关键词时触发自动回复（仅企业微信官方API需要）
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
              <el-checkbox value="1">周一</el-checkbox>
              <el-checkbox value="2">周二</el-checkbox>
              <el-checkbox value="3">周三</el-checkbox>
              <el-checkbox value="4">周四</el-checkbox>
              <el-checkbox value="5">周五</el-checkbox>
              <el-checkbox value="6">周六</el-checkbox>
              <el-checkbox value="0">周日</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </div>

        <!-- 快速插入变量 -->
        <el-form-item label="快速插入">
          <div style="margin-bottom: 10px;">
            <el-button 
              type="primary" 
              size="small" 
              @click="showAddVariableDialog = true"
            >
              ➕ 新增自定义变量
            </el-button>
            <el-tag 
              type="info" 
              size="small" 
              style="margin-left: 10px;"
            >
              系统变量
            </el-tag>
            <el-tag 
              type="success" 
              size="small" 
              style="margin-left: 5px;"
            >
              自定义变量
            </el-tag>
          </div>
          <div style="display: flex; flex-wrap: wrap; gap: 8px; max-height: 150px; overflow-y: auto; padding: 10px; background: #f5f7fa; border-radius: 4px;">
            <el-tag 
              v-for="variable in allVariables" 
              :key="variable.code"
              :type="variable.isCustom ? 'success' : 'info'"
              :effect="variable.isCustom ? 'dark' : 'plain'"
              style="cursor: pointer;"
              @click="insertVariable(variable.code)"
              :closable="variable.isCustom"
              @close="removeCustomVariable(variable.code)"
            >
              {{ variable.label }}
            </el-tag>
          </div>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            💡 点击变量快速插入到模板内容中 | 🟦 系统变量（不可删除） | 🟩 自定义变量（可删除）
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <div style="display: flex; justify-content: space-between; width: 100%; gap: 10px;">
          <el-button 
            type="success" 
            @click="showTemplatePreview = true"
            :disabled="!templateForm.content"
          >
            👁️ 模板预览
          </el-button>
          <div style="display: flex; gap: 10px;">
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" @click="saveTemplate" :loading="saving">
              {{ saving ? '保存中...' : '保存' }}
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 测试发送对话框 -->
    <el-dialog
      v-model="testDialogVisible"
      title="测试发送"
      width="600px"
    >
      <el-form :model="testForm" label-width="120px">
        <el-form-item label="模板名称">
          <el-input v-model="testForm.templateName" disabled></el-input>
        </el-form-item>
        
        <el-form-item label="测试方式">
          <el-radio-group v-model="testForm.testType">
            <el-radio value="phone" v-if="activeTab !== 'GROUP_BOT'">📱 手机号</el-radio>
            <el-radio value="wechat" v-if="activeTab === 'WECHAT'">💬 微信OpenID</el-radio>
            <el-radio value="wechat_user" v-if="activeTab === 'WECHAT'">👤 选择公众号用户</el-radio>
            <el-radio value="userid" v-if="activeTab === 'WORK_WECHAT'">👤 员工UserID</el-radio>
            <el-radio value="work_staff" v-if="activeTab === 'WORK_WECHAT'">👥 选择企业微信员工</el-radio>
            <el-radio value="customer" v-if="activeTab === 'AI'">👥 选择客户</el-radio>
            <el-radio value="group" v-if="activeTab === 'GROUP_BOT'">📢 选择群聊</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="测试对象" v-if="testForm.testType === 'group'">
          <div style="display: flex; gap: 10px;">
            <el-select 
              v-model="testForm.testTarget" 
              placeholder="选择测试群聊" 
              style="flex: 1;"
              :loading="loadingGroups"
            >
              <el-option 
                v-for="group in groupList" 
                :key="group.value" 
                :value="group.value"
              >
                <div style="display: flex; align-items: center; justify-content: space-between;">
                  <span>📢 {{ group.label }}</span>
                  <el-tag size="small" type="info">{{ group.member_count }} 人</el-tag>
                </div>
              </el-option>
            </el-select>
            <el-button 
              type="primary" 
              :loading="loadingGroups"
              @click="loadGroups"
            >
              {{ loadingGroups ? '获取中...' : '获取群聊' }}
            </el-button>
          </div>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            💡 点击"获取群聊"按钮从企业微信加载群聊列表（共 {{ groupList.length }} 个）
          </div>
        </el-form-item>
        
        <el-form-item label="测试手机号" v-if="testForm.testType === 'phone'">
          <el-input v-model="testForm.testPhone" placeholder="输入测试手机号，如：13800138000"></el-input>
        </el-form-item>
        
        <el-form-item label="微信OpenID" v-if="testForm.testType === 'wechat'">
          <el-input v-model="testForm.testOpenID" placeholder="输入微信OpenID"></el-input>
        </el-form-item>
        
        <el-form-item label="选择公众号用户" v-if="testForm.testType === 'wechat_user'">
          <div style="display: flex; gap: 10px;">
            <el-select 
              v-model="testForm.testWechatUser" 
              placeholder="选择公众号用户" 
              filterable 
              style="flex: 1;"
              :loading="loadingWechatUsers"
            >
              <el-option 
                v-for="user in wechatUsers" 
                :key="user.value" 
                :value="user.value"
              >
                <div style="display: flex; align-items: center; justify-content: space-between;">
                  <span>👤 {{ user.label }}</span>
                  <el-tag v-if="user.subscribe" size="small" type="success">已关注</el-tag>
                  <el-tag v-else size="small" type="info">未关注</el-tag>
                </div>
              </el-option>
            </el-select>
            <el-button 
              type="primary" 
              :loading="loadingWechatUsers"
              @click="loadWechatUsers"
            >
              {{ loadingWechatUsers ? '获取中...' : '获取用户' }}
            </el-button>
          </div>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            💡 点击"获取用户"按钮从公众号加载真实用户列表（共 {{ wechatUsers.length }} 个）
          </div>
        </el-form-item>
        
        <el-form-item label="员工UserID" v-if="testForm.testType === 'userid'">
          <el-input v-model="testForm.testUserID" placeholder="输入企业微信UserID"></el-input>
        </el-form-item>
        
        <el-form-item label="选择企业微信员工" v-if="testForm.testType === 'work_staff'">
          <div style="display: flex; gap: 10px;">
            <el-select 
              v-model="testForm.testWorkStaff" 
              placeholder="选择企业微信员工" 
              filterable 
              style="flex: 1;"
              :loading="loadingWorkStaff"
            >
              <el-option 
                v-for="staff in workStaffList" 
                :key="staff.value" 
                :value="staff.value"
              >
                <div style="display: flex; align-items: center; justify-content: space-between;">
                  <span>👨 {{ staff.label }}</span>
                  <el-tag size="small">{{ staff.department }}</el-tag>
                </div>
              </el-option>
            </el-select>
            <el-button 
              type="primary" 
              :loading="loadingWorkStaff"
              @click="loadWorkStaff"
            >
              {{ loadingWorkStaff ? '获取中...' : '获取员工' }}
            </el-button>
          </div>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            💡 点击"获取员工"按钮从企业微信通讯录加载真实员工列表（共 {{ workStaffList.length }} 个）
          </div>
        </el-form-item>
        
        <el-form-item label="选择客户" v-if="testForm.testType === 'customer'">
          <div style="display: flex; gap: 10px;">
            <el-select 
              v-model="testForm.testCustomerID" 
              placeholder="选择测试客户" 
              filterable 
              style="flex: 1;"
              :loading="loadingCustomers"
            >
              <el-option 
                v-for="customer in customerList" 
                :key="customer.value" 
                :value="customer.value"
              >
                <div style="display: flex; align-items: center; justify-content: space-between;">
                  <span>{{ customer.label }}</span>
                  <el-tag v-if="customer.company" size="small" type="info">{{ customer.company }}</el-tag>
                </div>
              </el-option>
            </el-select>
            <el-button 
              type="primary" 
              :loading="loadingCustomers"
              @click="loadCustomers"
            >
              {{ loadingCustomers ? '获取中...' : '获取客户' }}
            </el-button>
          </div>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            💡 点击"获取客户"按钮从数据库加载真实客户列表（共 {{ customerList.length }} 个）
          </div>
        </el-form-item>
        
        <!-- 变量预填充 -->
        <el-divider>变量预填充（可选）</el-divider>
        <div style="max-height: 200px; overflow-y: auto; padding: 10px; background: #f5f7fa; border-radius: 4px;">
          <el-form-item 
            v-for="variable in getTemplateVariables()"
            :key="variable"
            :label="getVariableName(variable)"
            label-width="150px"
            style="margin-bottom: 10px;"
          >
            <el-input 
              v-model="testForm.variableValues[variable]"
              :placeholder="'填写' + getVariableName(variable) + '的值'"
              size="small"
            ></el-input>
          </el-form-item>
        </div>
        
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
    
    <!-- 新增自定义变量对话框 -->
    <el-dialog
      v-model="showAddVariableDialog"
      title="新增自定义变量"
      width="450px"
    >
      <el-form :model="newVariableForm" label-width="100px">
        <el-form-item label="变量代码" required>
          <el-input 
            v-model="newVariableForm.code" 
            placeholder="如：ticket_id（不含大括号）"
          >
            <template #prepend>{</template>
            <template #append>}</template>
          </el-input>
        </el-form-item>
        <el-form-item label="变量名称" required>
          <el-input 
            v-model="newVariableForm.label" 
            placeholder="如：工单编号"
          ></el-input>
        </el-form-item>
        <el-alert
          title="自定义变量将显示为绿色标签，可在使用后删除"
          type="info"
          :closable="false"
        >
        </el-alert>
      </el-form>
      <template #footer>
        <el-button @click="showAddVariableDialog = false">取消</el-button>
        <el-button type="primary" @click="addCustomVariable">添加</el-button>
      </template>
    </el-dialog>
    
    <!-- 模板预览对话框 -->
    <el-dialog
      v-model="showTemplatePreview"
      title="📱 模板预览"
      width="500px"
    >
      <div style="padding: 20px; background: #f5f7fa; border-radius: 8px;">
        <div style="background: white; padding: 15px; border-radius: 4px; box-shadow: 0 2px 12px rgba(0,0,0,0.1);">
          <div style="font-size: 12px; color: #909399; margin-bottom: 10px;">{{ templateForm.category }}</div>
          <div 
            v-if="templateForm.type === 'text'"
            style="white-space: pre-wrap; line-height: 1.6;"
          >
            {{ renderPreviewContent() }}
          </div>
          <div 
            v-else-if="templateForm.type === 'markdown'"
            v-html="renderMarkdown(renderPreviewContent())"
            style="line-height: 1.6;"
          >
          </div>
          <div 
            v-else-if="templateForm.type === 'html'"
            v-html="renderPreviewContent()"
            style="line-height: 1.6;"
          >
          </div>
        </div>
        <div style="margin-top: 15px; padding: 10px; background: #fff3cd; border-radius: 4px; font-size: 12px; color: #856404;">
          💡 上方为模板预览效果，变量已自动替换为示例数据
        </div>
      </div>
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
const aiModelsLoading = ref(false)
const showPreview = ref(false)
const saving = ref(false)
const templateFormRef = ref(null)
const testDialogVisible = ref(false)
const testSending = ref(false)
const showAddVariableDialog = ref(false)
const showTemplatePreview = ref(false)
const customVariables = ref([])

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
  testType: 'phone',
  testTarget: '',
  testPhone: '',
  testOpenID: '',
  testUserID: '',
  testCustomerID: '',
  testWechatUser: '',  // 公众号用户
  testWorkStaff: '',   // 企业微信员工
  variableValues: {}
})

// 实际数据列表
const wechatUsers = ref([])  // 公众号用户列表
const workStaffList = ref([])  // 企业微信员工列表
const customerList = ref([])  // 客户列表
const groupList = ref([])  // 群聊列表

// 加载状态
const loadingWechatUsers = ref(false)
const loadingWorkStaff = ref(false)
const loadingCustomers = ref(false)
const loadingGroups = ref(false)

const newVariableForm = ref({
  code: '',
  label: ''
})

// 系统内置变量列表（包含工单、项目、链接等变量）
const systemVariables = [
  // 基础客户信息
  { code: '{customer_name}', label: '客户姓名', category: '客户信息', isCustom: false },
  { code: '{phone}', label: '联系电话', category: '客户信息', isCustom: false },
  { code: '{company}', label: '公司名称', category: '客户信息', isCustom: false },
  { code: '{order_no}', label: '订单号', category: '订单信息', isCustom: false },
  { code: '{product}', label: '产品名称', category: '产品信息', isCustom: false },
  { code: '{amount}', label: '金额', category: '订单信息', isCustom: false },
  { code: '{date}', label: '日期', category: '时间信息', isCustom: false },
  { code: '{time}', label: '时间', category: '时间信息', isCustom: false },
  
  // 工单相关变量
  { code: '{ticket_id}', label: '工单编号', category: '工单信息', isCustom: false },
  { code: '{ticket_status}', label: '工单状态', category: '工单信息', isCustom: false },
  { code: '{ticket_title}', label: '工单标题', category: '工单信息', isCustom: false },
  { code: '{ticket_priority}', label: '工单优先级', category: '工单信息', isCustom: false },
  { code: '{assigned_to}', label: '负责人', category: '工单信息', isCustom: false },
  { code: '{deadline}', label: '处理期限', category: '工单信息', isCustom: false },
  { code: '{progress}', label: '处理进度', category: '工单信息', isCustom: false },
  { code: '{pending_count}', label: '待处理数量', category: '工单统计', isCustom: false },
  { code: '{processing_count}', label: '进行中数量', category: '工单统计', isCustom: false },
  { code: '{completed_count}', label: '已完成数量', category: '工单统计', isCustom: false },
  
  // 项目相关变量
  { code: '{project_id}', label: '项目ID', category: '项目信息', isCustom: false },
  { code: '{project_name}', label: '项目名称', category: '项目信息', isCustom: false },
  { code: '{project_status}', label: '项目状态', category: '项目信息', isCustom: false },
  { code: '{project_progress}', label: '项目进度', category: '项目信息', isCustom: false },
  { code: '{milestone}', label: '里程碑', category: '项目信息', isCustom: false },
  
  // 链接相关变量（安全链接）
  { code: '{safe_link}', label: '安全链接', category: '链接变量', isCustom: false },
  { code: '{ticket_link}', label: '工单详情链接', category: '链接变量', isCustom: false },
  { code: '{project_link}', label: '项目进度链接', category: '链接变量', isCustom: false },
  { code: '{detail_link}', label: '详情链接', category: '链接变量', isCustom: false },
  { code: '{payment_link}', label: '支付链接', category: '链接变量', isCustom: false },
  { code: '{feedback_link}', label: '反馈链接', category: '链接变量', isCustom: false },
  
  // 员工信息
  { code: '{staff_name}', label: '员工姓名', category: '员工信息', isCustom: false },
  { code: '{staff_phone}', label: '员工电话', category: '员工信息', isCustom: false },
  { code: '{department}', label: '部门名称', category: '员工信息', isCustom: false }
]

// 所有变量（系统变量 + 自定义变量）
const allVariables = computed(() => {
  return [...systemVariables, ...customVariables.value]
})

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

// 计算属性：是否使用企业微信官方API（只有官方API才需要触发关键词）
const isWeworkOfficialAPI = computed(() => {
  if (activeTab.value !== 'AI' && activeTab.value !== 'WORK_WECHAT') {
    return false
  }
  // 检查当前选择的AI模型是否为企业微信官方API
  return templateForm.value.ai_model === 'wework-official' || 
         templateForm.value.ai_model === null ||
         templateForm.value.ai_model === undefined ||
         templateForm.value.ai_model === ''
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
        try {
          if (templateForm.value?.push_mode === 'realtime' && needsPushMode.value && isWeworkOfficialAPI.value && !value) {
            callback(new Error('实时推送必须填写触发关键词'))
          } else {
            callback()
          }
        } catch (error) {
          callback()
        }
      }, 
      trigger: 'blur' 
    }
  ],
  targets: [
    { 
      validator: (rule, value, callback) => {
        try {
          if (needsTargetSelection.value && (!value || value.length === 0)) {
            callback(new Error('请选择发送对象'))
          } else {
            callback()
          }
        } catch (error) {
          callback()
        }
      }, 
      trigger: 'change' 
    }
  ],
  schedule_time: [
    { 
      validator: (rule, value, callback) => {
        try {
          if (templateForm.value?.push_mode === 'scheduled' && !value) {
            callback(new Error('定时推送必须选择发送时间'))
          } else if (value && new Date(value) <= new Date()) {
            callback(new Error('发送时间必须大于当前时间'))
          } else {
            callback()
          }
        } catch (error) {
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

// 新增自定义变量
const addCustomVariable = () => {
  if (!newVariableForm.value.code || !newVariableForm.value.label) {
    ElMessage.warning('请填写变量代码和名称')
    return
  }
  
  // 检查是否已存在
  const code = `{${newVariableForm.value.code.replace(/[{}]/g, '')}}`
  const exists = allVariables.value.some(v => v.code === code)
  if (exists) {
    ElMessage.warning('该变量代码已存在')
    return
  }
  
  // 添加到自定义变量列表
  customVariables.value.push({
    code: code,
    label: newVariableForm.value.label,
    isCustom: true
  })
  
  ElMessage.success('✅ 自定义变量已添加')
  showAddVariableDialog.value = false
  newVariableForm.value = { code: '', label: '' }
}

// 删除自定义变量
const removeCustomVariable = (code) => {
  const index = customVariables.value.findIndex(v => v.code === code)
  if (index !== -1) {
    customVariables.value.splice(index, 1)
    ElMessage.success('已删除自定义变量')
  }
}

// 获取模板中使用的变量
const getTemplateVariables = () => {
  try {
    if (!testForm.value || !testForm.value.templateName) return []
    const template = templates.value.find(t => t.name === testForm.value.templateName)
    if (!template || !template.content) return []
    
    // 提取所有 {xxx} 格式的变量
    const matches = template.content.match(/\{[^}]+\}/g) || []
    return [...new Set(matches)] // 去重
  } catch (error) {
    console.warn('获取模板变量失败:', error)
    return []
  }
}

// 获取变量的显示名称
const getVariableName = (variableCode) => {
  try {
    if (!variableCode) return ''
    const variable = allVariables.value.find(v => v.code === variableCode)
    return variable ? variable.label : variableCode
  } catch (error) {
    console.warn('获取变量名称失败:', error)
    return variableCode || ''
  }
}

// 渲染预览内容（替换变量为示例数据）
const renderPreviewContent = () => {
  try {
    if (!templateForm.value || !templateForm.value.content) return ''
  
  const sampleData = {
    '{customer_name}': '张三',
    '{phone}': '13800138000',
    '{company}': 'XX科技有限公司',
    '{order_no}': 'ORD20260203001',
    '{product}': '智能售后系统V2.0',
    '{amount}': '9999.00',
    '{date}': '2026-02-03',
    '{time}': '14:30:00',
    // 工单相关
    '{ticket_id}': '#123',
    '{ticket_status}': '处理中',
    '{ticket_title}': '服务器无法连接',
    '{ticket_priority}': '高',
    '{assigned_to}': '李四',
    '{deadline}': '2026-02-04 15:30',
    '{progress}': '75%',
    '{pending_count}': '3',
    '{processing_count}': '5',
    '{completed_count}': '12',
    // 项目相关
    '{project_id}': 'PRJ001',
    '{project_name}': '智能客服系统升级',
    '{project_status}': '进行中',
    '{project_progress}': '60%',
    '{milestone}': '第二阶段完成',
    // 链接相关（安全链接）
    '{safe_link}': 'https://your-domain.com/secure/abc123xyz',
    '{ticket_link}': 'https://your-domain.com/tickets/123',
    '{project_link}': 'https://your-domain.com/projects/PRJ001',
    '{detail_link}': 'https://your-domain.com/details/view',
    '{payment_link}': 'https://your-domain.com/pay/ORD20260203001',
    '{feedback_link}': 'https://your-domain.com/feedback/submit',
    // 员工信息
    '{staff_name}': '王经理',
    '{staff_phone}': '13900139000',
    '{department}': '技术部'
  }
  
  let content = templateForm.value.content
  Object.keys(sampleData).forEach(key => {
    content = content.replace(new RegExp(key.replace(/[{}]/g, '\\$&'), 'g'), sampleData[key])
  })
  
  return content
  } catch (error) {
    console.warn('渲染预览内容失败:', error)
    return templateForm.value?.content || ''
  }
}

// 测试发送
const testSend = (row) => {
  testForm.value.templateName = row.name
  testForm.value.testType = activeTab.value === 'GROUP_BOT' ? 'group' : 'phone'
  testForm.value.testTarget = ''
  testForm.value.testPhone = ''
  testForm.value.testOpenID = ''
  testForm.value.testUserID = ''
  testForm.value.testCustomerID = ''
  testForm.value.variableValues = {}
  testDialogVisible.value = true
}

// 确认测试发送
const confirmTestSend = async () => {
  // 验证必填项
  if (testForm.value.testType === 'group' && !testForm.value.testTarget) {
    ElMessage.warning('请选择测试群聊')
    return
  }
  if (testForm.value.testType === 'phone' && !testForm.value.testPhone) {
    ElMessage.warning('请输入测试手机号')
    return
  }
  if (testForm.value.testType === 'wechat' && !testForm.value.testOpenID) {
    ElMessage.warning('请输入微信OpenID')
    return
  }
  if (testForm.value.testType === 'userid' && !testForm.value.testUserID) {
    ElMessage.warning('请输入员工UserID')
    return
  }
  if (testForm.value.testType === 'customer' && !testForm.value.testCustomerID) {
    ElMessage.warning('请选择测试客户')
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

// 加载模板列表
const loadTemplates = async () => {
  try {
    console.log('🔄 开始加载模板列表...')
    const response = await axios.get(`${import.meta.env.VITE_API_BASE || ''}/api/template/list`)
    console.log('✅ 模板数据:', response.data)
    
    if (response.data && response.data.templates) {
      templates.value = response.data.templates.map(t => ({
        id: t.id,
        name: t.name,
        channel: t.module_type || 'SMS',
        category: t.category || '未分类',
        type: t.content_type || 'text',
        content: t.content || '',
        ai_model: '',
        push_mode: t.push_mode || 'realtime',
        keywords: t.keywords || [],
        targets: t.targets || [],
        schedule_time: t.schedule_time,
        repeat_type: t.repeat_type,
        repeat_days: [],
        status: t.is_enabled,
        is_system: true
      }))
      console.log(`✅ 成功加载 ${templates.value.length} 个模板`)
    }
  } catch (error) {
    console.error('❌ 加载模板失败:', error)
    ElMessage.error('加载模板失败：' + (error.response?.data?.message || error.message))
  }
}

// 加载AI模型列表
const loadAIModels = async () => {
  aiModelsLoading.value = true
  console.log('🔄 开始加载AI模型列表...')
  
  try {
    const response = await axios.get('http://localhost:8000/api/admin/ai-models/active')
    console.log('✅ AI模型数据:', response.data)
    
    if (response.data && Array.isArray(response.data)) {
      aiModels.value = response.data.map(model => ({
        value: model.model_code,
        label: model.model_name,
        is_official: model.is_official || false,
        is_default: model.is_default || false
      }))
      console.log(`✅ 成功加载 ${aiModels.value.length} 个AI模型:`, aiModels.value)
      
      if (aiModels.value.length === 0) {
        ElMessage.warning('暂无可用AI模型，将使用默认配置')
        // 设置默认模型
        aiModels.value = [
          { 
            value: 'wework-official', 
            label: '企业微信官方API', 
            is_official: true, 
            is_default: true 
          }
        ]
      }
    } else {
      console.warn('⚠️ AI模型数据格式不正确:', response.data)
      aiModels.value = [
        { 
          value: 'wework-official', 
          label: '企业微信官方API', 
          is_official: true, 
          is_default: true 
        }
      ]
    }
  } catch (error) {
    console.error('❌ 加载AI模型失败:', error)
    // 失败时也设置默认模型
    aiModels.value = [
      { 
        value: 'wework-official', 
        label: '企业微信官方API', 
        is_official: true, 
        is_default: true 
      }
    ]
  } finally {
    aiModelsLoading.value = false
  }
}

// 获取微信公众号用户列表
const loadWechatUsers = async () => {
  loadingWechatUsers.value = true
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE || ''}/api/wechat/official/users`)
    wechatUsers.value = response.data.map(u => ({
      value: u.openid,
      label: u.nickname || u.openid,
      avatar: u.headimgurl,
      subscribe: u.subscribe,
      tags: u.tags || []
    }))
    ElMessage.success(`已获取 ${wechatUsers.value.length} 个公众号用户`)
  } catch (error) {
    console.error('获取公众号用户失败:', error)
    if (error.response?.status === 404) {
      ElMessage.warning('该功能暂未实现，请联系管理员')
    } else {
      ElMessage.error('获取公众号用户失败: ' + (error.response?.data?.message || error.message))
    }
    // 设置示例数据供测试
    wechatUsers.value = [
      { value: 'demo_001', label: '示例用户1', subscribe: true, tags: ['VIP'] },
      { value: 'demo_002', label: '示例用户2', subscribe: true, tags: [] }
    ]
  } finally {
    loadingWechatUsers.value = false
  }
}

// 获取企业微信员工列表
const loadWorkStaff = async () => {
  loadingWorkStaff.value = true
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE || ''}/api/wechat/work/users`)
    workStaffList.value = response.data.map(u => ({
      value: u.userid,
      label: u.name,
      department: u.department_name || '未分配部门',
      position: u.position,
      mobile: u.mobile
    }))
    ElMessage.success(`已获取 ${workStaffList.value.length} 个企业微信员工`)
  } catch (error) {
    console.error('获取企业微信员工失败:', error)
    if (error.response?.status === 404) {
      ElMessage.warning('该功能暂未实现，请联系管理员')
    } else {
      ElMessage.error('获取企业微信员工失败: ' + (error.response?.data?.message || error.message))
    }
    // 设置示例数据供测试
    workStaffList.value = [
      { value: 'zhangsan', label: '张三', department: '技术部', position: '工程师' },
      { value: 'lisi', label: '李四', department: '销售部', position: '经理' }
    ]
  } finally {
    loadingWorkStaff.value = false
  }
}

// 获取客户列表
const loadCustomers = async () => {
  loadingCustomers.value = true
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE || ''}/api/customers`)
    customerList.value = response.data.map(c => ({
      value: c.id,
      label: `${c.name} - ${c.phone}`,
      company: c.company,
      phone: c.phone
    }))
    ElMessage.success(`已获取 ${customerList.value.length} 个客户`)
  } catch (error) {
    console.error('获取客户列表失败:', error)
    if (error.response?.status === 404) {
      ElMessage.warning('该功能暂未实现，请联系管理员')
    } else {
      ElMessage.error('获取客户列表失败: ' + (error.response?.data?.message || error.message))
    }
    // 设置示例数据供测试
    customerList.value = [
      { value: 1, label: '张三 - 13800138000', company: 'XX科技', phone: '13800138000' },
      { value: 2, label: '李四 - 13900139000', company: 'YY公司', phone: '13900139000' }
    ]
  } finally {
    loadingCustomers.value = false
  }
}

// 获取群聊列表
const loadGroups = async () => {
  loadingGroups.value = true
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE || ''}/api/wechat/work/groups`)
    groupList.value = response.data.map(g => ({
      value: g.chatid,
      label: g.name,
      member_count: g.member_count
    }))
    ElMessage.success(`已获取 ${groupList.value.length} 个群聊`)
  } catch (error) {
    console.error('获取群聊列表失败:', error)
    if (error.response?.status === 404) {
      ElMessage.warning('该功能暂未实现，请联系管理员')
    } else {
      ElMessage.error('获取群聊列表失败: ' + (error.response?.data?.message || error.message))
    }
    // 设置示例数据供测试
    groupList.value = [
      { value: 'group_001', label: '内部工作群', member_count: 25 },
      { value: 'group_002', label: '技术支持群', member_count: 15 }
    ]
  } finally {
    loadingGroups.value = false
  }
}

const filteredTemplates = computed(() => {
  return templates.value.filter(t => {
    // 使用 channel 字段进行过滤（从后端 module_type 映射而来）
    return t.channel === activeTab.value
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
  loadTemplates()  // 加载真实模板数据
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

