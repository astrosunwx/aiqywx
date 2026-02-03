# 消息模板管理系统 - 完整实施方案（数据库+后端+前端）

## 🎯 核心问题

当前状态：
```
✅ 规划文档已完成（5个预留模块定义）
❌ 数据库模型未创建
❌ 后端API未实现
❌ 前端UI未完善
```

本方案包含：从数据库设计 → 后端API → 前端UI 的完整实现步骤

---

## 📊 第1部分：数据库设计

### 1.1 创建预留模块数据表

**文件：`backend/app/models.py`**

在现有模型的基础上添加：

```python
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, JSONB
from sqlalchemy.sql import func

# 1. 预留模块定义表（系统内置，不可修改）
class TemplateModule(Base):
    __tablename__ = "template_modules"
    
    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(String(50), unique=True, nullable=False, index=True)  # 如：QUERY_PROJECT
    module_name = Column(String(100), nullable=False)  # 如：查询项目
    description = Column(String(500))  # 模块描述
    trigger_keywords = Column(JSONB, default=[])  # 触发关键词列表
    template_content = Column(Text)  # 预设模板内容
    available_variables = Column(JSONB, default=[])  # 可用变量列表
    use_scenario = Column(String(100))  # 使用场景（如：查询项目）
    is_system = Column(Boolean, default=True)  # 是否系统内置
    is_active = Column(Boolean, default=True)  # 是否启用
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = (
        Index('idx_module_id', 'module_id'),
    )


# 2. 消息模板表（用户自定义的模板）
class MessageTemplate(Base):
    __tablename__ = "message_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(50), unique=True, nullable=False, index=True)  # 模板唯一ID
    template_name = Column(String(100), nullable=False)  # 模板名称
    template_type = Column(String(20), nullable=False)  # SMS/EMAIL/WECHAT/WORK_WECHAT/AI/GROUP_BOT
    use_scenario = Column(String(100))  # 使用场景
    
    # 对于AI回复模板，这些字段非常重要
    module_id = Column(String(50), nullable=True, index=True)  # 关联的预留模块ID（如果是预留模块）
    trigger_keywords = Column(JSONB, default=[])  # 触发关键词（仅AI模板）
    response_type = Column(String(20), default='preset')  # preset（预设）或custom（自定义）
    
    template_content = Column(Text, nullable=False)  # 模板内容（可包含变量如{technician}）
    available_variables = Column(JSONB, default=[])  # 可用变量列表
    
    # 状态管理
    is_enabled = Column(Boolean, default=True)  # 是否启用
    target_audience = Column(String(50), default='all_external')  # 应答对象：all_external/all_customers/指定员工ID等
    
    # 记录信息
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))  # 创建者（用户ID）
    
    __table_args__ = (
        Index('idx_template_type', 'template_type'),
        Index('idx_module_id', 'module_id'),
    )


# 3. 模板变量定义表
class TemplateVariable(Base):
    __tablename__ = "template_variables"
    
    id = Column(Integer, primary_key=True, index=True)
    variable_name = Column(String(50), unique=True, nullable=False)  # 如：{technician}
    variable_label = Column(String(100))  # 显示名称：技术员
    description = Column(String(200))  # 描述：负责此工单的技术员姓名
    default_value = Column(String(100))  # 默认值
    is_system = Column(Boolean, default=True)  # 是否系统内置
    applicable_modules = Column(JSONB, default=[])  # 适用的模块列表
    
    __table_args__ = (
        Index('idx_variable_name', 'variable_name'),
    )
```

**迁移命令：**

```bash
# 创建这些新表
cd backend
python -c "
from app.database import Base, engine
from app.models import TemplateModule, MessageTemplate, TemplateVariable
Base.metadata.create_all(bind=engine)
print('✅ 表创建成功')
"
```

---

### 1.2 初始化预留模块数据

**文件：`backend/scripts/init_template_modules.py`（新建）**

