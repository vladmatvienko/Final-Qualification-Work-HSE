from __future__ import annotations

"""
Service отправки приглашения сотруднику.
"""

from app.models.candidate_search_models import JobInvitationCommand, ServiceResult
from app.repositories.job_invitation_repository import JobInvitationRepository
from app.services.hr_candidate_search_service import HRCandidateSearchService


class JobInvitationService:
    """
    Высокоуровневая логика приглашения кандидата.
    """

    def __init__(self) -> None:
        self._repository = JobInvitationRepository()
        self._candidate_search_service = HRCandidateSearchService()

    def send_invitation(
        self,
        hr_user_id: int,
        anonymous_code: str,
        requirements_text: str,
        comment_text: str = "",
    ) -> ServiceResult:
        if not hr_user_id:
            return ServiceResult(
                success=False,
                message="Не удалось определить HR-пользователя.",
            )

        anonymous_code = (anonymous_code or "").strip()
        if not anonymous_code:
            return ServiceResult(
                success=False,
                message="Сначала выберите кандидата из рейтинговой таблицы.",
            )

        employee_user_id = self._candidate_search_service.resolve_employee_user_id(anonymous_code)
        if employee_user_id is None:
            return ServiceResult(
                success=False,
                message="Не удалось сопоставить анонимного кандидата с сотрудником. Перезапустите поиск.",
            )

        position_title = self._candidate_search_service.derive_position_title(requirements_text)

        command = JobInvitationCommand(
            hr_user_id=int(hr_user_id),
            employee_user_id=int(employee_user_id),
            anonymous_code=anonymous_code,
            position_title=position_title,
            requirements_text=(requirements_text or "").strip(),
            comment_text=(comment_text or "").strip(),
        )

        invitation_id, created_new = self._repository.create_job_invitation(command)

        notification_title = f"Новое приглашение на роль: {position_title}"
        notification_message = (
            f"HR-менеджер направил вам приглашение на роль «{position_title}». "
            f"Откройте уведомление в системе «Эльбрус» и ознакомьтесь с деталями."
        )
        if command.comment_text:
            notification_message += f" Комментарий HR: {command.comment_text}"

        notification_created = self._repository.create_employee_notification_if_missing(
            employee_user_id=command.employee_user_id,
            title=notification_title,
            message=notification_message,
            related_entity_id=invitation_id,
        )

        if created_new:
            return ServiceResult(
                success=True,
                message=f"Приглашение по кандидату {anonymous_code} сохранено и отправлено сотруднику.",
                payload={
                    "invitation_id": invitation_id,
                    "employee_user_id": command.employee_user_id,
                    "anonymous_code": anonymous_code,
                    "created_new": True,
                    "notification_created": notification_created,
                },
            )

        if notification_created:
            message = (
                f"Приглашение по кандидату {anonymous_code} уже существовало, "
                "но уведомление сотруднику было восстановлено."
            )
        else:
            message = (
                f"Приглашение по кандидату {anonymous_code} уже было отправлено ранее. "
                "Повторная запись не создана."
            )

        return ServiceResult(
            success=True,
            message=message,
            payload={
                "invitation_id": invitation_id,
                "employee_user_id": command.employee_user_id,
                "anonymous_code": anonymous_code,
                "created_new": False,
                "notification_created": notification_created,
            },
        )
