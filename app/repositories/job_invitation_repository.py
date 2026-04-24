from __future__ import annotations

from typing import Any

from mysql.connector import errors as mysql_errors

from app.db.mysql_connection import get_connection
from app.models.candidate_search_models import JobInvitationCommand


class JobInvitationRepository:
    """
    Репозиторий приглашений сотрудникам по результатам HR-подбора.
    """

    # =========================================================
    # Общие helpers
    # =========================================================
    def _table_exists(self, connection, table_name: str) -> bool:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                  AND table_name = %s
                """,
                (table_name,),
            )
            return int(cursor.fetchone()[0]) > 0
        finally:
            cursor.close()

    def _get_columns(self, connection, table_name: str) -> set[str]:
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                  AND table_name = %s
                """,
                (table_name,),
            )
            rows = cursor.fetchall() or []
            return {str(row[0]) for row in rows}
        finally:
            cursor.close()

    def _pick_first_existing(self, columns: set[str], candidates: tuple[str, ...]) -> str | None:
        for candidate in candidates:
            if candidate in columns:
                return candidate
        return None

    def _safe_attr(self, obj: Any, attr_name: str, default: Any = None) -> Any:
        return getattr(obj, attr_name, default)

    # =========================================================
    # job_openings
    # =========================================================
    def _find_existing_opening_id(self, connection, command: JobInvitationCommand) -> int | None:
        if not self._table_exists(connection, "job_openings"):
            return None

        columns = self._get_columns(connection, "job_openings")

        title_col = self._pick_first_existing(columns, ("title", "position_title", "name"))
        requirements_col = self._pick_first_existing(columns, ("requirements_text", "requirements", "description"))
        created_by_col = self._pick_first_existing(columns, ("created_by_hr_user_id", "hr_user_id", "created_by"))
        status_col = self._pick_first_existing(columns, ("status",))

        if not title_col or not requirements_col or not created_by_col:
            return None

        where_parts = [
            f"{created_by_col} = %s",
            f"{title_col} = %s",
            f"{requirements_col} = %s",
        ]
        params: list[Any] = [
            int(command.hr_user_id),
            (self._safe_attr(command, "position_title", None) or "Внутренняя вакансия").strip(),
            (self._safe_attr(command, "requirements_text", None) or "").strip(),
        ]

        if status_col:
            where_parts.append(f"{status_col} IN ('draft', 'open')")

        query = f"""
            SELECT id
            FROM job_openings
            WHERE {" AND ".join(where_parts)}
            ORDER BY id DESC
            LIMIT 1
        """

        cursor = connection.cursor()
        try:
            cursor.execute(query, tuple(params))
            row = cursor.fetchone()
            return int(row[0]) if row else None
        finally:
            cursor.close()

    def _create_opening(self, connection, command: JobInvitationCommand) -> int:
        if not self._table_exists(connection, "job_openings"):
            raise RuntimeError(
                "В БД отсутствует таблица job_openings. "
                "Примените stage9_hr_rating_table_migration.sql."
            )

        columns = self._get_columns(connection, "job_openings")

        title_col = self._pick_first_existing(columns, ("title",))
        requirements_col = self._pick_first_existing(columns, ("requirements_text",))
        created_by_col = self._pick_first_existing(columns, ("created_by_hr_user_id",))
        responsibilities_col = self._pick_first_existing(columns, ("responsibilities_text",))
        location_col = self._pick_first_existing(columns, ("location_text",))
        employment_type_col = self._pick_first_existing(columns, ("employment_type",))
        status_col = self._pick_first_existing(columns, ("status",))
        published_at_col = self._pick_first_existing(columns, ("published_at",))
        created_at_col = self._pick_first_existing(columns, ("created_at",))
        updated_at_col = self._pick_first_existing(columns, ("updated_at",))

        column_names: list[str] = []
        value_fragments: list[str] = []
        params: list[Any] = []

        def add_value(column_name: str | None, value: Any):
            if column_name is None:
                return
            column_names.append(column_name)
            value_fragments.append("%s")
            params.append(value)

        def add_now(column_name: str | None):
            if column_name is None:
                return
            column_names.append(column_name)
            value_fragments.append("NOW()")

        position_title = (self._safe_attr(command, "position_title", None) or "Внутренняя вакансия").strip()
        requirements_text = (self._safe_attr(command, "requirements_text", None) or "").strip()

        add_value(title_col, position_title)
        add_value(requirements_col, requirements_text)
        add_value(created_by_col, int(command.hr_user_id))
        add_value(
            responsibilities_col,
            "Ad-hoc вакансия, автоматически созданная из сценария внутреннего HR-подбора.",
        )
        add_value(location_col, "Не указано")
        add_value(employment_type_col, "office")
        add_value(status_col, "open")
        add_now(published_at_col)
        add_now(created_at_col)
        add_now(updated_at_col)

        if not title_col or not requirements_col or not created_by_col:
            raise RuntimeError(
                "Не удалось определить обязательные колонки таблицы job_openings "
                "(title, requirements_text, created_by_hr_user_id)."
            )

        query = f"""
            INSERT INTO job_openings (
                {", ".join(column_names)}
            )
            VALUES (
                {", ".join(value_fragments)}
            )
        """

        cursor = connection.cursor()
        try:
            cursor.execute(query, tuple(params))
            return int(cursor.lastrowid)
        finally:
            cursor.close()

    def _resolve_opening_id(self, connection, command: JobInvitationCommand) -> int:
        existing_opening_id = self._find_existing_opening_id(connection, command)
        if existing_opening_id is not None:
            return existing_opening_id
        return self._create_opening(connection, command)

    # =========================================================
    # job_invitations
    # =========================================================
    def _find_existing_invitation_id(
        self,
        connection,
        opening_id: int,
        employee_user_id: int,
    ) -> int | None:
        """
        Ищет уже существующее приглашение по уникальной паре
        """
        if not self._table_exists(connection, "job_invitations"):
            return None

        query = """
            SELECT id
            FROM job_invitations
            WHERE opening_id = %s
              AND employee_user_id = %s
            LIMIT 1
        """

        cursor = connection.cursor()
        try:
            cursor.execute(query, (opening_id, employee_user_id))
            row = cursor.fetchone()
            return int(row[0]) if row else None
        finally:
            cursor.close()

    def create_job_invitation(self, command: JobInvitationCommand) -> tuple[int, bool]:
        """
        Создаёт запись приглашения и возвращает:
        - invitation_id
        - created_new
        """
        with get_connection() as connection:
            if not self._table_exists(connection, "job_invitations"):
                raise RuntimeError(
                    "В БД отсутствует таблица job_invitations. "
                    "Нужно применить миграцию stage 9 для приглашений."
                )

            opening_id = self._resolve_opening_id(connection, command)

            existing_invitation_id = self._find_existing_invitation_id(
                connection=connection,
                opening_id=opening_id,
                employee_user_id=int(command.employee_user_id),
            )
            if existing_invitation_id is not None:
                return existing_invitation_id, False

            columns = self._get_columns(connection, "job_invitations")

            opening_id_col = self._pick_first_existing(columns, ("opening_id",))
            hr_user_id_col = self._pick_first_existing(columns, ("hr_user_id",))
            employee_user_id_col = self._pick_first_existing(columns, ("employee_user_id",))
            anonymous_code_col = self._pick_first_existing(columns, ("anonymous_code_snapshot", "anonymous_code"))
            position_title_col = self._pick_first_existing(
                columns,
                ("position_title", "vacancy_title", "target_position", "role_title"),
            )
            requirements_col = self._pick_first_existing(columns, ("requirements_text",))
            comment_col = self._pick_first_existing(columns, ("comment_text", "hr_comment", "comment", "message_text"))
            status_col = self._pick_first_existing(columns, ("invitation_status", "status"))
            sent_at_col = self._pick_first_existing(columns, ("sent_at", "created_at"))

            column_names: list[str] = []
            value_fragments: list[str] = []
            params: list[Any] = []

            def add_value(column_name: str | None, value: Any):
                if column_name is None:
                    return
                column_names.append(column_name)
                value_fragments.append("%s")
                params.append(value)

            def add_now(column_name: str | None):
                if column_name is None:
                    return
                column_names.append(column_name)
                value_fragments.append("NOW()")

            add_value(opening_id_col, opening_id)
            add_value(hr_user_id_col, int(command.hr_user_id))
            add_value(employee_user_id_col, int(command.employee_user_id))
            add_value(anonymous_code_col, self._safe_attr(command, "anonymous_code"))
            add_value(
                position_title_col,
                self._safe_attr(command, "position_title", None) or "Внутренняя вакансия",
            )
            add_value(requirements_col, self._safe_attr(command, "requirements_text"))
            add_value(comment_col, self._safe_attr(command, "comment_text"))
            add_value(status_col, "sent")
            add_now(sent_at_col)

            if not opening_id_col or not hr_user_id_col or not employee_user_id_col:
                raise RuntimeError(
                    "Не удалось определить обязательные колонки таблицы job_invitations "
                    "(opening_id, hr_user_id, employee_user_id)."
                )

            query = f"""
                INSERT INTO job_invitations (
                    {", ".join(column_names)}
                )
                VALUES (
                    {", ".join(value_fragments)}
                )
            """

            cursor = connection.cursor()
            try:
                try:
                    cursor.execute(query, tuple(params))
                    invitation_id = int(cursor.lastrowid)
                    connection.commit()
                    return invitation_id, True
                except mysql_errors.IntegrityError:
                    connection.rollback()
                    existing_invitation_id = self._find_existing_invitation_id(
                        connection=connection,
                        opening_id=opening_id,
                        employee_user_id=int(command.employee_user_id),
                    )
                    if existing_invitation_id is not None:
                        return existing_invitation_id, False
                    raise
            finally:
                cursor.close()

    # =========================================================
    # employee_notifications
    # =========================================================
    def create_employee_notification_if_missing(
        self,
        employee_user_id: int,
        title: str,
        message: str,
        related_entity_id: int,
    ) -> bool:
        """
        Создаёт уведомление сотруднику, только если оно ещё не существует
        для выбранного invitation_id.
        """
        with get_connection() as connection:
            if not self._table_exists(connection, "employee_notifications"):
                raise RuntimeError("В БД отсутствует таблица employee_notifications.")

            columns = self._get_columns(connection, "employee_notifications")

            employee_user_id_col = self._pick_first_existing(columns, ("employee_user_id",))
            notification_type_col = self._pick_first_existing(columns, ("notification_type", "type"))
            notification_key_col = self._pick_first_existing(columns, ("notification_key",))
            title_col = self._pick_first_existing(columns, ("title",))
            message_col = self._pick_first_existing(columns, ("message", "text"))
            status_col = self._pick_first_existing(columns, ("notification_status", "status"))
            created_at_col = self._pick_first_existing(columns, ("created_at",))
            related_type_col = self._pick_first_existing(columns, ("related_entity_type", "related_type"))
            related_id_col = self._pick_first_existing(columns, ("related_entity_id", "entity_id"))
            expires_at_col = self._pick_first_existing(columns, ("expires_at",))

            notification_key = f"job_invitation:{int(related_entity_id)}"

            if notification_key_col:
                exists_query = f"""
                    SELECT 1
                    FROM employee_notifications
                    WHERE {employee_user_id_col} = %s
                      AND {notification_key_col} = %s
                    LIMIT 1
                """
                cursor = connection.cursor()
                try:
                    cursor.execute(exists_query, (int(employee_user_id), notification_key))
                    row = cursor.fetchone()
                    if row:
                        return False
                finally:
                    cursor.close()

            column_names: list[str] = []
            value_fragments: list[str] = []
            params: list[Any] = []

            def add_value(column_name: str | None, value: Any):
                if column_name is None:
                    return
                column_names.append(column_name)
                value_fragments.append("%s")
                params.append(value)

            def add_now(column_name: str | None):
                if column_name is None:
                    return
                column_names.append(column_name)
                value_fragments.append("NOW()")

            add_value(employee_user_id_col, int(employee_user_id))
            add_value(notification_type_col, "job_invitation")
            add_value(notification_key_col, notification_key)
            add_value(title_col, title)
            add_value(message_col, message)
            add_value(status_col, "new")
            add_value(related_type_col, "job_invitation")
            add_value(related_id_col, int(related_entity_id))
            add_value(expires_at_col, None)
            add_now(created_at_col)

            if not employee_user_id_col or not notification_type_col or not title_col or not message_col:
                raise RuntimeError(
                    "Не удалось определить обязательные колонки для вставки в employee_notifications."
                )

            query = f"""
                INSERT INTO employee_notifications (
                    {", ".join(column_names)}
                )
                VALUES (
                    {", ".join(value_fragments)}
                )
            """

            cursor = connection.cursor()
            try:
                cursor.execute(query, tuple(params))
                connection.commit()
                return True
            finally:
                cursor.close()

    def create_employee_notification(
        self,
        employee_user_id: int,
        title: str,
        message: str,
        related_entity_id: int,
    ) -> None:
        self.create_employee_notification_if_missing(
            employee_user_id=employee_user_id,
            title=title,
            message=message,
            related_entity_id=related_entity_id,
        )
