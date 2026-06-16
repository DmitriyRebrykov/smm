from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

from config import settings


class Course(models.Model):
    title = models.CharField('Название', max_length=200)
    slug = models.SlugField('URL slug', unique=True)
    description = models.TextField('Описание')
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    currency = models.CharField('Валюта', max_length=3, default='UAH')
    is_active = models.BooleanField('Активен', default=True)

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Пользователь')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='Курс')

    granted_at = models.DateTimeField('Доступ предоставлен', auto_now_add=True)
    # expires_at = None означает ВЕЧНЫЙ доступ (покупка)
    # expires_at = дата означает временный доступ (ручное ограничение через админку)
    expires_at = models.DateTimeField('Доступ истекает', null=True, blank=True)
    is_active = models.BooleanField('Активен', default=True)

    purchase = models.ForeignKey('Purchase', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Доступ к курсу'
        verbose_name_plural = 'Доступы к курсам'
        unique_together = ['user', 'course']
        ordering = ['-granted_at']

    def __str__(self):
        return f"{self.user.email} - {self.course.title}"

    def has_access(self):
        """
        Возвращает True если доступ активен.
        expires_at=None — вечный доступ (стандартная покупка).
        expires_at=дата — временный (только если задано вручную в админке).
        """
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    @classmethod
    def user_has_access(cls, user, course):
        """
        Удобный метод для проверки доступа пользователя к курсу.
        Используйте его во views вместо ручных filter().
        """
        if not user or not user.is_authenticated:
            return False
        try:
            access = cls.objects.get(user=user, course=course)
            return access.has_access()
        except cls.DoesNotExist:
            return False


class Purchase(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Ожидание оплаты'),
        ('processing', 'Обработка'),
        ('success', 'Успешно'),
        ('failure', 'Ошибка'),
        ('reversed', 'Возврат'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Покупатель')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='Курс')

    amount = models.DecimalField('Сумма', max_digits=10, decimal_places=2)
    currency = models.CharField('Валюта', max_length=3, default='UAH')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')

    order_id = models.CharField('ID заказа', max_length=100, unique=True, db_index=True)
    liqpay_order_id = models.CharField('LiqPay Order ID', max_length=100, blank=True)
    payment_id = models.CharField('ID платежа', max_length=100, blank=True)

    customer_email = models.EmailField('Email покупателя')
    customer_name = models.CharField('Имя покупателя', max_length=200, blank=True)

    callback_data = models.JSONField('Данные callback', null=True, blank=True)

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
        """Отмечает покупку как оплаченную и выдаёт вечный доступ к курсу."""
        if self.status == 'success':
            return

        self.status = 'success'
        self.paid_at = timezone.now()
        self.save()

        # expires_at намеренно НЕ передаём — None = вечный доступ
        def mark_as_paid(self):
            """Отмечает покупку как оплаченную и выдаёт вечный доступ к курсу."""
            import logging
            logger = logging.getLogger(__name__)

            if self.status == 'success':
                return

            self.status = 'success'
            self.paid_at = timezone.now()
            self.save()

            # 🔑 КЛЮЧЕВОЙ ШАГ: выдаём доступ
            access, created = CourseAccess.objects.update_or_create(
                user=self.user,
                course=self.course,
                defaults={
                    'is_active': True,
                    'expires_at': None,  # ← ВЕЧНЫЙ доступ
                    'purchase': self,
                    'granted_at': timezone.now(),
                }
            )

            logger.info(f"✅ Доступ выдан: {self.user.email} → {self.course.title}")

            try:
                from apps.courses.services.email_service import send_purchase_confirmation
                send_purchase_confirmation(self)
            except Exception as e:
                logger.error(f"Email ошибка: {e}")

        # Отправляем email — в отдельном try/except, чтобы не сломать логику оплаты
        try:
            from apps.courses.services.email_service import send_purchase_confirmation
            send_purchase_confirmation(self)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Не удалось отправить email: {e}")


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons', verbose_name='Курс')

    title = models.CharField('Название', max_length=200)
    slug = models.SlugField('URL slug')
    description = models.TextField('Описание', blank=True)

    video_url = models.URLField('Ссылка на видео', blank=True)
    content = models.TextField('Контент урока', blank=True)

    files = models.JSONField('Файлы для скачивания', default=list, blank=True)

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


class LessonProgress(models.Model):
    """Прогресс прохождения урока пользователем"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lesson_progress',
        verbose_name='Пользователь'
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='progress_records',
        verbose_name='Урок'
    )
    is_completed = models.BooleanField('Завершён', default=False)
    completed_at = models.DateTimeField('Завершён в', null=True, blank=True)

    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Прогресс урока'
        verbose_name_plural = 'Прогресс уроков'
        unique_together = ['user', 'lesson']

    def __str__(self):
        status = "✓" if self.is_completed else "○"
        return f"{status} {self.user.email} — {self.lesson.title}"

    def mark_completed(self):
        if not self.is_completed:
            self.is_completed = True
            self.completed_at = timezone.now()
            self.save()

    @classmethod
    def get_course_progress(cls, user, course):
        """Возвращает процент прохождения курса (0-100)"""
        total_lessons = course.lessons.count()
        if total_lessons == 0:
            return 0
        completed = cls.objects.filter(
            user=user,
            lesson__course=course,
            is_completed=True
        ).count()
        return int((completed / total_lessons) * 100)

    @classmethod
    def get_completed_ids(cls, user, course):
        """Возвращает set ID завершённых уроков"""
        return set(cls.objects.filter(
            user=user,
            lesson__course=course,
            is_completed=True
        ).values_list('lesson_id', flat=True))


def validate_submission_file(value):
    """Валидация: только PDF, изображения и видео"""
    import os
    from django.core.exceptions import ValidationError

    ALLOWED_EXTENSIONS = {
        '.pdf',
        '.jpg', '.jpeg', '.png', '.gif', '.webp',
        '.mp4', '.mov', '.avi', '.mkv', '.webm',
    }

    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f'Формат "{ext}" не поддерживается. '
            f'Разрешены: PDF, изображения (JPG, PNG, GIF, WEBP) и видео (MP4, MOV, AVI, MKV, WEBM).'
        )


class LessonSubmission(models.Model):
    """Домашняя работа студента"""
    STATUS_CHOICES = [
        ('pending', 'На проверке'),
        ('reviewed', 'Проверено'),
        ('approved', 'Принято'),
        ('rejected', 'На доработке'),
    ]

    ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp',
                          '.mp4', '.mov', '.avi', '.mkv', '.webm']

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Пользователь'
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Урок'
    )
    file = models.FileField(
        'Файл',
        upload_to='submissions/%Y/%m/',
        validators=[validate_submission_file],
        help_text='Разрешены: PDF, изображения (JPG, PNG, GIF, WEBP), видео (MP4, MOV, AVI, MKV, WEBM). До 50 МБ.'
    )
    comment = models.TextField('Комментарий', blank=True)

    status = models.CharField(
        'Статус', max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    feedback = models.TextField('Обратная связь преподавателя', blank=True)

    created_at = models.DateTimeField('Отправлено', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Работа студента'
        verbose_name_plural = 'Работы студентов'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} — {self.lesson.title} ({self.get_status_display()})"

    @property
    def filename(self):
        import os
        return os.path.basename(self.file.name)