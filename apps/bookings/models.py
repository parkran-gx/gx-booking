from django.db import models
from apps.classes.models import GxClass, ClassSession

class Booking(models.Model):
    STATUS_CHOICES = [
        ('confirmed', '예약확정'),
        ('waiting', '대기중'),
        ('cancelled', '취소'),
    ]
    gx_class = models.ForeignKey(GxClass, on_delete=models.CASCADE, related_name='bookings', verbose_name='수업')
    name = models.CharField('이름', max_length=20)
    phone = models.CharField('연락처', max_length=15)
    building = models.CharField('동', max_length=10)
    unit = models.CharField('호수', max_length=10)
    status = models.CharField('예약상태', max_length=15, choices=STATUS_CHOICES, default='confirmed')
    waiting_order = models.PositiveIntegerField('대기순번', null=True, blank=True)
    cancel_requested = models.BooleanField('변경요청', default=False)
    cancel_message = models.TextField('변경요청내용', blank=True)
    created_at = models.DateTimeField('예약일시', auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '예약'
        verbose_name_plural = '예약 목록'
        ordering = ['gx_class', 'created_at']

    def __str__(self):
        return f"{self.gx_class.name} - {self.name} ({self.building}동 {self.unit}호)"

    def save(self, *args, **kwargs):
        if self.status == 'waiting' and not self.waiting_order:
            last = Booking.objects.filter(
                gx_class=self.gx_class, status='waiting'
            ).order_by('-waiting_order').first()
            self.waiting_order = (last.waiting_order + 1) if last else 1
        super().save(*args, **kwargs)


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', '출석'),
        ('absent', '결석'),
        ('makeup', '보강'),
    ]
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name='attendances')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='attendances')
    status = models.CharField('출석상태', max_length=10, choices=STATUS_CHOICES, default='present')
    note = models.CharField('메모', max_length=100, blank=True)

    class Meta:
        verbose_name = '출석'
        verbose_name_plural = '출석 목록'
        unique_together = ['session', 'booking']

    def __str__(self):
        return f"{self.session} - {self.booking.name} ({self.get_status_display()})"


class PrivateLessonRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', '검토중'),
        ('confirmed', '확정'),
        ('rejected', '거절'),
    ]
    name = models.CharField('이름', max_length=20)
    phone = models.CharField('연락처', max_length=15)
    building = models.CharField('동', max_length=10)
    unit = models.CharField('호수', max_length=10)
    preferred_time = models.TextField('희망시간대')
    message = models.TextField('요청내용')
    status = models.CharField('처리상태', max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '개인레슨요청'
        verbose_name_plural = '개인레슨요청 목록'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.building}동 {self.unit}호) - {self.get_status_display()}"
