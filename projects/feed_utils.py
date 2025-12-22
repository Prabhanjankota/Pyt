from .models import Feed
from django.core.cache import cache


def create_feed_item(actor, activity_type, title, description='', 
                     task=None, project=None, comment=None, organization=None, metadata=None):
    """
    Helper function to create feed items and invalidate related caches
    """
    if not organization:
        if task:
            organization = task.project.organization
        elif project:
            organization = project.organization
    
    if not organization:
        raise ValueError("Organization is required for feed items")
    
    feed_item = Feed.objects.create(
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
    
    # Invalidate related caches
    invalidate_feed_caches(actor, organization, project)
    
    return feed_item


def invalidate_feed_caches(actor, organization, project=None):
    """
    Invalidate all related feed caches when new activity is created
    """
    # Invalidate actor's feed cache
    cache.delete(f'feed_queryset_user_{actor.id}')
    cache.delete(f'my_feed_user_{actor.id}')
    
    # Invalidate organization members' caches
    from organizations.models import Membership
    member_ids = Membership.objects.filter(
        organization=organization
    ).values_list('user_id', flat=True)
    
    for user_id in member_ids:
        cache.delete(f'feed_queryset_user_{user_id}')
        cache.delete(f'feed_list_user_{user_id}_page_1')
        cache.delete(f'org_feed_{organization.id}_user_{user_id}')
    
    # Invalidate project feed cache if project is provided
    if project:
        for user_id in member_ids:
            cache.delete(f'project_feed_{project.id}_user_{user_id}')