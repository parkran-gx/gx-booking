from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notice
from apps.classes.models import GxClass

@login_required
def notice_list(request):
    profile = request.user.profile
    if profile.is_super_admin:
        notice_list = Notice.objects.all().select_related('gx_class', 'author')
    elif profile.is_registered:
        from apps.bookings.models import Booking
        my_classes = Booking.objects.filter(
            phone=profile.phone, status='confirmed'
        ).values_list('gx_class_id', flat=True)
        notice_list = Notice.objects.filter(
            gx_class_id__in=my_classes
        ).select_related('gx_class', 'author') | Notice.objects.filter(
            is_global=True
        ).select_related('gx_class', 'author')
    else:
        notice_list = Notice.objects.filter(is_global=True)
    return render(request, 'notices/list.html', {'notices': notice_list.distinct()})

@login_required
def notice_detail(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    return render(request, 'notices/detail.html', {'notice': notice})

@login_required
def notice_create(request):
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('notices:list')
    classes = GxClass.objects.filter(is_active=True)
    if request.method == 'POST':
        Notice.objects.create(
            title=request.POST.get('title', '').strip(),
            content=request.POST.get('content', '').strip(),
            gx_class_id=request.POST.get('gx_class') or None,
            is_pinned=request.POST.get('is_pinned') == 'on',
            is_global=request.POST.get('is_global') == 'on',
            author=request.user,
        )
        messages.success(request, '공지가 등록되었습니다.')
        return redirect('notices:list')
    return render(request, 'notices/form.html', {'classes': classes})

@login_required
def notice_edit(request, pk):
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('notices:list')
    notice = get_object_or_404(Notice, pk=pk)
    classes = GxClass.objects.filter(is_active=True)
    if request.method == 'POST':
        notice.title = request.POST.get('title', '').strip()
        notice.content = request.POST.get('content', '').strip()
        notice.gx_class_id = request.POST.get('gx_class') or None
        notice.is_pinned = request.POST.get('is_pinned') == 'on'
        notice.is_global = request.POST.get('is_global') == 'on'
        notice.save()
        messages.success(request, '공지가 수정되었습니다.')
        return redirect('notices:detail', pk=pk)
    return render(request, 'notices/form.html', {'notice': notice, 'classes': classes})

@login_required
def notice_delete(request, pk):
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('notices:list')
    notice = get_object_or_404(Notice, pk=pk)
    if request.method == 'POST':
        notice.delete()
        messages.success(request, '공지가 삭제되었습니다.')
        return redirect('notices:list')
    return render(request, 'notices/confirm_delete.html', {'notice': notice})
