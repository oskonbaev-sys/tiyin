# Изменения на сервере (/opt/tiyin/tiyin-bot)

`2026-11-23-android-patch.py` — применён 23.11.2026, резервная копия: `/opt/tiyin/backup-20261123-223356`.

- `/start`: если телефон неизвестен — кнопка «Продолжить» открывает `/detect` (Telegram.WebApp.platform → sendData), платформа сохраняется в `users.settings.platform`.
- Android: приветствие с кнопками «Установить MacroDroid» и «Получить автозапись Tiyin»; `/setup` на Android присылает `Tiyin.macro` (шаблон `android/Tiyin.macro.tpl`, в адрес подставляется ключ пользователя).
- Сервер: `POST /api/ingest/<ключ>` (ключ в адресе, обычный текст пуша в теле), `GET /detect`.
- iOS: без изменений (шорткаты).

Откат: `cp -a /opt/tiyin/backup-20261123-223356/* /opt/tiyin/tiyin-bot/ && systemctl restart tiyin`

## 2026-11-24 — вход в приложение по коду
`2026-11-24-app-login-patch.py`, резервная копия: `/opt/tiyin/backup-login-20261124-202617`.
- Бот: `/login` выдаёт одноразовый 6-значный код (10 минут, таблица `app_codes`).
- Сервер: `POST /api/app/login {"code"}` → `{"token"}`; API мини-приложения принимает `Authorization: Bearer <token>`.
- Мини-приложение: берёт ключ из `#app_token=…`, хранит в localStorage.
- APK: экран входа по коду, мини-приложение в WebView, автозапись пушей на `/api/ingest` с этим ключом.

## 2026-11-24 — бот предлагает APK вместо MacroDroid
`2026-11-24-android-apk-in-bot.py`, копия до изменения: `/opt/tiyin/backup-login-20261124-202617/bot.py.before-p3`.
- Android: кнопки «Скачать Tiyin для Android» (Releases/latest) и «Получить код для входа»; /setup на Android — инструкция по APK.

## 2026-11-24 — чеки и скриншоты во вкладке AI
`2026-11-24-receipts-patch.py`, резервная копия: `/opt/tiyin/backup-receipt-20261124-205650`.
- Сервер: `POST /api/receipt {image, mime}` → черновики операций (Gemini через `vision.extract`, без сохранения); `POST /api/receipt/save {items}` → запись через `service.add_tx` (source=photo, проверка дублей, уведомление в бот).
- Мини-приложение, вкладка AI: «📎 Загрузить чек или скриншот», сжатие до 1280px, список с правкой (расход/доход, сумма, где, категория), «Записать».
- APK: выбор файла в WebView (onShowFileChooser).

## 2026-11-27 — валюта при вводе дохода (сом / $)
`2026-11-27-income-currency-patch.py`, резервная копия: `/opt/tiyin/backup-cur-20261126-190119` (время сервера UTC).
- Мини-приложение: в окне «Доход» переключатель «с | $»; сумма в $ показывается как «$500».
- Сервер: `POST /api/tx` принимает `currency`; доллары пересчитываются в сомы по курсу НБКР (`fx.py`), исходная сумма — в `orig_amount_minor/orig_currency`. Нет курса → ошибка 503, запись не создаётся.

Откат: `cp -a /opt/tiyin/backup-cur-20261126-190119/server.py tiyin/ && cp -a /opt/tiyin/backup-cur-20261126-190119/index.html webapp/ && systemctl restart tiyin`

## 2026-11-27 — Claude Haiku как запасной вариант распознавания чеков
- `tiyin/vision.py`: запрос к Anthropic теперь берёт `ANTHROPIC_API_KEY` (раньше по ошибке шёл ключ Gemini). Копия до правки: `/opt/tiyin/vision.py.bak-haiku-*`.
- В `.env` добавлен `ANTHROPIC_API_KEY` (вставлял владелец). Порядок: Gemini → при ошибке Haiku (`claude-haiku-5-5`, меняется через `VISION_MODEL`).
