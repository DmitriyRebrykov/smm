from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

from config import settings


class Course(models.Model):
    """Модель курса"""
    title = models.CharField('Название', max_length=200)
    slug = models.SlugField('URL slug', unique=True)
    description = models.TextField('Описание')
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    currency = models.CharField('Валюта', max_length=3, default='UAH')
    is_active = models.BooleanField('Активен', default=True)

    # Опциональные поля
    preview_image = models.ImageField('Превью', upload_to='courses/', blank=True, null=True)
    duration = models.CharField('Длительность', max_length=100, blank=True)
    lessons_count = models.IntegerField('Количество уроков', default=0)

    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлен', auto_now=True)

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class CourseAccess(models.Model):
    """Модель доступа к курсу"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Пользователь')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='Курс')

    # Информация о доступе
    granted_at = models.DateTimeField('Доступ предоставлен', auto_now_add=True)
    expires_at = models.DateTimeField('Доступ истекает', null=True, blank=True)
    is_active = models.BooleanField('Активен', default=True)

    # Связь с покупкой
    purchase = models.ForeignKey('Purchase', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Доступ к курсу'
        verbose_name_plural = 'Доступы к курсам'
        unique_together = ['user', 'course']
        ordering = ['-granted_at']

    def __str__(self):
        return f"{self.user.email} - {self.course.title}"

    def has_access(self):
        """Проверка активности доступа"""
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True


class Purchase(models.Model):
    """Модель покупки"""

    STATUS_CHOICES = [
        ('pending', 'Ожидание оплаты'),
        ('processing', 'Обработка'),
        ('success', 'Успешно'),
        ('failure', 'Ошибка'),
        ('reversed', 'Возврат'),
    ]

    # Основная информация
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Покупатель')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='Курс')

    # Финансовые данные
    amount = models.DecimalField('Сумма', max_digits=10, decimal_places=2)
    currency = models.CharField('Валюта', max_length=3, default='UAH')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')

    # LiqPay данные
    order_id = models.CharField('ID заказа', max_length=100, unique=True, db_index=True)
    liqpay_order_id = models.CharField('LiqPay Order ID', max_length=100, blank=True)
    payment_id = models.CharField('ID платежа', max_length=100, blank=True)

    # Метаданные
    customer_email = models.EmailField('Email покупателя')
    customer_name = models.CharField('Имя покупателя', max_length=200, blank=True)

    # Callback данные
    callback_data = models.JSONField('Данные callback', null=True, blank=True)

    # Временные метки
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)
    paid_at = models.DateTimeField('Оплачена', null=True, blank=True)

    class Meta:
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Заказ #{self.order_id} - {self.course.title}"

    def mark_as_paid(self):
        """Отметить заказ как оплаченный и предоставить доступ"""
        if self.status == 'success':
            return  # Уже оплачен

        self.status = 'success'
        self.paid_at = timezone.now()
        self.save()

        # Предоставляем доступ к курсу
        CourseAccess.objects.update_or_create(
            user=self.user,
            course=self.course,
            defaults={
                'is_active': True,
                'purchase': self,
            }
        )


class Lesson(models.Model):
    """Модель урока"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons', verbose_name='Курс')

    title = models.CharField('Название', max_length=200)
    slug = models.SlugField('URL slug')
    description = models.TextField('Описание', blank=True)

    # Контент
    video_url = models.URLField('Ссылка на видео', blank=True)
    content = models.TextField('Контент урока', blank=True)

    # Файлы
    files = models.JSONField('Файлы для скачивания', default=list, blank=True)

    # Порядок и доступность
    order = models.IntegerField('Порядок', default=0)
    is_free = models.BooleanField('Бесплатный', default=False)
    duration = models.CharField('Длительность', max_length=50, blank=True)

    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлен', auto_now=True)

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['course', 'order']
        unique_together = ['course', 'slug']

    def __str__(self):
        return f"{self.course.title} - {self.title}"