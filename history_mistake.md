# 错误历史记录

| 时间 | 错误信息 | 错误原因 | 解决方法 |
|------|---------|---------|---------|
| 2026-02-21 | JSONDecodeError: Expecting value | metadata.json 文件写入不完整导致损坏 | 添加 try-except 处理，损坏时重新创建 |
| 2026-02-21 | TypeError: Object of type datetime is not JSON serializable | datetime 对象无法直接 JSON 序列化 | 添加 json_serializer 函数处理 datetime 类型 |
| 2026-02-21 | 端口 8000 被占用 | 多个 uvicorn 进程同时运行 | 使用端口 8001 或关闭占用进程 |
