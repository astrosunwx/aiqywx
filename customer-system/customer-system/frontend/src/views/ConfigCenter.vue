<template>
  <div class="config-center">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside width="200px" class="sidebar">
        <el-menu
          :default-active="activeMenu"
          @select="handleMenuSelect"
        >
          <el-menu-item index="overview">
            <el-icon><Setting /></el-icon>
            <span>配置概览</span>
          </el-menu-item>
          <el-menu-item index="channels">
            <el-icon><Message /></el-icon>
            <span>消息渠道</span>
          </el-menu-item>
          <el-menu-item index="webhooks">
            <el-icon><ChatLineRound /></el-icon>
            <span>群机器人</span>
          </el-menu-item>
          <el-menu-item index="workflows">
            <el-icon><Operation /></el-icon>
            <span>业务流程</span>
          </el-menu-item>
          <el-menu-item index="permissions">
            <el-icon><Lock /></el-icon>
            <span>权限管理</span>
          </el-menu-item>
          <el-menu-item index="users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="logs">
            <el-icon><Document /></el-icon>
            <span>操作日志</span>
          </el-menu-item>
          <el-menu-item index="project-sync">
            <el-icon><RefreshRight /></el-icon>
            <span>项目同步</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-container>
        <el-header class="header">
          <h2>{{ pageTitle }}</h2>
          <el-button 
            v-if="activeMenu === 'overview'" 
            type="primary" 
            @click="saveAllConfigs"
            :loading="saving"
          >
            一键保存配置
          </el-button>
        </el-header>

        <el-main>
          <!-- 配置概览 -->
          <div v-if="activeMenu === 'overview'" class="config-overview">
            <el-alert
              title="极简配置理念"
              type="info"
              description="所有配置在一个页面完成，配置后立即生效，无需重启服务"
              :closable="false"
              style="margin-bottom: 20px;"
            />

            <div v-for="group in configGroups" :key="group.id" class="config-group">
              <h3>
                <el-icon v-if="group.icon"><component :is="getIconComponent(group.icon)" /></el-icon>
                {{ group.group_name }}
              </h3>
              <p class="group-description">{{ group.description }}</p>

              <el-form label-width="180px">
                <el-form-item 
                  v-for="config in group.configs" 
                  :key="config.id"
                  :label="config.display_name"
                  :required="config.is_required"
                >
                  <template v-if="config.config_type === 'boolean'">
                    <el-switch 
                      v-model="config.config_value"
                      :active-value="'true'"
                      :inactive-value="'false'"
                    />
                  </template>
                  <template v-else-if="config.config_type === 'password'">
                    <el-input 
                      v-model="config.config_value"
                      type="password"
                      show-password
                      :placeholder="config.description"
                    />
                  </template>
                  <template v-else>
                    <el-input 
                      v-model="config.config_value"
                      :placeholder="config.description"
                      :disabled="config.config_key === 'callback_url'"
                    />
                  </template>
                  <span class="config-hint">{{ config.description }}</span>
                </el-form-item>

                <!-- 企业微信回调URL -->
                <el-form-item 
                  v-if="group.group_code === 'wework'" 
                  label="企业微信接收消息URL"
                >
                  <el-input :value="callbackUrls.wework_callback_url" disabled>
                    <template #append>
                      <el-button @click="copyToClipboard(callbackUrls.wework_callback_url)">复制</el-button>
                    </template>
                  </el-input>
                  <span class="config-hint">将此URL配置到企业微信应用的接收消息服务器中</span>
                </el-form-item>

                <!-- 微信公众号服务器URL -->
                <el-form-item 
                  v-if="group.group_code === 'wechat_official'" 
                  label="服务器地址(URL)"
                >
                  <el-input :value="callbackUrls.wechat_official_url" disabled>
                    <template #append>
                      <el-button @click="copyToClipboard(callbackUrls.wechat_official_url)">复制</el-button>
                    </template>
                  </el-input>
                  <span class="config-hint">将此URL配置到微信公众平台的基本配置中</span>
                </el-form-item>
              </el-form>
            </div>
          </div>

          <!-- 消息渠道配置 -->
          <div v-if="activeMenu === 'channels'" class="channels-config">
            <el-alert
              title="消息渠道管理"
              type="info"
              description="统一管理所有消息发送渠道的配置和状态"
              :closable="false"
              style="margin-bottom: 20px;"
            />

            <el-row :gutter="20" style="margin-bottom: 20px;">
              <el-col :span="6">
                <el-statistic title="总渠道数" :value="channelStats.total_channels || 0" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="已启用" :value="channelStats.enabled_channels || 0">
                  <template #suffix>
                    <el-icon color="#67c23a"><CircleCheck /></el-icon>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="6">
                <el-statistic title="已禁用" :value="channelStats.disabled_channels || 0">
                  <template #suffix>
                    <el-icon color="#909399"><CircleClose /></el-icon>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="6">
                <el-button type="primary" @click="refreshChannels" style="margin-top: 20px;">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </el-col>
            </el-row>

            <el-table :data="channels" style="width: 100%">
              <el-table-column prop="channel_name" label="渠道名称" width="200">
                <template #default="scope">
                  <el-tag :type="getChannelTagType(scope.row.channel_type)">
                    {{ scope.row.channel_name }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="channel_type" label="渠道类型" width="150" />
              <el-table-column label="状态" width="100">
                <template #default="scope">
                  <el-switch 
                    v-model="scope.row.is_enabled" 
                    @change="toggleChannel(scope.row)"
                  />
                </template>
              </el-table-column>
              <el-table-column label="配置状态" width="120">
                <template #default="scope">
                  <el-tag v-if="isChannelConfigured(scope.row)" type="success">已配置</el-tag>
                  <el-tag v-else type="warning">待配置</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="180">
                <template #default="scope">
                  <el-button size="small" @click="configureChannel(scope.row)">
                    <el-icon><Setting /></el-icon>
                    配置
                  </el-button>
                  <el-button size="small" type="primary" @click="testChannel(scope.row)">
                    <el-icon><Connection /></el-icon>
                    测试
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 渠道配置对话框 -->
            <el-dialog 
              v-model="showChannelDialog" 
              :title="`配置 ${currentChannel?.channel_name || ''}`"
              width="700px"
            >
              <el-form :model="channelForm" label-width="140px">
                <el-form-item label="渠道名称">
                  <el-input v-model="channelForm.channel_name" />
                </el-form-item>
                <el-form-item label="启用状态">
                  <el-switch v-model="channelForm.is_enabled" />
                </el-form-item>

                <!-- 动态配置项 -->
                <el-divider>渠道专属配置</el-divider>
                <div v-if="channelForm.channel_type === 'GROUP_BOT'">
                  <el-form-item label="Webhook URL">
                    <el-input v-model="channelForm.config_data.webhook_url" type="textarea" :rows="2" />
                  </el-form-item>
                  <el-form-item label="@提及设置">
                    <el-select v-model="channelForm.config_data.mention_type" placeholder="选择@方式">
                      <el-option label="不@任何人" value="none" />
                      <el-option label="@所有人" value="all" />
                      <el-option label="@指定成员" value="specific" />
                    </el-select>
                  </el-form-item>
                </div>

                <div v-else-if="channelForm.channel_type === 'AI'">
                  <el-form-item label="AI模型">
                    <el-select v-model="channelForm.config_data.model_id">
                      <el-option label="GPT-4" value="gpt-4" />
                      <el-option label="GPT-3.5" value="gpt-3.5-turbo" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="温度参数">
                    <el-slider v-model="channelForm.config_data.temperature" :min="0" :max="2" :step="0.1" show-input />
                  </el-form-item>
                </div>

                <div v-else-if="channelForm.channel_type === 'WORK_WECHAT'">
                  <el-form-item label="Corp ID">
                    <el-input v-model="channelForm.config_data.corp_id" />
                  </el-form-item>
                  <el-form-item label="Agent ID">
                    <el-input v-model="channelForm.config_data.agent_id" />
                  </el-form-item>
                  <el-form-item label="Secret">
                    <el-input v-model="channelForm.config_data.secret" type="password" show-password />
                  </el-form-item>
                </div>

                <div v-else-if="channelForm.channel_type === 'SMS'">
                  <el-form-item label="短信服务商">
                    <el-select v-model="channelForm.config_data.provider">
                      <el-option label="阿里云" value="aliyun" />
                      <el-option label="腾讯云" value="tencent" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="Access Key">
                    <el-input v-model="channelForm.config_data.access_key" />
                  </el-form-item>
                  <el-form-item label="Secret Key">
                    <el-input v-model="channelForm.config_data.secret_key" type="password" show-password />
                  </el-form-item>
                </div>

                <div v-else-if="channelForm.channel_type === 'EMAIL'">
                  <el-form-item label="SMTP服务器">
                    <el-input v-model="channelForm.config_data.smtp_host" placeholder="smtp.example.com" />
                  </el-form-item>
                  <el-form-item label="端口">
                    <el-input-number v-model="channelForm.config_data.smtp_port" :min="1" :max="65535" />
                  </el-form-item>
                  <el-form-item label="发件邮箱">
                    <el-input v-model="channelForm.config_data.from_email" />
                  </el-form-item>
                  <el-form-item label="邮箱密码">
                    <el-input v-model="channelForm.config_data.password" type="password" show-password />
                  </el-form-item>
                </div>

                <el-alert 
                  v-else 
                  title="该渠道暂无专属配置项" 
                  type="info" 
                  :closable="false"
                />
              </el-form>
              <template #footer>
                <el-button @click="showChannelDialog = false">取消</el-button>
                <el-button type="primary" @click="saveChannelConfig">保存配置</el-button>
              </template>
            </el-dialog>
          </div>

          <!-- 群机器人配置 -->
          <div v-if="activeMenu === 'webhooks'" class="webhooks-config">
            <el-button type="primary" @click="showWebhookDialog = true">
              <el-icon><Plus /></el-icon>
              添加Webhook
            </el-button>

            <el-table :data="webhooks" style="margin-top: 20px;">
              <el-table-column prop="webhook_name" label="名称" width="200" />
              <el-table-column prop="webhook_type" label="类型" width="150" />
              <el-table-column prop="webhook_url" label="Webhook URL" show-overflow-tooltip />
              <el-table-column prop="send_count" label="发送次数" width="100" />
              <el-table-column label="状态" width="100">
                <template #default="scope">
                  <el-tag :type="scope.row.is_active ? 'success' : 'info'">
                    {{ scope.row.is_active ? '启用' : '禁用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150">
                <template #default="scope">
                  <el-button size="small" @click="editWebhook(scope.row)">编辑</el-button>
                  <el-button size="small" type="danger" @click="deleteWebhook(scope.row.id)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- Webhook编辑对话框 -->
            <el-dialog 
              v-model="showWebhookDialog" 
              :title="editingWebhook ? '编辑Webhook' : '添加Webhook'"
              width="600px"
            >
              <el-form :model="webhookForm" label-width="120px">
                <el-form-item label="Webhook名称" required>
                  <el-input v-model="webhookForm.webhook_name" placeholder="例如：新客户通知群" />
                </el-form-item>
                <el-form-item label="Webhook类型">
                  <el-select v-model="webhookForm.webhook_type" placeholder="请选择">
                    <el-option label="新客户通知" value="new_customer" />
                    <el-option label="销售日报" value="sales_daily" />
                    <el-option label="技术支援" value="tech_support" />
                    <el-option label="售后服务" value="after_sales" />
                    <el-option label="其他" value="other" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Webhook URL" required>
                  <el-input 
                    v-model="webhookForm.webhook_url" 
                    type="textarea"
                    :rows="3"
                    placeholder="从企业微信群机器人获取的Webhook地址"
                  />
                </el-form-item>
                <el-form-item label="描述">
                  <el-input 
                    v-model="webhookForm.description" 
                    type="textarea"
                    placeholder="简要描述这个机器人的用途"
                  />
                </el-form-item>
                <el-form-item label="是否启用">
                  <el-switch v-model="webhookForm.is_active" />
                </el-form-item>
              </el-form>
              <template #footer>
                <el-button @click="showWebhookDialog = false">取消</el-button>
                <el-button type="primary" @click="saveWebhook">保存</el-button>
              </template>
            </el-dialog>
          </div>

          <!-- 业务流程模板 -->
          <div v-if="activeMenu === 'workflows'" class="workflows-config">
            <el-alert
              title="业务流程选择"
              type="info"
              description="选择适合您业务的流程模板，配置后立即生效"
              :closable="false"
              style="margin-bottom: 20px;"
            />

            <el-row :gutter="20">
              <el-col 
                v-for="template in workflowTemplates" 
                :key="template.id"
                :span="8"
              >
                <el-card 
                  :class="{'active-template': template.template_code === activeWorkflow}"
                  class="workflow-card"
                  @click="activateWorkflow(template.template_code)"
                >
                  <template #header>
                    <div class="card-header">
                      <span>{{ template.template_name }}</span>
                      <el-tag v-if="template.is_default" type="success" size="small">推荐</el-tag>
                      <el-tag v-if="template.template_code === activeWorkflow" type="primary" size="small">当前</el-tag>
                    </div>
                  </template>
                  <div class="template-description">{{ template.description }}</div>
                  <div class="template-type">
                    <el-tag size="small">{{ getTemplateTypeText(template.template_type) }}</el-tag>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>

          <!-- 用户管理 -->
          <div v-if="activeMenu === 'users'" class="users-management">
            <el-button type="primary" @click="showUserDialog = true">
              <el-icon><Plus /></el-icon>
              添加用户
            </el-button>

            <el-table :data="users" style="margin-top: 20px;">
              <el-table-column prop="username" label="用户名" width="150" />
              <el-table-column prop="real_name" label="真实姓名" width="150" />
              <el-table-column prop="role_name" label="角色" width="150" />
              <el-table-column prop="email" label="邮箱" width="200" />
              <el-table-column prop="phone" label="手机号" width="150" />
              <el-table-column label="状态" width="100">
                <template #default="scope">
                  <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
                    {{ scope.row.is_active ? '激活' : '禁用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="200">
                <template #default="scope">
                  <el-button size="small" @click="editUser(scope.row)">编辑</el-button>
                  <el-button size="small" type="danger" @click="deleteUser(scope.row.id)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 用户编辑对话框 -->
            <el-dialog 
              v-model="showUserDialog" 
              :title="editingUser ? '编辑用户' : '添加用户'"
              width="600px"
            >
              <el-form :model="userForm" label-width="100px">
                <el-form-item label="用户名" required>
                  <el-input v-model="userForm.username" :disabled="editingUser" />
                </el-form-item>
                <el-form-item label="密码" :required="!editingUser">
                  <el-input v-model="userForm.password" type="password" show-password 
                    :placeholder="editingUser ? '留空表示不修改密码' : '请输入密码'" />
                </el-form-item>
                <el-form-item label="真实姓名">
                  <el-input v-model="userForm.real_name" />
                </el-form-item>
                <el-form-item label="邮箱">
                  <el-input v-model="userForm.email" />
                </el-form-item>
                <el-form-item label="手机号">
                  <el-input v-model="userForm.phone" />
                </el-form-item>
                <el-form-item label="角色">
                  <el-select v-model="userForm.role_id" placeholder="请选择角色">
                    <el-option 
                      v-for="role in roles" 
                      :key="role.id"
                      :label="role.role_display_name"
                      :value="role.id"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="状态">
                  <el-switch v-model="userForm.is_active" />
                </el-form-item>
              </el-form>
              <template #footer>
                <el-button @click="showUserDialog = false">取消</el-button>
                <el-button type="primary" @click="saveUser">保存</el-button>
              </template>
            </el-dialog>
          </div>

          <!-- 权限管理 -->
          <div v-if="activeMenu === 'permissions'" class="permissions-management">
            <el-table :data="roles" style="width: 100%">
              <el-table-column prop="role_display_name" label="角色名称" width="150" />
              <el-table-column prop="description" label="描述" width="250" />
              <el-table-column label="权限" min-width="400">
                <template #default="scope">
                  <el-tag 
                    v-for="(perm, index) in scope.row.permissions" 
                    :key="index"
                    size="small"
                    style="margin-right: 5px; margin-bottom: 5px;"
                  >
                    {{ perm }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="系统角色" width="100">
                <template #default="scope">
                  <el-tag v-if="scope.row.is_system" type="warning" size="small">是</el-tag>
                  <el-tag v-else type="info" size="small">否</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 操作日志 -->
          <div v-if="activeMenu === 'logs'" class="operation-logs">
            <el-table :data="logs" style="width: 100%">
              <el-table-column prop="username" label="操作用户" width="120" />
              <el-table-column prop="operation_type" label="操作类型" width="120" />
              <el-table-column prop="module" label="模块" width="120" />
              <el-table-column prop="description" label="操作描述" min-width="200" show-overflow-tooltip />
              <el-table-column prop="ip_address" label="IP地址" width="140" />
              <el-table-column prop="created_at" label="操作时间" width="180" />
            </el-table>

            <el-pagination
              v-if="logsPagination"
              @current-change="handleLogPageChange"
              :current-page="logsPagination.page"
              :page-size="logsPagination.page_size"
              :total="logsPagination.total"
              layout="total, prev, pager, next"
              style="margin-top: 20px; text-align: right;"
            />
          </div>

          <!-- 项目同步配置 -->
          <div v-if="activeMenu === 'project-sync'" class="project-sync-config">
            <el-alert
              title="项目状态同步说明"
              type="info"
              description="配置定时同步，避免AI机器人频繁调取远程项目库。客户查看项目详情时将显示缓存数据，仅在状态更新时发送通知。"
              :closable="false"
              style="margin-bottom: 20px;"
            />

            <!-- 数据源管理入口 -->
            <el-card class="datasource-entry" style="margin-bottom: 20px;">
              <template #header>
                <span>📚 数据源管理</span>
              </template>
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                  <p style="margin: 0 0 8px 0; color: #666;">
                    管理多个远程数据库连接配置,支持MySQL、PostgreSQL、SQL Server
                  </p>
                  <p style="margin: 0; color: #999; font-size: 13px;">
                    如果您需要对接多个客户的项目库,请在数据源管理中添加多个数据库连接
                  </p>
                </div>
                <el-button type="primary" size="large" @click="openDataSourceManager">
                  管理数据源 →
                </el-button>
              </div>
            </el-card>

            <!-- 同步配置 -->
            <el-card class="config-group">`}
              <template #header>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span>⚙️ 同步配置</span>
                  <el-button type="primary" @click="saveProjectSyncConfig" :loading="saving">
                    保存配置
                  </el-button>
                </div>
              </template>

              <el-form :model="projectSyncConfig" label-width="150px">
                <el-form-item label="启用自动同步">
                  <el-switch v-model="projectSyncConfig.auto_sync_enabled" />
                  <span class="config-hint">关闭后将不会自动同步项目状态</span>
                </el-form-item>

                <el-form-item label="同步频率" v-if="projectSyncConfig.auto_sync_enabled">
                  <el-select v-model="projectSyncConfig.sync_frequency" style="width: 300px;">
                    <el-option label="每5分钟" value="*/5 * * * *" />
                    <el-option label="每15分钟" value="*/15 * * * *" />
                    <el-option label="每30分钟" value="*/30 * * * *" />
                    <el-option label="每小时" value="0 * * * *" />
                    <el-option label="每2小时" value="0 */2 * * *" />
                    <el-option label="每天9点" value="0 9 * * *" />
                    <el-option label="自定义" value="custom" />
                  </el-select>
                  <el-button link type="primary" @click="openCronGenerator" style="margin-left: 10px;">
                    打开Cron表达式生成器
                  </el-button>
                </el-form-item>

                <el-form-item 
                  label="Cron表达式" 
                  v-if="projectSyncConfig.auto_sync_enabled && projectSyncConfig.sync_frequency === 'custom'"
                >
                  <el-input 
                    v-model="projectSyncConfig.cron_expression" 
                    placeholder="例如: */5 * * * * (每5分钟)"
                    style="width: 300px;"
                  />
                  <span class="config-hint">格式: 分 时 日 月 周</span>
                </el-form-item>

                <el-form-item label="缓存过期时间">
                  <el-input-number 
                    v-model="projectSyncConfig.cache_ttl" 
                    :min="5"
                    :max="1440"
                    :step="5"
                  />
                  <span class="config-hint">分钟，超过此时间将重新同步</span>
                </el-form-item>

                <el-form-item label="同步项目类型">
                  <el-checkbox-group v-model="projectSyncConfig.sync_types">
                    <el-checkbox label="presale">售前商机</el-checkbox>
                    <el-checkbox label="aftersales">售后工单</el-checkbox>
                    <el-checkbox label="sales">订单</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>

                <el-form-item label="状态变更通知">
                  <el-switch v-model="projectSyncConfig.notify_on_change" />
                  <span class="config-hint">状态更新时自动发送通知给相关人员</span>
                </el-form-item>

                <el-form-item label="通知渠道" v-if="projectSyncConfig.notify_on_change">
                  <el-checkbox-group v-model="projectSyncConfig.notify_channels">
                    <el-checkbox label="wechat">微信</el-checkbox>
                    <el-checkbox label="sms">短信</el-checkbox>
                    <el-checkbox label="email">邮件</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>
              </el-form>
            </el-card>

            <!-- 手动同步 -->
            <el-card class="config-group" style="margin-top: 20px;">
              <template #header>
                <span>🔄 手动同步</span>
              </template>

              <el-space direction="vertical" style="width: 100%;">
                <el-alert
                  type="warning"
                  :closable="false"
                  show-icon
                >
                  <template #title>
                    手动同步将立即从远程项目库获取所有项目的最新状态，可能需要较长时间
                  </template>
                </el-alert>

                <el-button 
                  type="primary" 
                  size="large"
                  @click="manualSyncProjects"
                  :loading="syncing"
                  style="width: 200px;"
                >
                  <el-icon><RefreshRight /></el-icon>
                  立即同步所有项目
                </el-button>

                <div v-if="lastSyncTime" style="color: #909399; font-size: 14px;">
                  上次同步时间: {{ lastSyncTime }}
                </div>
              </el-space>
            </el-card>

            <!-- 同步历史 -->
            <el-card class="config-group" style="margin-top: 20px;">
              <template #header>
                <span>📊 同步历史</span>
              </template>

              <el-table :data="syncHistory" style="width: 100%">
                <el-table-column prop="sync_time" label="同步时间" width="180" />
                <el-table-column prop="sync_type" label="同步类型" width="120">
                  <template #default="{ row }">
                    <el-tag :type="row.sync_type === 'auto' ? 'success' : 'primary'">
                      {{ row.sync_type === 'auto' ? '自动' : '手动' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="total_projects" label="项目总数" width="100" />
                <el-table-column prop="updated_count" label="更新数量" width="100" />
                <el-table-column prop="duration" label="耗时" width="100" />
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
                      {{ row.status === 'success' ? '成功' : '失败' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="message" label="备注" min-width="200" show-overflow-tooltip />
              </el-table>

              <el-pagination
                v-if="syncHistoryPagination"
                @current-change="handleSyncHistoryPageChange"
                :current-page="syncHistoryPagination.page"
                :page-size="syncHistoryPagination.page_size"
                :total="syncHistoryPagination.total"
                layout="total, prev, pager, next"
                style="margin-top: 20px; text-align: right;"
              />
            </el-card>

            <!-- 时间显示配置 -->
            <el-card class="config-group" style="margin-top: 20px;">
              <template #header>
                <span>🕐 时间显示配置</span>
              </template>

              <el-form :model="timeDisplayConfig" label-width="200px">
                <el-form-item label="售后工单时间格式">
                  <el-select v-model="timeDisplayConfig.aftersales_time_format" style="width: 300px;">
                    <el-option label="YYYY-MM-DD HH:mm:ss" value="YYYY-MM-DD HH:mm:ss" />
                    <el-option label="YYYY-MM-DD HH:mm" value="YYYY-MM-DD HH:mm" />
                    <el-option label="YYYY年MM月DD日 HH:mm" value="YYYY年MM月DD日 HH:mm" />
                    <el-option label="MM-DD HH:mm" value="MM-DD HH:mm" />
                    <el-option label="相对时间（如：2小时前）" value="relative" />
                  </el-select>
                </el-form-item>

                <el-form-item label="订单时间格式">
                  <el-select v-model="timeDisplayConfig.sales_time_format" style="width: 300px;">
                    <el-option label="YYYY-MM-DD HH:mm:ss" value="YYYY-MM-DD HH:mm:ss" />
                    <el-option label="YYYY-MM-DD HH:mm" value="YYYY-MM-DD HH:mm" />
                    <el-option label="YYYY年MM月DD日 HH:mm" value="YYYY年MM月DD日 HH:mm" />
                    <el-option label="MM-DD HH:mm" value="MM-DD HH:mm" />
                    <el-option label="相对时间（如：2天前）" value="relative" />
                  </el-select>
                </el-form-item>

                <el-form-item label="付款时间显示">
                  <el-switch v-model="timeDisplayConfig.show_payment_time" />
                  <span class="config-hint">是否在订单详情中显示付款时间</span>
                </el-form-item>

                <el-form-item label="时区设置">
                  <el-select v-model="timeDisplayConfig.timezone" style="width: 300px;">
                    <el-option label="北京时间 (UTC+8)" value="Asia/Shanghai" />
                    <el-option label="东京时间 (UTC+9)" value="Asia/Tokyo" />
                    <el-option label="香港时间 (UTC+8)" value="Asia/Hong_Kong" />
                    <el-option label="新加坡时间 (UTC+8)" value="Asia/Singapore" />
                  </el-select>
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="saveTimeDisplayConfig" :loading="saving">
                    保存时间配置
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </div>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Setting, ChatLineRound, Operation, Lock, User, Document, RefreshRight,
  Plus, Setting as SettingIcon, Message, CircleCheck, CircleClose, 
  Refresh, Connection
} from '@element-plus/icons-vue'
import axios from 'axios'

// 开发环境使用空字符串，让Vite代理处理；生产环境使用完整URL
const API_BASE = import.meta.env.VITE_API_BASE || ''

// 状态管理
const activeMenu = ref('overview')
const pageTitle = ref('配置概览')
const saving = ref(false)

// 配置数据
const configGroups = ref([])
const callbackUrls = ref({
  wework_callback_url: '',
  wechat_official_url: ''
})
const webhooks = ref([])
const channels = ref([])
const channelStats = ref({})
const workflowTemplates = ref([])
const activeWorkflow = ref('')
const users = ref([])
const roles = ref([])
const permissions = ref({})
const logs = ref([])
const logsPagination = ref(null)

// 对话框
const showWebhookDialog = ref(false)
const showChannelDialog = ref(false)
const showUserDialog = ref(false)
const editingWebhook = ref(null)
const currentChannel = ref(null)
const editingUser = ref(null)

// 表单数据
const webhookForm = ref({
  webhook_name: '',
  webhook_type: '',
  webhook_url: '',
  description: '',
  is_active: true
})

const userForm = ref({
  username: '',
  password: '',
  real_name: '',
  email: '',
  phone: '',
  role_id: null,
  is_active: true
})

const channelForm = ref({
  channel_name: '',
  channel_type: '',
  is_enabled: true,
  config_data: {}
})

// 项目同步配置
const projectSyncConfig = ref({
  auto_sync_enabled: true,
  sync_frequency: '*/15 * * * *',
  cron_expression: '',
  cache_ttl: 30,
  sync_types: ['presale', 'aftersales', 'sales'],
  notify_on_change: true,
  notify_channels: ['wechat', 'sms']
})

// 时间显示配置
const timeDisplayConfig = ref({
  aftersales_time_format: 'YYYY-MM-DD HH:mm',
  sales_time_format: 'YYYY-MM-DD HH:mm',
  show_payment_time: true,
  timezone: 'Asia/Shanghai'
})

// 同步历史
const syncHistory = ref([])
const syncHistoryPagination = ref(null)
const syncing = ref(false)
const lastSyncTime = ref('')

// 菜单选择
const handleMenuSelect = (index) => {
  activeMenu.value = index
  const titles = {
    overview: '配置概览',
    channels: '消息渠道配置',
    webhooks: '群机器人配置',
    workflows: '业务流程模板',
    permissions: '权限管理',
    users: '用户管理',
    logs: '操作日志',
    'project-sync': '项目同步配置'
  }
  pageTitle.value = titles[index] || '配置中心'
  
  // 加载对应数据
  if (index === 'channels') loadChannels()
  else if (index === 'webhooks') loadWebhooks()
  else if (index === 'workflows') loadWorkflows()
  else if (index === 'users') loadUsers()
  else if (index === 'permissions') loadRolesAndPermissions()
  else if (index === 'logs') loadLogs()
  else if (index === 'project-sync') loadProjectSyncConfig()
}

// 加载配置概览
const loadConfigOverview = async () => {
  try {
    const response = await axios.get(`${API_BASE}/api/admin/config-center/overview`)
    configGroups.value = response.data.groups
    
    // 获取回调URL
    const callbackResponse = await axios.get(`${API_BASE}/api/admin/config-center/callback-url`)
    callbackUrls.value = {
      wework_callback_url: callbackResponse.data.wework_callback_url || '',
      wechat_official_url: callbackResponse.data.wechat_official_url || ''
    }
  } catch (error) {
    ElMessage.error('加载配置失败')
  }
}

// 保存所有配置
const saveAllConfigs = async () => {
  saving.value = true
  try {
    const configs = []
    configGroups.value.forEach(group => {
      group.configs.forEach(config => {
        configs.push({
          config_key: config.config_key,
          config_value: config.config_value,
          config_type: config.config_type,
          display_name: config.display_name,
          description: config.description
        })
      })
    })
    
    await axios.post(`${API_BASE}/api/admin/config-center/batch-update`, {
      configs
    })
    
    ElMessage.success('配置保存成功！')
  } catch (error) {
    ElMessage.error('配置保存失败')
  } finally {
    saving.value = false
  }
}

// 复制到剪贴板
const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text)
  ElMessage.success('已复制到剪贴板')
}

// 消息渠道管理
const loadChannels = async () => {
  try {
    const [channelsRes, statsRes] = await Promise.all([
      axios.get(`${API_BASE}/api/channel-config/list`),
      axios.get(`${API_BASE}/api/channel-config/stats/summary`)
    ])
    channels.value = channelsRes.data.channels
    channelStats.value = statsRes.data
  } catch (error) {
    ElMessage.error('加载渠道配置失败: ' + (error.response?.data?.detail || error.message))
  }
}

const refreshChannels = () => {
  loadChannels()
  ElMessage.success('已刷新渠道列表')
}

const configureChannel = (channel) => {
  currentChannel.value = channel
  channelForm.value = {
    channel_name: channel.channel_name,
    channel_type: channel.channel_type,
    is_enabled: channel.is_enabled,
    config_data: channel.config_data || {}
  }
  showChannelDialog.value = true
}

const saveChannelConfig = async () => {
  try {
    await axios.put(
      `${API_BASE}/api/channel-config/${currentChannel.value.id}`,
      channelForm.value
    )
    ElMessage.success('渠道配置保存成功')
    showChannelDialog.value = false
    loadChannels()
  } catch (error) {
    ElMessage.error('保存失败: ' + (error.response?.data?.detail || error.message))
  }
}

const toggleChannel = async (channel) => {
  try {
    await axios.put(
      `${API_BASE}/api/channel-config/${channel.id}`,
      { is_enabled: channel.is_enabled }
    )
    ElMessage.success(channel.is_enabled ? '渠道已启用' : '渠道已禁用')
  } catch (error) {
    channel.is_enabled = !channel.is_enabled
    ElMessage.error('操作失败')
  }
}

const testChannel = async (channel) => {
  ElMessage.info(`测试发送功能即将推出: ${channel.channel_name}`)
}

const getChannelTagType = (type) => {
  const types = {
    'GROUP_BOT': 'success',
    'AI': 'primary',
    'WORK_WECHAT': 'warning',
    'WECHAT': 'info',
    'SMS': 'danger',
    'EMAIL': ''
  }
  return types[type] || 'info'
}

const isChannelConfigured = (channel) => {
  if (!channel.config_data) return false
  const data = channel.config_data
  if (channel.channel_type === 'GROUP_BOT') {
    return !!data.webhook_url
  } else if (channel.channel_type === 'WORK_WECHAT') {
    return !!data.corp_id && !!data.agent_id && !!data.secret
  } else if (channel.channel_type === 'SMS') {
    return !!data.provider && !!data.access_key
  } else if (channel.channel_type === 'EMAIL') {
    return !!data.smtp_host && !!data.from_email
  }
  return Object.keys(data).length > 0
}

// Webhook管理
const loadWebhooks = async () => {
  try {
    const response = await axios.get(`${API_BASE}/api/admin/config-center/webhooks`)
    webhooks.value = response.data.webhooks
  } catch (error) {
    ElMessage.error('加载Webhook配置失败')
  }
}

const editWebhook = (webhook) => {
  editingWebhook.value = webhook
  webhookForm.value = { ...webhook }
  showWebhookDialog.value = true
}

const saveWebhook = async () => {
  try {
    if (editingWebhook.value) {
      await axios.put(
        `${API_BASE}/api/admin/config-center/webhooks/${editingWebhook.value.id}`,
        webhookForm.value
      )
      ElMessage.success('Webhook更新成功')
    } else {
      await axios.post(`${API_BASE}/api/admin/config-center/webhooks`, webhookForm.value)
      ElMessage.success('Webhook创建成功')
    }
    showWebhookDialog.value = false
    editingWebhook.value = null
    webhookForm.value = {
      webhook_name: '',
      webhook_type: '',
      webhook_url: '',
      description: '',
      is_active: true
    }
    loadWebhooks()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const deleteWebhook = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个Webhook配置吗？', '提示', {
      type: 'warning'
    })
    await axios.delete(`${API_BASE}/api/admin/config-center/webhooks/${id}`)
    ElMessage.success('删除成功')
    loadWebhooks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 业务流程管理
const loadWorkflows = async () => {
  try {
    const response = await axios.get(`${API_BASE}/api/admin/config-center/workflows`)
    workflowTemplates.value = response.data.templates
    
    // 获取当前激活的模板
    const configResponse = await axios.get(`${API_BASE}/api/admin/config-center/overview`)
    const workflowConfig = configResponse.data.groups
      .find(g => g.group_code === 'workflow')
      ?.configs.find(c => c.config_key === 'active_workflow_template')
    
    if (workflowConfig) {
      activeWorkflow.value = workflowConfig.config_value
    }
  } catch (error) {
    ElMessage.error('加载业务流程失败')
  }
}

const activateWorkflow = async (templateCode) => {
  try {
    await axios.post(`${API_BASE}/api/admin/config-center/workflows/activate/${templateCode}`)
    activeWorkflow.value = templateCode
    ElMessage.success('业务流程已切换')
  } catch (error) {
    ElMessage.error('切换失败')
  }
}

const getTemplateTypeText = (type) => {
  const types = {
    presale: '售前流程',
    aftersale: '售后流程',
    mixed: '混合流程',
    custom: '自定义流程'
  }
  return types[type] || type
}

// 用户管理
const loadUsers = async () => {
  try {
    const [usersResponse, rolesResponse] = await Promise.all([
      axios.get(`${API_BASE}/api/admin/config-center/users`),
      axios.get(`${API_BASE}/api/admin/config-center/roles`)
    ])
    users.value = usersResponse.data.users
    roles.value = rolesResponse.data.roles
  } catch (error) {
    ElMessage.error('加载用户列表失败')
  }
}

const editUser = (user) => {
  editingUser.value = user
  userForm.value = { ...user, password: '' }
  showUserDialog.value = true
}

const saveUser = async () => {
  try {
    if (editingUser.value) {
      const updateData = { ...userForm.value }
      if (!updateData.password) {
        delete updateData.password
      }
      await axios.put(`${API_BASE}/api/admin/config-center/users/${editingUser.value.id}`, updateData)
      ElMessage.success('用户更新成功')
    } else {
      await axios.post(`${API_BASE}/api/admin/config-center/users`, userForm.value)
      ElMessage.success('用户创建成功')
    }
    showUserDialog.value = false
    editingUser.value = null
    userForm.value = {
      username: '',
      password: '',
      real_name: '',
      email: '',
      phone: '',
      role_id: null,
      is_active: true
    }
    loadUsers()
  } catch (error) {
    ElMessage.error('保存失败: ' + (error.response?.data?.detail || error.message))
  }
}

const deleteUser = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个用户吗？', '提示', {
      type: 'warning'
    })
    await axios.delete(`${API_BASE}/api/admin/config-center/users/${id}`)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 权限管理
const loadRolesAndPermissions = async () => {
  try {
    const [rolesResponse, permsResponse] = await Promise.all([
      axios.get(`${API_BASE}/api/admin/config-center/roles`),
      axios.get(`${API_BASE}/api/admin/config-center/permissions`)
    ])
    roles.value = rolesResponse.data.roles
    permissions.value = permsResponse.data.modules
  } catch (error) {
    ElMessage.error('加载权限数据失败')
  }
}

// 操作日志
const loadLogs = async (page = 1) => {
  try {
    const response = await axios.get(`${API_BASE}/api/admin/config-center/logs`, {
      params: { page, page_size: 50 }
    })
    logs.value = response.data.logs
    logsPagination.value = response.data.pagination
  } catch (error) {
    ElMessage.error('加载日志失败')
  }
}

const handleLogPageChange = (page) => {
  loadLogs(page)
}

// ========== 项目同步配置 ==========

// 加载项目同步配置
const loadProjectSyncConfig = async () => {
  try {
    const response = await axios.get(`${API_BASE}/api/config/project-sync`)
    if (response.data.config) {
      projectSyncConfig.value = response.data.config
    }
    if (response.data.last_sync_time) {
      lastSyncTime.value = response.data.last_sync_time
    }
    loadSyncHistory()
  } catch (error) {
    console.error('加载项目同步配置失败:', error)
    ElMessage.warning('使用默认配置')
  }
}

// 保存项目同步配置
const saveProjectSyncConfig = async () => {
  saving.value = true
  try {
    await axios.post(`${API_BASE}/api/config/project-sync`, projectSyncConfig.value)
    ElMessage.success('配置已保存')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 保存时间显示配置
const saveTimeDisplayConfig = async () => {
  saving.value = true
  try {
    await axios.post(`${API_BASE}/api/config/time-display`, timeDisplayConfig.value)
    ElMessage.success('时间配置已保存')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 手动同步所有项目
const manualSyncProjects = async () => {
  try {
    await ElMessageBox.confirm(
      '手动同步将从远程项目库获取所有项目的最新状态，可能需要较长时间，确定继续？',
      '确认同步',
      {
        type: 'warning',
        confirmButtonText: '立即同步',
        cancelButtonText: '取消'
      }
    )
    
    syncing.value = true
    const response = await axios.post(`${API_BASE}/api/projects/sync`, {
      sync_type: 'manual',
      force: true
    })
    
    ElMessage.success(`同步完成！共同步 ${response.data.total} 个项目，更新 ${response.data.updated} 个`)
    lastSyncTime.value = response.data.sync_time
    loadSyncHistory()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('同步失败:', error)
      ElMessage.error('同步失败: ' + (error.response?.data?.detail || error.message))
    }
  } finally {
    syncing.value = false
  }
}

// 加载同步历史
const loadSyncHistory = async (page = 1) => {
  try {
    const response = await axios.get(`${API_BASE}/api/projects/sync-history`, {
      params: { page, page_size: 20 }
    })
    syncHistory.value = response.data.history || []
    syncHistoryPagination.value = response.data.pagination
  } catch (error) {
    console.error('加载同步历史失败:', error)
    // 使用模拟数据
    syncHistory.value = [
      {
        sync_time: '2024-02-02 15:30:00',
        sync_type: 'auto',
        total_projects: 150,
        updated_count: 5,
        duration: '2.3秒',
        status: 'success',
        message: '自动同步完成'
      },
      {
        sync_time: '2024-02-02 15:15:00',
        sync_type: 'auto',
        total_projects: 150,
        updated_count: 3,
        duration: '1.8秒',
        status: 'success',
        message: '自动同步完成'
      },
      {
        sync_time: '2024-02-02 14:00:00',
        sync_type: 'manual',
        total_projects: 148,
        updated_count: 12,
        duration: '5.6秒',
        status: 'success',
        message: '手动同步完成'
      }
    ]
  }
}

const handleSyncHistoryPageChange = (page) => {
  loadSyncHistory(page)
}

// 打开Cron表达式生成器
const openCronGenerator = () => {
  window.open('http://cron.ciding.cc/', '_blank')
}

// 打开数据源管理器
const openDataSourceManager = () => {
  window.open('http://localhost:3000/datasource', '_blank')
}

// 图标组件
const getIconComponent = (iconName) => {
  const icons = {
    wechat: ChatLineRound,
    message: ChatLineRound,
    robot: ChatLineRound,
    flow: Operation,
    notification: ChatLineRound,
    settings: Setting
  }
  return icons[iconName] || Setting
}

// 初始化
onMounted(() => {
  loadConfigOverview()
})
</script>

<style scoped>
.config-center {
  height: 100vh;
  background-color: #f5f5f5;
}

.sidebar {
  background-color: #fff;
  border-right: 1px solid #e0e0e0;
}

.header {
  background-color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e0e0e0;
  padding: 0 20px;
}

.header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.el-main {
  background-color: #f5f5f5;
  padding: 20px;
}

.config-group {
  background-color: #fff;
  padding: 20px;
  margin-bottom: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.config-group h3 {
  margin-top: 0;
  color: #409eff;
  display: flex;
  align-items: center;
  gap: 8px;
}

.group-description {
  color: #666;
  margin-bottom: 20px;
}

.config-hint {
  color: #999;
  font-size: 12px;
  margin-left: 10px;
}

.workflow-card {
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 20px;
}

.workflow-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
  transform: translateY(-2px);
}

.workflow-card.active-template {
  border: 2px solid #409eff;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.template-description {
  margin-bottom: 15px;
  color: #666;
  line-height: 1.6;
}

.template-type {
  margin-top: 10px;
}
</style>
