"""
Repository-слой магазина бонусов.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


class StoreRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    # =========================================================
    # Каталог бонусов
    # =========================================================
    def get_active_bonus_catalog(self):
        query = text(
            """
            SELECT
                id,
                code,
                name,
                description,
                price_points,
                icon,
                level_label,
                sort_order,
                is_active
            FROM bonus_catalog
            WHERE is_active = TRUE
            ORDER BY price_points ASC, sort_order ASC, id ASC
            """
        )
        return self.session.execute(query).mappings().all()

    def get_active_bonus_by_id(self, bonus_id: int):
        query = text(
            """
            SELECT
                id,
                code,
                name,
                description,
                price_points,
                icon,
                level_label,
                sort_order,
                is_active
            FROM bonus_catalog
            WHERE id = :bonus_id
              AND is_active = TRUE
            LIMIT 1
            """
        )
        return self.session.execute(query, {"bonus_id": bonus_id}).mappings().first()

    # =========================================================
    # Баланс сотрудника
    # =========================================================
    def get_employee_points_balance(self, employee_user_id: int) -> int:
        query = text(
            """
            SELECT points_balance
            FROM employee_profiles
            WHERE user_id = :employee_user_id
            LIMIT 1
            """
        )
        row = self.session.execute(query, {"employee_user_id": employee_user_id}).mappings().first()
        return int(row["points_balance"]) if row and row["points_balance"] is not None else 0

    def get_employee_points_balance_for_update(self, employee_user_id: int) -> int | None:
        query = text(
            """
            SELECT points_balance
            FROM employee_profiles
            WHERE user_id = :employee_user_id
            LIMIT 1
            FOR UPDATE
            """
        )
        row = self.session.execute(query, {"employee_user_id": employee_user_id}).mappings().first()
        if not row:
            return None
        return int(row["points_balance"]) if row["points_balance"] is not None else 0

    def sync_employee_points_balance(self, employee_user_id: int) -> None:
        query = text(
            """
            UPDATE employee_profiles
            SET points_balance = COALESCE((
                SELECT SUM(points_delta)
                FROM employee_point_transactions
                WHERE employee_user_id = :employee_user_id
            ), 0)
            WHERE user_id = :employee_user_id
            """
        )
        self.session.execute(query, {"employee_user_id": employee_user_id})

    # =========================================================
    # Покупки
    # =========================================================
    def get_bonus_purchase_by_token(self, purchase_token: str):
        query = text(
            """
            SELECT
                id,
                employee_user_id,
                bonus_id,
                status
            FROM bonus_purchases
            WHERE purchase_token = :purchase_token
            LIMIT 1
            """
        )
        return self.session.execute(query, {"purchase_token": purchase_token}).mappings().first()

    def create_bonus_purchase(
        self,
        employee_user_id: int,
        bonus_id: int,
        purchase_token: str,
        bonus_snapshot_name: str,
        bonus_snapshot_price_points: int,
    ) -> int:
        query = text(
            """
            INSERT INTO bonus_purchases (
                employee_user_id,
                bonus_id,
                purchase_token,
                bonus_snapshot_name,
                bonus_snapshot_price_points,
                status,
                requested_at
            ) VALUES (
                :employee_user_id,
                :bonus_id,
                :purchase_token,
                :bonus_snapshot_name,
                :bonus_snapshot_price_points,
                'pending_hr',
                NOW()
            )
            """
        )

        result = self.session.execute(
            query,
            {
                "employee_user_id": employee_user_id,
                "bonus_id": bonus_id,
                "purchase_token": purchase_token,
                "bonus_snapshot_name": bonus_snapshot_name,
                "bonus_snapshot_price_points": bonus_snapshot_price_points,
            },
        )

        return int(result.lastrowid)

    def create_store_purchase_points_transaction(
        self,
        employee_user_id: int,
        bonus_purchase_id: int,
        points_to_spend: int,
        bonus_name: str,
    ) -> None:
        query = text(
            """
            INSERT INTO employee_point_transactions (
                employee_user_id,
                transaction_type,
                points_delta,
                source_entity_type,
                source_entity_id,
                comment
            ) VALUES (
                :employee_user_id,
                'store_purchase',
                :points_delta,
                'bonus_purchase',
                :bonus_purchase_id,
                :comment
            )
            """
        )

        self.session.execute(
            query,
            {
                "employee_user_id": employee_user_id,
                "points_delta": -abs(points_to_spend),
                "bonus_purchase_id": bonus_purchase_id,
                "comment": f"Списание баллов за бонус: {bonus_name}",
            },
        )

    # =========================================================
    # HR-уведомления
    # =========================================================
    def get_active_hr_user_ids(self) -> list[int]:
        query = text(
            """
            SELECT u.id
            FROM users u
            INNER JOIN roles r
                ON r.id = u.role_id
            WHERE r.code = 'HR_MANAGER'
              AND u.is_active = 1
            ORDER BY u.id ASC
            """
        )

        rows = self.session.execute(query).mappings().all()
        return [int(row["id"]) for row in rows]

    def get_user_display_name(self, user_id: int) -> str:
        query = text(
            """
            SELECT CONCAT_WS(' ', last_name, first_name, middle_name) AS full_name
            FROM users
            WHERE id = :user_id
            LIMIT 1
            """
        )
        row = self.session.execute(query, {"user_id": user_id}).mappings().first()
        return str(row["full_name"]) if row and row["full_name"] else f"Пользователь #{user_id}"

    def create_bonus_purchase_notifications(
        self,
        bonus_purchase_id: int,
        employee_user_id: int,
        title: str,
        message: str,
    ) -> None:
        """
        Создаём по одному уведомлению для каждого активного HR.
        """
        hr_user_ids = self.get_active_hr_user_ids()

        if not hr_user_ids:
            return

        query = text(
            """
            INSERT INTO bonus_purchase_notifications (
                bonus_purchase_id,
                hr_user_id,
                employee_user_id,
                title,
                message,
                notification_status,
                created_at
            ) VALUES (
                :bonus_purchase_id,
                :hr_user_id,
                :employee_user_id,
                :title,
                :message,
                'unread',
                NOW()
            )
            """
        )

        for hr_user_id in hr_user_ids:
            self.session.execute(
                query,
                {
                    "bonus_purchase_id": bonus_purchase_id,
                    "hr_user_id": hr_user_id,
                    "employee_user_id": employee_user_id,
                    "title": title,
                    "message": message,
                },
            )