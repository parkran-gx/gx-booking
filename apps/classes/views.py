from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import GxClass, ClassSession, ClassSchedule
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
    # 활성 일정 목록
    if profile.is_super_admin:
        schedules = ClassSchedule.objects.all().select_related('gx_class')
    else:
        schedules = ClassSchedule.objects.filter(
            gx_class__complex=profile.complex
        ).select_related('gx_class')
    return render(request, 'classes/calendar.html', {
        'year': year, 'month': month,
        'weeks': weeks, 'session_map': session_map,
        'prev': prev_month, 'next': next_month,
        'today': date.today(),
        'schedules': schedules,
    })

@login_required
def schedule_create(request):
    """수업 일정 생성 - 자동으로 ClassSession 일괄 생성"""
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('classes:calendar')
    profile = request.user.profile
    if profile.is_super_admin:
        classes = GxClass.objects.filter(is_active=True)
    else:
        classes = GxClass.objects.filter(complex=profile.complex, is_active=True)
    # 서식 불러오기: 이전 일정 목록
    templates = ClassSchedule.objects.filter(
        gx_class__in=classes
    ).order_by('-created_at')[:10]
    # 서식 선택 시 해당 일정 데이터 불러오기
    template_id = request.GET.get('template')
    template_obj = None
    if template_id:
        try:
            template_obj = ClassSchedule.objects.get(id=template_id)
        except ClassSchedule.DoesNotExist:
            pass
    if request.method == 'POST':
        class_input_type = request.POST.get('class_input_type', 'select')
        gx_class_id = request.POST.get('gx_class')
        # 직접 입력 시 새 수업 생성
        if class_input_type == 'manual':
            class_name_manual = request.POST.get('class_name_manual', '').strip()
            if class_name_manual and profile.complex:
                from apps.classes.models import GxClass
                new_class = GxClass.objects.create(
                    name=class_name_manual,
                    complex=profile.complex,
                    days='MON',
                    start_time='09:00',
                    end_time='10:00',
                    capacity=10,
                    monthly_fee=0,
                )
                gx_class_id = new_class.id
                messages.info(request, f'새 수업 [{class_name_manual}]이 생성되었습니다. 수업 설정에서 세부 정보를 수정해주세요.')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        repeat_type = request.POST.get('repeat_type', 'weekly_1')
        day_1 = request.POST.get('day_1')
        day_2 = request.POST.get('day_2')
        day_3 = request.POST.get('day_3')
        custom_dates = request.POST.get('custom_dates', '')
        notice = request.POST.get('notice', '').strip()
        try:
            schedule = ClassSchedule.objects.create(
                gx_class_id=gx_class_id,
                start_date=start_date,
                end_date=end_date,
                repeat_type=repeat_type,
                day_1=int(day_1) if day_1 else None,
                day_2=int(day_2) if day_2 else None,
                day_3=int(day_3) if day_3 else None,
                custom_dates=custom_dates,
                notice=notice,
            )
            count = schedule.generate_sessions()
            messages.success(request, f'일정이 등록되었습니다. 수업 {count}회 자동 생성됨.')
            return redirect('classes:calendar')
        except Exception as e:
            messages.error(request, f'오류: {e}')
    return render(request, 'classes/schedule_form.html', {
        'classes': classes,
        'templates': templates,
        'template_obj': template_obj,
        'weekdays': ClassSchedule.WEEKDAY_CHOICES,
    })

@login_required
def schedule_edit(request, schedule_id):
    """일정 수정"""
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('classes:calendar')
    schedule = get_object_or_404(ClassSchedule, id=schedule_id)
    profile = request.user.profile
    if profile.is_super_admin:
        classes = GxClass.objects.filter(is_active=True)
    else:
        classes = GxClass.objects.filter(complex=profile.complex, is_active=True)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'regenerate':
            # 기존 세션 삭제 후 재생성
            ClassSession.objects.filter(
                gx_class=schedule.gx_class,
                date__gte=schedule.start_date,
                date__lte=schedule.end_date,
            ).delete()
            schedule.start_date = request.POST.get('start_date')
            schedule.end_date = request.POST.get('end_date')
            schedule.repeat_type = request.POST.get('repeat_type')
            day_1 = request.POST.get('day_1')
            day_2 = request.POST.get('day_2')
            day_3 = request.POST.get('day_3')
            schedule.day_1 = int(day_1) if day_1 else None
            schedule.day_2 = int(day_2) if day_2 else None
            schedule.day_3 = int(day_3) if day_3 else None
            schedule.custom_dates = request.POST.get('custom_dates', '')
            schedule.notice = request.POST.get('notice', '').strip()
            schedule.save()
            count = schedule.generate_sessions()
            messages.success(request, f'일정 재생성 완료. 수업 {count}회 생성됨.')
        elif action == 'delete':
            ClassSession.objects.filter(
                gx_class=schedule.gx_class,
                date__gte=schedule.start_date,
                date__lte=schedule.end_date,
            ).delete()
            schedule.delete()
            messages.success(request, '일정이 삭제되었습니다.')
            return redirect('classes:calendar')
        return redirect('classes:calendar')
    return render(request, 'classes/schedule_form.html', {
        'schedule': schedule,
        'classes': classes,
        'weekdays': ClassSchedule.WEEKDAY_CHOICES,
    })

@login_required
def session_edit(request, session_id):
    """개별 수업 회차 수동 변경"""
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('classes:calendar')
    session = get_object_or_404(ClassSession, id=session_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update':
            session.date = request.POST.get('date', session.date)
            session.is_cancelled = request.POST.get('is_cancelled') == 'on'
            session.substitute_instructor = request.POST.get('substitute_instructor', '').strip()
            session.note = request.POST.get('note', '').strip()
            session.save()
            messages.success(request, '수업 회차가 수정되었습니다.')
        elif action == 'delete':
            session.delete()
            messages.success(request, '수업 회차가 삭제되었습니다.')
            return redirect('classes:calendar')
        return redirect('classes:calendar')
    return render(request, 'classes/session_edit.html', {'session': session})

@login_required
def attendance_view(request, session_id):
    session = get_object_or_404(ClassSession, id=session_id)
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('classes:calendar')
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
    profile = request.user.profile
    attendances = Attendance.objects.filter(
        booking__phone=profile.phone
    ).select_related('session__gx_class', 'booking').order_by('-session__date')
    # 진행 중인 일정에서 기간 내 이용 안내
    from datetime import date
    today = date.today()
    active_schedules = ClassSchedule.objects.filter(
        gx_class__complex=profile.complex,
        end_date__gte=today
    ).select_related('gx_class') if profile.complex else []
    return render(request, 'classes/my_attendance.html', {
        'attendances': attendances,
        'active_schedules': active_schedules,
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
