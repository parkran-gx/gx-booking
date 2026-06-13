from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import GxClass, ClassSession
from apps.bookings.models import Booking, Attendance
from apps.complexes.models import Complex

def landing(request):
    if request.user.is_authenticated:
        return redirect('classes:list')
    complex_code = request.GET.get('c')
    if complex_code:
        try:
            c = Complex.objects.get(code=complex_code, is_active=True)
            request.session['complex_id'] = c.id
            request.session['complex_name'] = c.name
        except Complex.DoesNotExist:
            pass
    complex_name = request.session.get('complex_name')
    return render(request, 'classes/landing.html', {'complex_name': complex_name})

def class_list(request):
    classes = GxClass.objects.filter(is_active=True)
    complex_name = None
    complex_obj = None
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            if profile.complex:
                classes = classes.filter(complex=profile.complex)
                complex_name = profile.complex.name
                complex_obj = profile.complex
        except Exception:
            pass
    else:
        complex_id = request.session.get('complex_id')
        if complex_id:
            try:
                complex_obj = Complex.objects.get(id=complex_id, is_active=True)
                classes = classes.filter(complex=complex_obj)
                complex_name = complex_obj.name
            except Complex.DoesNotExist:
                pass
    class_data = []
    for c in classes:
        available = c.available_spots()
        class_data.append({
            'obj': c,
            'available': available,
            'is_full': available <= 0,
            'waiting_count': Booking.objects.filter(gx_class=c, status='waiting').count(),
        })
    return render(request, 'classes/list.html', {
        'class_data': class_data,
        'complex_name': complex_name,
    })

@login_required
def admin_dashboard(request):
    profile = request.user.profile
    if profile.is_super_admin:
        classes = GxClass.objects.filter(is_active=True)
    else:
        classes = GxClass.objects.filter(is_active=True, complex=profile.complex)
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
    """월별 캘린더 - 수업일정·휴강·대강·출석"""
    from datetime import date, timedelta
    import calendar as cal
    year = int(request.GET.get('year', date.today().year))
    month = int(request.GET.get('month', date.today().month))
    first_day = date(year, month, 1)
    import calendar
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    profile = request.user.profile
    if profile.is_super_admin:
        sessions = ClassSession.objects.filter(
            date__gte=first_day, date__lte=last_day
        ).select_related('gx_class')
    else:
        sessions = ClassSession.objects.filter(
            date__gte=first_day, date__lte=last_day,
            gx_class__complex=profile.complex
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

@login_required
def session_create(request):
    """수업 회차 생성 (관리자)"""
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('classes:calendar')
    profile = request.user.profile
    if profile.is_super_admin:
        classes = GxClass.objects.filter(is_active=True)
    else:
        classes = GxClass.objects.filter(complex=profile.complex, is_active=True)
    if request.method == 'POST':
        gx_class_id = request.POST.get('gx_class')
        date_val = request.POST.get('date')
        is_cancelled = request.POST.get('is_cancelled') == 'on'
        substitute = request.POST.get('substitute_instructor', '').strip()
        note = request.POST.get('note', '').strip()
        try:
            session, created = ClassSession.objects.get_or_create(
                gx_class_id=gx_class_id,
                date=date_val,
                defaults={
                    'is_cancelled': is_cancelled,
                    'substitute_instructor': substitute,
                    'note': note,
                }
            )
            if not created:
                session.is_cancelled = is_cancelled
                session.substitute_instructor = substitute
                session.note = note
                session.save()
            messages.success(request, '수업 회차가 등록되었습니다.')
        except Exception as e:
            messages.error(request, f'오류: {e}')
        return redirect('classes:calendar')
    return render(request, 'classes/session_form.html', {'classes': classes})

@login_required
def attendance_view(request, session_id):
    """출석 체크 페이지"""
    session = get_object_or_404(ClassSession, id=session_id)
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('classes:calendar')
    from apps.enrollments.models import Enrollment, EnrollmentPeriod
    bookings = Booking.objects.filter(
        gx_class=session.gx_class, status='confirmed'
    ).order_by('building', 'unit')
    if request.method == 'POST':
        for b in bookings:
            status = request.POST.get(f'att_{b.id}', 'absent')
            Attendance.objects.update_or_create(
                session=session, booking=b,
                defaults={'status': status}
            )
        messages.success(request, '출석이 저장되었습니다.')
        return redirect('classes:attendance', session_id=session_id)
    attendance_map = {a.booking_id: a for a in Attendance.objects.filter(session=session)}
    return render(request, 'classes/attendance.html', {
        'session': session,
        'bookings': bookings,
        'attendance_map': attendance_map,
    })

@login_required
def my_attendance(request):
    """내 출석 현황"""
    profile = request.user.profile
    from apps.bookings.models import Attendance
    attendances = Attendance.objects.filter(
        booking__phone=profile.phone
    ).select_related('session__gx_class', 'booking').order_by('-session__date')
    return render(request, 'classes/my_attendance.html', {
        'attendances': attendances,
    })

@login_required
def qr_generate(request):
    import qrcode
    from django.http import HttpResponse
    from io import BytesIO
    complex_id = request.GET.get('complex_id')
    try:
        if request.user.profile.is_super_admin:
            complex_obj = Complex.objects.get(id=complex_id)
        else:
            complex_obj = request.user.profile.complex
    except (Complex.DoesNotExist, TypeError):
        complex_obj = request.user.profile.complex
    if not complex_obj:
        messages.error(request, '단지 정보가 없습니다.')
        return redirect('accounts:dashboard')
    base_url = request.build_absolute_uri('/')
    url = f"{base_url}?c={complex_obj.code}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#6366f1', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="{complex_obj.name}_QR.png"'
    return response

@login_required
def qr_view(request):
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('accounts:dashboard')
    if request.user.profile.is_super_admin:
        complexes = Complex.objects.filter(is_active=True)
    else:
        complexes = Complex.objects.filter(id=request.user.profile.complex_id)
    return render(request, 'classes/qr_view.html', {'complexes': complexes})
