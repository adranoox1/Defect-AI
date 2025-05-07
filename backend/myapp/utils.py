from .models import ActivityLog

def log_activity(request, action, object_id=None, object_name=None, details=None):
    ActivityLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        object_id=object_id,
        object_name=object_name,
        details=details,
        ip_address=request.META.get('REMOTE_ADDR')
    ) 