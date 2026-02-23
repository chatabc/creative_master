import httpx
import json

BASE_URL = "http://localhost:8002"

def test_conflict():
    print("=== 测试后缀冲突检测 ===")
    
    # 先获取现有文件类型
    print("\n0. 获取现有文件类型...")
    resp = httpx.get(f"{BASE_URL}/api/v1/file-types", timeout=10)
    file_types = resp.json()
    
    # 删除之前可能创建的测试类型
    for ft in file_types:
        if ft["name"] == "test_conflict":
            print(f"删除已存在的测试类型: {ft['id']}")
            httpx.delete(f"{BASE_URL}/api/v1/file-types/{ft['id']}", timeout=10)
    
    print("\n1. 尝试添加包含已存在后缀的文件类型...")
    resp = httpx.post(
        f"{BASE_URL}/api/v1/file-types",
        json={
            "name": "test_conflict",
            "display_name": "测试冲突类型",
            "extensions": [".py", ".js", ".custom_ext"],
            "color": "#ff0000"
        },
        timeout=10
    )
    print(f"状态码: {resp.status_code}")
    result = resp.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get("status") == "conflict":
        print("\n2. 检测到冲突，确认替换后缀...")
        conflicts = result.get("conflicts", [])
        extensions_to_replace = [c["extension"] for c in conflicts]
        print(f"需要替换的后缀: {extensions_to_replace}")
        
        resp = httpx.post(
            f"{BASE_URL}/api/v1/file-types",
            json={
                "name": "test_conflict",
                "display_name": "测试冲突类型",
                "extensions": [".py", ".js", ".custom_ext"],
                "color": "#ff0000",
                "force_replace": True,
                "extensions_to_replace": extensions_to_replace
            },
            timeout=10
        )
        print(f"状态码: {resp.status_code}")
        result = resp.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get("status") == "success":
            print("\n✅ 后缀替换成功！")
    elif result.get("id"):
        print("\n文件类型创建成功（无冲突后缀）")

if __name__ == "__main__":
    test_conflict()
