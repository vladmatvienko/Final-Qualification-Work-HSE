"""
Repository для создания заявки на изменение резюме и связанных сущностей:
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


class ResumeRequestRepository:
    """
    Репозиторий для сохранения заявки на изменение резюме.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_section_by_id(self, section_id: int):
        """
        Проверяет, существует ли раздел резюме, и возвращает его данные.
        """
        query = text(
            """
            SELECT id, name
            FROM resume_sections
            WHERE id = :section_id
            LIMIT 1
            """
        )

        return self.session.execute(
            query,
            {"section_id": section_id},
        ).mappings().first()

    def get_employee_full_name(self, employee_user_id: int) -> str | None:
        """
        Возвращает ФИО сотрудника для текста уведомления HR.
        """
        query = text(
            """
            SELECT CONCAT_WS(' ', last_name, first_name, middle_name) AS full_name
            FROM users
            WHERE id = :employee_user_id
            LIMIT 1
            """
        )

        row = self.session.execute(
            query,
            {"employee_user_id": employee_user_id},
        ).mappings().first()

        return row["full_name"] if row else None

    def get_active_hr_user_ids(self) -> list[int]:
        """
        Возвращает список активных HR-пользователей.
        """
        query = text(
            """
            SELECT u.id AS user_id
            FROM users u
            INNER JOIN roles r
                ON r.id = u.role_id
            WHERE r.code = 'HR_MANAGER'
              AND u.is_active = TRUE
            ORDER BY u.id ASC
            """
        )

        rows = self.session.execute(query).mappings().all()
        return [int(row["user_id"]) for row in rows]

    def create_resume_change_request(
        self,
        employee_user_id: int,
        section_id: int,
        change_description: str,
        proposed_payload_json: str | None = None,
    ) -> int:
        """
        Создаёт запись в resume_change_requests.
        """
        query = text(
            """
            INSERT INTO resume_change_requests (
                employee_user_id,
                section_id,
                target_entity_type,
                target_entity_id,
                change_description,
                proposed_payload,
                status,
                submitted_at,
                reviewed_by_hr_user_id,
                reviewed_at,
                review_comment
            ) VALUES (
                :employee_user_id,
                :section_id,
                NULL,
                NULL,
                :change_description,
                :proposed_payload_json,
                'pending',
                NOW(),
                NULL,
                NULL,
                NULL
            )
            """
        )

        result = self.session.execute(
            query,
            {
                "employee_user_id": employee_user_id,
                "section_id": section_id,
                "change_description": change_description,
                "proposed_payload_json": proposed_payload_json,
            },
        )

        last_id_result = self.session.execute(text("SELECT LAST_INSERT_ID()"))
        last_id = last_id_result.scalar_one()
        return int(last_id)

    def create_employee_document_for_request(
        self,
        owner_user_id: int,
        request_id: int,
        file_path: str,
        original_filename: str,
        mime_type: str | None,
        file_size_bytes: int,
        file_checksum: str,
    ) -> int:
        """
        Создаёт запись о прикреплённом документе.
        """
        query = text(
            """
            INSERT INTO employee_documents (
                owner_user_id,
                document_type,
                source_entity_type,
                source_entity_id,
                file_path,
                original_filename,
                mime_type,
                file_size_bytes,
                file_checksum,
                extracted_text,
                extraction_status,
                indexed_at,
                created_at,
                updated_at
            ) VALUES (
                :owner_user_id,
                'resume_change_attachment',
                'resume_change_request',
                :request_id,
                :file_path,
                :original_filename,
                :mime_type,
                :file_size_bytes,
                :file_checksum,
                NULL,
                'pending',
                NULL,
                NOW(),
                NOW()
            )
            """
        )

        result = self.session.execute(
            query,
            {
                "owner_user_id": owner_user_id,
                "request_id": request_id,
                "file_path": file_path,
                "original_filename": original_filename,
                "mime_type": mime_type,
                "file_size_bytes": file_size_bytes,
                "file_checksum": file_checksum,
            },
        )

        last_id_result = self.session.execute(text("SELECT LAST_INSERT_ID()"))
        last_id = last_id_result.scalar_one()
        return int(last_id)

    def create_hr_notification(
        self,
        employee_user_id: int,
        request_id: int,
        employee_full_name: str,
        section_name: str,
        file_attached: bool,
    ) -> int:
        """
        Создаёт уведомление для HR о новой заявке сотрудника.
        """
        attachment_text = " Файл приложен." if file_attached else ""
        title = "Новая заявка на изменение резюме"
        message = (
            f"Сотрудник {employee_full_name} отправил заявку на обновление раздела "
            f"«{section_name}».{attachment_text}"
        )

        query = text(
            """
            INSERT INTO notifications (
                notification_type,
                title,
                message,
                sender_user_id,
                related_entity_type,
                related_entity_id,
                priority,
                created_at,
                expires_at
            ) VALUES (
                'hr_resume_change_request',
                :title,
                :message,
                :employee_user_id,
                'resume_change_request',
                :request_id,
                'high',
                NOW(),
                NULL
            )
            """
        )

        result = self.session.execute(
            query,
            {
                "title": title,
                "message": message,
                "employee_user_id": employee_user_id,
                "request_id": request_id,
            },
        )

        last_id_result = self.session.execute(text("SELECT LAST_INSERT_ID()"))
        last_id = last_id_result.scalar_one()
        return int(last_id)

    def add_notification_recipients(
        self,
        notification_id: int,
        recipient_user_ids: list[int],
    ) -> None:
        """
        Связывает уведомление с конкретными получателями.
        """
        if not recipient_user_ids:
            return

        query = text(
            """
            INSERT INTO notification_recipients (
                notification_id,
                recipient_user_id,
                status,
                read_at,
                created_at
            ) VALUES (
                :notification_id,
                :recipient_user_id,
                'unread',
                NULL,
                NOW()
            )
            """
        )

        for recipient_user_id in recipient_user_ids:
            self.session.execute(
                query,
                {
                    "notification_id": notification_id,
                    "recipient_user_id": recipient_user_id,
                },
            )