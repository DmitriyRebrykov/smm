from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User, UserProfile


class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации пользователя"""

    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input-glow w-full bg-luxury-black border border-white/10 px-4 py-3 text-white placeholder-luxury-muted/50 focus:outline-none focus:border-luxury-gold transition-all',
            'placeholder': 'Ваше имя'
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'input-glow w-full bg-luxury-black border border-white/10 px-4 py-3 text-white placeholder-luxury-muted/50 focus:outline-none focus:border-luxury-gold transition-all',
            'placeholder': 'your@email.com'
        })
    )

    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'input-glow w-full bg-luxury-black border border-white/10 px-4 py-3 text-white placeholder-luxury-muted/50 focus:outline-none focus:border-luxury-gold transition-all',
            'placeholder': 'Минимум 6 символов'
        })
    )

    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'input-glow w-full bg-luxury-black border border-white/10 px-4 py-3 text-white placeholder-luxury-muted/50 focus:outline-none focus:border-luxury-gold transition-all',
            'placeholder': 'Повторите пароль'
        })
    )

    class Meta:
        model = User
        fields = ('first_name', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже существует.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        user.username = self.cleaned_data['email'].lower()  # username = email

        if commit:
            user.save()
            # Создаем профиль автоматически
            UserProfile.objects.create(user=user)

        return user


class CustomAuthenticationForm(AuthenticationForm):
    """Форма входа"""

    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'input-glow w-full bg-luxury-black border border-white/10 px-4 py-3 text-white placeholder-luxury-muted/50 focus:outline-none focus:border-luxury-gold transition-all',
            'placeholder': 'your@email.com',
            'autofocus': True
        })
    )

    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'input-glow w-full bg-luxury-black border border-white/10 px-4 py-3 text-white placeholder-luxury-muted/50 focus:outline-none focus:border-luxury-gold transition-all',
            'placeholder': 'Ваш пароль'
        })
    )


class UserUpdateForm(forms.ModelForm):
    """Форма обновления профиля пользователя"""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'avatar', 'bio', 'email_notifications')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full bg-luxury-black border border-white/10 px-4 py-3 text-white focus:outline-none focus:border-luxury-gold transition-all',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full bg-luxury-black border border-white/10 px-4 py-3 text-white focus:outline-none focus:border-luxury-gold transition-all',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full bg-luxury-black border border-white/10 px-4 py-3 text-white focus:outline-none focus:border-luxury-gold transition-all',
                'placeholder': '+380...'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full bg-luxury-black border border-white/10 px-4 py-3 text-white focus:outline-none focus:border-luxury-gold transition-all',
                'rows': 4,
                'placeholder': 'Расскажите о себе...'
            }),
        }


class UserProfileUpdateForm(forms.ModelForm):
    """Форма обновления расширенного профиля"""

    class Meta:
        model = UserProfile
        fields = (
            'occupation', 'company', 'website',
            'instagram', 'telegram', 'linkedin',
            'learning_goal', 'experience_level'
        )
        widgets = {
            'occupation': forms.TextInput(attrs={
                'class': 'w-full bg-luxury-black border border-white/10 px-4 py-3 text-white focus:outline-none focus:border-luxury-gold transition-all',
                'placeholder': 'Например: SMM-специалист'
            }),
            'company': forms.TextInput(attrs={
                'class': 'w-full bg-luxury-black border border-white/10 px-4 py-3 text-white focus:outline-none focus:border-luxury-gold transition-all',
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full bg-luxury-black border border-white/10 px-4 py-3 text-white focus:outline-none focus:border-luxury-gold transition-all',
                'placeholder': 'https://'
            }),
            'instagram': forms.TextInput(attrs={
                'class': 'w-full bg-luxury-black border border-white/10 px-4 py-3 text-white focus:outline-none focus:border-luxury-gold transition-all',
                'placeholder': 'username'
            }),
            'telegram': forms.TextInput(attrs={
                'class': 'w-full bg-luxury-black border border-white/10 px-4 py-3 text-white focus:outline-none focus:border-luxury-gold transition-all',
                'placeholder': 'username'
            }),
            'linkedin': forms.URLInput(attrs={
                'class': 'w-full bg-luxury-black border border-white/10 px-4 py-3 text-white focus:outline-none focus:border-luxury-gold transition-all',
            }),
            'learning_goal': forms.Textarea(attrs={
                'class': 'w-full bg-luxury-black border border-white/10 px-4 py-3 text-white focus:outline-none focus:border-luxury-gold transition-all',
                'rows': 3,
            }),
            'experience_level': forms.Select(attrs={
                'class': 'w-full bg-luxury-black border border-white/10 px-4 py-3 text-white focus:outline-none focus:border-luxury-gold transition-all',
            }),
        }