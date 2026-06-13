from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Complex

@login_required
def complex_list(request):
    if not request.user.profile.is_super_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('accounts:dashboard')
    complexes = Complex.objects.all()
    return render(request, 'complexes/list.html', {'complexes': complexes})

@login_required
def complex_create(request):
    if not request.user.profile.is_super_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('accounts:dashboard')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        address = request.POST.get('address', '').strip()
        if not name:
            messages.error(request, '단지명을 입력해주세요.')
            return render(request, 'complexes/form.html')
        code = Complex.generate_code()
        Complex.objects.create(name=name, code=code, address=address)
        messages.success(request, f'{name} 단지가 등록되었습니다.')
        return redirect('complexes:list')
    return render(request, 'complexes/form.html')

@login_required
def complex_edit(request, pk):
    if not request.user.profile.is_super_admin:
        messages.error(request, '권한이 없습니다.')
        return redirect('accounts:dashboard')
    complex_obj = get_object_or_404(Complex, pk=pk)
    if request.method == 'POST':
        complex_obj.name = request.POST.get('name', '').strip()
        complex_obj.address = request.POST.get('address', '').strip()
        complex_obj.is_active = request.POST.get('is_active') == 'on'
        complex_obj.save()
        messages.success(request, '단지 정보가 수정되었습니다.')
        return redirect('complexes:list')
    return render(request, 'complexes/form.html', {'complex': complex_obj})
