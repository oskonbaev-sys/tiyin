# Tiyin

Учёт расходов в Telegram (@tiyinplus_bot) + Android-приложение для автозаписи пушей банков.

- `android/` — приложение (WebView мини-приложения + автозапись из уведомлений). APK собирается GitHub Actions → Releases → `latest/Tiyin.apk`.
- `server/` — модули для бота: `/start` с определением iOS/Android; на Android автозапись через MacroDroid (бот присылает готовый файл макроса), приём пушей `/api/ingest/android/<ключ>`.
- `server/tiyin_android.macro` — шаблон макроса MacroDroid (вместо ключа `TIYIN_KEY`); бот подставляет ключ и присылает `Tiyin.macro`. Собран по образцу настоящих экспортов MacroDroid, импорт на телефоне ещё не проверен.

## Подключение на сервере
1. Скопировать `server/platform_start.py`, `server/android_ingest.py` к боту.
2. `dp.include_router(platform_router)` до старого обработчика `/start`.
3. `setup_android_ingest(app, user_by_key=..., get_key=..., save_push=..., on_linked=...)` в aiohttp-приложении.
4. `detect.html` — в корень сайта tiyin.fr8mastersllc.com.
