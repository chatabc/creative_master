
| 日期 | 操作 | 详情 |
|------|------|------|
| 2026-02-24 | 优化：移除重要/次要文档 | 修改 ai_summarizer.py 和 InspirationsView.vue，移除重要和次要文档的生成和显示逻辑，专注于递归总结 |
| 2026-02-25 | 启动后端服务 | 执行命令 `python -m uvicorn backend.main:app --port 8002 --reload`，后端成功启动在 http://127.0.0.1:8002 |
| 2026-02-25 | 启动前端服务 | 使用 fnm 管理的 Node.js v24.13.1，执行命令启动 Vite 开发服务器，前端成功启动在 http://localhost:3001 |
| 2026-02-25 | 修复文件夹总结显示为空 | FolderSummarizer 类缺少 _get_file_importance 方法，导致文件总结时抛出 AttributeError，在 ai_summarizer.py 中添加该方法 |
| 2026-02-25 | 优化文件夹总结功能 | 修改总结逻辑：每个文件夹总结只基于直接子项；忽略文件夹时自动忽略其所有子项；添加更多文件类型支持 |
| 2026-02-25 | 更新 README 启动方式 | 修改启动命令为用户指定的方式，提醒其他用户替换路径 |
| 2026-02-25 | 提交代码到本地 Git | 代码已提交到本地仓库（commit: 622f6f6），GitHub 推送因网络超时失败 |
