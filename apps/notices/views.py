from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notice
from apps.classes.models import GxClass

@login_required
def notice_list(request):
    profile = request.user.profile
    class_id = request.GET.get('class_id')
    from apps.bookings.models import Booking

    # 내가 예약한 수업 목록
    if profile.is_super_admin:
        my_classes = GxClass.objects.filter(is_active=True)
    else:
        my_class_ids = Booking.objects.filter(
            phone=profile.phone, status='confirmed'
        ).values_list('gx_class_id', flat=True)
        my_classes = GxClass.objects.filter(id__in=my_class_ids, is_active=True)

    # 전체 공지
    global_notices = Notice.objects.filter(is_global=True).select_related('author')

    # 선택된 클래스 공지
    selected_class = None
    class_notices = Notice.objects.none()
    if class_id:
        selected_class = get_object_or_404(GxClass, id=class_id)
        class_notices = Notice.objects.filter(
            gx_class_id=class_id
        ).select_related('author')
    elif my_classes.exists():
        selected_class = my_classes.first()
        class_notices = Notice.objects.filter(
            gx_class=selected_class
        ).select_related('author')

    return render(request, 'notices/list.html', {
        'my_classes': my_classes,
        'selected_class': selected_class,
        'global_notices': global_notices,
        'class_notices': class_notices,
    })

@login_required
def notice_detail(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    can_edit = (
        request.user.profile.is_complex_admin or
        notice.author == request.user
    )
    return render(request, 'notices/detail.html', {
        'notice': notice,
        'can_edit': can_edit,
    })

@login_required
def notice_create(request):
    profile = request.user.profile
    class_id = request.GET.get('class_id')
    from apps.bookings.models import Booking

    # 관리자 또는 해당 클래스 등록 회원만 작성 가능
    if profile.is_complex_admin:
        classes = GxClass.objects.filter(is_active=True)
    else:
        my_class_ids = Booking.objects.filter(
            phone=profile.phone, status='confirmed'
        ).values_list('gx_class_id', flat=True)
        classes = GxClass.objects.filter(id__in=my_class_ids, is_active=True)
        if not classes.exists():
            messages.error(request, '수강 등록된 수업이 없습니다.')
            return redirect('notices:list')

    if request.method == 'POST':
        gx_class_id = request.POST.get('gx_class') or None
        is_global = request.POST.get('is_global') == 'on' and profile.is_complex_admin
        Notice.objects.create(
            title=request.POST.get('title', '').strip(),
            content=request.POST.get('content', '').strip(),
            gx_class_id=gx_class_id,
            is_pinned=request.POST.get('is_pinned') == 'on' and profile.is_complex_admin,
            is_global=is_global,
            author=request.user,
        )
        messages.success(request, '게시물이 등록되었습니다.')
        if gx_class_id:
            return redirect(f'/notices/?class_id={gx_class_id}')
        return redirect('notices:list')

    return render(request, 'notices/form.html', {
        'classes': classes,
        'default_class_id': class_id,
        'is_admin': profile.is_complex_admin,
    })

@login_required
def notice_edit(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    profile = request.user.profile
    if not (profile.is_complex_admin or notice.author == request.user):
        messages.error(request, '수정 권한이 없습니다.')
        return redirect('notices:detail', pk=pk)
    classes = GxClass.objects.filter(is_active=True)
    if request.method == 'POST':
        notice.title = request.POST.get('title', '').strip()
        notice.content = request.POST.get('content', '').strip()
        notice.gx_class_id = request.POST.get('gx_class') or None
        if profile.is_complex_admin:
            notice.is_pinned = request.POST.get('is_pinned') == 'on'
            notice.is_global = request.POST.get('is_global') == 'on'
        notice.save()
        messages.success(request, '게시물이 수정되었습니다.')
        return redirect('notices:detail', pk=pk)
    return render(request, 'notices/form.html', {
        'notice': notice,
        'classes': classes,
        'is_admin': profile.is_complex_admin,
    })

@login_required
def notice_delete(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    profile = request.user.profile
    if not (profile.is_complex_admin or notice.author == request.user):
        messages.error(request, '삭제 권한이 없습니다.')
        return redirect('notices:detail', pk=pk)
    if request.method == 'POST':
        class_id = notice.gx_class_id
        notice.delete()
        messages.success(request, '게시물이 삭제되었습니다.')
        if class_id:
            return redirect(f'/notices/?class_id={class_id}')
        return redirect('notices:list')
    return render(request, 'notices/confirm_delete.html', {'notice': notice})
