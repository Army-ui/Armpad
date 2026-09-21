from .models import Notification, Message


def notifications(request):
    if not request.user.is_authenticated:
        return {
            'unread_notifications_count': 0,
            'recent_notifications': [],
            'unread_messages_count': 0,
        }

    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    recent = Notification.objects.filter(user=request.user).select_related('sender')[:10]
    unread_msgs = Message.objects.filter(
        receiver=request.user, is_read=False
    ).values('sender').distinct().count()

    return {
        'unread_notifications_count': unread_count,
        'recent_notifications': recent,
        'unread_messages_count': unread_msgs,
    }