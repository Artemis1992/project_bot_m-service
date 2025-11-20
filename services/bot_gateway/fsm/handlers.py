from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..api.categories_service import (
    CategoriesServiceClient,
    Warehouse,
    Category,
    Subcategory,
)
from ..api.files_service import FilesServiceClient
from ..api.requests_service import (
    AttachmentPayload,
    RequestPayload,
    RequestsServiceClient,
)
from ..api.reporting_service import ReportingServiceClient
from ..api.approvals_service import ApprovalsServiceClient
from . import keyboards
from .states import RequestFormStates


@dataclass(slots=True)
class BotDependencies:
    categories_client: CategoriesServiceClient
    requests_client: RequestsServiceClient
    files_client: FilesServiceClient
    reporting_client: ReportingServiceClient
    approvals_client: ApprovalsServiceClient


def serialize_warehouses(tree: List[Warehouse]) -> List[Dict[str, Any]]:
    return [warehouse.model_dump() for warehouse in tree]


def deserialize_warehouses(raw: List[Dict[str, Any]]) -> List[Warehouse]:
    return [Warehouse.model_validate(item) for item in raw]


def serialize_category(category: Category | Subcategory) -> Dict[str, Any]:
    return category.model_dump()


def build_summary(data: Dict[str, Any]) -> str:
    lines = [
        "Проверьте данные:",
        f"Склад: {data['warehouse_name']}",
        f"Категория: {data['category_name']}",
        f"Подкатегория: {data['subcategory_name']}",
        f"Сумма: {data['amount']} тг",
    ]
    comment = data.get("comment")
    if comment:
        lines.append(f"Комментарий: {comment}")
    if file_info := data.get("file_info"):
        lines.append(f"Файл: {file_info['file_name']}")
    return "\n".join(lines)