```python
"""
初始化系统预留模块数据
"""
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import TemplateModule, TemplateVariable

def init_template_modules():
    """初始化5个预留模块"""
    db = SessionLocal()
    
    # 1. 清空旧数据（可选）
    db.query(TemplateModule).delete()
    
    modules_data = [
        {
            'module_id': 'QUERY_PROJECT',
            'module_name': '查询项目',
            'description': '客户查询项目进度',
            'trigger_keywords': ['查询项目', '查项目', '项目进度', '订单'],
            'use_scenario': '查询项目',
            'template_content': '''您好，{customer_name}！

我们为您查询到以下项目：

{projects_list}

📊 项目列表链接：
🔗 https://{baseUrl}/project/list?customer_id={customer_id}

点击链接可以：
✅ 查看详细进度
✅ 上传/下载资料
✅ 提交售后工单
✅ 申请加急或取消

如有任何问题，欢迎随时咨询！''',
            'available_variables': [
                '{customer_name}', '{customer_id}', '{baseUrl}', 
                '{projects_list}', '{project_count}', '{recent_status}'
            ]
        },
        {
            'module_id': 'URGENT_REQUEST',
            'module_name': '查询加急',
            'description': '客户申请项目加急',
            'trigger_keywords': ['加急', '催促', '急件', '尽快'],
            'use_scenario': '查询加急',
            'template_content': '''您好，{customer_name}！

感谢您提出加急需求。我们可以为您加快处理。

⏰ 加急处理流程：

1️⃣ 确认加急事由
   • 项目号：{project_id}
   • 项目名称：{project_title}
   • 当前状态：{current_status}
   • 您的加急原因：{urgency_reason}

2️⃣ 加急费用（如适用）
   • 标准处理：无额外费用，工作日3-5天
   • 加急处理：+20% 费用，1-2个工作日
   • 特急处理：+50% 费用，24小时内

3️⃣ 申请加急
   请回复确认即可

⚠️ 工作时间：工作日 10:00-18:30''',
            'available_variables': [
                '{customer_name}', '{project_id}', '{project_title}', 
                '{current_status}', '{urgency_reason}', '{technician}', '{expected_completion}'
            ]
        },
        {
            'module_id': 'CANCEL_REQUEST',
            'module_name': '申请取消',
            'description': '客户申请项目取消或退单',
            'trigger_keywords': ['取消', '退单', '作废', '反悔'],
            'use_scenario': '申请取消',
            'template_content': '''您好，{customer_name}！

您已提出取消申请。我们会为您评估取消可行性。

❌ 取消流程与条件：

1️⃣ 核实项目信息
   • 项目号：{project_id}
   • 项目名称：{project_title}
   • 当前状态：{current_status}
   • 下单时间：{order_date}
   • 已执行：{executed_percentage}%

2️⃣ 取消条件评估
   ✅ 可以取消的情况：
      • 【未开始】项目未开始施工（可全额退款）
      • 【已开始】项目已开始但未完成
        └─ 退款：合同金额 × (100% - 已执行%) - 已发生费用
      
   ❌ 可能不能取消：
      • 【已完成】项目已全部完成（不可取消）
      • 【材料采购】已购买材料（需承担材料费）

3️⃣ 申请取消
   请确认是否继续

⚠️ 重要提示：
   • 取消一旦确认，不可再要求恢复
   • 未动工项目可全额退款
   • 已动工项目需扣除已发生费用

📞 取消咨询电话：{contact_phone}''',
            'available_variables': [
                '{customer_name}', '{project_id}', '{project_title}', 
                '{current_status}', '{order_date}', '{executed_percentage}', '{contact_phone}'
            ]
        },
        {
            'module_id': 'AFTERSALE_SERVICE',
            'module_name': '售后维修',
            'description': '客户报告故障，申请售后服务',
            'trigger_keywords': ['售后', '维修', '故障', '坏了', '维修'],
            'use_scenario': '售后服务',
            'template_content': '''感谢您的反馈，{customer_name}！

我们已为您创建售后工单，将尽快处理。

🔧 工单信息：

工单号：{ticket_id}
客户：{customer_name}（{customer_phone}）
产品：{product_name}
故障描述：{fault_description}
创建时间：{created_time}

📍 预计上门时间：
✅ {expected_visit_date} {expected_visit_time}

👨‍🔧 技术员信息：
姓名：{technician}
电话：{technician_phone}
工程等级：{technician_level}

💡 上门前准备：
✅ 清空产品周围空间（便于操作）
✅ 确保电源畅通
✅ 准备好发票或订单证明
✅ 记住故障现象描述

🚨 重要提示：
我们的技术员 {technician} 将准时上门服务。
请保持电话畅通，如有变化请及时通知我们。

📞 工单咨询：{contact_phone}
🔗 工单详情：https://{baseUrl}/secure/project/{project_token}
   （此链接24小时内有效，请勿分享给他人）

如需取消或修改时间，请在 {service_deadline} 前告知！''',
            'available_variables': [
                '{customer_name}', '{customer_phone}', '{ticket_id}', '{product_name}',
                '{fault_description}', '{created_time}', '{expected_visit_date}',
                '{expected_visit_time}', '{technician}', '{technician_phone}',
                '{technician_level}', '{contact_phone}', '{baseUrl}', '{project_token}',
                '{service_deadline}'
            ]
        },
        {
            'module_id': 'PRESALE_INQUIRY',
            'module_name': '售前咨询',
            'description': '客户咨询产品、价格、方案',
            'trigger_keywords': ['咨询', '价格', '产品', '报价'],
            'use_scenario': '售前咨询',
            'template_content': '''您好，{customer_name}！

感谢您的咨询，我们很高兴为您服务。

📋 咨询记录：
您咨询的：{inquiry_content}
咨询时间：{inquiry_time}
咨询来源：{source}

👨‍💼 您的销售顾问：
姓名：{sales_representative_name}
电话：{sales_representative_phone}
微信：{sales_representative_wechat}
工作时间：工作日 9:00-18:00

📞 联系销售顾问：
✅ 电话咨询：直接致电上述电话
✅ 微信咨询：扫描二维码或搜索微信号
✅ 上门考察：我们可以免费上门勘察

💡 常见问题快速答复：
Q: 价格怎么算？
A: 我们根据您的具体需求定制报价，无隐性费用

Q: 多久能安装？
A: 确认方案后，通常一周内完成安装

Q: 有质保吗？
A: 所有产品享受 {warranty_period} 保修期

Q: 支付方式？
A: 支持：现金、刷卡、银行转账、分期付款

🔗 了解更多：
• 产品介绍：https://{baseUrl}/products
• 成功案例：https://{baseUrl}/cases
• 技术支持：https://{baseUrl}/support

{sales_representative_name} 会在 {response_time} 小时内与您联系。
请保持电话畅通！

感谢您选择我们！''',
            'available_variables': [
                '{customer_name}', '{inquiry_content}', '{inquiry_time}', '{source}',
                '{sales_representative_name}', '{sales_representative_phone}',
                '{sales_representative_wechat}', '{warranty_period}', '{response_time}', '{baseUrl}'
            ]
        }
    ]
    
    # 插入所有模块
    for module_data in modules_data:
        module = TemplateModule(**module_data)
        db.add(module)
    
    db.commit()
    print("✅ 5个预留模块初始化成功！")
    db.close()

def init_template_variables():
    """初始化系统变量定义"""
    db = SessionLocal()
    
    db.query(TemplateVariable).delete()
    
    variables_data = [
        {
            'variable_name': '{customer_name}',
            'variable_label': '客户名称',
            'description': '客户的姓名',
            'is_system': True,
            'applicable_modules': ['QUERY_PROJECT', 'URGENT_REQUEST', 'CANCEL_REQUEST', 'AFTERSALE_SERVICE', 'PRESALE_INQUIRY']
        },
        {
            'variable_name': '{technician}',
            'variable_label': '技术员名称',
            'description': '负责此工单的技术员姓名',
            'is_system': True,
            'applicable_modules': ['AFTERSALE_SERVICE', 'URGENT_REQUEST']
        },
        {
            'variable_name': '{technician_phone}',
            'variable_label': '技术员电话',
            'description': '负责技术员的联系电话',
            'is_system': True,
            'applicable_modules': ['AFTERSALE_SERVICE']
        },
        {
            'variable_name': '{baseUrl}',
            'variable_label': '基础域名',
            'description': '从localStorage读取的基础域名',
            'default_value': 'http://localhost:3000',
            'is_system': True,
            'applicable_modules': ['QUERY_PROJECT', 'AFTERSALE_SERVICE', 'PRESALE_INQUIRY']
        },
        {
            'variable_name': '{project_id}',
            'variable_label': '项目ID',
            'description': '项目的唯一标识符',
            'is_system': True,
            'applicable_modules': ['QUERY_PROJECT', 'URGENT_REQUEST', 'CANCEL_REQUEST']
        },
        # ... 更多变量定义
    ]
    
    for var_data in variables_data:
        var = TemplateVariable(**var_data)
        db.add(var)
    
    db.commit()
    print("✅ 系统变量初始化成功！")
    db.close()

if __name__ == '__main__':
    init_template_modules()
    init_template_variables()
```

