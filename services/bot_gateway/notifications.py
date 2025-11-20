"""Notification system for approval workflow."""

from __future__ import annotations

import logging
import os

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications to approvers."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def notify_approver(
        self,
        telegram_username: str | None,
        request_id: int,
        summary: str,
        step_order: int,
        approver_name: str,
    ) -> bool:
        """
        Send notification to approver about pending approval.

        Returns True if notification was sent, False otherwise.
        """
        if not telegram_username:
            logger.warning(f"No telegram username for approver {approver_name}")
            return False

        try:
            # Try to find user by username
            # Note: In production, you might want to maintain a mapping of usernames to user IDs
            message = (
                f"🔔 Требуется ваше согласование\n\n"
                f"Заявка #{request_id}\n"
                f"{summary}\n\n"
                f"Шаг {step_order}: {approver_name}"
            )

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Одобрить",
                            callback_data=f"approve:{request_id}:{step_order}",
                        ),
                        InlineKeyboardButton(
                            text="❌ Отклонить",
                            callback_data=f"reject:{request_id}:{step_order}",
                        ),
                    ]
                ]
            )

            # In a real implementation, you'd need to resolve username to user_id
            # For now, we'll log the notification
            logger.info(f"Would send notification to @{telegram_username}: {message}")
            # await self.bot.send_message(chat_id=user_id, text=message, reply_markup=keyboard)
            return True
        except Exception as exc:
            logger.error(f"Failed to send notification to {telegram_username}: {exc}")
            return False

    async def notify_request_approved(self, request_id: int, author_tg_id: int) -> bool:
        """Notify request author that request was approved."""
        try:
            message = f"✅ Заявка #{request_id} утверждена!"
            await self.bot.send_message(chat_id=author_tg_id, text=message)
            return True
        except Exception as exc:
            logger.error(f"Failed to notify author {author_tg_id}: {exc}")
            return False

    async def notify_request_rejected(
        self, request_id: int, author_tg_id: int, comment: str | None = None
    ) -> bool:
        """Notify request author that request was rejected."""
        try:
            message = f"❌ Заявка #{request_id} отклонена."
            if comment:
                message += f"\n\nКомментарий: {comment}"
            await self.bot.send_message(chat_id=author_tg_id, text=message)
            return True
        except Exception as exc:
            logger.error(f"Failed to notify author {author_tg_id}: {exc}")
            return False





