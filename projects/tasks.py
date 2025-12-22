from celery import shared_task
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import Task, ActivityLog, Feed

User = get_user_model()


@shared_task(bind=True, max_retries=3)
def send_task_assignment_email(self, task_id, assignee_id):
    """
    Send email notification when a task is assigned
    
    Args:
        task_id: ID of the assigned task
        assignee_id: ID of the user assigned to the task
    """
    try:
        task = Task.objects.select_related('project', 'assignee', 'reporter').get(id=task_id)
        assignee = User.objects.get(id=assignee_id)
        
        subject = f'New Task Assigned: {task.title}'
        message = f"""
        Hi {assignee.get_full_name()},
        
        You have been assigned a new task:
        
        Task: {task.title}
        Project: {task.project.name}
        Priority: {task.priority}
        Due Date: {task.due_date or 'Not set'}
        Description: {task.description}
        
        Assigned by: {task.reporter.get_full_name() if task.reporter else 'System'}
        
        Please log in to view more details.
        
        Best regards,
        Project Management Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email='noreply@projectmanagement.com',
            recipient_list=[assignee.email],
            fail_silently=False,
        )
        
        print(f"✅ Email sent to {assignee.email} for task: {task.title}")
        return f"Email sent successfully to {assignee.email}"
        
    except Task.DoesNotExist:
        print(f"❌ Task {task_id} not found")
        return f"Task {task_id} not found"
    except User.DoesNotExist:
        print(f"❌ User {assignee_id} not found")
        return f"User {assignee_id} not found"
    except Exception as exc:
        print(f"❌ Error sending email: {exc}")
        # Retry after 60 seconds
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_comment_notification(self, comment_id, mentioned_user_ids):
    """
    Send email notifications to mentioned users in comments
    
    Args:
        comment_id: ID of the comment
        mentioned_user_ids: List of user IDs mentioned in the comment
    """
    try:
        from .models import Comment
        comment = Comment.objects.select_related('task', 'author').get(id=comment_id)
        mentioned_users = User.objects.filter(id__in=mentioned_user_ids)
        
        for user in mentioned_users:
            subject = f'You were mentioned in a comment'
            message = f"""
            Hi {user.get_full_name()},
            
            {comment.author.get_full_name()} mentioned you in a comment on task "{comment.task.title}":
            
            "{comment.content}"
            
            Click here to view the task and respond.
            
            Best regards,
            Project Management Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email='noreply@projectmanagement.com',
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            print(f"✅ Mention notification sent to {user.email}")
        
        return f"Notifications sent to {len(mentioned_users)} users"
        
    except Exception as exc:
        print(f"❌ Error sending mention notifications: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def send_weekly_summary():
    """
    Send weekly summary email to all active users
    Runs every Monday at 9 AM
    """
    print("📧 Starting weekly summary email job...")
    
    # Get date range (last 7 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)
    
    # Get all active users
    users = User.objects.filter(is_active=True)
    
    for user in users:
        # Get user's tasks
        tasks_created = Task.objects.filter(
            reporter=user,
            created_at__gte=start_date
        ).count()
        
        tasks_completed = Task.objects.filter(
            assignee=user,
            status='DONE',
            updated_at__gte=start_date
        ).count()
        
        tasks_pending = Task.objects.filter(
            assignee=user,
            status__in=['TODO', 'IN_PROGRESS']
        ).count()
        
        # Get user's activities
        activities = ActivityLog.objects.filter(
            actor=user,
            created_at__gte=start_date
        ).count()
        
        subject = f'Weekly Summary - {start_date.strftime("%B %d")} to {end_date.strftime("%B %d")}'
        message = f"""
        Hi {user.get_full_name()},
        
        Here's your weekly summary:
        
        📊 Your Activity This Week:
        - Tasks Created: {tasks_created}
        - Tasks Completed: {tasks_completed}
        - Total Activities: {activities}
        
        📋 Current Status:
        - Pending Tasks: {tasks_pending}
        
        Keep up the great work!
        
        Best regards,
        Project Management Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email='noreply@projectmanagement.com',
            recipient_list=[user.email],
            fail_silently=True,
        )
        
        print(f"✅ Weekly summary sent to {user.email}")
    
    print(f"📧 Weekly summary sent to {users.count()} users")
    return f"Weekly summary sent to {users.count()} users"


@shared_task
def cleanup_old_activities():
    """
    Clean up activity logs older than 90 days
    Runs daily at 2 AM
    """
    print("🧹 Starting cleanup of old activity logs...")
    
    cutoff_date = timezone.now() - timedelta(days=90)
    
    # Delete old activity logs
    deleted_count = ActivityLog.objects.filter(
        created_at__lt=cutoff_date
    ).delete()[0]
    
    # Delete old feed items
    deleted_feed = Feed.objects.filter(
        created_at__lt=cutoff_date
    ).delete()[0]
    
    print(f"🧹 Cleaned up {deleted_count} activity logs and {deleted_feed} feed items")
    return f"Cleaned up {deleted_count} activity logs and {deleted_feed} feed items"


@shared_task(bind=True, max_retries=3)
def send_due_date_reminders(self):
    """
    Send reminder emails for tasks due in the next 24 hours
    """
    try:
        print("⏰ Checking for tasks with upcoming due dates...")
        
        tomorrow = timezone.now() + timedelta(days=1)
        today = timezone.now()
        
        # Get tasks due tomorrow
        upcoming_tasks = Task.objects.filter(
            due_date__date=tomorrow.date(),
            status__in=['TODO', 'IN_PROGRESS']
        ).select_related('assignee', 'project')
        
        for task in upcoming_tasks:
            if task.assignee:
                subject = f'Reminder: Task "{task.title}" is due tomorrow'
                message = f"""
                Hi {task.assignee.get_full_name()},
                
                This is a reminder that your task is due tomorrow:
                
                Task: {task.title}
                Project: {task.project.name}
                Due Date: {task.due_date}
                Priority: {task.priority}
                Status: {task.status}
                
                Please make sure to complete it on time.
                
                Best regards,
                Project Management Team
                """
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email='noreply@projectmanagement.com',
                    recipient_list=[task.assignee.email],
                    fail_silently=False,
                )
                
                print(f"✅ Due date reminder sent to {task.assignee.email} for task: {task.title}")
        
        print(f"⏰ Sent {upcoming_tasks.count()} due date reminders")
        return f"Sent {upcoming_tasks.count()} due date reminders"
        
    except Exception as exc:
        print(f"❌ Error sending due date reminders: {exc}")
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes