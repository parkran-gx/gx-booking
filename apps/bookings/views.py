from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from apps.classes.models import GxClass, ClassSession
from .models import Booking, Attendance, PrivateLessonRequest
import csv

def book_class(request, class_id):
    # 비로그인 → 회원가입 페이지로
    if not request.user.is_authenticated:
        messages.warning(request, '예약하려면 먼저 회원가입 후 로그인해주세요.')
        return redirect(f'/accounts/register/?next=/bookings/book/{class_id}/')
    gx_class = get_object_or_404(GxClass, id=class_id, is_active=True)
    profile = request.user.profile
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        building = request.POST.get('building', '').strip()
        unit = request.POST.get('unit', '').strip()
        if not all([name, phone, building, unit]):
            messages.error(request, '모든 항목을 입력해주세요.')
            return render(request, 'bookings/book.html', {'gx_class': gx_class, 'profile': profile})
        exists = Booking.objects.filter(
            gx_class=gx_class, phone=phone
        ).exclude(status='cancelled').first()
        if exists:
            messages.error(request, '이미 해당 수업에 예약되어 있습니다.')
            return render(request, 'bookings/book.html', {'gx_class': gx_class, 'profile': profile})
        available = gx_class.available_spots()
        status = 'confirmed' if available > 0 else 'waiting'
        booking = Booking.objects.create(
            gx_class=gx_class, name=name, phone=phone,
            building=building, unit=unit, status=status
        )
        if profile.role == 'unregistered':
            profile.role = 'registered'
            profile.is_approved = True
            profile.save()
        return redirect('bookings:confirm', booking_id=booking.id)
    return render(request, 'bookings/book.html', {
        'gx_class': gx_class,
        'profile': profile,
    })

def booking_confirm(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'bookings/confirm.html', {'booking': booking})

@login_required
def booking_check(request):
    profile = request.user.profile
    bookings = []
    if profile.phone:
        bookings = Booking.objects.filter(
            phone=profile.phone
        ).exclude(status='cancelled').select_related('gx_class')
    return render(request, 'bookings/check.html', {'bookings': bookings})

def cancel_request(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        msg = request.POST.get('message', '').strip()
        booking.cancel_requested = True
        booking.cancel_message = msg
        booking.save()
        messages.success(request, '변경 요청이 접수되었습니다.')
        return redirect('accounts:dashboard')
    return render(request, 'bookings/cancel_request.html', {'booking': booking})

def private_lesson_request(request):
    if request.method == 'POST':
        PrivateLessonRequest.objects.create(
            name=request.POST.get('name', '').strip(),
            phone=request.POST.get('phone', '').strip(),
            building=request.POST.get('building', '').strip(),
            unit=request.POST.get('unit', '').strip(),
            preferred_time=request.POST.get('preferred_time', '').strip(),
            message=request.POST.get('message', '').strip(),
        )
        messages.success(request, '개인 레슨 요청이 접수되었습니다.')
        return redirect('/')
    return render(request, 'bookings/private_lesson.html')

@login_required
def admin_booking_list(request, class_id):
    gx_class = get_object_or_404(GxClass, id=class_id)
    confirmed = Booking.objects.filter(gx_class=gx_class, status='confirmed').order_by('building', 'unit')
    waiting = Booking.objects.filter(gx_class=gx_class, status='waiting').order_by('waiting_order')
    cancel_reqs = Booking.objects.filter(gx_class=gx_class, cancel_requested=True)
    if request.method == 'POST':
        action = request.POST.get('action')
        booking_id = request.POST.get('booking_id')
        b = get_object_or_404(Booking, id=booking_id)
        if action == 'cancel':
            b.status = 'cancelled'
            b.save()
            first_waiting = Booking.objects.filter(
                gx_class=gx_class, status='waiting'
            ).order_by('waiting_order').first()
            if first_waiting:
                first_waiting.status = 'confirmed'
                first_waiting.waiting_order = None
                first_waiting.save()
                messages.success(request, f'{b.name}님 취소 → {first_waiting.name}님 예약확정')
            else:
                messages.success(request, f'{b.name}님 예약이 취소되었습니다.')
        elif action == 'clear_request':
            b.cancel_requested = False
            b.cancel_message = ''
            b.save()
        return redirect('bookings:admin_list', class_id=class_id)
    return render(request, 'bookings/admin_list.html', {
        'gx_class': gx_class,
        'confirmed': confirmed,
        'waiting': waiting,
        'cancel_reqs': cancel_reqs,
    })

@login_required
def admin_attendance(request, session_id):
    session = get_object_or_404(ClassSession, id=session_id)
    bookings = Booking.objects.filter(gx_class=session.gx_class, status='confirmed')
    if request.method == 'POST':
        for b in bookings:
            status = request.POST.get(f'att_{b.id}', 'absent')
            Attendance.objects.update_or_create(
                session=session, booking=b,
                defaults={'status': status}
            )
        messages.success(request, '출석이 저장되었습니다.')
        return redirect('bookings:admin_attendance', session_id=session_id)
    attendance_map = {a.booking_id: a for a in Attendance.objects.filter(session=session)}
    return render(request, 'bookings/admin_attendance.html', {
        'session': session,
        'bookings': bookings,
        'attendance_map': attendance_map,
    })

@login_required
def export_booking_list(request, class_id):
    gx_class = get_object_or_404(GxClass, id=class_id)
    bookings = Booking.objects.filter(gx_class=gx_class, status='confirmed').order_by('building', 'unit')
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="{gx_class.name}_예약명단.csv"'
    writer = csv.writer(response)
    writer.writerow(['번호', '이름', '동', '호수', '연락처', '예약일'])
    for i, b in enumerate(bookings, 1):
        writer.writerow([i, b.name, b.building, b.unit, b.phone, b.created_at.strftime('%Y-%m-%d')])
    return response
