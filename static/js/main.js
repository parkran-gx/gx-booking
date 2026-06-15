document.addEventListener('DOMContentLoaded', function() {

  // 1. 알림 메시지 3초 후 자동 닫기
  setTimeout(function() {
    document.querySelectorAll('.alert.alert-dismissible').forEach(function(el) {
      var btn = el.querySelector('.btn-close');
      if (btn) btn.click();
    });
  }, 3000);

  // 2. 폼 제출 시 버튼 로딩 상태
  document.querySelectorAll('form').forEach(function(form) {
    form.addEventListener('submit', function() {
      var btn = form.querySelector('button[type="submit"]');
      if (btn && !btn.dataset.noloading) {
        var orig = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i>처리 중...';
        btn.disabled = true;
        setTimeout(function() {
          btn.innerHTML = orig;
          btn.disabled = false;
        }, 8000);
      }
    });
  });

  // 3. 모바일 하단 탭 현재 페이지 활성화
  var path = window.location.pathname;
  document.querySelectorAll('.gx-bottom-nav a').forEach(function(a) {
    var href = a.getAttribute('href');
    if (href && path.startsWith(href) && href !== '/') {
      a.classList.add('active');
      a.style.color = 'var(--rose)';
    }
  });

  // 4. 입력 필드 포커스 시 라벨 강조
  document.querySelectorAll('.form-control, .form-select').forEach(function(el) {
    el.addEventListener('focus', function() {
      var label = this.closest('.mb-3, .mb-4, .col-6')?.querySelector('label');
      if (label) label.style.color = 'var(--rose)';
    });
    el.addEventListener('blur', function() {
      var label = this.closest('.mb-3, .mb-4, .col-6')?.querySelector('label');
      if (label) label.style.color = '';
    });
  });

  // 5. 카드 클릭 시 부드러운 피드백
  document.querySelectorAll('.gx-card a, a.gx-card').forEach(function(el) {
    el.addEventListener('click', function() {
      this.style.opacity = '0.7';
    });
  });

});
