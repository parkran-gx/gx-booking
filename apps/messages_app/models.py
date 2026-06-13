from django.db import models
from django.contrib.auth.models import User
from apps.classes.models import GxClass

class Message(models.Model):
    TYPE_CHOICES = [
        ('guest', '비회원'),
        ('member', '회원'),
        ('registered', '등록회원'),
    ]
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_messages')
    sender_name = models.CharField('보내는 분', max_length=20, blank=True)
    sender_phone = models.CharField('연락처', max_length=15, blank=True)
    gx_class = models.ForeignKey(GxClass, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='관련수업')
    message_type = models.CharField('유형', max_length=15, choices=TYPE_CHOICES, default='guest')
    content = models.TextField('내용')
    is_read = models.BooleanField('읽음', default=False)
    reply = models.TextField('답변', blank=True)
    replied_at = models.DateTimeField('답변일시', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '쪽지'
        verbose_name_plural = '쪽지 목록'
        ordering = ['-created_at']

    def __str__(self):
        sender = self.sender_name or (self.sender.get_full_name() if self.sender else '알수없음')
        return f"{sender} - {self.content[:30]}"
