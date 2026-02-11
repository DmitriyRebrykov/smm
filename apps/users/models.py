from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _("Пользователь с таким email уже существует."),
        }
    )

    phone = models.CharField(
        'Телефон',
        max_length=20,
        blank=True,
        help_text='Контактный телефон'
    )

    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/',
        blank=True,
        null=True
    )

    bio = models.TextField(
        'О себе',
        blank=True,
        max_length=500
    )

    email_notifications = models.BooleanField(
        'Email уведомления',
        default=True,
        help_text='Получать уведомления на email'
    )

    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']

    def __str__(self):
        return self.email

    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username

    def get_short_name(self):
        return self.first_name or self.username

    def get_initials(self):
        if self.first_name:
            return self.first_name[0].upper()
        return self.email[0].upper()


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )

    occupation = models.CharField(
        'Род деятельности',
        max_length=100,
        blank=True
    )

    company = models.CharField(
        'Компания',
        max_length=100,
        blank=True
    )

    website = models.URLField(
        'Веб-сайт',
        blank=True
    )

    instagram = models.CharField(
        'Instagram',
        max_length=100,
        blank=True,
        help_text='Username без @'
    )

    telegram = models.CharField(
        'Telegram',
        max_length=100,
        blank=True,
        help_text='Username без @'
    )

    linkedin = models.URLField(
        'LinkedIn',
        blank=True
    )

    learning_goal = models.TextField(
        'Цель обучения',
        blank=True,
        help_text='Что хотите достичь?'
    )

    experience_level = models.CharField(
        'Уровень опыта',
        max_length=20,
        choices=[
            ('beginner', 'Новичок'),
            ('intermediate', 'Средний'),
            ('advanced', 'Продвинутый'),
            ('expert', 'Эксперт'),
        ],
        default='beginner'
    )

    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлен', auto_now=True)

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f"Профиль {self.user.email}"