**运行初始化脚本：**

```bash
cd backend
python scripts/init_template_modules.py
```

---

## 🔌 第2部分：后端 API

### 2.1 创建模板管理服务

**文件：`backend/app/services/template_service.py`（新建）**

```python
"""
消息模板管理服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import MessageTemplate, TemplateModule, TemplateVariable
from typing import List, Optional

class TemplateService:
    """消息模板服务"""
    
    @staticmethod
    async def get_template_modules(db: Session, template_type: str = 'AI') -> List[dict]:
        """获取预留模块列表"""
        modules = db.query(TemplateModule).filter(
            TemplateModule.is_active == True
        ).all()
        
        return [
            {
                'module_id': m.module_id,
                'module_name': m.module_name,
                'description': m.description,
                'trigger_keywords': m.trigger_keywords,
                'template_content': m.template_content,
                'available_variables': m.available_variables,
                'use_scenario': m.use_scenario
            }
            for m in modules
        ]
    
    @staticmethod
    async def create_template(
        db: Session,
        template_name: str,
        template_type: str,
        use_scenario: str,
        template_content: str,
        module_id: Optional[str] = None,
        trigger_keywords: List[str] = None,
        target_audience: str = 'all_external'
    ) -> dict:
        """创建消息模板"""
        
        template = MessageTemplate(
            template_id=f"{template_type}_{int(time.time())}",
            template_name=template_name,
            template_type=template_type,
            use_scenario=use_scenario,
            template_content=template_content,
            module_id=module_id,
            trigger_keywords=trigger_keywords or [],
            target_audience=target_audience
        )
        
        db.add(template)
        db.commit()
        db.refresh(template)
        
        return {
            'template_id': template.template_id,
            'template_name': template.template_name,
            'status': 'created'
        }
    
    @staticmethod
    async def get_ai_templates(db: Session) -> List[dict]:
        """获取所有AI回复模板"""
        templates = db.query(MessageTemplate).filter(
            and_(
                MessageTemplate.template_type == 'AI',
                MessageTemplate.is_enabled == True
            )
        ).all()
        
        return [
            {
                'id': t.id,
                'template_id': t.template_id,
                'template_name': t.template_name,
                'use_scenario': t.use_scenario,
                'module_id': t.module_id,
                'trigger_keywords': t.trigger_keywords,
                'template_content': t.template_content,
                'available_variables': t.available_variables,
                'is_enabled': t.is_enabled,
                'target_audience': t.target_audience,
                'created_at': t.created_at.isoformat() if t.created_at else None
            }
            for t in templates
        ]
    
    @staticmethod
    async def update_template(
        db: Session,
        template_id: str,
        **kwargs
    ) -> dict:
        """更新模板"""
        template = db.query(MessageTemplate).filter(
            MessageTemplate.template_id == template_id
        ).first()
        
        if not template:
            return {'error': '模板不存在'}
        
        for key, value in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        db.commit()
        db.refresh(template)
        
        return {'status': 'updated', 'template_id': template_id}
    
    @staticmethod
    async def delete_template(db: Session, template_id: str) -> dict:
        """删除模板"""
        template = db.query(MessageTemplate).filter(
            MessageTemplate.template_id == template_id
        ).first()
        
        if not template:
            return {'error': '模板不存在'}
        
        db.delete(template)
        db.commit()
        
        return {'status': 'deleted', 'template_id': template_id}
```

