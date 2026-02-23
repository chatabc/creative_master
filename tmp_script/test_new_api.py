import httpx
import json

BASE_URL = "http://127.0.0.1:8001"

def test_api():
    print("=== 1. 测试健康检查 ===")
    try:
        resp = httpx.get(f"{BASE_URL}/health", timeout=5)
        print(f"状态码: {resp.status_code}")
        print(f"响应: {resp.text}")
    except Exception as e:
        print(f"错误: {e}")

    print("\n=== 2. 测试获取文件类型 ===")
    try:
        resp = httpx.get(f"{BASE_URL}/api/v1/file-types", timeout=5)
        print(f"状态码: {resp.status_code}")
        data = resp.json()
        print(f"文件类型数量: {len(data)}")
        for ft in data[:3]:
            print(f"  - {ft['display_name']} ({ft['name']}): {len(ft['extensions'])} 个后缀")
    except Exception as e:
        print(f"错误: {e}")

    print("\n=== 3. 测试添加文件类型 ===")
    try:
        resp = httpx.post(
            f"{BASE_URL}/api/v1/file-types",
            json={
                "name": "test_type",
                "display_name": "测试类型",
                "extensions": [".test", ".tst"],
                "color": "#ff0000",
                "description": "这是一个测试类型"
            },
            timeout=5
        )
        print(f"状态码: {resp.status_code}")
        print(f"响应: {resp.text}")
    except Exception as e:
        print(f"错误: {e}")

    print("\n=== 4. 测试获取灵感列表 ===")
    try:
        resp = httpx.get(f"{BASE_URL}/api/v1/inspirations", timeout=5)
        print(f"状态码: {resp.status_code}")
        print(f"响应: {resp.text}")
    except Exception as e:
        print(f"错误: {e}")

    print("\n=== 5. 测试文件上传 ===")
    try:
        test_content = "这是一个测试文件的内容".encode('utf-8')
        files = {"file": ("test_upload.txt", test_content, "text/plain")}
        resp = httpx.post(
            f"{BASE_URL}/api/v1/inspirations/upload",
            files=files,
            timeout=10
        )
        print(f"状态码: {resp.status_code}")
        print(f"响应: {resp.text}")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_api()
