"""
Моковый сервис сотрудника.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.models.employee_view_models import (
    AchievementCard,
    EmployeeDashboardViewModel,
    NotificationCard,
    ResumeSection,
    StoreItemCard,
)


def get_mock_employee_dashboard() -> EmployeeDashboardViewModel:
    """
    Возвращает моковые данные сотрудника для экрана после входа.
    """
    settings = get_settings()

    return EmployeeDashboardViewModel(
        full_name=settings.demo_employee_name,
        achievements_done=10,
        achievements_total=50,
        points=1000,
        resume_sections=[
            ResumeSection(
                title="Пол",
                lines=["Мужской"],
            ),
            ResumeSection(
                title="Дата рождения",
                lines=["05/05/2005"],
            ),
            ResumeSection(
                title="Семейное положение",
                lines=["Женат, 2 детей"],
            ),
            ResumeSection(
                title="Гражданство",
                lines=["Российская Федерация"],
            ),
            ResumeSection(
                title="Образование",
                lines=[
                    'Диплом бакалавриата НИУ ВШЭ: "Бизнес-информатика"',
                    'Диплом с отличием магистратуры ИТМО: "Программная инженерия"',
                ],
            ),
            ResumeSection(
                title="Опыт работы",
                lines=[
                    "3 года программист C/C++ Junior",
                    "4 года программист C/C++ Senior",
                ],
            ),
            ResumeSection(
                title="Участие в соревнованиях",
                lines=[
                    "Хакатон 1 (2019)",
                    "Хакатон 2 (2020)",
                    "Соревнования (2020)",
                    "Чемпионат по программированию (2022)",
                ],
            ),
            ResumeSection(
                title="Личные навыки",
                lines=[
                    "Пунктуален",
                    "Серьёзно относится к заданиям",
                    "Soft skills развиты",
                    "Общителен",
                ],
            ),
            ResumeSection(
                title="Пройденные доп. курсы",
                lines=[
                    "C/C++ для начинающих (SkillBox)",
                    "Программирование на Unreal Engine (Яндекс Практикум)",
                ],
            ),
        ],
        achievements=[
            AchievementCard(
                icon="🏆",
                title="Покоритель хакатонов",
                description="Принял участие минимум в 3 корпоративных или внешних соревнованиях.",
                points=150,
                completed=True,
            ),
            AchievementCard(
                icon="📘",
                title="Всегда в тонусе",
                description="Своевременно обновил обязательный курс повышения квалификации.",
                points=100,
                completed=True,
            ),
            AchievementCard(
                icon="🧠",
                title="Усиление профиля",
                description="Добавил в резюме новый подтверждённый навык.",
                points=50,
                completed=False,
            ),
            AchievementCard(
                icon="🚀",
                title="Готов к следующему уровню",
                description="Собрал 5 выполненных достижений и поддерживает профиль актуальным.",
                points=200,
                completed=False,
            ),
            AchievementCard(
                icon="🤝",
                title="Командный игрок",
                description="Принял участие в межфункциональном проекте компании.",
                points=120,
                completed=True,
            ),
            AchievementCard(
                icon="🎯",
                title="Без промаха",
                description="Закрыл персональный план развития без просрочек.",
                points=180,
                completed=False,
            ),
        ],
        store_items=[
            StoreItemCard(
                icon="🎁",
                title="Мерч-бокс компании",
                description="Футболка, кружка и набор корпоративных стикеров.",
                price_points=60,
            ),
            StoreItemCard(
                icon="🏖️",
                title="Дополнительный выходной",
                description="Один согласуемый оплачиваемый выходной день.",
                price_points=120,
            ),
            StoreItemCard(
                icon="🎫",
                title="Бюджет на конференцию",
                description="Компенсация участия в профессиональном мероприятии.",
                price_points=200,
            ),
            StoreItemCard(
                icon="☕",
                title="Подарочный сертификат",
                description="Небольшой бонус на кофе / маркетплейс / книгу.",
                price_points=80,
            ),
            StoreItemCard(
                icon="📚",
                title="Оплата онлайн-курса",
                description="Поддержка обучения по согласованной теме.",
                price_points=250,
            ),
            StoreItemCard(
                icon="💻",
                title="Техника для рабочего места",
                description="Небольшое улучшение домашнего или офисного рабочего места.",
                price_points=300,
            ),
        ],
        notifications=[
            NotificationCard(
                title="Пора обновить курс повышения квалификации",
                description="Срок действия одного из обязательных курсов подходит к завершению. Запланируйте обновление заранее.",
                priority_label="Высокий приоритет",
                status_label="Новое",
            ),
            NotificationCard(
                title="Проверьте полноту профиля",
                description="В резюме не хватает нескольких структурированных пунктов. Их заполнение повысит качество подбора на внутренние роли.",
                priority_label="Обычный приоритет",
                status_label="Новое",
            ),
            NotificationCard(
                title="Новые достижения скоро доступны",
                description="После подключения бизнес-логики здесь появятся события по новым бейджам, баллам и рекомендациям.",
                priority_label="Инфо",
                status_label="Системное",
            ),
        ],
    )