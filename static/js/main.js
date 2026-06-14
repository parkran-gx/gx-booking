// GX 예약 시스템 메인 스크립트
document.addEventListener('DOMContentLoaded', function() {
    // 자동 알림 닫기 (3초)
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert.alert-dismissible');
        alerts.forEach(function(alert) {
            var btn = alert.querySelector('.btn-close');
            if (btn) btn.click();
        });
    }, 3000);
});
