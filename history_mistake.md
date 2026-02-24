# 错误历史记录

| 时间 | 错误信息 | 错误原因 | 解决方法 |
|------|---------|---------|---------|
| 2026-02-21 | JSONDecodeError: Expecting value | metadata.json 文件写入不完整导致损坏 | 添加 try-except 处理，损坏时重新创建 |
| 2026-02-21 | TypeError: Object of type datetime is not JSON serializable | datetime 对象无法直接 JSON 序列化 | 添加 json_serializer 函数处理 datetime 类型 |
| 2026-02-21 | 端口 8000 被占用 | 多个 uvicorn 进程同时运行 | 使用端口 8001 或关闭占用进程 |
| 2026-02-24 | 400 Bad Request: No AI model configured | FolderSummarizer 未正确初始化默认模型 | 在 routes.py 中添加默认模型初始化逻辑 |
| 2026-02-24 | Folder Tree Display Issue | max_depth=4 太小且显示文件限制 | 修改 ai_summarizer.py 增加深度至10并移除限制 |
| 2026-02-24 | Frontend Syntax Error | 缺少函数结束大括号 | 在 inspiration.ts 中添加缺失的 `}` |
| 2026-02-24 | 400 Bad Request: No AI model configured | 文件夹总结模型未正确注册，仅默认模型生效 | 修改 ai_summarizer.py 显式注册 folder 类型模型，routes.py 添加详细日志 |
| 2026-02-24 | TypeError: cannot unpack non-iterable WindowsPath object | 运行的后端代码为旧版本，其中 important_files 为路径列表而非元组 | 重启后端服务以加载已修复的代码（将路径列表改为元组列表） |
| 2026-02-24 | Request timed out | 文件夹文件较多时，顺序处理摘要导致总耗时过长，或 OpenAI 客户端默认超时时间过短 | 优化 ai_summarizer.py，使用 asyncio.gather 并发处理文件摘要，并增加客户端超时时间至 120s |
| 2026-02-24 | 总结逻辑优化需求 | 原总结逻辑为平铺式，用户希望改为自底向上的递归总结（文件->子文件夹->父文件夹） | 重构 FolderSummarizer，实现 _summarize_recursive 方法，支持递归生成文件夹总结 |
| 2026-02-24 | 递归总结返回空 | 递归逻辑中对相对路径的处理可能有误，导致根目录被误判或忽略 | 优化路径处理逻辑，增加日志输出，并确保根目录即使无子内容也能返回基本结构 |
| 2026-02-24 | NameError: name 'asyncio' is not defined | ai_summarizer.py 中 summarize 方法内部 import asyncio 被移动位置或作用域问题导致 _summarize_recursive 无法访问 | 确保 asyncio 在方法顶部正确导入，或在模块级别导入（本次修复是在方法内部调整导入位置） |
| 2026-02-24 | NameError: name 'asyncio' is not defined (again) | 虽然在 summarize 中导入了 asyncio，但 _summarize_recursive 是独立方法，仍无法访问 | 在 _summarize_recursive 方法内部显式导入 asyncio |
