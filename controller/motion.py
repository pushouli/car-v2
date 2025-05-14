import time
from flask import request
from flask_restful import Resource
from flasgger import swag_from
import service.motion as motion


class MotionController(Resource):
    @swag_from(
        {
            "tags": ["Motion"],
            "parameters": [
                {
                    "name": "body",
                    "in": "body",
                    "required": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "left": {
                                "type": "number",
                                "minimum": -400,
                                "maximum": 400,
                                "description": "左电机速度，每秒钟行走的毫米数，范围 [-400, 400]",
                            },
                            "right": {
                                "type": "number",
                                "minimum": -400,
                                "maximum": 400,
                                "description": "右电机速度，每秒钟行走的毫米数，范围 [-400, 400]",
                            },
                            "duration": {
                                "type": "number",
                                "minimum": -10,
                                "maximum": 10,
                                "description": "持续时间，单位秒，范围 [-10, 10]",
                            },
                        },
                        "required": ["left", "right"],
                    },
                }
            ],
            "responses": {
                200: {
                    "description": "运动控制成功",
                    "schema": {
                        "type": "object",
                        "properties": {"message": {"type": "string"}},
                    },
                }
            },
        }
    )
    def post(self):
        """控制电机行走"""
        left: int = request.json.get("left")
        right: int = request.json.get("right")
        duration: float = request.json.get("duration", 0)

        motion.walk(left, right)
        if duration:
            time.sleep(duration)
            motion.walk(0, 0)
        return {"message": "Motion detection started"}, 200