### 2.2 创建模板管理路由

**文件：`backend/app/routers/template_router.py`（新建）**

```python
"""
消息模板管理API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.template_service import TemplateService
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/templates", tags=["templates"])

# Pydantic模型
class TemplateModuleResponse(BaseModel):
    module_id: str
    module_name: str
    description: str
    trigger_keywords: List[str]
    template_content: str
    available_variables: List[str]
    use_scenario: str

class CreateTemplateRequest(BaseModel):
    template_name: str
    template_type: str  # SMS/EMAIL/WECHAT/WORK_WECHAT/AI/GROUP_BOT
    use_scenario: str
    template_content: str
    module_id: Optional[str] = None
    trigger_keywords: Optional[List[str]] = None
    target_audience: Optional[str] = 'all_external'

@router.get("/modules")
async def get_template_modules(db: AsyncSession = Depends(get_db)):
    """获取所有预留模块"""
    modules = await TemplateService.get_template_modules(db)
    return {'data': modules}

@router.get("/ai-templates")
async def get_ai_templates(db: AsyncSession = Depends(get_db)):
    """获取所有AI回复模板"""
    templates = await TemplateService.get_ai_templates(db)
    return {'data': templates}

@router.post("/create")
async def create_template(
    request: CreateTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    """创建新模板"""
    result = await TemplateService.create_template(
        db,
        template_name=request.template_name,
        template_type=request.template_type,
        use_scenario=request.use_scenario,
        template_content=request.template_content,
        module_id=request.module_id,
        trigger_keywords=request.trigger_keywords,
        target_audience=request.target_audience
    )
    return result

@router.put("/{template_id}")
async def update_template(
    template_id: str,
    request: CreateTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    """更新模板"""
    result = await TemplateService.update_template(
        db,
        template_id=template_id,
        template_name=request.template_name,
        template_content=request.template_content,
        is_enabled=True
    )
    return result

@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除模板"""
    result = await TemplateService.delete_template(db, template_id)
    return result
```

