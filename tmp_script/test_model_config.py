import httpx
import json

BASE_URL = "http://localhost:8002"

def test_model_config():
    print("=== 1. 测试添加AI模型配置 ===")
    try:
        resp = httpx.post(
            f"{BASE_URL}/api/v1/config/models",
            json={
                "name": "Test-GPT4",
                "provider": "openai",
                "model_name": "gpt-4",
                "api_key": "sk-test-key-12345",
                "file_types": ["image", "text"],
                "is_default": True
            },
            timeout=10
        )
        print(f"状态码: {resp.status_code}")
        print(f"响应: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"错误: {e}")

    print("\n=== 2. 测试获取模型配置列表 ===")
    try:
        resp = httpx.get(f"{BASE_URL}/api/v1/config/models", timeout=10)
        print(f"状态码: {resp.status_code}")
        data = resp.json()
        print(f"模型数量: {len(data)}")
        for m in data:
            print(f"  - {m['name']} ({m['provider']}/{m['model_name']})")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_model_config()
