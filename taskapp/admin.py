
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StaffProfile, TechnicalProfile, Category, Post, Comment, PostView

class StaffProfileInline(admin.StackedInline):
    model = StaffProfile
    can_delete = False
    verbose_name_plural = 'Staff Profile'
    fk_name = 'user'

class TechnicalProfileInline(admin.StackedInline):
    model = TechnicalProfile
    can_delete = False
    verbose_name_plural = 'Technical Profile'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (StaffProfileInline, TechnicalProfileInline)
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_verified')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'is_verified')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'role')}),
        ('Verification', {'fields': ('otp', 'otp_expiry', 'is_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)

class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'position', 'is_teaching')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'position')

class TechnicalProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'position', 'expertise')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'position', 'expertise')

class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'published_at')
    list_filter = ('status', 'category', 'author')
    search_fields = ('title', 'summary', 'content')
    raw_id_fields = ('author', 'reviewed_by')

# Register your models
admin.site.register(User, CustomUserAdmin)
admin.site.register(StaffProfile, StaffProfileAdmin)
admin.site.register(TechnicalProfile, TechnicalProfileAdmin)
admin.site.register(Category)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment)
admin.site.register(PostView)