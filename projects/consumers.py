import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications
    Each user gets their own notification channel
    """
    
    # async def connect(self):
    #     """Called when WebSocket connection is established"""
    #     self.user = self.scope['user']
        
    #     if self.user.is_anonymous:
    #         # Reject anonymous users
    #         await self.close()
    #     else:
    #         # Create unique channel name for this user
    #         self.room_group_name = f'notifications_{self.user.id}'
            
    #         # Join room group
    #         await self.channel_layer.group_add(
    #             self.room_group_name,
    #             self.channel_name
    #         )
            
    #         await self.accept()
            
    #         # Send connection success message
    #         await self.send(text_data=json.dumps({
    #             'type': 'connection_established',
    #             'message': 'Connected to notifications'
    #         }))

    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": "Connected (anonymous test)"
        }))
    # The above is for testing(test_websocket.html) purposes only. Replace with the commented code for production.
    
    async def disconnect(self, close_code):
        """Called when WebSocket connection is closed"""
        if hasattr(self, 'room_group_name'):
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Called when we receive a message from WebSocket"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'ping':
            # Respond to ping to keep connection alive
            await self.send(text_data=json.dumps({
                'type': 'pong'
            }))
    
    async def notification_message(self, event):
        """Send notification to WebSocket"""
        await self.send(text_data=json.dumps(event['data']))


class TaskConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for task updates
    Multiple users can watch the same task
    """
    
    async def connect(self):
        """Connect to task channel"""
        self.user = self.scope['user']
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.room_group_name = f'task_{self.task_id}'
        
        if self.user.is_anonymous:
            await self.close()
        else:
            # Join task room
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Notify others that user joined
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_joined',
                    'user_id': self.user.id,
                    'user_email': self.user.email,
                }
            )
    
    async def disconnect(self, close_code):
        """Disconnect from task channel"""
        if hasattr(self, 'room_group_name'):
            # Notify others that user left
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user_id': self.user.id,
                    'user_email': self.user.email,
                }
            )
            
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'typing':
            # Broadcast typing indicator
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': self.user.id,
                    'user_email': self.user.email,
                }
            )
    
    async def task_updated(self, event):
        """Send task update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'task_updated',
            'data': event['data']
        }))
    
    async def comment_added(self, event):
        """Send new comment notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'comment_added',
            'data': event['data']
        }))
    
    async def status_changed(self, event):
        """Send status change to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'status_changed',
            'data': event['data']
        }))
    
    async def user_joined(self, event):
        """Notify that a user joined"""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'user_email': event['user_email'],
        }))
    
    async def user_left(self, event):
        """Notify that a user left"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'user_email': event['user_email'],
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator"""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'user_email': event['user_email'],
        }))


class FeedConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for live feed updates
    Users see real-time activity from their organization
    """
    
    async def connect(self):
        """Connect to organization feed"""
        self.user = self.scope['user']
        
        if self.user.is_anonymous:
            await self.close()
        else:
            # Get user's organizations
            org_ids = await self.get_user_organizations()
            
            # Join all organization feed rooms
            self.room_groups = []
            for org_id in org_ids:
                room_name = f'feed_org_{org_id}'
                self.room_groups.append(room_name)
                await self.channel_layer.group_add(
                    room_name,
                    self.channel_name
                )
            
            await self.accept()
            
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to live feed',
                'organizations': org_ids
            }))
    
    async def disconnect(self, close_code):
        """Disconnect from feed"""
        if hasattr(self, 'room_groups'):
            for room_group in self.room_groups:
                await self.channel_layer.group_discard(
                    room_group,
                    self.channel_name
                )
    
    async def receive(self, text_data):
        """Handle incoming messages"""
        data = json.loads(text_data)
        
        if data.get('type') == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))
    
    async def feed_update(self, event):
        """Send feed update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'feed_update',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_user_organizations(self):
        """Get list of organization IDs user belongs to"""
        from organizations.models import Membership
        return list(
            Membership.objects.filter(user=self.user)
            .values_list('organization_id', flat=True)
        )