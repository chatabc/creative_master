# Creative Master - 创意灵感管理系统

## 项目概述
Creative Master 是一个AI驱动的创意灵感管理工具，帮助用户收集、组织、组合灵感，并生成创意提示词。

## 项目结构

```
creative_master/
├── backend/                 # 后端服务
│   ├── api/                # API接口
│   │   └── routes.py       # FastAPI路由定义
│   ├── core/               # 核心功能模块
│   │   ├── inspiration.py  # 灵感存储与管理
│   │   ├── ai_summarizer.py # AI内容总结
│   │   ├── creative_gen.py # 创意生成
│   │   ├── prompt_gen.py   # 提示词生成
│   │   ├── config_manager.py # 配置管理
│   │   └── file_type_manager.py # 文件类型管理
│   ├── models/             # 数据模型
│   │   └── __init__.py     # Pydantic模型定义
│   ├── main.py             # FastAPI应用入口
│   └── requirements.txt    # Python依赖
├── frontend/               # 前端界面 (Vue 3 + TypeScript)
│   ├── src/
│   │   ├── components/     # UI组件
│   │   │   ├── AppHeader.vue      # 顶部导航
│   │   │   ├── AppSidebar.vue     # 侧边栏
│   │   │   ├── FileDropZone.vue   # 文件上传组件
│   │   │   ├── TopologyEditor.vue # 拓扑编辑器
│   │   │   ├── TopologyGraph.vue  # 拓扑图组件
│   │   │   └── TopologyPreview.vue # 拓扑预览
│   │   ├── views/          # 页面视图
│   │   │   ├── HomeView.vue           # 工作台
│   │   │   ├── InspirationsView.vue   # 灵感库
│   │   │   ├── CombineView.vue        # 生成组合
│   │   │   ├── CombinationsView.vue   # 组合管理
│   │   │   ├── CreativesView.vue      # 生成创意
│   │   │   ├── CreativeManagementView.vue # 创意管理
│   │   │   └── SettingsView.vue       # 设置
│   │   ├── stores/         # Pinia状态管理
│   │   │   ├── inspiration.ts  # 灵感状态
│   │   │   ├── combination.ts  # 组合状态
│   │   │   ├── creative.ts     # 创意状态
│   │   │   ├── fileType.ts     # 文件类型状态
│   │   │   ├── settings.ts     # 设置状态
│   │   │   └── prompt.ts       # 提示词状态
│   │   ├── types/          # TypeScript类型定义
│   │   ├── router/         # Vue Router配置
│   │   ├── App.vue         # 根组件
│   │   ├── main.ts         # 入口文件
│   │   └── style.css       # 全局样式
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
├── data/                   # JSON数据存储
│   ├── combinations.json   # 组合数据
│   ├── creatives.json      # 创意数据
│   ├── model_configs.json  # AI模型配置
│   ├── relation_types.json # 关系类型
│   └── file_types.json     # 文件类型配置
├── storage/                # 灵感文件存储
│   ├── inspirations/       # 按类型分类存储
│   │   ├── image/
│   │   ├── code/
│   │   ├── text/
│   │   ├── video/
│   │   ├── audio/
│   │   ├── document/
│   │   └── folder/
├── tmp_script/             # 临时脚本存放
├── .env.example            # 环境变量示例
├── .gitignore
├── pyproject.toml          # Python项目配置
├── project.md              # 项目说明
├── history_procession.md   # 开发历史记录
├── history_mistake.md      # 错误记录
└── history_command.md      # 命令记录
```

## 项目模块

### 1. 灵感存储模块 (Inspiration Storage)
- 支持多种类型：图片、代码、文字、视频、音频、文档、文件夹
- 文件元数据管理
- 分类与标签系统
- 支持文件上传和路径添加两种方式
- 支持文件夹上传

### 2. AI总结模块 (AI Summarizer)
- 图片内容识别与描述
- 代码结构分析与功能总结
- 文字内容提取与摘要
- 文件夹项目结构分析
- 支持文件夹结构化总结（目录树、概览、重要/次要文档）
- 支持分段重新生成总结
- 支持多种AI模型配置

### 3. 可视化组合模块 (Visual Combination)
- 拖拽式灵感组合
- 拓扑图可视化编辑
- 灵感关系定义（主次、支持关系）
- AI智能推荐组合

### 4. 创意生成模块 (Creative Generator)
- 基于灵感组合生成多个创意方案
- 支持用户反馈迭代优化
- 创意持久化存储

### 5. 提示词生成模块 (Prompt Generator)
- 根据选中创意生成详细提示词
- 自动整理相关灵感文件信息
- 支持复制与导出
- 提示词持久化存储

### 6. 文件聚合模块 (File Aggregation)
- 将创意相关的源文件聚合到指定文件夹
- 按文件类型分类存放
- 支持批量文件操作

## 数据流程

```
灵感输入 → 内容分析 → AI总结 → 灵感组合 → 关系定义 → 创意生成 → 提示词生成 → 文件聚合/导出
```

## 技术栈

### 后端
- Python 3.10+
- FastAPI (Web框架)
- Pydantic (数据验证)
- OpenAI API / 其他LLM API
- Pillow (图片处理)
- python-multipart (文件上传)

### 前端
- Vue 3 (Composition API)
- TypeScript
- TailwindCSS
- Pinia (状态管理)
- Vue Router
- Axios (HTTP客户端)

## API端点

### 灵感管理
- `GET /api/v1/inspirations` - 获取灵感列表
- `POST /api/v1/inspirations` - 添加灵感
- `POST /api/v1/inspirations/upload` - 上传单个文件
- `POST /api/v1/inspirations/upload-batch` - 批量上传文件
- `GET /api/v1/inspirations/{id}` - 获取单个灵感
- `DELETE /api/v1/inspirations/{id}` - 删除灵感
- `POST /api/v1/inspirations/{id}/summarize` - AI总结灵感
- `POST /api/v1/inspirations/{id}/summarize/section` - 重新生成总结部分

### 组合管理
- `GET /api/v1/combinations` - 获取组合列表
- `POST /api/v1/combinations` - 创建组合
- `PUT /api/v1/combinations/{id}` - 更新组合
- `DELETE /api/v1/combinations/{id}` - 删除组合

### 创意管理
- `GET /api/v1/creatives` - 获取创意列表
- `POST /api/v1/creatives` - 创建创意
- `PUT /api/v1/creatives/{id}` - 更新创意
- `DELETE /api/v1/creatives/{id}` - 删除创意
- `POST /api/v1/creatives/aggregate-files` - 聚合源文件

### 提示词生成
- `POST /api/v1/prompts/generate-from-creative` - 从创意生成提示词

### AI模型配置
- `GET /api/v1/model-configs` - 获取模型配置
- `POST /api/v1/model-configs` - 添加模型配置
- `PUT /api/v1/model-configs/{id}` - 更新模型配置
- `DELETE /api/v1/model-configs/{id}` - 删除模型配置

## 启动方式

### 后端
```bash
cd creative_master
python -m uvicorn backend.main:app --port 8002 --reload
```

### 前端
```bash
cd creative_master/frontend
npm install
npm run dev -- --port 3001
```

## 开发历史

详见 [history_procession.md](./history_procession.md)
