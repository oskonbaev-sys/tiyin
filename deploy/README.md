# Изменения на сервере (/opt/tiyin/tiyin-bot)

`2026-11-23-android-patch.py` — применён 23.11.2026, резервная копия: `/opt/tiyin/backup-20261123-223356`.

- `/start`: если телефон неизвестен — кнопка «Продолжить» открывает `/detect` (Telegram.WebApp.platform → sendData), платформа сохраняется в `users.settings.platform`.
- Android: приветствие с кнопками «Установить MacroDroid» и «Получить автозапись Tiyin»; `/setup` на Android присылает `Tiyin.macro` (шаблон `android/Tiyin.macro.tpl`, в адрес подставляется ключ пользователя).
- Сервер: `POST /api/ingest/<ключ>` (ключ в адресе, обычный текст пуша в теле), `GET /detect`.
- iOS: без изменений (шорткаты).

Откат: `cp -a /opt/tiyin/backup-20261123-223356/* /opt/tiyin/tiyin-bot/ && systemctl restart tiyin`
