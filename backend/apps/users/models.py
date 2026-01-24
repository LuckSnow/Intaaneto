from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom user manager"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user"""
        if not email:
            raise ValueError(_('Email address is required'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model"""
    
    ROLE_CHOICES = [
        ('student', 'Học sinh'),
        ('parent', 'Phụ huynh'),
        ('teacher', 'Giáo viên'),
        ('admin', 'Quản trị viên'),
    ]
    
    email = models.EmailField(_('email address'), unique=True, db_index=True)
    username = models.CharField(_('username'), max_length=150, unique=True, db_index=True)
    full_name = models.CharField(_('full name'), max_length=255)
    role = models.CharField(_('role'), max_length=20, choices=ROLE_CHOICES, default='student')
    
    phone_regex = RegexValidator(
        regex=r'^(\+84|0)[0-9]{9,10}$',
        message="Phone number must be in format: '+84xxxxxxxxx' or '0xxxxxxxxx'"
    )
    phone_number = models.CharField(_('phone number'), validators=[phone_regex], max_length=15, blank=True)
    
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    avatar = models.ImageField(_('avatar'), upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(_('bio'), blank=True)
    
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_active = models.BooleanField(_('active'), default=True)
    is_verified = models.BooleanField(_('verified'), default=False)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    last_login = models.DateTimeField(_('last login'), null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'role']),
            models.Index(fields=['username']),
        ]
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    def get_full_name(self):
        return self.full_name
    
    def get_short_name(self):
        return self.username


class Profile(models.Model):
    """Extended profile for users"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # For students
    grade_level = models.CharField(_('grade level'), max_length=50, blank=True)
    school_name = models.CharField(_('school name'), max_length=255, blank=True)
    learning_style = models.CharField(_('learning style'), max_length=50, blank=True)
    
    # For parents - link to student
    student = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='parent_profiles',
        limit_choices_to={'role': 'student'}
    )
    
    # For teachers
    specialization = models.CharField(_('specialization'), max_length=255, blank=True)
    years_of_experience = models.PositiveIntegerField(_('years of experience'), default=0)
    
    # Preferences
    notification_enabled = models.BooleanField(_('notification enabled'), default=True)
    email_notification = models.BooleanField(_('email notification'), default=True)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('profile')
        verbose_name_plural = _('profiles')
    
    def __str__(self):
        return f"Profile of {self.user.full_name}"
