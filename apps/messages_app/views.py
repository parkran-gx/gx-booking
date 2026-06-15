from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Message
from apps.classes.models import GxClass

def send_message(request):
    classes = GxClass.objects.filter(is_active=True)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if not content:
            messages.error(request, '내용을 입력해주세요.')
            return render(request, 'messages_app/send.html', {'classes': classes})
        if request.user.is_authenticated:
            profile = request.user.profile
            msg_type = 'registered' if profile.is_registered else 'member'
            Message.objects.create(
                sender=request.user,
                sender_name=request.user.profile.display_name,
                sender_phone=profile.phone,
                gx_class_id=request.POST.get('gx_class') or None,
                message_type=msg_type,
                content=content,
            )
        else:
            sender_name = request.POST.get('sender_name', '').strip()
            sender_phone = request.POST.get('sender_phone', '').strip()
            if not all([sender_name, sender_phone]):
                messages.error(request, '이름과 연락처를 입력해주세요.')
                return render(request, 'messages_app/send.html', {'classes': classes})
            Message.objects.create(
                sender_name=sender_name,
                sender_phone=sender_phone,
                gx_class_id=request.POST.get('gx_class') or None,
                message_type='guest',
                content=content,
            )
        messages.success(request, '쪽지가 전송되었습니다. 확인 후 답변드리겠습니다.')
        return redirect('/')
    return render(request, 'messages_app/send.html', {'classes': classes})

@login_required
def inbox(request):
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    msg_list = Message.objects.all().select_related('sender', 'gx_class')
    unread = msg_list.filter(is_read=False).count()
    return render(request, 'messages_app/inbox.html', {
        'msg_list': msg_list,
        'unread': unread,
    })

@login_required
def message_detail(request, pk):
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    msg = get_object_or_404(Message, pk=pk)
    msg.is_read = True
    msg.save()
    return render(request, 'messages_app/detail.html', {'msg': msg})

@login_required
def message_reply(request, pk):
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    msg = get_object_or_404(Message, pk=pk)
    if request.method == 'POST':
        msg.reply = request.POST.get('reply', '').strip()
        msg.replied_at = timezone.now()
        msg.save()
        messages.success(request, '답변이 저장되었습니다.')
        return redirect('messages_app:detail', pk=pk)
    return redirect('messages_app:detail', pk=pk)


@login_required
def sent_box(request):
    """관리자 보낸 쪽지함"""
    if not request.user.profile.is_complex_admin:
        return redirect('/')
    sent = Message.objects.filter(
        sender_name__startswith='[강사]'
    ).order_by('-created_at')
    return render(request, 'messages_app/sent_box.html', {'sent': sent})


@login_required
def admin_send(request):
    """관리자가 회원에게 쪽지 보내기"""
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    from apps.accounts.models import UserProfile
    from apps.classes.models import GxClass
    members = UserProfile.objects.filter(
        is_approved=True
    ).select_related('user', 'complex').order_by('complex__name', 'building', 'unit')
    classes = GxClass.objects.filter(is_active=True)

    if request.method == 'POST':
        target_user_id = request.POST.get('target_user')
        content = request.POST.get('content', '').strip()
        gx_class_id = request.POST.get('gx_class') or None
        if content:
            from django.contrib.auth.models import User as DjangoUser
            target = DjangoUser.objects.filter(id=target_user_id).first()
            if target:
                Message.objects.create(
                    sender_name=f'[강사] {request.user.first_name or request.user.username}',
                    sender_phone='',
                    message_type='registered',
                    content=content,
                    gx_class_id=gx_class_id,
                    is_read=False,
                )
            messages.success(request, '쪽지를 보냈습니다.')
        return redirect('messages_app:admin_send')

    return render(request, 'messages_app/admin_send.html', {
        'members': members,
        'classes': classes,
    })
