from django.db import models

class GxClass(models.Model):
    DAYS_CHOICES = [
        ('MON', '월요일'),
        ('THU', '목요일'),
        ('MON_THU', '월/목'),
    ]
    complex = models.ForeignKey(
        'complexes.Complex',
        on_delete=models.CASCADE,
        related_name='classes',
        verbose_name='단지',
        null=True, blank=True
    )
    name = models.CharField('수업명', max_length=50)
    description = models.TextField('설명', blank=True)
    days = models.CharField('수업 요일', max_length=10, choices=DAYS_CHOICES)
    start_time = models.TimeField('시작 시간')
    end_time = models.TimeField('종료 시간')
    capacity = models.PositiveIntegerField('정원', default=10)
    monthly_fee = models.PositiveIntegerField('월 수강료')
    is_active = models.BooleanField('운영 중', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '수업'
        verbose_name_plural = '수업 목록'
        ordering = ['start_time']

    def __str__(self):
        complex_name = self.complex.name if self.complex else '전체'
        return f"[{complex_name}] {self.name} ({self.get_days_display()} {self.start_time.strftime('%H:%M')})"

    @property
    def per_session_fee(self):
        sessions = 8 if self.days == 'MON_THU' else 4
        return self.monthly_fee // sessions

    @property
    def sessions_per_week(self):
        return 2 if self.days == 'MON_THU' else 1

    def available_spots(self):
        from apps.bookings.models import Booking
        confirmed = Booking.objects.filter(gx_class=self, status='confirmed').count()
        return self.capacity - confirmed


class ClassSession(models.Model):
    gx_class = models.ForeignKey(GxClass, on_delete=models.CASCADE, related_name='sessions')
    date = models.DateField('수업 날짜')
    is_cancelled = models.BooleanField('휴강', default=False)
    substitute_instructor = models.CharField('대강 강사', max_length=50, blank=True)
    note = models.TextField('메모', blank=True)

    class Meta:
        verbose_name = '수업 회차'
        verbose_name_plural = '수업 회차 목록'
        ordering = ['-date']
        unique_together = ['gx_class', 'date']

    def __str__(self):
        return f"{self.gx_class} - {self.date}"
