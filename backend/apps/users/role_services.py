"""Teacher-role application and review workflow."""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import TeacherApplication, User


logger = logging.getLogger(__name__)


class TeacherApplicationError(Exception):
    """Safe workflow failure that can be returned without internal details."""


def _notify_admins(application_id):
    recipients = list(
        User.objects.filter(
            role='admin',
            is_active=True,
            is_verified=True,
        ).values_list('email', flat=True)
    )
    if not recipients:
        return
    try:
        send_mail(
            subject='Hồ sơ đăng ký giáo viên mới - Intaaneto',
            message=(
                f'Có hồ sơ đăng ký giáo viên #{application_id} đang chờ duyệt. '
                'Vui lòng đăng nhập khu vực quản trị để xem xét.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
    except Exception:
        logger.warning(
            'Teacher application admin notification failed for application %s',
            application_id,
        )


def _notify_applicant(application_id):
    application = TeacherApplication.objects.select_related('applicant').filter(
        pk=application_id,
    ).first()
    if application is None:
        return
    status_label = 'đã được duyệt' if application.status == 'approved' else 'đã bị từ chối'
    message = f'Hồ sơ đăng ký giáo viên #{application.pk} {status_label}.'
    if application.review_note:
        message = f'{message}\nPhản hồi của quản trị viên: {application.review_note}'
    try:
        send_mail(
            subject='Kết quả hồ sơ giáo viên - Intaaneto',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[application.applicant.email],
            fail_silently=False,
        )
    except Exception:
        logger.warning(
            'Teacher application result notification failed for application %s',
            application_id,
        )


def submit_teacher_application(*, applicant, validated_data):
    if applicant.role != 'student':
        raise TeacherApplicationError('Chỉ tài khoản học viên mới có thể gửi hồ sơ')
    if not applicant.is_verified:
        raise TeacherApplicationError('Bạn cần xác thực email trước khi gửi hồ sơ')

    try:
        with transaction.atomic():
            application = TeacherApplication.objects.create(
                applicant=applicant,
                **validated_data,
            )
            transaction.on_commit(
                lambda application_id=application.pk: _notify_admins(application_id)
            )
    except IntegrityError as exc:
        raise TeacherApplicationError(
            'Bạn đã có một hồ sơ đang chờ quản trị viên duyệt'
        ) from exc
    return application


def review_teacher_application(*, reviewer, application_id, decision, review_note):
    if reviewer.role != 'admin' or not reviewer.is_verified:
        raise TeacherApplicationError('Bạn không có quyền duyệt hồ sơ giáo viên')

    with transaction.atomic():
        application = (
            TeacherApplication.objects.select_for_update()
            .select_related('applicant__profile')
            .filter(pk=application_id)
            .first()
        )
        if application is None:
            raise TeacherApplicationError('Không tìm thấy hồ sơ giáo viên')
        if application.status != 'pending':
            raise TeacherApplicationError('Hồ sơ này đã được xử lý')

        applicant = application.applicant
        if decision == 'approved':
            if applicant.role != 'student':
                raise TeacherApplicationError('Tài khoản không còn là học viên')
            applicant.role = 'teacher'
            applicant.save(update_fields=['role'])
            profile = applicant.profile
            profile.specialization = application.specialization
            profile.years_of_experience = application.years_of_experience
            profile.save(update_fields=[
                'specialization',
                'years_of_experience',
                'updated_at',
            ])

        application.status = decision
        application.reviewed_by = reviewer
        application.review_note = review_note
        application.reviewed_at = timezone.now()
        application.save(update_fields=[
            'status',
            'reviewed_by',
            'review_note',
            'reviewed_at',
        ])
        transaction.on_commit(
            lambda reviewed_id=application.pk: _notify_applicant(reviewed_id)
        )
    return application
