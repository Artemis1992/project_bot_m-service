from __future__ import annotations

from typing import Iterable, Sequence

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from ..api.categories_service import Warehouse, Category, Subcategory


def warehouses_keyboard(warehouses: Sequence[Warehouse]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for warehouse in warehouses:
        builder.button(
            text=warehouse.name,
            callback_data=f"warehouse:{warehouse.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def categories_keyboard(categories: Sequence[Category]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(
            text=category.name,
            callback_data=f"category:{category.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def subcategories_keyboard(subcategories: Sequence[Subcategory]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for subcategory in subcategories:
        suffix = " ✏️" if subcategory.is_custom_input else ""
        builder.button(
            text=f"{subcategory.name}{suffix}",
            callback_data=f"subcategory:{subcategory.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def confirmation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm:yes")
    builder.button(text="🔁 Начать заново", callback_data="confirm:restart")
    builder.adjust(1)
    return builder.as_markup()


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота с основными функциями."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="📝 Создать заявку")
    builder.button(text="📋 Мои заявки")
    builder.button(text="ℹ️ Помощь")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


def approval_keyboard(request_id: int, step_order: int) -> InlineKeyboardMarkup:
    """Клавиатура для согласования заявки."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Одобрить",
        callback_data=f"approve:{request_id}:{step_order}"
    )
    builder.button(
        text="❌ Отклонить",
        callback_data=f"reject:{request_id}:{step_order}"
    )
    builder.adjust(1)
    return builder.as_markup()


def rejection_comment_keyboard(request_id: int, step_order: int) -> InlineKeyboardMarkup:
    """Клавиатура для ввода комментария при отклонении."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⏭️ Отклонить без комментария",
        callback_data=f"reject_no_comment:{request_id}:{step_order}"
    )
    builder.adjust(1)
    return builder.as_markup()


def requests_list_keyboard(requests: list, page: int = 0, page_size: int = 5) -> InlineKeyboardMarkup:
    """Клавиатура для списка заявок с пагинацией."""
    builder = InlineKeyboardBuilder()
    start_idx = page * page_size
    end_idx = start_idx + page_size
    page_requests = requests[start_idx:end_idx]
    
    for req in page_requests:
        status_emoji = {
            "new": "🆕",
            "in_progress": "⏳",
            "approved": "✅",
            "rejected": "❌",
            "paid": "💰"
        }.get(req.get("status", ""), "📄")
        builder.button(
            text=f"{status_emoji} Заявка #{req.get('id')} - {req.get('status_display', '')}",
            callback_data=f"request_detail:{req.get('id')}"
        )
    
    # Кнопки пагинации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"requests_page:{page-1}")
        )
    if end_idx < len(requests):
        nav_buttons.append(
            InlineKeyboardButton(text="Вперед ▶️", callback_data=f"requests_page:{page+1}")
        )
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.button(text="🔙 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def request_detail_keyboard(request_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для детального просмотра заявки."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 К списку заявок", callback_data="requests_list")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

