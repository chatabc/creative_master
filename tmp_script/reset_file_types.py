import httpx

BASE_URL = "http://localhost:8002"

print("重置文件类型...")
resp = httpx.post(f"{BASE_URL}/api/v1/file-types/reset", timeout=10)
data = resp.json()
print(f"重置后文件类型数量: {len(data)}")
print("\n文件类型列表:")
for ft in data:
    print(f"  - {ft['display_name']} ({ft['name']}): {len(ft['extensions'])} 个后缀")
