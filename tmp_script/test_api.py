"""
API Test Script for Creative Master
"""

import httpx
import json
import asyncio

BASE_URL = "http://127.0.0.1:8001"

async def test_api():
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("=" * 50)
        print("1. 测试根路由")
        print("=" * 50)
        response = await client.get(f"{BASE_URL}/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        print("\n" + "=" * 50)
        print("2. 测试健康检查")
        print("=" * 50)
        response = await client.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        print("\n" + "=" * 50)
        print("3. 配置AI模型")
        print("=" * 50)
        model_config = {
            "name": "Test-GPT4",
            "provider": "openai",
            "model_name": "gpt-4",
            "api_key": "sk-test-key-12345",
            "file_types": ["image", "text"],
            "is_default": True
        }
        response = await client.post(
            f"{BASE_URL}/api/v1/config/models",
            json=model_config
        )
        print(f"状态码: {response.status_code}")
        model_data = response.json()
        print(f"响应: {json.dumps(model_data, indent=2, ensure_ascii=False)}")
        
        print("\n" + "=" * 50)
        print("4. 获取模型配置列表")
        print("=" * 50)
        response = await client.get(f"{BASE_URL}/api/v1/config/models")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        print("\n" + "=" * 50)
        print("5. 添加灵感 - 创建测试文件")
        print("=" * 50)
        import os
        test_dir = "d:/python_project/creative_master/storage/test_inspirations"
        os.makedirs(test_dir, exist_ok=True)
        
        test_file = os.path.join(test_dir, "test_inspiration.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("这是一个测试灵感文件。\n它包含了创意想法和灵感内容。")
        
        inspiration_data = {
            "source_path": test_file,
            "name": "测试灵感文本",
            "tags": ["测试", "创意"],
            "copy_file": True
        }
        response = await client.post(
            f"{BASE_URL}/api/v1/inspirations",
            json=inspiration_data
        )
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        if response.status_code == 200:
            inspiration = response.json()
            print(f"响应: {json.dumps(inspiration, indent=2, ensure_ascii=False)}")
            inspiration_id = inspiration.get("id")
        else:
            inspiration_id = None
            inspiration = None
        
        print("\n" + "=" * 50)
        print("6. 获取灵感列表")
        print("=" * 50)
        response = await client.get(f"{BASE_URL}/api/v1/inspirations")
        print(f"状态码: {response.status_code}")
        inspirations = response.json()
        print(f"响应: {json.dumps(inspirations, indent=2, ensure_ascii=False)}")
        
        if inspiration_id:
            print("\n" + "=" * 50)
            print("7. 创建灵感组合")
            print("=" * 50)
            combination_data = {
                "name": "测试组合",
                "inspiration_ids": [inspiration_id]
            }
            response = await client.post(
                f"{BASE_URL}/api/v1/combinations",
                json=combination_data
            )
            print(f"状态码: {response.status_code}")
            combination = response.json()
            print(f"响应: {json.dumps(combination, indent=2, ensure_ascii=False)}")
            combination_id = combination.get("id")
            
            print("\n" + "=" * 50)
            print("8. 获取组合列表")
            print("=" * 50)
            response = await client.get(f"{BASE_URL}/api/v1/combinations")
            print(f"状态码: {response.status_code}")
            print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        print("\n" + "=" * 50)
        print("9. 搜索灵感")
        print("=" * 50)
        response = await client.get(f"{BASE_URL}/api/v1/inspirations/search/测试")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        print("\n" + "=" * 50)
        print("✅ 所有基础API测试完成!")
        print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_api())
