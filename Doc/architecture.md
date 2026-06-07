# FlowForge 项目架构文档

## 项目概述

FlowForge 是一个低代码流程引擎平台，包含可视化表单设计器和流程审批引擎。用户可通过拖拽方式设计表单，定义审批流程，并在运行时填写表单、发起流程、进行审批操作。

---

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端框架 | React | ^18.3.1 |
| 路由 | react-router-dom | ^6.26.2 |
| 拖拽 | @dnd-kit/core + sortable | ^6.1.0 / ^8.0.0 |
| 构建工具 | Vite | ^5.4.7 |
| 后端框架 | FastAPI (Python) | latest |
| ORM | SQLAlchemy | latest |
| 数据验证 | Pydantic | latest |
| 数据库 | SQLite | -- |
| 测试 | pytest + httpx | -- |

---

## 项目结构

```
FlowForge/
├── Doc/                                   # 文档
│   ├── requirement-lowcode-flow.md        # 需求文档
│   └── architecture.md                    # 架构文档（本文件）
├── frontend/                              # React 前端 SPA
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx                       # 入口 + 路由配置
│       ├── index.css                      # 全局样式
│       ├── pages/
│       │   ├── FormDesigner.jsx           # 表单设计器（拖拽）
│       │   ├── FormRenderer.jsx           # 表单渲染 + 提交
│       │   └── ProcessStart.jsx           # 流程发起页
│       └── components/
│           ├── DraggablePaletteItem.jsx   # 左侧控件拖拽源
│           ├── SortableFieldCard.jsx      # 画布中可排序字段卡片
│           └── PropertiesPanel.jsx        # 右侧属性配置面板
└── server/                                # Python FastAPI 后端
    ├── main.py                            # 应用启动、中间件、路由挂载
    ├── database.py                        # SQLAlchemy 引擎 + 会话工厂
    ├── requirements.txt                   # Python 依赖
    ├── api/
    │   ├── forms.py                       # 表单定义 CRUD
    │   └── processes.py                   # 流程定义 + 实例 API
    ├── engine/
    │   └── process_engine.py              # 流程引擎（状态机）
    ├── models/
    │   └── models.py                      # SQLAlchemy ORM 模型
    ├── schemas/
    │   └── schemas.py                     # Pydantic 请求/响应模型
    └── tests/
        ├── test_api.py                    # API 集成测试
        └── test_process_engine.py         # 引擎单元测试
```

---

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         浏览器 (Browser)                         │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ FormDesigner │  │ FormRenderer │  │     ProcessStart       │ │
│  │  (表单设计)   │  │  (表单填写)   │  │     (流程发起)         │ │
│  └──────────────┘  └──────────────┘  └────────────────────────┘ │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTP API (localhost:5173 → proxy → :8000)
┌───────────────────────────────▼─────────────────────────────────┐
│                      FastAPI Backend                              │
│                                                                   │
│  ┌─────────────────┐    ┌──────────────────┐                    │
│  │  Forms API      │    │  Processes API   │                    │
│  │  (表单管理)      │    │  (流程管理)       │                    │
│  └────────┬────────┘    └────────┬─────────┘                    │
│           │                      │                               │
│           │              ┌───────▼────────┐                      │
│           │              │ ProcessEngine  │                      │
│           │              │ (状态机引擎)    │                      │
│           │              └───────┬────────┘                      │
│           │                      │                               │
│  ┌────────▼──────────────────────▼─────────┐                    │
│  │           SQLAlchemy ORM                 │                    │
│  └────────────────────┬────────────────────┘                    │
└───────────────────────┼──────────────────────────────────────────┘
                        │
               ┌────────▼────────┐
               │   SQLite DB     │
               │  (flowforge.db) │
               └─────────────────┘
