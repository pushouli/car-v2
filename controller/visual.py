import io
import cv2
from flask import request, jsonify
from flask_restful import Resource
import requests

from service.base.camera import Camera
from service.front_distance import FrontDistance


class VisualController(Resource):
    def __init__(self):
        self.api_key = "app-gq5HHNvC3vtnzrNDbR2QBGs2"

    def post(self):
        prompt = request.json.get("prompt")
        if not prompt:
            return jsonify({"error": "Missing 'prompt' parameter"}), 400

        try:

            upload_file_id = self.capture_and_upload()
            result = self.run_workflow(prompt, upload_file_id)
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def capture_and_upload(self):
        camera = Camera()
        # 截图
        frame = camera.capture_frame()
        camera.stop()
        # 转为 JPEG 格式的字节流
        _, buffer = cv2.imencode(".jpg", frame)
        img_bytes = io.BytesIO(buffer.tobytes())
        # 上传文件
        upload_url = "https://dify.ycyw.com/v1/files/upload"
        response = requests.post(
            upload_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            files={"file": ("captured_frame.jpg", img_bytes, "image/jpeg")},
            data={"user": "car"},
        )
        response.raise_for_status()
        file_id = response.json().get("id")
        return file_id

    def run_workflow(self, prompt, upload_file_id):
        # 执行工作流
        workflow_url = "https://dify.ycyw.com/v1/workflows/run"
        payload = {
            "inputs": {
                "prompt": prompt,
                "image": {
                    "type": "image",
                    "transfer_method": "local_file",
                    "upload_file_id": upload_file_id,
                },
            },
            "response_mode": "blocking",
            "user": "car",
        }
        response = requests.post(
            workflow_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        return response.json()


class FrontDistanceController(Resource):
    def post(self):
        value = FrontDistance.get()
        return jsonify({"distance": value})


if __name__ == "__main__":
    visual_controller = VisualController()
    # Example usage
    result = visual_controller.post("图中有什么")
    print(result)
