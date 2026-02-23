# Creative Master

一个AI驱动的创意灵感管理工具，帮助用户收集、组织、组合灵感，并生成创意提示词。

## 功能特性

- **灵感管理** - 支持图片、代码、文字、视频、音频、文档、文件夹等多种类型
- **AI总结** - 自动分析灵感内容并生成摘要
- **可视化组合** - 拖拽式灵感组合，支持关系定义
- **创意生成** - 基于灵感组合生成多个创意方案
- **提示词生成** - 根据创意生成详细的AI提示词
- **文件聚合** - 将创意相关的源文件聚合到指定文件夹

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+

### 安装

```bash
# 克隆项目
git clone https://github.com/chatabc/creative_master.git
cd creative_master

# 安装后端依赖
pip install -r backend/requirements.txt

# 安装前端依赖
cd frontend
npm install
```

### 配置

1. 复制环境变量示例文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，配置AI模型API密钥：
```
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 启动

```bash
# 启动后端 (端口 8002)
python -m uvicorn backend.main:app --port 8002 --reload

# 启动前端 (端口 3001)
cd frontend
npm run dev -- --port 3001
```

访问 http://localhost:3001 开始使用。

## 项目结构

```
creative_master/
├── backend/           # FastAPI后端服务
│   ├── api/          # API路由
│   ├── core/         # 核心模块
│   └── models/       # 数据模型
├── frontend/         # Vue 3前端
│   └── src/
│       ├── components/  # UI组件
│       ├── views/       # 页面视图
│       └── stores/      # 状态管理
├── data/             # JSON数据存储
└── storage/          # 灵感文件存储
```

## 技术栈

| 后端 | 前端 |
|------|------|
| Python 3.10+ | Vue 3 |
| FastAPI | TypeScript |
| Pydantic | TailwindCSS |
| OpenAI API | Pinia |
| Pillow | Vue Router |

## API文档

启动后端后访问 http://localhost:8002/docs 查看Swagger API文档。

## 使用流程

1. **添加灵感** - 上传文件或添加文件路径
2. **AI总结** - 为灵感生成AI摘要
3. **创建组合** - 将多个灵感组合在一起
4. **生成创意** - 基于组合生成创意方案
5. **生成提示词** - 为创意生成详细的AI提示词
6. **聚合文件** - 将相关文件导出到指定文件夹

## 许可证

MIT License
