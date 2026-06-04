from flask import Flask
from flask_cors import CORS

from . import app as owe_app
from .config import load_env_config


def create_app(
  *,
  url_prefix: str | None = None,
  api_only: bool = False,
) -> Flask:
  """Create and configure the Flask application instance."""
  app = Flask(__name__, static_folder=None)
  app.config.update(load_env_config())
  owe_app.init(app)
  bp = owe_app.api if api_only else owe_app.app
  app.register_blueprint(bp, url_prefix=url_prefix)
  CORS(app)
  return app
