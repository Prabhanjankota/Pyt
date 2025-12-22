from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Clear all Redis cache'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pattern',
            type=str,
            help='Clear cache keys matching pattern',
        )

    def handle(self, *args, **options):
        pattern = options.get('pattern')
        
        if pattern:
            # Clear specific pattern
            from django_redis import get_redis_connection
            con = get_redis_connection("default")
            keys = con.keys(f"*{pattern}*")
            if keys:
                con.delete(*keys)
                self.stdout.write(
                    self.style.SUCCESS(f'Cleared {len(keys)} cache keys matching "{pattern}"')
                )
            else:
                self.stdout.write(self.style.WARNING(f'No cache keys found matching "{pattern}"'))
        else:
            # Clear all cache
            cache.clear()
            self.stdout.write(self.style.SUCCESS('Successfully cleared all cache'))