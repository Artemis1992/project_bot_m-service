"""Tests for bot_gateway FSM keyboards and main menu."""

from __future__ import annotations

import sys
from pathlib import Path

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup

# Add bot_gateway service to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "bot_gateway"))

from fsm import keyboards  # noqa: E402


def _flatten_reply_keyboard(kb: ReplyKeyboardMarkup) -> list[str]:
    """Helper to collect button texts from ReplyKeyboardMarkup."""
    return [button.text for row in kb.keyboard for button in row]


def _flatten_inline_keyboard(kb: InlineKeyboardMarkup) -> list[tuple[str, str]]:
    """Helper to collect (text, callback_data) from InlineKeyboardMarkup."""
    result: list[tuple[str, str]] = []
    for row in kb.inline_keyboard:
        for button in row:
            result.append((button.text, button.callback_data))
    return result


def test_main_menu_keyboard_structure():
    """Main menu should contain three buttons in one column."""
    kb = keyboards.main_menu_keyboard()

    assert isinstance(kb, ReplyKeyboardMarkup)
    texts = _flatten_reply_keyboard(kb)

    assert texts == [
        "📝 Создать заявку",
        "📋 Мои заявки",
        "ℹ️ Помощь",
    ]


def test_confirmation_keyboard_buttons():
    """Confirmation keyboard should have confirm and restart buttons."""
    kb = keyboards.confirmation_keyboard()

    assert isinstance(kb, InlineKeyboardMarkup)
    items = _flatten_inline_keyboard(kb)
    texts = [text for text, _ in items]
    callbacks = [cb for _, cb in items]

    assert "✅ Подтвердить" in texts
    assert "🔁 Начать заново" in texts
    assert "confirm:yes" in callbacks
    assert "confirm:restart" in callbacks


def test_approval_keyboard_callbacks():
    """Approval keyboard should contain approve/reject callback buttons."""
    request_id = 123
    step_order = 2

    kb = keyboards.approval_keyboard(request_id, step_order)
    assert isinstance(kb, InlineKeyboardMarkup)

    items = _flatten_inline_keyboard(kb)
    callbacks = {cb for _, cb in items}

    assert f"approve:{request_id}:{step_order}" in callbacks
    assert f"reject:{request_id}:{step_order}" in callbacks


def test_rejection_comment_keyboard_callbacks():
    """Rejection comment keyboard should allow rejecting without comment."""
    request_id = 10
    step_order = 1

    kb = keyboards.rejection_comment_keyboard(request_id, step_order)
    assert isinstance(kb, InlineKeyboardMarkup)

    items = _flatten_inline_keyboard(kb)
    callbacks = {cb for _, cb in items}

    assert f"reject_no_comment:{request_id}:{step_order}" in callbacks


def test_requests_list_keyboard_pagination_and_main_menu():
    """Requests list keyboard should build detail and pagination buttons."""
    requests = [
        {"id": 1, "status": "new", "status_display": "Новая"},
        {"id": 2, "status": "approved", "status_display": "Утверждена"},
        {"id": 3, "status": "in_progress", "status_display": "На согласовании"},
    ]

    kb = keyboards.requests_list_keyboard(requests, page=0, page_size=2)
    assert isinstance(kb, InlineKeyboardMarkup)

    items = _flatten_inline_keyboard(kb)
    callbacks = {cb for _, cb in items}

    # Должны быть detail-кнопки для первых двух заявок
    assert "request_detail:1" in callbacks
    assert "request_detail:2" in callbacks
    # Поскольку всего 3 заявки и page_size=2, должна быть кнопка перехода на следующую страницу
    assert "requests_page:1" in callbacks
    # Должна быть кнопка возврата в главное меню
    assert "main_menu" in callbacks


def test_request_detail_keyboard_buttons():
    """Request detail keyboard should include back and main menu buttons."""
    request_id = 5

    kb = keyboards.request_detail_keyboard(request_id)
    assert isinstance(kb, InlineKeyboardMarkup)

    items = _flatten_inline_keyboard(kb)
    callbacks = {cb for _, cb in items}

    assert "requests_list" in callbacks
    assert "main_menu" in callbacks


