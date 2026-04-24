"""
View-модели и структуры данных для вкладки сотрудника "Личные данные".
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ResumeDisplaySection:
    """
    Один раздел резюме для отображения на экране.
    """
    title: str
    lines: list[str]


@dataclass(frozen=True)
class ResumeRequestSectionOption:
    """
    Один вариант для dropdown в форме "Добавить информацию".
    """
    section_id: int
    label: str


@dataclass(frozen=True)
class EmployeePersonalDataViewModel:
    """
    Полная view-модель вкладки "Личные данные".
    """
    employee_user_id: int
    full_name: str
    points_balance: int
    completed_achievements_count: int
    total_achievements_count: int
    sections: list[ResumeDisplaySection] = field(default_factory=list)
    request_section_options: list[ResumeRequestSectionOption] = field(default_factory=list)
    db_available: bool = True
    load_error_message: str | None = None


@dataclass(frozen=True)
class ResumeChangeRequestResult:
    """
    Результат отправки формы сотрудником.
    """
    success: bool
    message: str