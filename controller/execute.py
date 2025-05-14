from flask import request, jsonify
import traceback
import time
from service.hand_distance import HandDistance
from service.hand_gesture import HandGesture
from service.traffic_light import TrafficLight
from service.front_distance import FrontDistance

import service.motion as motion
import service.headlight as headlight
from flask_restful import Resource

hand_gesture = HandGesture()
hand_distance = HandDistance()
traffic_light = TrafficLight()
front_distance = FrontDistance()

def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name in ("time",):
        return __import__(name, globals, locals, fromlist, level)
    raise ImportError(f"Module '{name}' is not allowed.")

class ExecuteController(Resource):
    def post(self):
        code = request.json.get("code")
        if not code:
            return jsonify({"error": "No code provided"}), 400

        hand_gesture.stop()
        hand_distance.stop()
        traffic_light.stop()
        front_distance.stop()

        print("Executing code:", code)
        result = {}
        try:
            # Allow access to time.sleep and motion.walk
            allowed_globals = {
                "__builtins__": {
                    "print": print,
                    "range": range,
                    "len": len,
                    "int": int,
                    "float": float,
                    "str": str,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "set": set,
                    "tuple": tuple,
                    "enumerate": enumerate,
                    "zip": zip,
                    "min": min,
                    "max": max,
                    "abs": abs,
                    "sum": sum,
                },
                "__import__": restricted_import,
                "time": time,
                "motion": motion,
                "headlight": headlight,
                "hand_gesture": hand_gesture,
                "hand_distance": hand_distance,
                "traffic_light": traffic_light,
                "front_distance": front_distance,
            }
            local_vars = {}
            exec(code, allowed_globals, local_vars)
            result["error"] = None
            result["result"] = local_vars.get("result", None)
        except Exception:
            result["error"] = traceback.format_exc()

        return jsonify(result)
