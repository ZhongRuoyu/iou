from flask import Flask
from flask_cors import CORS

from iou.app import blueprint, init


def create_app() -> Flask:
  init()
  app = Flask(__name__)
  app.register_blueprint(blueprint)
  CORS(app)
  return app
