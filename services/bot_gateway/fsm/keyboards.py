from __future__ import annotations

from typing import Iterable, Sequence

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

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

