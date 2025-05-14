from flask import Flask, Response
from flask_restful import Api
from flasgger import Swagger
from controller.motion import MotionController
from controller.execute import ExecuteController
from controller.visual import VisualController

from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 开启所有路由的跨域支持
api = Api(app)


@app.route("/")
def home():
    return "Hello, Flask!"


api.add_resource(MotionController, "/api/motion")
api.add_resource(ExecuteController, "/api/exec", endpoint="exec")
api.add_resource(VisualController, "/api/visual", endpoint="visual")
swagger = Swagger(app)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
