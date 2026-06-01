import logging

from flask import Flask
from flask_cors import CORS

from iou.app import blueprint, init
from iou.config import LOG_LEVEL

logging.basicConfig(
  format="%(asctime)s %(levelname)s %(name)s: %(message)s",
  level=getattr(logging, LOG_LEVEL, logging.INFO),
)

init()
app = Flask(__name__)
app.register_blueprint(blueprint)
CORS(app)
