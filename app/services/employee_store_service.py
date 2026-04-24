"""
Service-слой магазина бонусов.
"""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.db.session import get_db_session
from app.models.store_models import (
    EmployeeStoreDashboardViewModel,
    PurchaseBonusResult,
    StoreBonusCardViewModel,
)
from app.repositories.store_repository import StoreRepository


class EmployeeStoreService:
    def get_dashboard(self, employee_user_id: int) -> EmployeeStoreDashboardViewModel:
        """
        Загружает витрину магазина и текущий баланс сотрудника.
        """
        if not employee_user_id:
            return EmployeeStoreDashboardViewModel(
                points_balance=0,
                items=[],
                db_available=False,
                load_error_message="Сотрудник не определён.",
            )

        try:
            with get_db_session() as session:
                repo = StoreRepository(session)

                points_balance = repo.get_employee_points_balance(employee_user_id)
                bonus_rows = repo.get_active_bonus_catalog()

                items = [
                    StoreBonusCardViewModel(
                        bonus_id=int(row["id"]),
                        code=str(row["code"]),
                        title=str(row["name"]),
                        description=str(row["description"]),
                        cost_points=int(row["price_points"]),
                        icon=str(row["icon"] or "🎁"),
                        level_label=str(row["level_label"]),
                        is_affordable=points_balance >= int(row["price_points"]),
                    )
                    for row in bonus_rows
                ]

                return EmployeeStoreDashboardViewModel(
                    points_balance=points_balance,
                    items=items,
                    db_available=True,
                    load_error_message=None,
                )

        except SQLAlchemyError:
            return EmployeeStoreDashboardViewModel(
                points_balance=0,
                items=[],
                db_available=False,
                load_error_message="База данных недоступна. Каталог магазина сейчас не удалось загрузить.",
            )

    def purchase_bonus(
        self,
        employee_user_id: int,
        bonus_id: int,
        purchase_token: str,
        expected_points_snapshot: int | None,
    ) -> PurchaseBonusResult:
        """
        Выполняет покупку бонуса.
        """
        if not purchase_token:
            return PurchaseBonusResult(
                success=False,
                message="Не удалось подтвердить покупку: отсутствует токен операции.",
            )

        try:
            with get_db_session() as session:
                repo = StoreRepository(session)

                existing_purchase = repo.get_bonus_purchase_by_token(purchase_token)
                if existing_purchase:
                    updated_points = repo.get_employee_points_balance(employee_user_id)
                    return PurchaseBonusResult(
                        success=True,
                        message="Покупка уже была зарегистрирована ранее. Повторное списание баллов предотвращено.",
                        updated_points_balance=updated_points,
                        already_processed=True,
                    )

                bonus_row = repo.get_active_bonus_by_id(bonus_id)
                if not bonus_row:
                    return PurchaseBonusResult(
                        success=False,
                        message="Выбранный бонус не найден или больше недоступен.",
                    )

                current_points = repo.get_employee_points_balance_for_update(employee_user_id)
                if current_points is None:
                    return PurchaseBonusResult(
                        success=False,
                        message="Профиль сотрудника не найден. Покупка не выполнена.",
                    )

                if expected_points_snapshot is not None and current_points != expected_points_snapshot:
                    return PurchaseBonusResult(
                        success=False,
                        message=(
                            f"Баланс изменился с момента открытия подтверждения. "
                            f"Было: {expected_points_snapshot}, сейчас: {current_points}. "
                            f"Магазин обновлён, проверьте покупку ещё раз."
                        ),
                    )

                bonus_name = str(bonus_row["name"])
                price_points = int(bonus_row["price_points"])

                if current_points < price_points:
                    return PurchaseBonusResult(
                        success=False,
                        message=(
                            f"Недостаточно баллов для покупки «{bonus_name}». "
                            f"Нужно: {price_points}, доступно: {current_points}."
                        ),
                    )

                bonus_purchase_id = repo.create_bonus_purchase(
                    employee_user_id=employee_user_id,
                    bonus_id=int(bonus_row["id"]),
                    purchase_token=purchase_token,
                    bonus_snapshot_name=bonus_name,
                    bonus_snapshot_price_points=price_points,
                )

                repo.create_store_purchase_points_transaction(
                    employee_user_id=employee_user_id,
                    bonus_purchase_id=bonus_purchase_id,
                    points_to_spend=price_points,
                    bonus_name=bonus_name,
                )

                repo.sync_employee_points_balance(employee_user_id)
                updated_points = repo.get_employee_points_balance(employee_user_id)

                employee_name = repo.get_user_display_name(employee_user_id)
                title = f"Новая заявка на бонус: {bonus_name}"
                message = (
                    f"Сотрудник {employee_name} оформил покупку бонуса "
                    f"«{bonus_name}» за {price_points} баллов. "
                    f"Заявка #{bonus_purchase_id} ожидает обработки."
                )

                repo.create_bonus_purchase_notifications(
                    bonus_purchase_id=bonus_purchase_id,
                    employee_user_id=employee_user_id,
                    title=title,
                    message=message,
                )

                return PurchaseBonusResult(
                    success=True,
                    message=(
                        f"Покупка бонуса «{bonus_name}» подтверждена. "
                        f"Баллы списаны, заявка отправлена HR."
                    ),
                    updated_points_balance=updated_points,
                    already_processed=False,
                )

        except IntegrityError:
            return PurchaseBonusResult(
                success=True,
                message="Покупка уже была зарегистрирована. Повторное списание баллов предотвращено.",
                updated_points_balance=None,
                already_processed=True,
            )

        except SQLAlchemyError:
            return PurchaseBonusResult(
                success=False,
                message="База данных недоступна. Покупка сейчас не может быть выполнена.",
            )