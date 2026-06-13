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


class ClassSchedule(models.Model):
    """수업 일정 설정 - 저장 시 ClassSession 자동 일괄 생성"""
    REPEAT_CHOICES = [
        ('weekly_1', '주 1회'),
        ('weekly_2', '주 2회'),
        ('weekly_3', '주 3회'),
        ('custom', '직접 입력'),
    ]
    WEEKDAY_CHOICES = [
        (0, '월요일'), (1, '화요일'), (2, '수요일'),
        (3, '목요일'), (4, '금요일'), (5, '토요일'), (6, '일요일'),
    ]
    gx_class = models.ForeignKey(GxClass, on_delete=models.CASCADE, related_name='schedules', verbose_name='수업')
    start_date = models.DateField('시작일')
    end_date = models.DateField('종료일')
    repeat_type = models.CharField('반복유형', max_length=10, choices=REPEAT_CHOICES, default='weekly_1')
    day_1 = models.IntegerField('요일1', choices=WEEKDAY_CHOICES, null=True, blank=True)
    day_2 = models.IntegerField('요일2', choices=WEEKDAY_CHOICES, null=True, blank=True)
    day_3 = models.IntegerField('요일3', choices=WEEKDAY_CHOICES, null=True, blank=True)
    custom_dates = models.TextField('직접입력 날짜들', blank=True, help_text='쉼표로 구분: 2025-06-03,2025-06-10')
    notice = models.TextField('수강생 공지', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '수업 일정'
        verbose_name_plural = '수업 일정 목록'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.gx_class.name} {self.start_date}~{self.end_date}"

    def generate_sessions(self):
        """일정 설정에 따라 ClassSession 자동 생성"""
        from datetime import timedelta, date as date_type, datetime
        sessions_created = 0
        # start_date/end_date가 문자열이면 date로 변환
        start = self.start_date if hasattr(self.start_date, 'weekday') else datetime.strptime(str(self.start_date), '%Y-%m-%d').date()
        end = self.end_date if hasattr(self.end_date, 'weekday') else datetime.strptime(str(self.end_date), '%Y-%m-%d').date()
        if self.repeat_type == 'custom':
            dates = [d.strip() for d in self.custom_dates.split(',') if d.strip()]
            for d in dates:
                try:
                    dt = datetime.strptime(d, '%Y-%m-%d').date()
                    _, created = ClassSession.objects.get_or_create(
                        gx_class=self.gx_class, date=dt,
                        defaults={'note': f'일정: {self}'}
                    )
                    if created:
                        sessions_created += 1
                except ValueError:
                    pass
        else:
            weekdays = [self.day_1]
            if self.day_2 is not None and self.repeat_type in ('weekly_2', 'weekly_3'):
                weekdays.append(self.day_2)
            if self.day_3 is not None and self.repeat_type == 'weekly_3':
                weekdays.append(self.day_3)
            weekdays = [w for w in weekdays if w is not None]
            current = self.start_date
            while current <= self.end_date:
                if current.weekday() in weekdays:
                    _, created = ClassSession.objects.get_or_create(
                        gx_class=self.gx_class, date=current,
                        defaults={'note': f'일정: {self}'}
                    )
                    if created:
                        sessions_created += 1
                current += timedelta(days=1)
        return sessions_created
