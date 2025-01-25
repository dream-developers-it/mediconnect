from mediconnect_api.models import Notification, DoctorProfile

def notifications(request):
    context = {
        'unread_notifications_count': 0,
        'notifications': []
    }
    
    if request.user.is_authenticated:
        context['unread_notifications_count'] = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        # Get latest notifications for the modal
        context['notifications'] = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')[:10]  # Get last 10 notifications
    
    return context
