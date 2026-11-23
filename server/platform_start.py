"""
Tiyin: /start определяет устройство (iOS / Android) и показывает нужные настройки.

Telegram не сообщает боту платформу в обычном сообщении. Её знает только
мини-приложение (Telegram.WebApp.platform). Поэтому /start показывает одну
кнопку «Продолжить»: она на долю секунды открывает страницу detect.html,
та отправляет платформу боту через WebApp.sendData и сразу закрывается.
Если платформа неизвестна (Desktop/Web), бот спрашивает кнопками.

Подключение:
    from platform_start import router as platform_router
    dp.include_router(platform_router)   # до старого обработчика /start
Положить detect.html на сервер: https://tiyin.fr8mastersllc.com/detect.html
"""
from aiogram import F, Router

from android_ingest import create_link_token
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo,
)

BASE = "https://tiyin.fr8mastersllc.com"
DETECT_URL = f"{BASE}/detect.html"
ANDROID_PAGE = f"{BASE}/android.html"

router = Router(name="platform_start")

# Запоминаем платформу (замените на запись в вашу БД, если нужно хранить постоянно)
USER_PLATFORM: dict[int, str] = {}

GREETING = (
    "Привет, {name}! Я веду учёт расходов.\n\n"
    "Напишите трату, например «такси 350», и я её запишу. "
    "Отчёты и лимиты в приложении.\n\n"
    "Данные хранятся только для вашего учёта; удалить всё можно в настройках приложения."
)


def _app_button() -> InlineKeyboardButton:
    return InlineKeyboardButton(text="Открыть приложение", web_app=WebAppInfo(url=BASE))


def ios_kb() -> InlineKeyboardMarkup:
    # Ссылки на установку шорткатов — подставьте те, что уже используются в боте
    return InlineKeyboardMarkup(inline_keyboard=[
        [_app_button()],
        [InlineKeyboardButton(text="📲 Установить автозапись: Apple Pay", callback_data="setup:ios:applepay")],
        [InlineKeyboardButton(text="📲 Установить автозапись: Банки (пуши)", callback_data="setup:ios:banks")],
        [InlineKeyboardButton(text="У меня Android", callback_data="platform:android")],
    ])


def android_kb(user_id: int) -> InlineKeyboardMarkup:
    # токен в #фрагменте: не попадает в логи сервера, одноразовый, живёт 15 минут
    link = f"{ANDROID_PAGE}#t={create_link_token(user_id)}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [_app_button()],
        [InlineKeyboardButton(text="📲 Подключить автозапись", url=link)],
        [InlineKeyboardButton(text="У меня iPhone", callback_data="platform:ios")],
    ])


def ask_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📱 iPhone", callback_data="platform:ios"),
        InlineKeyboardButton(text="🤖 Android", callback_data="platform:android"),
    ]])


IOS_TEXT = ("Автозапись трат (iPhone)\n"
            "1. Нажмите кнопку → «Добавить шорткат».\n"
            "2. Запустите шорткат один раз — автозапись подключится сама.\n"
            "«Apple Pay» записывает оплаты из Wallet, «Банки» — пуши банков.")

ANDROID_TEXT = ("Автозапись трат (Android)\n"
                "1. Нажмите «Подключить автозапись» → «Скачать Tiyin» и установите.\n"
                "2. Там же нажмите «Подключить» и включите переключатель Tiyin.\n"
                "Ключ вводить не нужно — пуши банков начнут записываться сами.")


async def send_for_platform(message: Message, platform: str, name: str) -> None:
    USER_PLATFORM[message.chat.id] = platform
    greet = GREETING.format(name=name)
    if platform == "ios":
        await message.answer(f"{greet}\n\n{IOS_TEXT}", reply_markup=ios_kb())
    elif platform == "android":
        await message.answer(f"{greet}\n\n{ANDROID_TEXT}", reply_markup=android_kb(message.chat.id))
    else:
        await message.answer(f"{greet}\n\nКакой у вас телефон?", reply_markup=ask_kb())


@router.message(CommandStart())
async def start(message: Message) -> None:
    known = USER_PLATFORM.get(message.chat.id)
    if known:
        await send_for_platform(message, known, message.from_user.first_name)
        return
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="▶️ Продолжить", web_app=WebAppInfo(url=DETECT_URL))]],
        resize_keyboard=True, one_time_keyboard=True,
    )
    await message.answer("Нажмите «Продолжить», чтобы настроить Tiyin под ваш телефон.", reply_markup=kb)


@router.message(F.web_app_data)
async def got_platform(message: Message) -> None:
    raw = (message.web_app_data.data or "").lower()
    platform = raw if raw in ("ios", "android") else "unknown"
    await message.answer("✅", reply_markup=ReplyKeyboardRemove())
    await send_for_platform(message, platform, message.from_user.first_name)


@router.callback_query(F.data.startswith("platform:"))
async def pick_platform(cb: CallbackQuery) -> None:
    platform = cb.data.split(":", 1)[1]
    await cb.answer()
    await send_for_platform(cb.message, platform, cb.from_user.first_name)
