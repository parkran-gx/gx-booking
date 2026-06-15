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
    attendances = Attendance.objects.filter(session=session)
    attendance_presents = set(a.booking_id for a in attendances if a.status == 'present')
    attendance_absents = set(a.booking_id for a in attendances if a.status == 'absent')
    attendance_makeups = set(a.booking_id for a in attendances if a.status == 'makeup')
    return render(request, 'classes/attendance.html', {
        'session': session,
        'bookings': bookings,
        'attendance_presents': attendance_presents,
        'attendance_absents': attendance_absents,
        'attendance_makeups': attendance_makeups,
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


@login_required
def class_manage(request):
    """수업 목록 관리 (슈퍼관리자)"""
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    profile = request.user.profile
    if profile.is_super_admin:
        classes = GxClass.objects.all().select_related('complex')
    else:
        classes = GxClass.objects.filter(complex=profile.complex)
    return render(request, 'classes/manage.html', {'classes': classes})


@login_required
def class_create(request):
    """수업 생성"""
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    profile = request.user.profile
    from apps.complexes.models import Complex
    if profile.is_super_admin:
        complexes = Complex.objects.filter(is_active=True)
    else:
        complexes = Complex.objects.filter(id=profile.complex_id)
    if request.method == 'POST':
        try:
            GxClass.objects.create(
                name=request.POST.get('name', '').strip(),
                complex_id=request.POST.get('complex_id') or profile.complex_id,
                days=request.POST.get('days', 'MON'),
                start_time=request.POST.get('start_time', '09:00'),
                end_time=request.POST.get('end_time', '10:00'),
                capacity=int(request.POST.get('capacity', 10)),
                monthly_fee=int(request.POST.get('monthly_fee', 0)),
                description=request.POST.get('description', '').strip(),
                is_active=request.POST.get('is_active') == 'on',
            )
            messages.success(request, '수업이 생성되었습니다.')
            return redirect('classes:manage')
        except Exception as e:
            messages.error(request, f'오류: {e}')
    return render(request, 'classes/class_form.html', {'complexes': complexes})


@login_required
def class_edit(request, class_id):
    """수업 수정"""
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    gx_class = get_object_or_404(GxClass, id=class_id)
    profile = request.user.profile
    from apps.complexes.models import Complex
    if profile.is_super_admin:
        complexes = Complex.objects.filter(is_active=True)
    else:
        complexes = Complex.objects.filter(id=profile.complex_id)
    if request.method == 'POST':
        gx_class.name = request.POST.get('name', '').strip()
        gx_class.complex_id = request.POST.get('complex_id') or profile.complex_id
        gx_class.days = request.POST.get('days', 'MON')
        gx_class.start_time = request.POST.get('start_time', '09:00')
        gx_class.end_time = request.POST.get('end_time', '10:00')
        gx_class.capacity = int(request.POST.get('capacity', 10))
        gx_class.monthly_fee = int(request.POST.get('monthly_fee', 0))
        gx_class.description = request.POST.get('description', '').strip()
        gx_class.is_active = request.POST.get('is_active') == 'on'
        gx_class.save()
        messages.success(request, '수업이 수정되었습니다.')
        return redirect('classes:manage')
    return render(request, 'classes/class_form.html', {
        'gx_class': gx_class,
        'complexes': complexes,
    })


@login_required
def attendance_pdf(request, session_id):
    """출석부 PDF 출력"""
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from django.http import HttpResponse
    from io import BytesIO
    import datetime

    session = get_object_or_404(ClassSession, id=session_id)
    bookings = Booking.objects.filter(
        gx_class=session.gx_class, status='confirmed'
    ).order_by('building', 'unit')
    attendance_map = {
        a.booking_id: a for a in
        Attendance.objects.filter(session=session)
    }

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('title', fontSize=16, spaceAfter=4,
        alignment=1, fontName='Helvetica-Bold')
    sub_style = ParagraphStyle('sub', fontSize=9, spaceAfter=10,
        alignment=1, fontName='Helvetica')

    story = []
    story.append(Paragraph(f"{session.gx_class.name} 출석부", title_style))
    status_text = '휴강' if session.is_cancelled else (
        f"대강: {session.substitute_instructor}" if session.substitute_instructor else '정상수업'
    )
    story.append(Paragraph(
        f"날짜: {session.date} | 수업: {session.gx_class.get_days_display()} "
        f"{session.gx_class.start_time.strftime('%H:%M')}~{session.gx_class.end_time.strftime('%H:%M')} | "
        f"상태: {status_text} | 출력일: {datetime.date.today()}",
        sub_style
    ))
    story.append(Spacer(1, 5*mm))

    # 출석 통계
    present = sum(1 for b in bookings if attendance_map.get(b.id) and attendance_map[b.id].status == 'present')
    absent = sum(1 for b in bookings if attendance_map.get(b.id) and attendance_map[b.id].status == 'absent')
    makeup = sum(1 for b in bookings if attendance_map.get(b.id) and attendance_map[b.id].status == 'makeup')
    not_checked = bookings.count() - present - absent - makeup

    stat_data = [['출석', '결석', '보강', '미체크', '전체']]
    stat_data.append([str(present), str(absent), str(makeup), str(not_checked), str(bookings.count())])
    stat_table = Table(stat_data, colWidths=[30*mm]*5)
    stat_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#6366f1')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWHEIGHT', (0,0), (-1,-1), 8*mm),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,1), (0,1), colors.HexColor('#d1fae5')),
        ('BACKGROUND', (1,1), (1,1), colors.HexColor('#fee2e2')),
        ('BACKGROUND', (2,1), (2,1), colors.HexColor('#fef3c7')),
    ]))
    story.append(stat_table)
    story.append(Spacer(1, 5*mm))

    # 출석 명단 테이블
    headers = ['번호', '이름', '동/호수', '연락처', '출석', '서명']
    col_widths = [12*mm, 22*mm, 20*mm, 32*mm, 18*mm, 35*mm]
    data = [headers]
    status_labels = {'present': '출석', 'absent': '결석', 'makeup': '보강', None: ''}

    for i, b in enumerate(bookings, 1):
        att = attendance_map.get(b.id)
        att_status = att.status if att else None
        att_label = status_labels.get(att_status, '')
        data.append([
            str(i), b.name,
            f"{b.building}동 {b.unit}호",
            b.phone, att_label, ''
        ])

    table = Table(data, colWidths=col_widths)
    row_count = len(data)
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#6366f1')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dee2e6')),
        ('ROWHEIGHT', (0,0), (-1,-1), 9*mm),
    ])
    # 출석 상태별 색상
    for i, b in enumerate(bookings, 1):
        att = attendance_map.get(b.id)
        if att:
            if att.status == 'present':
                style.add('BACKGROUND', (4,i), (4,i), colors.HexColor('#d1fae5'))
            elif att.status == 'absent':
                style.add('BACKGROUND', (4,i), (4,i), colors.HexColor('#fee2e2'))
            elif att.status == 'makeup':
                style.add('BACKGROUND', (4,i), (4,i), colors.HexColor('#fef3c7'))
    table.setStyle(style)
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    filename = f"{session.gx_class.name}_{session.date}_출석부.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def admin_manual(request):
    """관리자 매뉴얼 페이지"""
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    return render(request, 'classes/admin_manual.html')
