from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api, init
from .config import load_env_config
from .static import static


def create_app() -> FastAPI:
  """Create and configure the FastAPI application instance."""
  app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
  )
  config = load_env_config()
  init(api, config)
  if config.api_only:
    app.mount(config.url_prefix, api)
    app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_methods=["*"],
      allow_headers=["*"],
    )
  else:
    app.mount(f"{config.url_prefix}/api", api)
    app.mount(config.url_prefix, static)
  return app
