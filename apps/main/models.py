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

    name = models.CharField('Имя', max_length=100)
    email = models.EmailField('Email')
    service = models.CharField('Услуга', max_length=50, choices=SERVICE_CHOICES, blank=True)
    message = models.TextField('Сообщение', blank=True)

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
    CATEGORY_CHOICES = [
        ('smm', 'SMM'),
        ('content', 'Контент & Reels'),
        ('target', 'Таргет'),
    ]

    title = models.CharField('Название', max_length=200)
    category = models.CharField('Категория', max_length=20, choices=CATEGORY_CHOICES)
    niche = models.CharField('Ниша / Тег', max_length=100, help_text='Например: E-commerce, Личный бренд')
    description = models.TextField('Описание')
    image = models.ImageField('Изображение', upload_to='cases/')
    metric_value = models.CharField('Значение метрики', max_length=50, help_text='Например: +150%')
    metric_label = models.CharField('Подпись метрики', max_length=50, help_text='Например: Продажи')
    secondary_value = models.CharField('Вторая метрика', max_length=50, help_text='Например: 3 мес')
    secondary_label = models.CharField('Подпись второй метрики', max_length=50, help_text='Например: Срок')
    is_active = models.BooleanField('Активен', default=True)
    order = models.IntegerField('Порядок', default=0)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        verbose_name = 'Кейс'
        verbose_name_plural = 'Кейсы'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title


class Review(models.Model):
    name = models.CharField('Имя', max_length=100)
    niche = models.CharField('Ниша', max_length=100, help_text='Например: Бьюти мастер')
    avatar = models.ImageField('Аватар', upload_to='reviews/avatars/', blank=True, null=True)
    text = models.TextField('Текст отзыва')
    result = models.CharField('Результат', max_length=200, help_text='Например: +1500 подписчиков за месяц')
    is_active = models.BooleanField('Активен', default=True)
    order = models.IntegerField('Порядок', default=0)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"{self.name} — {self.niche}"