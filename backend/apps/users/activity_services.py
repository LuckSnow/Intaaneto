from django.db import IntegrityError
from django.db.models import F
from django.utils import timezone

from .models import DailyActivity


def record_daily_activity(*, user, count_login=False):
    """Record server-observed authenticated activity for the local day."""
    activity_date = timezone.localdate()
    try:
        activity, created = DailyActivity.objects.get_or_create(
            user=user,
            activity_date=activity_date,
            defaults={'login_count': 1},
        )
    except IntegrityError:
        activity = DailyActivity.objects.get(
            user=user,
            activity_date=activity_date,
        )
        created = False

    if not created:
        updates = {'last_seen_at': timezone.now()}
        if count_login:
            updates['login_count'] = F('login_count') + 1
        DailyActivity.objects.filter(pk=activity.pk).update(**updates)

    return activity
