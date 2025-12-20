from .models import Feed


def create_feed_item(actor, activity_type, title, description='', 
                     task=None, project=None, comment=None, organization=None, metadata=None):
    """
    Helper function to create feed items
    
    Args:
        actor: User who performed the action
        activity_type: Type of activity (TASK_CREATED, etc.)
        title: Short title for the feed item
        description: Detailed description
        task: Related task (optional)
        project: Related project (optional)
        comment: Related comment (optional)
        organization: Organization for scoping
        metadata: Additional data (dict)
    """
    if not organization:
        # Try to get organization from task or project
        if task:
            organization = task.project.organization
        elif project:
            organization = project.organization
    
    if not organization:
        raise ValueError("Organization is required for feed items")
    
    return Feed.objects.create(
        actor=actor,
        activity_type=activity_type,
        title=title,
        description=description,
        task=task,
        project=project,
        comment=comment,
        organization=organization,
        metadata=metadata or {}
    )