from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .models import EnrollmentPeriod, Enrollment, PriorityMember
from apps.classes.models import GxClass
from apps.accounts.models import UserProfile
import csv

def parse_dt(val):
    """datetime-local 입력값을 aware datetime으로 변환"""
    if not val:
        return None
    from django.utils import timezone
    import datetime
    try:
        dt = datetime.datetime.strptime(val, '%Y-%m-%dT%H:%M')
        return timezone.make_aware(dt)
    except Exception:
        return None

@login_required
def enrollment_list(request):
    profile = request.user.profile
    if profile.complex:
        classes = GxClass.objects.filter(complex=profile.complex, is_active=True)
    else:
        classes = GxClass.objects.none()
    periods = EnrollmentPeriod.objects.filter(
        gx_class__in=classes
    ).select_related('gx_class').order_by('-year', '-month')
    for p in periods:
        p.update_status()
    period_data = []
    for p in periods:
        my_enrollment = None
        is_priority_member = False
        if request.user.is_authenticated:
            my_enrollment = Enrollment.objects.filter(
                period=p, phone=profile.phone
            ).first()
            is_priority_member = PriorityMember.objects.filter(
                period=p, user=request.user
            ).exists()
        can_enroll = False
        if p.is_open_for_general:
            can_enroll = True
        elif p.is_open_for_priority and is_priority_member:
            can_enroll = True
        period_data.append({
            'period': p,
            'my_enrollment': my_enrollment,
            'is_priority_member': is_priority_member,
            'can_enroll': can_enroll and not my_enrollment,
        })
    return render(request, 'enrollments/list.html', {'period_data': period_data})

@login_required
def enroll(request, period_id):
    period = get_object_or_404(EnrollmentPeriod, id=period_id)
    profile = request.user.profile
    is_priority = PriorityMember.objects.filter(period=period, user=request.user).exists()
    if not period.is_open_for_general and not (period.is_open_for_priority and is_priority):
        messages.error(request, '현재 접수 기간이 아닙니다.')
        return redirect('enrollments:list')
    exists = Enrollment.objects.filter(period=period, phone=profile.phone).first()
    if exists:
        messages.error(request, '이미 등록되어 있습니다.')
        return redirect('enrollments:list')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        building = request.POST.get('building', '').strip()
        unit = request.POST.get('unit', '').strip()
        if not all([name, phone, building, unit]):
            messages.error(request, '모든 항목을 입력해주세요.')
            return render(request, 'enrollments/enroll.html', {'period': period, 'profile': profile})
        available = period.available_spots
        status = 'confirmed' if available > 0 else 'waiting'
        enroll_type = 'priority' if is_priority and period.is_open_for_priority else 'general'
        Enrollment.objects.create(
            period=period, user=request.user,
            name=name, phone=phone,
            building=building, unit=unit,
            status=status, enroll_type=enroll_type,
        )
        if profile.role == 'unregistered':
            profile.role = 'registered'
            profile.is_approved = True
            profile.save()
        if status == 'confirmed':
            messages.success(request, f'{period.year}년 {period.month}월 {period.gx_class.name} 등록 완료!')
        else:
            messages.warning(request, '정원이 찼습니다. 대기 등록되었습니다.')
        return redirect('enrollments:list')
    return render(request, 'enrollments/enroll.html', {'period': period, 'profile': profile})

