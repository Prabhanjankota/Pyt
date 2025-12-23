from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
    path('ws/tasks/<int:task_id>/', consumers.TaskConsumer.as_asgi()),
    path('ws/feed/', consumers.FeedConsumer.as_asgi()),
]