```

---

## 核心模块详解

### 1. 表单设计器 (FormDesigner)

三栏式布局：

- **左侧控件面板** — 四种控件类型：文本框、数字输入、下拉选择、日期选择器
- **中间画布** — 拖拽放置区域，使用 `@dnd-kit/sortable` 实现字段排序
- **右侧属性面板** — 编辑选中字段的标签、占位符、选项列表、校验规则

**字段 Schema 结构：**

```json
{
  "fieldId": "field_1717000000_1",
  "type": "text | number | dropdown | date",
  "label": "显示标签",
  "placeholder": "提示文字",
  "options": ["选项1", "选项2"],
  "validations": [
    { "rule": "required", "message": "此项为必填" },
    { "rule": "maxLength", "value": 50, "message": "最大长度为50" },
    { "rule": "min", "value": 1, "message": "最小值为1" },
    { "rule": "max", "value": 30, "message": "最大值为30" },
    { "rule": "regex", "value": "^\\d+$", "message": "格式不正确" }
  ]
}
```

### 2. 表单渲染器 (FormRenderer)

- 从后端获取表单 Schema JSON
- 根据字段 `type` 动态渲染对应 HTML 控件
- 实现客户端校验：required、maxLength、regex、min、max
- 失焦时校验单个字段，提交时校验全部字段
- 校验通过后调用 `/api/processes/start` 发起流程

### 3. 流程引擎 (ProcessEngine)

无状态的状态机实现，每次请求实例化并计算下一状态。

**节点类型：**

| 类型 | 说明 |
|------|------|
| `start` | 开始节点，自动推进到下一节点 |
| `approval` | 审批节点，需要审批人做出决策（通过/拒绝/退回） |
| `condition` | 条件分支节点，根据表单数据评估走哪条边 |
| `end` | 结束节点，标记流程完成 |

**流程定义 JSON：**

```json
{
  "nodes": [
    { "id": "start", "type": "start" },
    { "id": "dept_mgr", "type": "approval", "assignee": "manager" },
    { "id": "check_days", "type": "condition" },
    { "id": "end", "type": "end" }
  ],
  "edges": [
    { "source": "start", "target": "dept_mgr" },
    { "source": "dept_mgr", "target": "check_days" },
    { "source": "check_days", "target": "gm_approval", "condition": "days > 3" },
    { "source": "check_days", "target": "end" }
  ]
}
```

**执行逻辑 (`advance` 方法)：**

1. 验证当前节点存在
2. `approval` 节点：根据 `decision` 参数判断
   - `"approve"` → 推进到下一节点
   - `"reject"` → 停留当前节点，状态变为 `rejected`
   - `"return"` → 跳回 start 节点，状态变为 `returned`
3. `condition` 节点：按序评估出边条件表达式，匹配第一个为真的，否则走默认边
4. 递归自动推进连续的 condition 节点
5. 返回 `(next_node_id, status)`

**条件表达式解析：**

- 正则模式：`^(\w+)\s*(>=|<=|!=|==|>|<)\s*(.+)$`
- 支持运算符：`>`、`>=`、`<`、`<=`、`==`、`!=`
- 优先尝试数值比较，失败则字符串比较

---

## 数据模型

```
┌──────────────────┐       ┌────────────────────┐
│ FormDefinition   │       │ ProcessDefinition  │
├──────────────────┤       ├────────────────────┤
│ id (PK)          │       │ id (PK)            │
│ name             │       │ name               │
│ schema_json      │       │ definition_json    │
│ version          │       │ version            │
│ created_at       │       │ created_at         │
│ updated_at       │       │ updated_at         │
└────────┬─────────┘       └─────────┬──────────┘
         │                           │
         │ 1:N                       │ 1:N
         ▼                           ▼
