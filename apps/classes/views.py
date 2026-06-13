from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import GxClass, ClassSession
from apps.bookings.models import Booking

def class_list(request):
    classes = GxClass.objects.filter(is_active=True)
    class_data = []
    for c in classes:
        available = c.available_spots()
        class_data.append({
            'obj': c,
            'available': available,
            'is_full': available <= 0,
            'waiting_count': Booking.objects.filter(gx_class=c, status='waiting').count(),
        })
    return render(request, 'classes/list.html', {'class_data': class_data})

@login_required
def admin_dashboard(request):
    classes = GxClass.objects.filter(is_active=True)
    dashboard = []
    for c in classes:
        confirmed = Booking.objects.filter(gx_class=c, status='confirmed').count()
        waiting = Booking.objects.filter(gx_class=c, status='waiting').count()
        cancel_req = Booking.objects.filter(gx_class=c, cancel_requested=True).count()
        dashboard.append({
            'obj': c,
            'confirmed': confirmed,
            'waiting': waiting,
            'cancel_req': cancel_req,
            'available': c.capacity - confirmed,
        })
    from apps.bookings.models import PrivateLessonRequest
    pending_lessons = PrivateLessonRequest.objects.filter(status='pending').count()
    return render(request, 'classes/admin_dashboard.html', {
        'dashboard': dashboard,
        'pending_lessons': pending_lessons,
    })

@login_required
def calendar_view(request):
    from datetime import date, timedelta
    import calendar as cal
    year = int(request.GET.get('year', date.today().year))
    month = int(request.GET.get('month', date.today().month))
    first_day = date(year, month, 1)
    import calendar
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    sessions = ClassSession.objects.filter(
        date__gte=first_day, date__lte=last_day
    ).select_related('gx_class')
    session_map = {}
    for s in sessions:
        session_map.setdefault(s.date.day, []).append(s)
    weeks = cal.monthcalendar(year, month)
    prev_month = first_day - timedelta(days=1)
    next_month = last_day + timedelta(days=1)
    return render(request, 'classes/calendar.html', {
        'year': year, 'month': month,
        'weeks': weeks, 'session_map': session_map,
        'prev': prev_month, 'next': next_month,
        'today': date.today(),
    })
