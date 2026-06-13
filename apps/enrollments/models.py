from django.db import models
from django.contrib.auth.models import User
from apps.classes.models import GxClass

class EnrollmentPeriod(models.Model):
    STATUS_CHOICES = [
        ('preparing', '준비중'),
        ('priority', '우선접수중'),
        ('general', '일반접수중'),
        ('closed', '마감'),
        ('done', '종료'),
    ]
    gx_class = models.ForeignKey(GxClass, on_delete=models.CASCADE, related_name='enrollment_periods', verbose_name='수업')
    year = models.IntegerField('연도')
    month = models.IntegerField('월')
    status = models.CharField('상태', max_length=15, choices=STATUS_CHOICES, default='preparing')
    capacity = models.PositiveIntegerField('정원')
    priority_start = models.DateTimeField('우선접수 시작', null=True, blank=True)
    priority_end = models.DateTimeField('우선접수 종료', null=True, blank=True)
    general_start = models.DateTimeField('일반접수 시작', null=True, blank=True)
    general_end = models.DateTimeField('일반접수 종료', null=True, blank=True)
    notice = models.TextField('공지 메시지', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '등록 기간'
        verbose_name_plural = '등록 기간 목록'
        ordering = ['-year', '-month', 'gx_class']
        unique_together = ['gx_class', 'year', 'month']

    def __str__(self):
        return f"{self.gx_class.name} {self.year}년 {self.month}월 ({self.get_status_display()})"

    def update_status(self):
        from django.utils import timezone
        now = timezone.now()
        # None 체크 후 비교
        if self.priority_start and self.priority_end and self.general_start and self.general_end:
            if now < self.priority_start:
                new_status = 'preparing'
            elif self.priority_start <= now <= self.priority_end:
                new_status = 'priority'
            elif self.general_start <= now <= self.general_end:
                new_status = 'general'
            elif now > self.general_end:
                if self.enrollments.filter(status='confirmed').count() >= self.capacity:
                    new_status = 'closed'
                else:
                    new_status = 'done'
            else:
                new_status = self.status
        else:
            new_status = self.status

        if new_status != self.status:
            self.status = new_status
            self.save(update_fields=['status'])

    @property
    def confirmed_count(self):
        return self.enrollments.filter(status='confirmed').count()

    @property
    def waiting_count(self):
        return self.enrollments.filter(status='waiting').count()

    @property
    def available_spots(self):
        return self.capacity - self.confirmed_count

    @property
    def is_open_for_priority(self):
        from django.utils import timezone
        now = timezone.now()
        if self.priority_start and self.priority_end:
            return self.priority_start <= now <= self.priority_end
        return False

    @property
    def is_open_for_general(self):
        from django.utils import timezone
        now = timezone.now()
        if self.general_start and self.general_end:
            return self.general_start <= now <= self.general_end
        return False


class PriorityMember(models.Model):
    period = models.ForeignKey(EnrollmentPeriod, on_delete=models.CASCADE, related_name='priority_members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='priority_memberships')
    note = models.CharField('메모', max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '우선접수 대상자'
        verbose_name_plural = '우선접수 대상자 목록'
        unique_together = ['period', 'user']

    def __str__(self):
        return f"{self.period} - {self.user.get_full_name()}"


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('confirmed', '등록확정'),
        ('waiting', '대기중'),
        ('cancelled', '취소'),
    ]
    TYPE_CHOICES = [
        ('priority', '우선접수'),
        ('general', '일반접수'),
        ('manual', '수동등록'),
    ]
    period = models.ForeignKey(EnrollmentPeriod, on_delete=models.CASCADE, related_name='enrollments', verbose_name='등록기간')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollments')
    name = models.CharField('이름', max_length=20)
    phone = models.CharField('연락처', max_length=15)
    building = models.CharField('동', max_length=10)
    unit = models.CharField('호수', max_length=10)
    status = models.CharField('상태', max_length=15, choices=STATUS_CHOICES, default='confirmed')
    enroll_type = models.CharField('접수유형', max_length=10, choices=TYPE_CHOICES, default='general')
    waiting_order = models.PositiveIntegerField('대기순번', null=True, blank=True)
    cancel_requested = models.BooleanField('변경요청', default=False)
    cancel_message = models.TextField('변경요청내용', blank=True)
    created_at = models.DateTimeField('등록일시', auto_now_add=True)

    class Meta:
        verbose_name = '수강 등록'
        verbose_name_plural = '수강 등록 목록'
        ordering = ['period', 'created_at']
        unique_together = ['period', 'phone']

    def __str__(self):
        return f"{self.period} - {self.name} ({self.building}동 {self.unit}호)"

    def save(self, *args, **kwargs):
        if self.status == 'waiting' and not self.waiting_order:
            last = Enrollment.objects.filter(
                period=self.period, status='waiting'
            ).order_by('-waiting_order').first()
            self.waiting_order = (last.waiting_order + 1) if last else 1
        super().save(*args, **kwargs)
