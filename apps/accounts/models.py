from django.db import models
from django.contrib.auth.models import User
from apps.complexes.models import Complex

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('super_admin', '슈퍼관리자'),
        ('complex_admin', '단지관리자'),
        ('registered', '등록회원'),
        ('unregistered', '미등록회원'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    complex = models.ForeignKey(Complex, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='단지')
    role = models.CharField('역할', max_length=20, choices=ROLE_CHOICES, default='unregistered')
    phone = models.CharField('연락처', max_length=15, blank=True)
    building = models.CharField('동', max_length=10, blank=True)
    unit = models.CharField('호수', max_length=10, blank=True)
    is_approved = models.BooleanField('승인여부', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '회원 프로필'
        verbose_name_plural = '회원 프로필 목록'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    @property
    def is_super_admin(self):
        return self.role == 'super_admin'

    @property
    def is_complex_admin(self):
        return self.role in ('super_admin', 'complex_admin')

    @property
    def is_registered(self):
        return self.role == 'registered' and self.is_approved

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
