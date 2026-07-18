from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Profile, TeacherApplication, User
from .role_services import TeacherApplicationError, review_teacher_application


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin"""
    
    list_display = ['email', 'username', 'full_name', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff', 'created_at']
    search_fields = ['email', 'username', 'full_name', 'phone_number']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('username', 'full_name', 'phone_number', 'date_of_birth', 'avatar', 'bio')}),
        (_('Permissions'), {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login']
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'full_name', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Profile Admin"""
    
    list_display = ['user', 'grade_level', 'school_name', 'specialization']
    list_filter = ['grade_level', 'notification_enabled']
    search_fields = ['user__email', 'user__full_name', 'school_name']
    raw_id_fields = ['user']


@admin.register(TeacherApplication)
class TeacherApplicationAdmin(admin.ModelAdmin):
    """Auditable teacher-role review queue."""

    list_display = [
        'id',
        'applicant',
        'specialization',
        'years_of_experience',
        'status',
        'submitted_at',
        'reviewed_by',
    ]
    list_filter = ['status', 'submitted_at', 'reviewed_at']
    search_fields = [
        'applicant__email',
        'applicant__full_name',
        'specialization',
    ]
    readonly_fields = [
        'applicant',
        'specialization',
        'years_of_experience',
        'reason',
        'status',
        'reviewed_by',
        'review_note',
        'submitted_at',
        'reviewed_at',
    ]
    actions = ['approve_applications', 'reject_applications']

    @admin.action(description='Duyệt các hồ sơ đang chờ')
    def approve_applications(self, request, queryset):
        processed = self._review_selected(
            request=request,
            queryset=queryset,
            decision='approved',
            note='Được duyệt qua khu vực quản trị.',
        )
        self.message_user(request, f'Đã duyệt {processed} hồ sơ.')

    @admin.action(description='Từ chối các hồ sơ đang chờ')
    def reject_applications(self, request, queryset):
        processed = self._review_selected(
            request=request,
            queryset=queryset,
            decision='rejected',
            note='Hồ sơ chưa đáp ứng yêu cầu hiện tại.',
        )
        self.message_user(request, f'Đã từ chối {processed} hồ sơ.')

    def _review_selected(self, *, request, queryset, decision, note):
        processed = 0
        for application_id in queryset.filter(status='pending').values_list(
            'id',
            flat=True,
        ):
            try:
                review_teacher_application(
                    reviewer=request.user,
                    application_id=application_id,
                    decision=decision,
                    review_note=note,
                )
                processed += 1
            except TeacherApplicationError:
                continue
        return processed