def setup_request_form_handlers(router: Router, deps: BotDependencies) -> None:
    @router.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer(
            "👋 Привет! Я бот для оформления служебок.\n\n"
            "Выберите действие:",
            reply_markup=keyboards.main_menu_keyboard()
        )

    @router.message(F.text == "📝 Создать заявку")
    async def cmd_create_request(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer(
            "📝 Создание новой заявки.\n"
            "Двигайтесь строго по шагам и используйте кнопки."
        )
        await ask_warehouse(message, state)

    @router.message(F.text == "📋 Мои заявки")
    async def cmd_my_requests(message: Message, state: FSMContext) -> None:
        await state.clear()
        try:
            requests_list = await deps.requests_client.get_user_requests(message.from_user.id)
            if not requests_list:
                await message.answer(
                    "📋 У вас пока нет заявок.\n"
                    "Создайте первую заявку, нажав на кнопку '📝 Создать заявку'.",
                    reply_markup=keyboards.main_menu_keyboard()
                )
                return
            
            await state.update_data(requests_list=requests_list, requests_page=0)
            await show_requests_list(message, state, page=0)
        except Exception as exc:
            await message.answer(
                f"❌ Ошибка при получении списка заявок: {exc}\n"
                "Попробуйте позже.",
                reply_markup=keyboards.main_menu_keyboard()
            )

    @router.message(F.text == "ℹ️ Помощь")
    async def cmd_help(message: Message, state: FSMContext) -> None:
        help_text = (
            "ℹ️ <b>Помощь по использованию бота</b>\n\n"
            "📝 <b>Создать заявку</b> - начать оформление новой служебки\n"
            "📋 <b>Мои заявки</b> - просмотреть список ваших заявок\n\n"
            "📌 <b>Процесс создания заявки:</b>\n"
            "1️⃣ Выберите склад\n"
            "2️⃣ Выберите категорию расходов\n"
            "3️⃣ Выберите подкатегорию\n"
            "4️⃣ Введите сумму (только число)\n"
            "5️⃣ Добавьте комментарий (при необходимости)\n"
            "6️⃣ Прикрепите файл (PDF или фото)\n"
            "7️⃣ Подтвердите данные\n\n"
            "🔧 <b>Команды:</b>\n"
            "/start - Главное меню\n"
            "/cancel - Отменить текущее действие\n\n"
            "❓ Если возникли вопросы, обратитесь к администратору."
        )
        await message.answer(help_text, reply_markup=keyboards.main_menu_keyboard())

    async def show_requests_list(message: Message, state: FSMContext, page: int = 0) -> None:
        """Показать список заявок с пагинацией."""
        data = await state.get_data()
        requests_list = data.get("requests_list", [])
        
        if not requests_list:
            await message.answer("У вас нет заявок.")
            return
        
        total = len(requests_list)
        page_size = 5
        start_idx = page * page_size
        
        if start_idx >= total:
            page = 0
            start_idx = 0
        
        page_requests = requests_list[start_idx:start_idx + page_size]
        
        text = f"📋 <b>Ваши заявки</b> (всего: {total})\n\n"
        for req in page_requests:
            status_emoji = {
                "new": "🆕",
                "in_progress": "⏳",
                "approved": "✅",
                "rejected": "❌",
                "paid": "💰"
            }.get(req.get("status", ""), "📄")
            
            text += (
                f"{status_emoji} <b>Заявка #{req.get('id')}</b>\n"
                f"   Склад: {req.get('warehouse')}\n"
                f"   Сумма: {req.get('amount')} тг\n"
                f"   Статус: {req.get('status_display')}\n\n"
            )
        
        await state.update_data(requests_page=page)
        await message.answer(
            text,
            reply_markup=keyboards.requests_list_keyboard(requests_list, page, page_size)
        )

    @router.callback_query(F.data == "main_menu")
    async def callback_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await callback.message.edit_text(
            "👋 Главное меню\n\nВыберите действие:"
        )
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=keyboards.main_menu_keyboard()
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("requests_page:"))
    async def callback_requests_page(callback: CallbackQuery, state: FSMContext) -> None:
        page = int(callback.data.split(":")[1])
        await show_requests_list(callback.message, state, page)
        await callback.answer()

    @router.callback_query(F.data.startswith("request_detail:"))
    async def callback_request_detail(callback: CallbackQuery, state: FSMContext) -> None:
        request_id = int(callback.data.split(":")[1])
        try:
            request_data = await deps.requests_client.get_request(request_id)
            
            status_emoji = {
                "new": "🆕",
                "in_progress": "⏳",
                "approved": "✅",
                "rejected": "❌",
                "paid": "💰"
            }.get(request_data.get("status", ""), "📄")
            
            text = (
                f"{status_emoji} <b>Заявка #{request_id}</b>\n\n"
                f"📦 Склад: {request_data.get('warehouse')}\n"
                f"📂 Категория: {request_data.get('category')}\n"
                f"📁 Подкатегория: {request_data.get('subcategory')}\n"
                f"💰 Сумма: {request_data.get('amount')} тг\n"
                f"📊 Статус: {request_data.get('status_display')}\n"
            )
            
            if request_data.get("comment"):
                text += f"💬 Комментарий: {request_data.get('comment')}\n"
            
            if request_data.get("current_level", 0) > 0:
                text += f"🔢 Уровень согласования: {request_data.get('current_level')}\n"
            
            text += f"\n📅 Создана: {request_data.get('created_at', '')[:10] if request_data.get('created_at') else 'N/A'}"
            
            if request_data.get("attachments"):
                text += f"\n📎 Файлов: {len(request_data.get('attachments', []))}"
            
            await callback.message.edit_text(text, reply_markup=keyboards.request_detail_keyboard(request_id))
        except Exception as exc:
            await callback.answer(f"Ошибка: {exc}", show_alert=True)
        await callback.answer()

    @router.callback_query(F.data == "requests_list")
    async def callback_requests_list(callback: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        page = data.get("requests_page", 0)
        await show_requests_list(callback.message, state, page)
        await callback.answer()

    @router.message(Command("cancel"))
    async def cmd_cancel(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer(
            "❌ Диалог отменён.",
            reply_markup=keyboards.main_menu_keyboard()
        )

    async def ask_warehouse(message: Message, state: FSMContext) -> None:
        warehouses = await deps.categories_client.list_warehouses()
        await state.update_data(
            warehouses=serialize_warehouses(warehouses),
        )
        await state.set_state(RequestFormStates.warehouse)
        await message.answer(
            "Шаг 1 — выберите склад:",
            reply_markup=keyboards.warehouses_keyboard(warehouses),
        )

    @router.callback_query(
        RequestFormStates.warehouse,
        F.data.startswith("warehouse:"),
    )
    async def select_warehouse(callback: CallbackQuery, state: FSMContext) -> None:
        warehouse_id = callback.data.split(":", maxsplit=1)[1]
        data = await state.get_data()
        warehouses = deserialize_warehouses(data.get("warehouses", []))
        warehouse = next((w for w in warehouses if w.id == warehouse_id), None)
        if not warehouse:
            await callback.answer("Не удалось определить склад. Попробуйте ещё раз.")
            return
        await state.update_data(
            warehouse_id=warehouse.id,
            warehouse_name=warehouse.name,
            categories=[serialize_category(cat) for cat in warehouse.categories],
        )
        await state.set_state(RequestFormStates.category)
        await callback.message.edit_text(
            f"Склад: {warehouse.name}\n"
            "Шаг 2 — выберите категорию расходов:",
            reply_markup=keyboards.categories_keyboard(warehouse.categories),
        )
        await callback.answer()

    @router.callback_query(
        RequestFormStates.category,
        F.data.startswith("category:"),
    )
    async def select_category(callback: CallbackQuery, state: FSMContext) -> None:
        category_id = callback.data.split(":", maxsplit=1)[1]
        data = await state.get_data()
        categories = [
            Category.model_validate(cat) for cat in data.get("categories", [])
        ]
        category = next((c for c in categories if c.id == category_id), None)
        if not category:
            await callback.answer("Категория недоступна.")
            return
        await state.update_data(
            category_id=category.id,
            category_name=category.name,
            subcategories=[serialize_category(sub) for sub in category.subcategories],
        )
        await state.set_state(RequestFormStates.subcategory)
        await callback.message.edit_text(
            f"Категория: {category.name}\n"
            "Шаг 3 — выберите подкатегорию.",
            reply_markup=keyboards.subcategories_keyboard(category.subcategories),
        )
        await callback.answer()

    @router.callback_query(
        RequestFormStates.subcategory,
        F.data.startswith("subcategory:"),
    )
    async def select_subcategory(callback: CallbackQuery, state: FSMContext) -> None:
        subcategory_id = callback.data.split(":", maxsplit=1)[1]
        data = await state.get_data()
        subcategories = [
            Subcategory.model_validate(sub) for sub in data.get("subcategories", [])
        ]
        subcategory = next((s for s in subcategories if s.id == subcategory_id), None)
        if not subcategory:
            await callback.answer("Подкатегория недоступна.")
            return

        if subcategory.is_custom_input:
            await state.update_data(
                awaiting_custom_subcategory=True,
            )
            await callback.answer()
            await callback.message.answer(
                "Эта подкатегория предполагает ручной ввод. "
                "Пожалуйста, введите название подкатегории сообщением."
            )
            return

        await accept_subcategory(subcategory, state, callback.message)
        await callback.answer()

    async def accept_subcategory(
        subcategory: Subcategory, state: FSMContext, message: Message
    ) -> None:
        await state.update_data(
            awaiting_custom_subcategory=False,
            subcategory_id=subcategory.id,
            subcategory_name=subcategory.name,
            comment_required=subcategory.requires_comment,
        )
        await state.set_state(RequestFormStates.amount)
        await message.answer(
            "Шаг 4 — введите сумму в тенге (только число):",
        )

    @router.message(RequestFormStates.subcategory)
    async def input_custom_subcategory(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        if not data.get("awaiting_custom_subcategory"):
            await message.answer("Пожалуйста, используйте кнопки для выбора.")
            return
        text = (message.text or "").strip()
        if not text:
            await message.answer("Название подкатегории не может быть пустым.")
            return
        subcategory = Subcategory(
            id=f"custom:{message.from_user.id}",
            name=text,
            is_custom_input=True,
            requires_comment=True,
        )
        await accept_subcategory(subcategory, state, message)

    @router.message(RequestFormStates.amount)
    async def input_amount(message: Message, state: FSMContext) -> None:
        raw_value = (message.text or "").replace(" ", "").replace(",", ".")
        try:
            value = Decimal(raw_value)
        except (InvalidOperation, ValueError):
            await message.answer("Введённое значение не похоже на число. Попробуйте ещё раз.")
            return
        if value <= 0:
            await message.answer("Сумма должна быть больше нуля.")
            return
        amount = float(value.quantize(Decimal("0.01")))
        await state.update_data(amount=amount)
        await state.set_state(RequestFormStates.comment)
        data = await state.get_data()
        if data.get("comment_required"):
            await message.answer(
                "Шаг 5 — обязательно укажите комментарий (например, причину штрафа)."
            )
        else:
            await message.answer(
                "Шаг 5 — добавьте комментарий (при необходимости). "
                "Если комментарий не нужен, отправьте дефис (-)."
            )

    @router.message(RequestFormStates.comment)
    async def input_comment(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        requires_comment = data.get("comment_required", False)
        text = (message.text or "").strip()
        if requires_comment and not text:
            await message.answer("Комментарий обязателен для выбранной подкатегории.")
            return
        comment = None if text in {"-", "—"} else text
        if requires_comment and not comment:
            await message.answer("Комментарий обязателен. Опишите причину.")
            return

        await state.update_data(comment=comment)
        await state.set_state(RequestFormStates.file)
        await message.answer(
            "Шаг 6 — прикрепите файл (PDF или фото). "
            "Просто отправьте документ или фотографию сообщением."
        )

    @router.message(RequestFormStates.file, F.document | F.photo)
    async def receive_file(message: Message, state: FSMContext, bot: Bot) -> None:
        document = message.document
        photo = message.photo[-1] if message.photo else None
        if document:
            file_id = document.file_id
            file_name = document.file_name or f"document_{document.file_unique_id}"
        elif photo:
            file_id = photo.file_id
            file_name = f"photo_{photo.file_unique_id}.jpg"
        else:
            await message.answer("Нужен документ или фотография.")
            return

        data = await state.get_data()
        upload_result = await deps.files_client.upload_telegram_file(
            telegram_file_id=file_id,
            file_name=file_name,
            warehouse=data["warehouse_name"],
            category=data["category_name"],
            subcategory=data["subcategory_name"],
            author_id=message.from_user.id,
        )
        await state.update_data(
            file_info=upload_result.model_dump(),
        )

        await state.set_state(RequestFormStates.confirmation)
        summary = build_summary(await state.get_data())
        await message.answer(
            "Шаг 7 — подтверждение.\n" + summary,
            reply_markup=keyboards.confirmation_keyboard(),
        )

    @router.message(RequestFormStates.file)
    async def file_required(message: Message) -> None:
        await message.answer("Пожалуйста, прикрепите файл (PDF или фото).")

    @router.callback_query(
        RequestFormStates.confirmation,
        F.data == "confirm:restart",
    )
    async def restart(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await callback.answer("Начнём заново.")
        await callback.message.answer("Диалог сброшен.")
        await ask_warehouse(callback.message, state)

    @router.callback_query(
        RequestFormStates.confirmation,
        F.data == "confirm:yes",
    )
    async def confirm(callback: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        await callback.answer("Отправляем заявку...")
        payload = RequestPayload(
            tg_user_id=callback.from_user.id,
            author_username=callback.from_user.username,
            author_full_name=callback.from_user.full_name,
            warehouse=data["warehouse_name"],
            category=data["category_name"],
            subcategory=data["subcategory_name"],
            amount=data["amount"],
            comment=data.get("comment"),
        )
        request_body = await deps.requests_client.create_request(payload)
        file_info = data.get("file_info")
        if file_info:
            attachment_payload = AttachmentPayload(**file_info)
            await deps.requests_client.attach_file(
                request_id=request_body["id"],
                payload=attachment_payload,
            )
        await callback.message.answer(
            "✅ Шаг 8 — отправка завершена.\n"
            f"Заявка №{request_body['id']} создана и передана на согласование.",
            reply_markup=keyboards.main_menu_keyboard()
        )
        await state.clear()

    # Обработчики для согласования заявок (работают вне FSM)
    @router.callback_query(F.data.startswith("approve:"))
    async def callback_approve_request(callback: CallbackQuery, state: FSMContext) -> None:
        """Обработчик кнопки одобрения заявки."""
        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer("❌ Неверный формат запроса.", show_alert=True)
            return
        
        request_id = int(parts[1])
        step_order = int(parts[2])
        
        try:
            await callback.answer("⏳ Обрабатываю...")
            result = await deps.approvals_client.approve_request(
                request_id=request_id,
                actor_username=callback.from_user.username,
            )
            
            chain_status = result.get("status", "")
            if chain_status == "approved":
                await callback.message.edit_text(
                    f"✅ Заявка #{request_id} полностью утверждена!\n\n"
                    "Все шаги согласования пройдены."
                )
            else:
                await callback.message.edit_text(
                    f"✅ Заявка #{request_id} одобрена на шаге {step_order}.\n\n"
                    "Заявка передана следующему согласующему."
                )
        except Exception as exc:
            await callback.answer(f"❌ Ошибка: {exc}", show_alert=True)

    @router.callback_query(F.data.startswith("reject:"))
    async def callback_reject_request(callback: CallbackQuery, state: FSMContext) -> None:
        """Обработчик кнопки отклонения заявки - запрашивает комментарий."""
        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer("❌ Неверный формат запроса.", show_alert=True)
            return
        
        request_id = int(parts[1])
        step_order = int(parts[2])
        
        await callback.answer()
        await state.update_data(
            rejection_request_id=request_id,
            rejection_step_order=step_order
        )
        await state.set_state(RequestFormStates.rejection_comment)
        await callback.message.answer(
            f"❌ Отклонение заявки #{request_id}\n\n"
            "Пожалуйста, укажите причину отклонения (комментарий):\n"
            "Или нажмите кнопку для отклонения без комментария.",
            reply_markup=keyboards.rejection_comment_keyboard(request_id, step_order)
        )

    @router.callback_query(F.data.startswith("reject_no_comment:"))
    async def callback_reject_no_comment(callback: CallbackQuery, state: FSMContext) -> None:
        """Обработчик отклонения без комментария."""
        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer("❌ Неверный формат запроса.", show_alert=True)
            return
        
        request_id = int(parts[1])
        step_order = int(parts[2])
        
        try:
            await callback.answer("⏳ Обрабатываю...")
            await deps.approvals_client.reject_request(
                request_id=request_id,
                actor_username=callback.from_user.username,
            )
            
            await callback.message.edit_text(
                f"❌ Заявка #{request_id} отклонена на шаге {step_order}.\n\n"
                "Автор заявки получит уведомление."
            )
            await state.clear()
        except Exception as exc:
            await callback.answer(f"❌ Ошибка: {exc}", show_alert=True)

    @router.message(RequestFormStates.rejection_comment)
    async def input_rejection_comment(message: Message, state: FSMContext) -> None:
        """Обработка ввода комментария при отклонении."""
        data = await state.get_data()
        request_id = data.get("rejection_request_id")
        step_order = data.get("rejection_step_order")
        
        if not request_id:
            await message.answer("❌ Ошибка: не найдена информация о заявке.")
            await state.clear()
            return
        
        comment = (message.text or "").strip()
        if not comment:
            await message.answer("⚠️ Комментарий не может быть пустым. Введите причину отклонения или используйте кнопку.")
            return
        
        try:
            await deps.approvals_client.reject_request(
                request_id=request_id,
                actor_username=message.from_user.username,
                comment=comment
            )
            
            await message.answer(
                f"❌ Заявка #{request_id} отклонена на шаге {step_order}.\n\n"
                f"Комментарий: {comment}\n\n"
                "Автор заявки получит уведомление."
            )
            await state.clear()
        except Exception as exc:
            await message.answer(f"❌ Ошибка при отклонении заявки: {exc}")


router = Router(name="request_form")
