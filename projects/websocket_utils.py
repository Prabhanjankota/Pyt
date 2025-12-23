from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def send_notification_to_user(user_id, notification_type, data):
    """
    Send real-time notification to a specific user
    
    Args:
        user_id: ID of the user to notify
        notification_type: Type of notification (task_assigned, comment_added, etc.)
        data: Notification data (dict)
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'notifications_{user_id}',
        {
            'type': 'notification_message',
            'data': {
                'notification_type': notification_type,
                'data': data,
            }
        }
    )


def broadcast_task_update(task_id, update_type, data):
    """
    Broadcast task update to all users watching the task
    
    Args:
        task_id: ID of the task
        update_type: Type of update (status_changed, comment_added, etc.)
        data: Update data (dict)
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'task_{task_id}',
        {
            'type': update_type,
            'data': data,
        }
    )


def broadcast_feed_update(organization_id, activity_data):
    """
    Broadcast new activity to organization feed
    
    Args:
        organization_id: ID of the organization
        activity_data: Activity data (dict)
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'feed_org_{organization_id}',
        {
            'type': 'feed_update',
            'data': activity_data,
        }
    )