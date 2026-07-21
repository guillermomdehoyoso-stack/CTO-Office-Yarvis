"""ASGI convenience adapter; application composition belongs to bootstrap."""

from yarvis_api.bootstrap import create_app

app = create_app()
