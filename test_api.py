
import requests
import json

def test_api():
    """测试镜像同步API"""
    base_url = "http://localhost:5000"

    # 测试数据
    test_images = ["nginx:latest", "redis:alpine"]
    destination_registry = "docker.io/testuser"

    # 测试同步API
    sync_data = {
        "images": test_images,
        "destination_registry": destination_registry,
        "source_registry": "docker.io/library"
    }

    print("测试镜像同步API...")
    try:
        response = requests.post(
            f"{base_url}/api/sync",
            json=sync_data
        )

        if response.status_code == 200:
            result = response.json()
            print("API调用成功!")
            print(f"同步结果: {json.dumps(result, indent=2)}")
        else:
            print(f"API调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")

    except requests.exceptions.ConnectionError:
        print("无法连接到API服务器，请确保服务器已启动")
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    test_api()
