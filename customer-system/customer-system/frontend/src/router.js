import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import Reports from './views/Reports.vue'
import ConfigCenter from './views/ConfigCenter.vue'
import MessageMonitor from './views/MessageMonitor.vue'
import MessageManager from './views/MessageManager.vue'
import TemplateMessageManager from './views/TemplateMessageManager.vue'
import TemplateManager from './views/TemplateManager.vue'
import AIModelManager from './views/AIModelManager.vue'
import ProjectDetail from './views/ProjectDetail.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/settings',
    redirect: '/config'
  },
  {
    path: '/reports',
    name: 'Reports',
    component: Reports
  },
  {
    path: '/config',
    name: 'ConfigCenter',
    component: ConfigCenter
  },
  {
    path: '/monitor',
    name: 'MessageMonitor',
    component: MessageMonitor,
    meta: {
      title: '消息监控大屏'
    }
  },
  {
    path: '/messages',
    name: 'MessageManager',
    component: MessageManager,
    meta: {
      title: '消息管理（旧版）'
    }
  },
  {
    path: '/template-messages',
    name: 'TemplateMessageManager',
    component: TemplateMessageManager,
    meta: {
      title: '消息系统（模板版）'
    }
  },
  {
    path: '/templates',
    name: 'TemplateManager',
    component: TemplateManager,
    meta: {
      title: '模板管理'
    }
  },
  {
    path: '/ai-models',
    name: 'AIModelManager',
    component: AIModelManager,
    meta: {
      title: 'AI模型配置'
    }
  },
  {
    path: '/project/:id',
    name: 'ProjectDetail',
    component: ProjectDetail,
    meta: {
      title: '工单详情'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
