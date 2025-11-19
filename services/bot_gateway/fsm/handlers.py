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
from . import keyboards
from .states import RequestFormStates


@dataclass(slots=True)
class BotDependencies:
    categories_client: CategoriesServiceClient
    requests_client: RequestsServiceClient
    files_client: FilesServiceClient


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
            "Привет! Я помогу оформить служебку. "
            "Двигайтесь строго по шагам и используйте кнопки."
        )
        await ask_warehouse(message, state)

    @router.message(Command("cancel"))
    async def cmd_cancel(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer("Диалог сброшен. Введите /start чтобы начать заново.")

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
            "Шаг 8 — отправка завершена.\n"
            f"Заявка №{request_body['id']} создана и передана на согласование."
        )
        await state.clear()


router = Router(name="request_form")
