from django.db import models

class ContactRequest(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_progress', 'В обработке'),
        ('completed', 'Завершена'),
    ]
    
    SERVICE_CHOICES = [
        ('smm-strategy', 'SMM стратегия'),
        ('content-creation', 'Создание контента'),
        ('ai-content', 'AI контент'),
        ('analytics', 'Аналитика и отчеты'),
        ('consultation', 'Консультация'),
    ]
    
    # Основные поля
    name = models.CharField('Имя', max_length=100)
    email = models.EmailField('Email')
    service = models.CharField('Услуга', max_length=50, choices=SERVICE_CHOICES, blank=True)
    message = models.TextField('Сообщение', blank=True)
    
    # Метаданные
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    telegram_sent = models.BooleanField('Отправлено в Telegram', default=False)
    telegram_message_id = models.IntegerField('ID сообщения в Telegram', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.email} ({self.created_at.strftime('%d.%m.%Y %H:%M')})"


class Case(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField()
    image = models.ImageField()
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

