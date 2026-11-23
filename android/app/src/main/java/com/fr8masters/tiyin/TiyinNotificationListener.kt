package com.fr8masters.tiyin

import android.app.Notification
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import org.json.JSONObject

/** Читает пуши банков и отправляет их в Tiyin. Остальные уведомления не трогает. */
class TiyinNotificationListener : NotificationListenerService() {

    private val recent = LinkedHashMap<String, Long>()

    override fun onNotificationPosted(sbn: StatusBarNotification) {
        if (sbn.packageName == packageName || sbn.packageName in IGNORED) return
        if (!Store.enabled(this)) return
        val key = Store.key(this) ?: return
        if (sbn.notification.flags and Notification.FLAG_GROUP_SUMMARY != 0) return

        val ex = sbn.notification.extras
        val title = ex.getCharSequence(Notification.EXTRA_TITLE)?.toString().orEmpty()
        val text = (ex.getCharSequence(Notification.EXTRA_BIG_TEXT)
            ?: ex.getCharSequence(Notification.EXTRA_TEXT))?.toString().orEmpty()
        val all = "$title $text"
        if (!MONEY.containsMatchIn(all)) return   // только сообщения с суммой

        // один и тот же пуш часто приходит повторно — отсекаем дубли за 2 минуты
        val now = System.currentTimeMillis()
        val sig = sbn.packageName + all
        synchronized(recent) {
            recent.entries.removeAll { now - it.value > 120_000 }
            if (recent.containsKey(sig)) return
            recent[sig] = now
        }

        val body = JSONObject()
            .put("app", sbn.packageName)
            .put("title", title)
            .put("text", text)
        Net.async { Net.post("/api/ingest/android", body, key) }
    }

    companion object {
        private val MONEY = Regex(
            """\d[\d\s.,]*\s?(KGS|kgs|сом|som|с\.?(?=\s|$)|USD|\$|RUB|₽|KZT|₸)""",
            RegexOption.IGNORE_CASE
        )
        private val IGNORED = setOf(
            "org.telegram.messenger", "org.telegram.messenger.web", "org.thunderdog.challegram",
            "com.whatsapp", "com.whatsapp.w4b", "com.instagram.android",
            "com.google.android.gm", "com.android.systemui", "com.google.android.youtube"
        )
    }
}