**在 main.py 中注册路由：**

```python
# backend/app/main.py
from app.routers import template_router

app.include_router(template_router.router)
```

---

## 🎨 第3部分：前端 UI 完善

### 3.1 更新 TemplateManager.vue

前端需要显示 5 个预留模块的选择。在创建新模板时，应该显示：

```vue
<!-- 在 "新建模板" 对话框中添加 -->

<el-dialog v-model="dialogVisible" title="新建模板">
  <!-- 现有字段... -->
  
  <!-- 模块选择（仅AI回复模板显示） -->
  <el-form-item v-if="form.template_type === 'AI'" label="使用预留模块">
    <el-select 
      v-model="form.module_id" 
      placeholder="选择预留模块（可选）"
      @change="onModuleSelect"
    >
      <el-option label="不使用预留模块（自定义）" value=""></el-option>
      <el-option 
        v-for="module in templateModules" 
        :key="module.module_id"
        :label="`${module.module_name} - ${module.use_scenario}`"
        :value="module.module_id"
      ></el-option>
    </el-select>
  </el-form-item>
  
  <!-- 模块信息显示 -->
  <el-alert 
    v-if="form.module_id"
    :title="`预留模块: ${selectedModule?.module_name}`"
    type="info"
    show-icon
    :closable="false"
    style="margin-bottom: 15px"
  >
    <div>触发关键词：{{ selectedModule?.trigger_keywords?.join('、') }}</div>
    <div>可用变量：{{ selectedModule?.available_variables?.join('、') }}</div>
  </el-alert>
  
  <!-- 模板内容 -->
  <el-form-item label="模板内容">
    <el-input 
      v-model="form.template_content"
      type="textarea"
      rows="15"
      placeholder="输入模板内容（如已选择预留模块，将自动填充）"
    />
  </el-form-item>
  
  <!-- ... 其他字段 -->
</el-dialog>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const templateModules = ref([])  // 预留模块列表
const selectedModule = computed(() => 
  templateModules.value.find(m => m.module_id === form.value.module_id)
)

// 获取预留模块列表
onMounted(async () => {
  try {
    const response = await axios.get('/api/templates/modules')
    templateModules.value = response.data.data
  } catch (error) {
    console.error('获取预留模块失败:', error)
  }
})

// 模块选择时，自动填充内容
const onModuleSelect = (moduleId) => {
  if (moduleId) {
    const module = templateModules.value.find(m => m.module_id === moduleId)
    if (module) {
      form.value.template_content = module.template_content
      form.value.trigger_keywords = module.trigger_keywords
    }
  }
}
</script>
```

