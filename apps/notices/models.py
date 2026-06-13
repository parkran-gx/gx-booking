from django.db import models
from django.contrib.auth.models import User
from apps.classes.models import GxClass

class Notice(models.Model):
    gx_class = models.ForeignKey(GxClass, on_delete=models.CASCADE, related_name='notices', verbose_name='수업', null=True, blank=True)
    title = models.CharField('제목', max_length=200)
    content = models.TextField('내용')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='notices')
    is_pinned = models.BooleanField('상단고정', default=False)
    is_global = models.BooleanField('전체공지', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '공지'
        verbose_name_plural = '공지 목록'
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title
