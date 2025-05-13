from flask import request, jsonify
import traceback
import time
from service.hand_distance import HandDistance
from service.hand_gesture import HandGesture
import service.motion as motion
import service.headlight as headlight
from flask_restful import Resource

hand_gesture = HandGesture()
hand_distance = HandDistance()


class ExecuteResource(Resource):
    def post(self):
        code = request.json.get("code")
        if not code:
            return jsonify({"error": "No code provided"}), 400

        hand_gesture.stop()
        hand_distance.stop()
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
                "time": time,
                "motion": motion,
                "hand_gesture": hand_gesture,
                "hand_distance": hand_distance,
                "headlight": headlight,
            }
            local_vars = {}
            exec(code, allowed_globals, local_vars)
            result["error"] = None
            result["result"] = local_vars.get("result", None)
        except Exception:
            result["error"] = traceback.format_exc()

        return jsonify(result)
