from django.db import models
import uuid

class Complex(models.Model):
    name = models.CharField('단지명', max_length=100)
    code = models.CharField('단지코드', max_length=20, unique=True)
    address = models.CharField('주소', max_length=200, blank=True)
    is_active = models.BooleanField('운영중', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '단지'
        verbose_name_plural = '단지 목록'
        ordering = ['name']

    def __str__(self):
        return self.name

    @staticmethod
    def generate_code():
        return uuid.uuid4().hex[:8].upper()