┌──────────────────┐       ┌────────────────────┐
│ FormInstance     │◄──────│ ProcessInstance    │
├──────────────────┤  1:1  ├────────────────────┤
│ id (PK)          │       │ id (PK)            │
│ form_def_id (FK) │       │ process_def_id(FK) │
│ data_json        │       │ form_instance_id   │
│ process_inst_id  │       │ current_node_id    │
│ created_at       │       │ status             │
└──────────────────┘       │ created_at         │
                           │ updated_at         │
                           └─────────┬──────────┘
                                     │ 1:N
                                     ▼
                           ┌────────────────────┐
                           │ ApprovalRecord     │
                           ├────────────────────┤
                           │ id (PK)            │
                           │ process_inst_id(FK)│
                           │ node_id            │
                           │ assignee           │
                           │ decision           │
                           │ comment            │
                           │ created_at         │
                           └────────────────────┘
```

**版本管理策略：** 每次保存表单/流程定义时，按 `name` 查找已有最大版本号并 +1，保留完整历史。

---

## API 接口

### 表单相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/forms/` | 创建/保存表单定义（自动版本） |
| GET | `/api/forms/` | 获取所有表单定义列表 |
| GET | `/api/forms/{form_id}` | 获取单个表单定义 |
| GET | `/api/forms/schema/{form_id}` | 获取表单渲染用 Schema |

### 流程相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/processes/definitions` | 创建流程定义 |
| GET | `/api/processes/definitions` | 获取所有流程定义 |
| GET | `/api/processes/definitions/{id}` | 获取单个流程定义 |
| POST | `/api/processes/start` | 发起流程实例 |
| POST | `/api/processes/approve` | 审批操作 |
| POST | `/api/processes/resubmit` | 退回后重新提交 |
| GET | `/api/processes/instances/{id}` | 获取流程实例状态 |
| GET | `/api/processes/instances/{id}/records` | 获取审批记录 |

---

## 前端路由

| 路径 | 组件 | 说明 |
|------|------|------|
| `/` | FormDesigner | 表单设计器首页 |
| `/render/:formId` | FormRenderer | 表单填写（支持 `?processId=` 参数） |
| `/process/start` | ProcessStart | 流程发起 / 表单列表 |

---

## 组件层级

```
<React.StrictMode>
  <BrowserRouter>
    <Routes>
      ├── "/" → <FormDesigner>
      │         ├── <DndContext>
      │         │     ├── <DraggablePaletteItem /> × 4
      │         │     ├── <SortableContext>
      │         │     │     └── <SortableFieldCard /> × N
      │         │     └── <PropertiesPanel />
      │         └── </DndContext>
      │
      ├── "/render/:formId" → <FormRenderer>
      │         └── <form> (动态渲染字段)
      │
      └── "/process/start" → <ProcessStart>
                └── 表单列表 + 流程定义列表
    </Routes>
  </BrowserRouter>
</React.StrictMode>
```

---

## 状态管理

- **前端**：纯 React 本地状态（useState），无全局状态管理库
- **后端**：数据库作为唯一持久化真相源
- **流程引擎**：无状态设计，每次请求从 JSON 定义实例化，计算结果写回数据库

---

## 关键架构特征

1. **Monorepo 双部署单元** — React SPA + Python FastAPI，通过 Vite 代理连接
2. **Schema 驱动的表单渲染** — JSON Schema 设计即运行，无代码生成步骤
3. **无状态流程引擎** — 每次请求实例化，确定性计算下一状态，数据库存储当前指针
4. **自动版本管理** — 表单和流程定义按名称自增版本号，保留完整变更历史
5. **条件表达式引擎** — 简单正则解析 + 数值/字符串比较，支持分支路由
6. **认证占位** — main.py 中预留中间件钩子，当前为直通
7. **测试覆盖** — pytest 覆盖引擎单元测试和 API 集成测试全生命周期

---

## 开发运行

```bash
# 前端
cd frontend
npm install
npm run dev          # → http://localhost:5173

# 后端
cd server
pip install -r requirements.txt
uvicorn main:app --reload  # → http://localhost:8000

# 测试
cd server
pytest
```

Vite 开发服务器将 `/api` 请求代理到 `http://localhost:8000`。
