from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator
import random
from datetime import timedelta
from django.urls import reverse



class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('REGULAR', 'Regular User'),
        ('STAFF', 'Staff/Content Creator'),
        ('TECHNICAL', 'Technical Official/Reviewer'),
    )
    
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='REGULAR')
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def generate_otp(self):
        """Generate and save a new OTP"""
        self.otp = str(random.randint(100000, 999999))
        self.otp_expiry = timezone.now() + timedelta(minutes=30)
        self.save()
        return self.otp

    def verify_otp(self, otp):
        """Verify OTP with proper null checks"""
        if not self.otp or not self.otp_expiry:
            return False

        if timezone.now() > self.otp_expiry:
            return False

        if self.otp == otp:
            self.otp = None
            self.otp_expiry = None
            self.is_verified = True
            self.save()
            return True

        return False


class StaffProfile(models.Model):
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="staff_profile"
    )
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, null=True, blank=True
    )
    position = models.CharField(max_length=100)
    is_teaching = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["position"]),
        ]

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.position})"


class TechnicalProfile(models.Model):
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="technical_profile"
    )
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, null=True, blank=True
    )
    position = models.CharField(max_length=100)
    expertise = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.position})"



class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_published_posts_count(self):
        return self.post_category.filter(status='PUBLISHED').count()

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Post(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING_REVIEW', 'Pending Review'),
        ('PUBLISHED', 'Published'),
        ('REJECTED', 'Rejected'),
    ]
    
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='post_category'
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='authored_posts'
    )
    title = models.CharField(max_length=200, validators=[MinLengthValidator(10)])
    # REMOVED SLUG FIELD
    summary = models.TextField(max_length=300)
    content = models.TextField()
    featured_image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_posts'
    )
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('post_detail', kwargs={'pk': self.id})
    
    def get_meta_description(self):
        return self.summary[:160]  # Recommended length for meta description
    
    def get_keywords(self):
        # Extract keywords from title and content
        from collections import Counter
        import re
        
        text = f"{self.title} {self.summary}"
        words = re.findall(r'\w+', text.lower())
        most_common = Counter(words).most_common(5)
        return ', '.join([word[0] for word in most_common])
    

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['-created_at'])]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.status == 'PUBLISHED' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_meta_description(self):
        return self.summary[:160]  # Recommended length for meta description
    
    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'slug': self.title})
    def get_keywords(self):
        # Extract keywords from title and content
        from collections import Counter
        import re
        
        text = f"{self.title} {self.summary}"
        words = re.findall(r'\w+', text.lower())
        most_common = Counter(words).most_common(5)
        return ', '.join([word[0] for word in most_common])



class Comment(models.Model):
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='post_comments'  # Changed related name
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='user_comments'  # Changed related name
    )
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.user.email} on {self.post.title}'


class PostView(models.Model):
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='post_views'  # Changed related name
    )
    ip_address = models.GenericIPAddressField()
    user = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='user_views'  # Added related name
    )
    view_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Post View'
        verbose_name_plural = 'Post Views'
        ordering = ['-view_date']