---

## 🚀 完整实施步骤（按顺序）

### 步骤1：更新数据库模型

```bash
# 编辑 backend/app/models.py
# 添加 TemplateModule、MessageTemplate、TemplateVariable 类
```

### 步骤2：运行初始化脚本

```bash
cd backend
python scripts/init_template_modules.py
```

验证数据：

```bash
python -c "
from app.database import SessionLocal
from app.models import TemplateModule
db = SessionLocal()
modules = db.query(TemplateModule).all()
print(f'✅ 已初始化 {len(modules)} 个预留模块')
for m in modules:
    print(f'  - {m.module_id}: {m.module_name}')
"
```

### 步骤3：添加后端服务和路由

```bash
# 1. 创建 backend/app/services/template_service.py
# 2. 创建 backend/app/routers/template_router.py  
# 3. 在 backend/app/main.py 注册路由
```

### 步骤4：更新前端 UI

```bash
# 编辑 frontend/src/views/TemplateManager.vue
# 添加模块选择功能
```

### 步骤5：测试

```bash
# 后端
python -m uvicorn app.main:app --reload

# 前端
npm run dev

# 访问 http://localhost:3000/templates
# AI回复模板标签页
# 新建模板 → 模板类型选择"AI回复模板"
# 应该能看到 5 个预留模块的下拉选择
```

---

## 📸 预期效果

当完成以上实施后，模板管理页面应该显示：

```
消息模板管理 → 🤖 AI回复模板 标签

【现有模板列表】
ID  模板名称                使用场景      可用变量                        状态    操作
5   价格咨询AI回复         售前咨询      {product}, {price_basic}...     启用    编辑 预览 删除
6   售后维修AI回复         售后服务      {product}, {technician}...      启用    编辑 预览 删除

【新建模板对话框】
┌────────────────────────────────┐
│ 新建模板                        │
├────────────────────────────────┤
│ 模板名称：[_______________]    │
│ 模板类型：[AI回复模板  ▼]      │
│ 使用场景：[売前咨询      ▼]    │
│                                │
│ 使用预留模块：[不使用预设 ▼]   │  ← 新增选项
│               [① 查询项目]      │
│               [② 查询加急]      │
│               [③ 申请取消]      │  ← 5个预留模块
│               [④ 售后维修]      │
│               [⑤ 售前咨询]      │
│                                │
│ 当选择"④ 售后维修"时：          │
│ ℹ️ 预留模块：售后维修           │
│   触发关键词：售后、故障、坏了   │
│   可用变量：{technician}...     │
│                                │
│ 模板内容：                      │
│ [感谢您的反馈，{customer_name}!│
│  ...                            │
│  我们的技术员 {technician}      │
│  将准时上门服务。              │
│  请保持电话畅通...]             │
│                                │
│ [取消]  [保存模板]              │
└────────────────────────────────┘
```

完成后，AI回复模板列表会显示：

```
模板ID  模板名称              使用场景      触发关键词              状态    操作
5      价格咨询AI回复        售前咨询      咨询、价格、报价        启用    编辑 删除
6      售后维修AI回复        售后服务      售后、故障、坏了        启用    编辑 删除
7      查询项目提示          查询项目      查询、项目、进度    ✅ 已启用 编辑 删除
8      加急处理流程          查询加急      加急、催促、尽快    ✅ 已启用 编辑 删除
9      取消流程说明          申请取消      取消、退单、作废    ✅ 已启用 编辑 删除
```

---

## ✅ 完成清单

- [ ] 在 models.py 添加 3 个新表
- [ ] 创建 init_template_modules.py 脚本
- [ ] 运行初始化脚本，验证数据
- [ ] 创建 template_service.py 服务
- [ ] 创建 template_router.py 路由
- [ ] 在 main.py 注册路由
- [ ] 更新 TemplateManager.vue 前端
- [ ] 测试：新建AI模板 → 选择预留模块 → 保存
- [ ] 验证列表中出现 5 个预留模块对应的模板

---

这样就从 0 到 1 完整实现了 **5 个预留模块的完整系统**！🎉

