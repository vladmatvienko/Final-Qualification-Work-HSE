"""
Repository-слой HR-уведомлений.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


class HRNotificationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    # =========================================================
    # ВСПОМОГАТЕЛЬНЫЕ СПРАВОЧНИКИ
    # =========================================================
    def get_active_hr_user_ids(self) -> list[int]:
        """
        Возвращает всех активных HR-пользователей.
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

    # =========================================================
    # УВЕДОМЛЕНИЯ ПО ИЗМЕНЕНИЯМ РЕЗЮМЕ
    # =========================================================
    def get_resume_change_notifications(self, hr_user_id: int):
        """
        Возвращает уведомления HR по заявкам на изменение резюме.
        """
        query = text(
            """
            SELECT
                nr.id AS queue_record_id,
                nr.status AS queue_status,
                nr.read_at AS queue_read_at,
                nr.created_at AS queue_created_at,

                n.id AS notification_id,
                n.title AS notification_title,
                n.message AS notification_message,
                n.priority AS notification_priority,
                n.created_at AS notification_created_at,

                rcr.id AS request_id,
                rcr.status AS request_status,
                rcr.change_description AS change_description,
                rcr.submitted_at AS submitted_at,

                rs.name AS section_name,

                u.id AS employee_user_id,
                CONCAT_WS(' ', u.last_name, u.first_name, u.middle_name) AS employee_full_name,

                (
                    SELECT ed.original_filename
                    FROM employee_documents ed
                    WHERE ed.source_entity_type = 'resume_change_request'
                      AND ed.source_entity_id = rcr.id
                    ORDER BY ed.id DESC
                    LIMIT 1
                ) AS attachment_original_filename,

                (
                    SELECT ed.file_path
                    FROM employee_documents ed
                    WHERE ed.source_entity_type = 'resume_change_request'
                      AND ed.source_entity_id = rcr.id
                    ORDER BY ed.id DESC
                    LIMIT 1
                ) AS attachment_file_path,

                (
                    SELECT ed.mime_type
                    FROM employee_documents ed
                    WHERE ed.source_entity_type = 'resume_change_request'
                      AND ed.source_entity_id = rcr.id
                    ORDER BY ed.id DESC
                    LIMIT 1
                ) AS attachment_mime_type,

                (
                    SELECT ed.file_size_bytes
                    FROM employee_documents ed
                    WHERE ed.source_entity_type = 'resume_change_request'
                      AND ed.source_entity_id = rcr.id
                    ORDER BY ed.id DESC
                    LIMIT 1
                ) AS attachment_size_bytes

            FROM notification_recipients nr
            INNER JOIN notifications n
                ON n.id = nr.notification_id
            INNER JOIN resume_change_requests rcr
                ON rcr.id = n.related_entity_id
               AND n.related_entity_type = 'resume_change_request'
            INNER JOIN resume_sections rs
                ON rs.id = rcr.section_id
            INNER JOIN users u
                ON u.id = rcr.employee_user_id
            WHERE nr.recipient_user_id = :hr_user_id
              AND n.notification_type = 'hr_resume_change_request'
            ORDER BY COALESCE(rcr.submitted_at, n.created_at) DESC, nr.id DESC
            """
        )
        return self.session.execute(query, {"hr_user_id": hr_user_id}).mappings().all()

    def get_resume_change_notification_by_queue_id(self, hr_user_id: int, queue_record_id: int):
        """
        Возвращает одно resume-уведомление по queue_record_id.
        """
        query = text(
            """
            SELECT
                nr.id AS queue_record_id,
                nr.status AS queue_status
            FROM notification_recipients nr
            INNER JOIN notifications n
                ON n.id = nr.notification_id
            WHERE nr.id = :queue_record_id
              AND nr.recipient_user_id = :hr_user_id
              AND n.notification_type = 'hr_resume_change_request'
            LIMIT 1
            """
        )
        return self.session.execute(
            query,
            {"hr_user_id": hr_user_id, "queue_record_id": queue_record_id},
        ).mappings().first()

    def mark_resume_change_notification_as_read(self, hr_user_id: int, queue_record_id: int) -> int:
        """
        Помечает resume-уведомление как прочитанное.
        """
        query = text(
            """
            UPDATE notification_recipients
            SET
                status = 'read',
                read_at = NOW()
            WHERE id = :queue_record_id
              AND recipient_user_id = :hr_user_id
              AND status = 'unread'
            """
        )
        result = self.session.execute(
            query,
            {"hr_user_id": hr_user_id, "queue_record_id": queue_record_id},
        )
        return int(result.rowcount or 0)

    def archive_resume_change_notification(self, hr_user_id: int, queue_record_id: int) -> int:
        """
        Переводит resume-уведомление в статус archived = обработано.
        """
        query = text(
            """
            UPDATE notification_recipients
            SET
                status = 'archived',
                read_at = COALESCE(read_at, NOW())
            WHERE id = :queue_record_id
              AND recipient_user_id = :hr_user_id
              AND status <> 'archived'
            """
        )
        result = self.session.execute(
            query,
            {"hr_user_id": hr_user_id, "queue_record_id": queue_record_id},
        )
        return int(result.rowcount or 0)

    # =========================================================
    # УВЕДОМЛЕНИЯ ПО ПОКУПКАМ БОНУСОВ
    # =========================================================
    def get_bonus_purchase_notifications(self, hr_user_id: int):
        """
        Возвращает HR-уведомления по покупкам бонусов.
        """
        query = text(
            """
            SELECT
                bpn.id AS queue_record_id,
                bpn.notification_status AS queue_status,
                bpn.read_at AS queue_read_at,
                bpn.created_at AS queue_created_at,

                bp.id AS purchase_id,
                bp.status AS purchase_status,
                bp.requested_at AS requested_at,
                bp.processed_at AS processed_at,
                bp.hr_comment AS hr_comment,
                bp.bonus_snapshot_name AS bonus_name,
                bp.bonus_snapshot_price_points AS bonus_cost_points,

                u.id AS employee_user_id,
                CONCAT_WS(' ', u.last_name, u.first_name, u.middle_name) AS employee_full_name,

                bpn.title AS notification_title,
                bpn.message AS notification_message
            FROM bonus_purchase_notifications bpn
            INNER JOIN bonus_purchases bp
                ON bp.id = bpn.bonus_purchase_id
            INNER JOIN users u
                ON u.id = bp.employee_user_id
            WHERE bpn.hr_user_id = :hr_user_id
            ORDER BY COALESCE(bp.requested_at, bpn.created_at) DESC, bpn.id DESC
            """
        )
        return self.session.execute(query, {"hr_user_id": hr_user_id}).mappings().all()

    def get_bonus_purchase_notification_by_queue_id(self, hr_user_id: int, queue_record_id: int):
        """
        Возвращает одно bonus-уведомление по queue_record_id.
        """
        query = text(
            """
            SELECT
                id AS queue_record_id,
                notification_status AS queue_status
            FROM bonus_purchase_notifications
            WHERE id = :queue_record_id
              AND hr_user_id = :hr_user_id
            LIMIT 1
            """
        )
        return self.session.execute(
            query,
            {"hr_user_id": hr_user_id, "queue_record_id": queue_record_id},
        ).mappings().first()

    def mark_bonus_purchase_notification_as_read(self, hr_user_id: int, queue_record_id: int) -> int:
        """
        Помечает bonus-уведомление как прочитанное.
        """
        query = text(
            """
            UPDATE bonus_purchase_notifications
            SET
                notification_status = 'read',
                read_at = NOW()
            WHERE id = :queue_record_id
              AND hr_user_id = :hr_user_id
              AND notification_status = 'unread'
            """
        )
        result = self.session.execute(
            query,
            {"hr_user_id": hr_user_id, "queue_record_id": queue_record_id},
        )
        return int(result.rowcount or 0)

    def archive_bonus_purchase_notification(self, hr_user_id: int, queue_record_id: int) -> int:
        """
        Переводит bonus-уведомление в статус archived = обработано.
        """
        query = text(
            """
            UPDATE bonus_purchase_notifications
            SET
                notification_status = 'archived',
                read_at = COALESCE(read_at, NOW())
            WHERE id = :queue_record_id
              AND hr_user_id = :hr_user_id
              AND notification_status <> 'archived'
            """
        )
        result = self.session.execute(
            query,
            {"hr_user_id": hr_user_id, "queue_record_id": queue_record_id},
        )
        return int(result.rowcount or 0)

    # =========================================================
    # HR-ОЧЕРЕДЬ ПО ИСТЕКАЮЩИМ КУРСАМ
    # =========================================================
    def get_expiring_qualification_courses_for_generation(self, days_before_expiry: int):
        """
        Возвращает курсы, срок действия которых истекает в ближайшие N дней.
        """
        query = text(
            """
            SELECT
                eqc.id AS qualification_course_id,
                eqc.employee_user_id AS employee_user_id,
                CONCAT_WS(' ', u.last_name, u.first_name, u.middle_name) AS employee_full_name,
                COALESCE(
                    qcc.name,
                    eqc.course_name_override,
                    CONCAT('Курс повышения квалификации #', eqc.id)
                ) AS course_name,
                eqc.valid_until AS valid_until,
                DATEDIFF(eqc.valid_until, CURDATE()) AS days_left
            FROM employee_qualification_courses eqc
            INNER JOIN users u
                ON u.id = eqc.employee_user_id
            LEFT JOIN qualification_courses_catalog qcc
                ON qcc.id = eqc.course_id
            WHERE eqc.status = 'completed'
              AND eqc.valid_until IS NOT NULL
              AND DATEDIFF(eqc.valid_until, CURDATE()) BETWEEN 0 AND :days_before_expiry
            ORDER BY eqc.valid_until ASC, eqc.id ASC
            """
        )
        return self.session.execute(
            query,
            {"days_before_expiry": days_before_expiry},
        ).mappings().all()

    def create_hr_course_expiry_notification_if_missing(
        self,
        qualification_course_id: int,
        hr_user_id: int,
        employee_user_id: int,
        title: str,
        message: str,
    ) -> bool:
        """
        Создаёт HR-уведомление по курсу, только если запись ещё не существует.
        """
        exists_query = text(
            """
            SELECT id
            FROM hr_course_expiry_notifications
            WHERE qualification_course_id = :qualification_course_id
              AND hr_user_id = :hr_user_id
            LIMIT 1
            """
        )
        exists_row = self.session.execute(
            exists_query,
            {
                "qualification_course_id": qualification_course_id,
                "hr_user_id": hr_user_id,
            },
        ).mappings().first()

        if exists_row:
            return False

        insert_query = text(
            """
            INSERT INTO hr_course_expiry_notifications (
                qualification_course_id,
                hr_user_id,
                employee_user_id,
                title,
                message,
                notification_status,
                reminder_sent_at,
                read_at,
                created_at,
                updated_at
            ) VALUES (
                :qualification_course_id,
                :hr_user_id,
                :employee_user_id,
                :title,
                :message,
                'unread',
                NULL,
                NULL,
                NOW(),
                NOW()
            )
            """
        )
        self.session.execute(
            insert_query,
            {
                "qualification_course_id": qualification_course_id,
                "hr_user_id": hr_user_id,
                "employee_user_id": employee_user_id,
                "title": title,
                "message": message,
            },
        )
        return True

    def get_course_expiry_notifications(self, hr_user_id: int):
        """
        Возвращает HR-уведомления по истекающим курсам.
        """
        query = text(
            """
            SELECT
                hcn.id AS queue_record_id,
                hcn.notification_status AS queue_status,
                hcn.read_at AS queue_read_at,
                hcn.created_at AS queue_created_at,
                hcn.reminder_sent_at AS reminder_sent_at,

                eqc.id AS qualification_course_id,
                eqc.valid_until AS valid_until,
                eqc.status AS qualification_status,

                COALESCE(
                    qcc.name,
                    eqc.course_name_override,
                    CONCAT('Курс повышения квалификации #', eqc.id)
                ) AS course_name,

                u.id AS employee_user_id,
                CONCAT_WS(' ', u.last_name, u.first_name, u.middle_name) AS employee_full_name,

                hcn.title AS notification_title,
                hcn.message AS notification_message
            FROM hr_course_expiry_notifications hcn
            INNER JOIN employee_qualification_courses eqc
                ON eqc.id = hcn.qualification_course_id
            INNER JOIN users u
                ON u.id = hcn.employee_user_id
            LEFT JOIN qualification_courses_catalog qcc
                ON qcc.id = eqc.course_id
            WHERE hcn.hr_user_id = :hr_user_id
            ORDER BY COALESCE(eqc.valid_until, CURDATE()) ASC, hcn.id DESC
            """
        )
        return self.session.execute(query, {"hr_user_id": hr_user_id}).mappings().all()

    def get_course_expiry_notification_by_queue_id(self, hr_user_id: int, queue_record_id: int):
        """
        Возвращает одно course-expiry уведомление.
        """
        query = text(
            """
            SELECT
                hcn.id AS queue_record_id,
                hcn.notification_status AS queue_status,
                hcn.reminder_sent_at AS reminder_sent_at,
                hcn.qualification_course_id AS qualification_course_id,
                hcn.employee_user_id AS employee_user_id,
                COALESCE(
                    qcc.name,
                    eqc.course_name_override,
                    CONCAT('Курс повышения квалификации #', eqc.id)
                ) AS course_name,
                eqc.valid_until AS valid_until
            FROM hr_course_expiry_notifications hcn
            INNER JOIN employee_qualification_courses eqc
                ON eqc.id = hcn.qualification_course_id
            LEFT JOIN qualification_courses_catalog qcc
                ON qcc.id = eqc.course_id
            WHERE hcn.id = :queue_record_id
              AND hcn.hr_user_id = :hr_user_id
            LIMIT 1
            """
        )
        return self.session.execute(
            query,
            {"hr_user_id": hr_user_id, "queue_record_id": queue_record_id},
        ).mappings().first()

    def mark_course_expiry_notification_as_read(self, hr_user_id: int, queue_record_id: int) -> int:
        """
        Помечает course-expiry уведомление как прочитанное.
        """
        query = text(
            """
            UPDATE hr_course_expiry_notifications
            SET
                notification_status = 'read',
                read_at = NOW()
            WHERE id = :queue_record_id
              AND hr_user_id = :hr_user_id
              AND notification_status = 'unread'
            """
        )
        result = self.session.execute(
            query,
            {"hr_user_id": hr_user_id, "queue_record_id": queue_record_id},
        )
        return int(result.rowcount or 0)

    def archive_course_expiry_notification(self, hr_user_id: int, queue_record_id: int) -> int:
        """
        Переводит course-expiry уведомление в статус archived = обработано.
        """
        query = text(
            """
            UPDATE hr_course_expiry_notifications
            SET
                notification_status = 'archived',
                read_at = COALESCE(read_at, NOW())
            WHERE id = :queue_record_id
              AND hr_user_id = :hr_user_id
              AND notification_status <> 'archived'
            """
        )
        result = self.session.execute(
            query,
            {"hr_user_id": hr_user_id, "queue_record_id": queue_record_id},
        )
        return int(result.rowcount or 0)

    def mark_course_employee_reminder_sent(self, hr_user_id: int, queue_record_id: int) -> int:
        """
        Фиксирует, что HR уже отправил сотруднику напоминание.
        """
        query = text(
            """
            UPDATE hr_course_expiry_notifications
            SET reminder_sent_at = NOW()
            WHERE id = :queue_record_id
              AND hr_user_id = :hr_user_id
              AND reminder_sent_at IS NULL
            """
        )
        result = self.session.execute(
            query,
            {"hr_user_id": hr_user_id, "queue_record_id": queue_record_id},
        )
        return int(result.rowcount or 0)

    # =========================================================
    # СОТРУДНИКУ НАПОМНИЛИ О КУРСЕ
    # =========================================================
    def employee_course_reminder_exists_today(
        self,
        employee_user_id: int,
        qualification_course_id: int,
    ) -> bool:
        """
        Проверяет, не отправлялось ли уже сегодня универсальное уведомление
        сотруднику по этому же курсу.
        """
        query = text(
            """
            SELECT n.id
            FROM notifications n
            INNER JOIN notification_recipients nr
                ON nr.notification_id = n.id
            WHERE n.notification_type = 'employee_course_reminder'
              AND n.related_entity_type = 'employee_qualification_courses'
              AND n.related_entity_id = :qualification_course_id
              AND nr.recipient_user_id = :employee_user_id
              AND DATE(n.created_at) = CURDATE()
            LIMIT 1
            """
        )
        row = self.session.execute(
            query,
            {
                "employee_user_id": employee_user_id,
                "qualification_course_id": qualification_course_id,
            },
        ).mappings().first()

        return row is not None

    def create_employee_course_reminder(
        self,
        hr_user_id: int,
        employee_user_id: int,
        qualification_course_id: int,
        title: str,
        message: str,
    ) -> int:
        """
        Создаёт универсальное уведомление сотруднику и привязывает получателя.
        """
        insert_notification_query = text(
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
                'employee_course_reminder',
                :title,
                :message,
                :hr_user_id,
                'employee_qualification_courses',
                :qualification_course_id,
                'critical',
                NOW(),
                NULL
            )
            """
        )
        self.session.execute(
            insert_notification_query,
            {
                "title": title,
                "message": message,
                "hr_user_id": hr_user_id,
                "qualification_course_id": qualification_course_id,
            },
        )

        notification_id = int(self.session.execute(text("SELECT LAST_INSERT_ID()")).scalar_one())

        insert_recipient_query = text(
            """
            INSERT INTO notification_recipients (
                notification_id,
                recipient_user_id,
                status,
                read_at,
                created_at
            ) VALUES (
                :notification_id,
                :employee_user_id,
                'unread',
                NULL,
                NOW()
            )
            """
        )
        self.session.execute(
            insert_recipient_query,
            {
                "notification_id": notification_id,
                "employee_user_id": employee_user_id,
            },
        )

        return notification_id