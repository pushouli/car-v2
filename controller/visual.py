import base64
import io
import cv2
from flask import request, jsonify
from flask_restful import Resource
import requests

from service.base.camera import Camera
from service.front_distance import FrontDistance


# GET 返回图片时缩到这个宽度。图片按 token 计费，1920 原图又贵又慢，
# 768 已经足够看清桌面尺度的东西。高度按原比例算。
# 只作用于 GET；POST 走 Dify 那条仍按原样上传原图。
CAPTURE_WIDTH = 768

# JPEG 质量。95（cv2 默认）在这个尺寸上纯属浪费带宽。
JPEG_QUALITY = 80


class VisualController(Resource):
    """/api/visual —— 两个入口，按请求方法分流。

    POST { prompt }   拍照 → 上传 Dify → 跑视觉工作流 → 返回文字分析。
                      当年语音模型看不见图，只能让另一个模型看完转述给它。
                      行为原样保留。

    GET               只拍照，返回 { image: base64 JPEG }。Realtime 支持原生
                      图像输入之后，前端把图直接插进对话让模型自己看：省掉一趟
                      Dify 往返、不因转述丢细节，模型还能带着完整上下文就同一
                      张图追问。Realtime 控制台走这条。

    新入口用 GET 而不是再开一个 POST：它没有请求体、没有参数，语义就是
    "取当前这一帧"。启摄像头是实现细节，不构成资源变更。
    """

    def __init__(self):
        self.api_key = "app-gq5HHNvC3vtnzrNDbR2QBGs2"

    def get(self):
        try:
            response = jsonify({"image": self.capture_base64_jpeg()})
        except Exception as e:
            # 会一路交回给模型读出来，所以要是句人话。
            return jsonify({"error": f"拍照失败：{e}"}), 500

        # GET 会被浏览器和中间代理缓存，那就会拿到一张旧照片。
        response.headers["Cache-Control"] = "no-store"
        return response

    def capture_base64_jpeg(self):
        camera = Camera()
        try:
            frame = camera.capture_frame()
        finally:
            # Picamera2 是独占的：不释放会让手势、信号灯那些检测再也起不来，
            # 所以拍失败了也得关。
            camera.stop()

        height, width = frame.shape[:2]
        if width > CAPTURE_WIDTH:
            new_height = round(height * CAPTURE_WIDTH / width)
            # 缩小用 INTER_AREA，比默认的双线性干净。
            frame = cv2.resize(
                frame, (CAPTURE_WIDTH, new_height), interpolation=cv2.INTER_AREA
            )

        # Camera 配的是 picamera2 的 "RGB888"，在 numpy 里实际是 BGR 排列，
        # 正好是 cv2 要的顺序，不用转。
        ok, buffer = cv2.imencode(
            ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
        )
        if not ok:
            raise RuntimeError("JPEG 编码失败")

        return base64.b64encode(buffer.tobytes()).decode("ascii")

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