@login_required
def cancel_request(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    if request.method == 'POST':
        enrollment.cancel_requested = True
        enrollment.cancel_message = request.POST.get('message', '').strip()
        enrollment.save()
        messages.success(request, '변경 요청이 접수되었습니다.')
        return redirect('enrollments:list')
    return render(request, 'enrollments/cancel_request.html', {'enrollment': enrollment})

@login_required
def admin_period_list(request):
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    profile = request.user.profile
    if profile.is_super_admin:
        periods = EnrollmentPeriod.objects.all().select_related('gx_class')
    else:
        periods = EnrollmentPeriod.objects.filter(
            gx_class__complex=profile.complex
        ).select_related('gx_class')
    for p in periods:
        p.update_status()
    return render(request, 'enrollments/admin_list.html', {'periods': periods})

@login_required
def admin_period_create(request):
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    profile = request.user.profile
    if profile.is_super_admin:
        classes = GxClass.objects.filter(is_active=True)
    else:
        classes = GxClass.objects.filter(complex=profile.complex, is_active=True)
    if request.method == 'POST':
        gx_class_id = request.POST.get('gx_class')
        year = request.POST.get('year')
        month = request.POST.get('month')
        capacity = request.POST.get('capacity')
        notice = request.POST.get('notice', '').strip()
        try:
            period = EnrollmentPeriod.objects.create(
                gx_class_id=gx_class_id,
                year=int(year), month=int(month),
                capacity=int(capacity),
                priority_start=parse_dt(request.POST.get('priority_start')),
                priority_end=parse_dt(request.POST.get('priority_end')),
                general_start=parse_dt(request.POST.get('general_start')),
                general_end=parse_dt(request.POST.get('general_end')),
                notice=notice,
            )
            period.update_status()
            messages.success(request, f'{year}년 {month}월 등록 기간이 생성되었습니다.')
            return redirect('enrollments:admin_detail', period_id=period.id)
        except Exception as e:
            messages.error(request, f'오류: {e}')
    from datetime import date
    today = date.today()
    return render(request, 'enrollments/admin_form.html', {
        'classes': classes,
        'today': today,
    })

@login_required
def admin_period_edit(request, period_id):
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    period = get_object_or_404(EnrollmentPeriod, id=period_id)
    profile = request.user.profile
    if profile.is_super_admin:
        classes = GxClass.objects.filter(is_active=True)
    else:
        classes = GxClass.objects.filter(complex=profile.complex, is_active=True)
    if request.method == 'POST':
        period.capacity = int(request.POST.get('capacity', period.capacity))
        period.priority_start = parse_dt(request.POST.get('priority_start'))
        period.priority_end = parse_dt(request.POST.get('priority_end'))
        period.general_start = parse_dt(request.POST.get('general_start'))
        period.general_end = parse_dt(request.POST.get('general_end'))
        period.notice = request.POST.get('notice', '').strip()
        period.status = request.POST.get('status', period.status)
        period.save()
        messages.success(request, '등록 기간이 수정되었습니다.')
        return redirect('enrollments:admin_detail', period_id=period.id)
    return render(request, 'enrollments/admin_form.html', {
        'period': period,
        'classes': classes,
    })

@login_required
def admin_period_detail(request, period_id):
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    period = get_object_or_404(EnrollmentPeriod, id=period_id)
    period.update_status()
    confirmed = period.enrollments.filter(status='confirmed').order_by('building', 'unit')
    waiting = period.enrollments.filter(status='waiting').order_by('waiting_order')
    cancelled = period.enrollments.filter(status='cancelled').order_by('-created_at')
    cancel_reqs = period.enrollments.filter(cancel_requested=True)
    priority_members = period.priority_members.select_related('user__profile')
    return render(request, 'enrollments/admin_detail.html', {
        'period': period,
        'confirmed': confirmed,
        'waiting': waiting,
        'cancelled': cancelled,
        'cancel_reqs': cancel_reqs,
        'priority_members': priority_members,
    })

@login_required
def admin_priority_members(request, period_id):
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    period = get_object_or_404(EnrollmentPeriod, id=period_id)
    from django.contrib.auth.models import User
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        if action == 'add' and user_id:
            try:
                user = User.objects.get(id=user_id)
                PriorityMember.objects.get_or_create(
                    period=period, user=user,
                    defaults={'note': request.POST.get('note', '')}
                )
                messages.success(request, f'{user.get_full_name()} 우선접수 대상자 추가')
            except User.DoesNotExist:
                messages.error(request, '회원을 찾을 수 없습니다.')
        elif action == 'remove':
            pm_id = request.POST.get('pm_id')
            PriorityMember.objects.filter(id=pm_id, period=period).delete()
            messages.success(request, '우선접수 대상자에서 제거했습니다.')
        return redirect('enrollments:admin_priority', period_id=period_id)
    members = UserProfile.objects.filter(
        complex=period.gx_class.complex
    ).select_related('user')
    priority_members = period.priority_members.select_related('user')
    priority_ids = list(priority_members.values_list('user_id', flat=True))
    return render(request, 'enrollments/admin_priority.html', {
        'period': period,
        'members': members,
        'priority_members': priority_members,
        'priority_ids': priority_ids,
    })

@login_required
def admin_promote(request, period_id, enrollment_id):
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    enrollment.status = 'confirmed'
    enrollment.waiting_order = None
    enrollment.save()
    messages.success(request, f'{enrollment.name}님 등록 확정')
    return redirect('enrollments:admin_detail', period_id=period_id)

@login_required
def admin_cancel(request, period_id, enrollment_id):
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    period = get_object_or_404(EnrollmentPeriod, id=period_id)
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    enrollment.status = 'cancelled'
    enrollment.save()
    first_waiting = period.enrollments.filter(
        status='waiting'
    ).order_by('waiting_order').first()
    if first_waiting:
        first_waiting.status = 'confirmed'
        first_waiting.waiting_order = None
        first_waiting.save()
        messages.success(request, f'{enrollment.name}님 취소 → {first_waiting.name}님 자동 확정')
    else:
        messages.success(request, f'{enrollment.name}님 등록 취소')
    return redirect('enrollments:admin_detail', period_id=period_id)

@login_required
def admin_manual_enroll(request, period_id):
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    period = get_object_or_404(EnrollmentPeriod, id=period_id)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        building = request.POST.get('building', '').strip()
        unit = request.POST.get('unit', '').strip()
        if not all([name, phone, building, unit]):
            messages.error(request, '모든 항목을 입력해주세요.')
        elif Enrollment.objects.filter(period=period, phone=phone).exists():
            messages.error(request, '이미 등록된 연락처입니다.')
        else:
            available = period.available_spots
            status = 'confirmed' if available > 0 else 'waiting'
            Enrollment.objects.create(
                period=period, name=name, phone=phone,
                building=building, unit=unit,
                status=status, enroll_type='manual',
            )
            messages.success(request, f'{name}님 수동 등록 완료')
        return redirect('enrollments:admin_detail', period_id=period_id)
    return redirect('enrollments:admin_detail', period_id=period_id)

@login_required
def admin_export(request, period_id):
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    period = get_object_or_404(EnrollmentPeriod, id=period_id)
    enrollments = period.enrollments.filter(status='confirmed').order_by('building', 'unit')
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    filename = f"{period.gx_class.name}_{period.year}년{period.month}월_등록명단.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(['번호', '이름', '동', '호수', '연락처', '접수유형', '등록일'])
    for i, e in enumerate(enrollments, 1):
        writer.writerow([
            i, e.name, e.building, e.unit, e.phone,
            e.get_enroll_type_display(),
            e.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    return response

@login_required
def admin_sync_status(request, period_id):
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    period = get_object_or_404(EnrollmentPeriod, id=period_id)
    period.update_status()
    messages.success(request, f'상태 업데이트: {period.get_status_display()}')
    return redirect('enrollments:admin_detail', period_id=period_id)
