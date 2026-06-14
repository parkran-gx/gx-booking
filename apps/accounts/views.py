from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from apps.complexes.models import Complex
from .models import UserProfile

def register(request):
    complexes = Complex.objects.filter(is_active=True)
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        building = request.POST.get('building', '').strip()
        unit = request.POST.get('unit', '').strip()
        complex_id = request.POST.get('complex_id', '')
        email = request.POST.get('email', '').strip()
        if not all([username, password1, name, phone, building, unit, complex_id]):
            messages.error(request, '모든 항목을 입력해주세요.')
            return render(request, 'accounts/register.html', {'complexes': complexes})
        if password1 != password2:
            messages.error(request, '비밀번호가 일치하지 않습니다.')
            return render(request, 'accounts/register.html', {'complexes': complexes})
        if len(password1) < 8:
            messages.error(request, '비밀번호는 8자 이상이어야 합니다.')
            return render(request, 'accounts/register.html', {'complexes': complexes})
        if User.objects.filter(username=username).exists():
            messages.error(request, '이미 사용 중인 아이디입니다.')
            return render(request, 'accounts/register.html', {'complexes': complexes})
        try:
            complex_obj = Complex.objects.get(id=complex_id)
        except Complex.DoesNotExist:
            messages.error(request, '올바른 단지를 선택해주세요.')
            return render(request, 'accounts/register.html', {'complexes': complexes})
        user = User.objects.create_user(
            username=username, password=password1,
            email=email, first_name=name
        )
        profile = user.profile
        profile.complex = complex_obj
        profile.phone = phone
        profile.building = building
        profile.unit = unit
        profile.role = 'unregistered'
        profile.save()
        login(request, user)
        messages.success(request, f'{name}님 가입을 환영합니다! 수업 예약 후 등록회원이 됩니다.')
        return redirect('classes:list')
    return render(request, 'accounts/register.html', {'complexes': complexes})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', '/dashboard/')
            return redirect(next_url)
        messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
    return render(request, 'accounts/login.html')

def user_logout(request):
    logout(request)
    return redirect('/')

@login_required
def dashboard(request):
    profile = request.user.profile
    from apps.bookings.models import Booking
    my_bookings = Booking.objects.filter(
        phone=profile.phone
    ).exclude(status='cancelled').select_related('gx_class') if profile.phone else []
    return render(request, 'accounts/dashboard.html', {
        'profile': profile,
        'my_bookings': my_bookings,
    })

@login_required
def profile_edit(request):
    profile = request.user.profile
    if request.method == 'POST':
        request.user.first_name = request.POST.get('name', '').strip()
        request.user.email = request.POST.get('email', '').strip()
        request.user.save()
        profile.phone = request.POST.get('phone', '').strip()
        profile.building = request.POST.get('building', '').strip()
        profile.unit = request.POST.get('unit', '').strip()
        profile.save()
        messages.success(request, '정보가 수정되었습니다.')
        return redirect('accounts:dashboard')
    return render(request, 'accounts/profile_edit.html', {'profile': profile})

@login_required
def password_change(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, '비밀번호가 변경되었습니다.')
            return redirect('accounts:dashboard')
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/password_change.html', {'form': form})

def password_reset_request(request):
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        username = request.POST.get('username', '').strip()
        try:
            profile = UserProfile.objects.get(phone=phone, user__username=username)
            request.session['reset_user_id'] = profile.user.id
            return redirect('accounts:password_reset_confirm')
        except UserProfile.DoesNotExist:
            messages.error(request, '아이디 또는 연락처가 일치하지 않습니다.')
    return render(request, 'accounts/password_reset.html')

def password_reset_confirm(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('accounts:password_reset')
    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        if password1 != password2:
            messages.error(request, '비밀번호가 일치하지 않습니다.')
        elif len(password1) < 8:
            messages.error(request, '비밀번호는 8자 이상이어야 합니다.')
        else:
            user = User.objects.get(id=user_id)
            user.set_password(password1)
            user.save()
            del request.session['reset_user_id']
            messages.success(request, '비밀번호가 재설정되었습니다. 다시 로그인해주세요.')
            return redirect('accounts:login')
    return render(request, 'accounts/password_reset_confirm.html')


@login_required
def member_manage(request):
    """회원 목록 및 승인 관리"""
    if not request.user.profile.is_complex_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('/')
    profile = request.user.profile
    from apps.accounts.models import UserProfile
    if profile.is_super_admin:
        members = UserProfile.objects.all().select_related('user', 'complex').order_by('-created_at')
    else:
        members = UserProfile.objects.filter(
            complex=profile.complex
        ).select_related('user', 'complex').order_by('-created_at')

    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        action = request.POST.get('action')
        try:
            member = UserProfile.objects.get(id=member_id)
            if action == 'approve':
                member.is_approved = True
                member.role = 'registered'
                member.save()
                messages.success(request, f'{member.display_name}님을 승인했습니다.')
            elif action == 'reject':
                member.is_approved = False
                member.role = 'unregistered'
                member.save()
                messages.success(request, f'{member.display_name}님을 미승인 처리했습니다.')
            elif action == 'set_admin':
                member.role = 'complex_admin'
                member.is_approved = True
                member.save()
                messages.success(request, f'{member.display_name}님을 단지관리자로 변경했습니다.')
            elif action == 'set_super':
                member.role = 'super_admin'
                member.is_approved = True
                member.save()
                messages.success(request, f'{member.display_name}님을 슈퍼관리자로 변경했습니다.')
            elif action == 'delete':
                name = member.display_name
                member.user.delete()
                messages.success(request, f'{name}님 계정을 삭제했습니다.')
        except UserProfile.DoesNotExist:
            messages.error(request, '회원을 찾을 수 없습니다.')
        return redirect('accounts:member_manage')

    return render(request, 'accounts/member_manage.html', {'members': members})
