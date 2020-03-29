from channels.routing import route

from django.conf.urls import url

from pokerboard.consumers import ws_connect , ws_message, ws_disconnect

channel_routing = [
    route('websocket.connect', ws_connect , path=r"^/new/(?P<name>\w+)/(?P<token>\w+)"),
    route('websocket.disconnect', ws_disconnect , path=r"^/new/(?P<name>\w+)/(?P<token>\w+)"),
    route("websocket.receive", ws_message, path=r"^/new/(?P<name>\w+)/(?P<token>\w+)"),
]
