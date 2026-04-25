from __future__ import annotations

"""
Репозиторий приглашений сотрудникам по результатам HR-подбора.
"""

import re
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models.candidate_search_models import JobInvitationCommand


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class JobInvitationRepository:
    """
    Репозиторий приглашений сотрудникам по результатам HR-подбора.
    """

    # =========================================================
    # Общие helpers
    # =========================================================
    def _quote_identifier(self, name: str) -> str:
        """
        Безопасно экранирует имя таблицы/колонки.
        """
        if not _IDENTIFIER_RE.match(name):
            raise ValueError(f"Некорректный SQL identifier: {name}")
        return f"`{name}`"

    def _table_exists(self, session: Session, table_name: str) -> bool:
        """
        Проверяет, существует ли таблица в текущей БД.
        """
        query = text(
            """
            SELECT COUNT(*) AS total_count
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name = :table_name
            """
        )

        row = session.execute(
            query,
            {"table_name": table_name},
        ).mappings().first()

        if not row:
            return False

        row_dict = dict(row)

        value = (
            row_dict.get("total_count")
            or row_dict.get("TOTAL_COUNT")
            or row_dict.get("Total_count")
            or row_dict.get("COUNT(*)")
        )

        if value is None and row_dict:
            value = next(iter(row_dict.values()))

        return int(value or 0) > 0

    def _get_columns(self, session: Session, table_name: str) -> set[str]:
        """
        Возвращает множество имён колонок таблицы.
        """
        query = text(
            """
            SELECT column_name AS column_name
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
            AND table_name = :table_name
            """
        )

        rows = session.execute(
            query,
            {"table_name": table_name},
        ).mappings().all()

        columns: set[str] = set()

        for row in rows:
            row_dict = dict(row)

            value = (
                row_dict.get("column_name")
                or row_dict.get("COLUMN_NAME")
                or row_dict.get("Column_name")
            )

            if value is None and row_dict:
                value = next(iter(row_dict.values()))

            if value is not None:
                columns.add(str(value))

        return columns

    def _pick_first_existing(self, columns: set[str], candidates: tuple[str, ...]) -> str | None:
        for candidate in candidates:
            if candidate in columns:
                return candidate
        return None

    def _safe_attr(self, obj: Any, attr_name: str, default: Any = None) -> Any:
        return getattr(obj, attr_name, default)

    def _last_insert_id(self, session: Session, result: Any) -> int:
        """
        Получает id последней вставленной записи.
        """
        lastrowid = getattr(result, "lastrowid", None)

        if lastrowid:
            return int(lastrowid)

        return int(session.execute(text("SELECT LAST_INSERT_ID()")).scalar_one())

    def _insert_dynamic(
        self,
        session: Session,
        table_name: str,
        values: dict[str, Any],
        now_columns: list[str] | None = None,
    ) -> int:
        """
        Выполняет INSERT с динамическим набором колонок.
        """
        now_columns = now_columns or []

        column_names = list(values.keys()) + now_columns
        value_fragments = [f":{column_name}" for column_name in values.keys()]
        value_fragments.extend(["NOW()" for _ in now_columns])

        if not column_names:
            raise RuntimeError(f"Не переданы колонки для вставки в {table_name}.")

        query = text(
            f"""
            INSERT INTO {self._quote_identifier(table_name)} (
                {", ".join(self._quote_identifier(column_name) for column_name in column_names)}
            )
            VALUES (
                {", ".join(value_fragments)}
            )
            """
        )

        result = session.execute(query, values)
        return self._last_insert_id(session, result)

    # =========================================================
    # job_openings
    # =========================================================
    def _find_existing_opening_id(self, session: Session, command: JobInvitationCommand) -> int | None:
        """
        Ищет уже существующую вакансию HR по названию и требованиям.
        """
        if not self._table_exists(session, "job_openings"):
            return None

        columns = self._get_columns(session, "job_openings")

        title_col = self._pick_first_existing(columns, ("title", "position_title", "name"))
        requirements_col = self._pick_first_existing(columns, ("requirements_text", "requirements", "description"))
        created_by_col = self._pick_first_existing(columns, ("created_by_hr_user_id", "hr_user_id", "created_by"))
        status_col = self._pick_first_existing(columns, ("status",))

        if not title_col or not requirements_col or not created_by_col:
            return None

        position_title = (
            self._safe_attr(command, "position_title", None)
            or "Внутренняя вакансия"
        ).strip()

        requirements_text = (
            self._safe_attr(command, "requirements_text", None)
            or ""
        ).strip()

        where_parts = [
            f"{self._quote_identifier(created_by_col)} = :created_by_hr_user_id",
            f"{self._quote_identifier(title_col)} = :position_title",
            f"{self._quote_identifier(requirements_col)} = :requirements_text",
        ]

        params: dict[str, Any] = {
            "created_by_hr_user_id": int(command.hr_user_id),
            "position_title": position_title,
            "requirements_text": requirements_text,
        }

        if status_col:
            where_parts.append(f"{self._quote_identifier(status_col)} IN ('draft', 'open')")

        query = text(
            f"""
            SELECT id
            FROM job_openings
            WHERE {" AND ".join(where_parts)}
            ORDER BY id DESC
            LIMIT 1
            """
        )

        row = session.execute(query, params).mappings().first()
        return int(row["id"]) if row else None

    def _create_opening(self, session: Session, command: JobInvitationCommand) -> int:
        """
        Создаёт ad-hoc вакансию для сценария внутреннего HR-подбора.
        """
        if not self._table_exists(session, "job_openings"):
            raise RuntimeError(
                "В БД отсутствует таблица job_openings. "
                "Примените stage9_hr_rating_table_migration.sql."
            )

        columns = self._get_columns(session, "job_openings")

        title_col = self._pick_first_existing(columns, ("title", "position_title", "name"))
        requirements_col = self._pick_first_existing(columns, ("requirements_text", "requirements", "description"))
        created_by_col = self._pick_first_existing(columns, ("created_by_hr_user_id", "hr_user_id", "created_by"))

        responsibilities_col = self._pick_first_existing(columns, ("responsibilities_text", "responsibilities"))
        location_col = self._pick_first_existing(columns, ("location_text", "location"))
        employment_type_col = self._pick_first_existing(columns, ("employment_type",))
        status_col = self._pick_first_existing(columns, ("status",))
        published_at_col = self._pick_first_existing(columns, ("published_at",))
        created_at_col = self._pick_first_existing(columns, ("created_at",))
        updated_at_col = self._pick_first_existing(columns, ("updated_at",))

        if not title_col or not requirements_col or not created_by_col:
            raise RuntimeError(
                "Не удалось определить обязательные колонки таблицы job_openings "
                "(title/position_title/name, requirements_text/requirements/description, "
                "created_by_hr_user_id/hr_user_id/created_by)."
            )

        position_title = (
            self._safe_attr(command, "position_title", None)
            or "Внутренняя вакансия"
        ).strip()

        requirements_text = (
            self._safe_attr(command, "requirements_text", None)
            or ""
        ).strip()

        values: dict[str, Any] = {}
        now_columns: list[str] = []

        def add_value(column_name: str | None, value: Any) -> None:
            if column_name is None:
                return
            values[column_name] = value

        def add_now(column_name: str | None) -> None:
            if column_name is None:
                return
            if column_name not in now_columns:
                now_columns.append(column_name)

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

        return self._insert_dynamic(
            session=session,
            table_name="job_openings",
            values=values,
            now_columns=now_columns,
        )

    def _resolve_opening_id(self, session: Session, command: JobInvitationCommand) -> int:
        existing_opening_id = self._find_existing_opening_id(session, command)
        if existing_opening_id is not None:
            return existing_opening_id

        return self._create_opening(session, command)

    # =========================================================
    # job_invitations
    # =========================================================
    def _find_existing_invitation_id(
        self,
        session: Session,
        opening_id: int,
        employee_user_id: int,
    ) -> int | None:
        """
        Ищет уже существующее приглашение по паре opening_id + employee_user_id.
        """
        if not self._table_exists(session, "job_invitations"):
            return None

        columns = self._get_columns(session, "job_invitations")

        if "opening_id" not in columns or "employee_user_id" not in columns:
            return None

        query = text(
            """
            SELECT id
            FROM job_invitations
            WHERE opening_id = :opening_id
              AND employee_user_id = :employee_user_id
            LIMIT 1
            """
        )

        row = session.execute(
            query,
            {
                "opening_id": int(opening_id),
                "employee_user_id": int(employee_user_id),
            },
        ).mappings().first()

        return int(row["id"]) if row else None

    def create_job_invitation(self, command: JobInvitationCommand) -> tuple[int, bool]:
        """
        Создаёт запись приглашения и возвращает:
        - invitation_id;
        - created_new.
        """
        with get_db_session() as session:
            if not self._table_exists(session, "job_invitations"):
                raise RuntimeError(
                    "В БД отсутствует таблица job_invitations. "
                    "Нужно применить миграцию stage 9 для приглашений."
                )

            opening_id = self._resolve_opening_id(session, command)

            existing_invitation_id = self._find_existing_invitation_id(
                session=session,
                opening_id=opening_id,
                employee_user_id=int(command.employee_user_id),
            )

            if existing_invitation_id is not None:
                return existing_invitation_id, False

            columns = self._get_columns(session, "job_invitations")

            opening_id_col = self._pick_first_existing(columns, ("opening_id",))
            hr_user_id_col = self._pick_first_existing(columns, ("hr_user_id",))
            employee_user_id_col = self._pick_first_existing(columns, ("employee_user_id",))

            anonymous_code_col = self._pick_first_existing(
                columns,
                ("anonymous_code_snapshot", "anonymous_code"),
            )
            position_title_col = self._pick_first_existing(
                columns,
                ("position_title", "vacancy_title", "target_position", "role_title"),
            )
            requirements_col = self._pick_first_existing(
                columns,
                ("requirements_text", "requirements", "description"),
            )
            comment_col = self._pick_first_existing(
                columns,
                ("comment_text", "hr_comment", "comment", "message_text"),
            )
            status_col = self._pick_first_existing(
                columns,
                ("invitation_status", "status"),
            )
            sent_at_col = self._pick_first_existing(
                columns,
                ("sent_at", "created_at"),
            )
            updated_at_col = self._pick_first_existing(columns, ("updated_at",))

            if not opening_id_col or not hr_user_id_col or not employee_user_id_col:
                raise RuntimeError(
                    "Не удалось определить обязательные колонки таблицы job_invitations "
                    "(opening_id, hr_user_id, employee_user_id)."
                )

            values: dict[str, Any] = {}
            now_columns: list[str] = []

            def add_value(column_name: str | None, value: Any) -> None:
                if column_name is None:
                    return
                values[column_name] = value

            def add_now(column_name: str | None) -> None:
                if column_name is None:
                    return
                if column_name not in now_columns:
                    now_columns.append(column_name)

            add_value(opening_id_col, int(opening_id))
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
            add_now(updated_at_col)

            try:
                invitation_id = self._insert_dynamic(
                    session=session,
                    table_name="job_invitations",
                    values=values,
                    now_columns=now_columns,
                )
                return invitation_id, True

            except IntegrityError:
                session.rollback()

                existing_invitation_id = self._find_existing_invitation_id(
                    session=session,
                    opening_id=opening_id,
                    employee_user_id=int(command.employee_user_id),
                )

                if existing_invitation_id is not None:
                    return existing_invitation_id, False

                raise

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
        Создаёт уведомление сотруднику, только если оно ещё не существует для выбранного invitation_id.
        """
        with get_db_session() as session:
            if not self._table_exists(session, "employee_notifications"):
                raise RuntimeError("В БД отсутствует таблица employee_notifications.")

            columns = self._get_columns(session, "employee_notifications")

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

            if not employee_user_id_col or not notification_type_col or not title_col or not message_col:
                raise RuntimeError(
                    "Не удалось определить обязательные колонки для вставки в employee_notifications "
                    "(employee_user_id, notification_type/type, title, message/text)."
                )

            notification_key = f"job_invitation:{int(related_entity_id)}"

            if notification_key_col:
                exists_query = text(
                    f"""
                    SELECT 1
                    FROM employee_notifications
                    WHERE {self._quote_identifier(employee_user_id_col)} = :employee_user_id
                      AND {self._quote_identifier(notification_key_col)} = :notification_key
                    LIMIT 1
                    """
                )

                exists_row = session.execute(
                    exists_query,
                    {
                        "employee_user_id": int(employee_user_id),
                        "notification_key": notification_key,
                    },
                ).first()

                if exists_row:
                    return False

            values: dict[str, Any] = {}
            now_columns: list[str] = []

            def add_value(column_name: str | None, value: Any) -> None:
                if column_name is None:
                    return
                values[column_name] = value

            def add_now(column_name: str | None) -> None:
                if column_name is None:
                    return
                if column_name not in now_columns:
                    now_columns.append(column_name)

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

            self._insert_dynamic(
                session=session,
                table_name="employee_notifications",
                values=values,
                now_columns=now_columns,
            )

            return True

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