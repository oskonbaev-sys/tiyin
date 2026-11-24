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
