package com.fr8masters.tiyin

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.os.Build
import android.provider.Settings
import androidx.core.app.NotificationManagerCompat

object Store {
    const val BASE = "https://tiyin.fr8mastersllc.com"
    const val BOT = "tiyinplus_bot"
    private const val PREFS = "tiyin"

    private fun p(c: Context) = c.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
    fun key(c: Context): String? = p(c).getString("ingest_key", null)
    fun setKey(c: Context, k: String) = p(c).edit().putString("ingest_key", k).apply()
    fun enabled(c: Context) = p(c).getBoolean("enabled", true)
    fun setEnabled(c: Context, v: Boolean) = p(c).edit().putBoolean("enabled", v).apply()

    fun hasAccess(c: Context) =
        NotificationManagerCompat.getEnabledListenerPackages(c).contains(c.packageName)

    /** Открывает сразу переключатель Tiyin (Android 11+), иначе общий список. */
    fun openAccess(c: Context) {
        val i = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            Intent(Settings.ACTION_NOTIFICATION_LISTENER_DETAIL_SETTINGS).putExtra(
                Settings.EXTRA_NOTIFICATION_LISTENER_COMPONENT_NAME,
                ComponentName(c, TiyinNotificationListener::class.java).flattenToString()
            )
        } else Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
        try {
            c.startActivity(i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        } catch (_: Exception) {
            c.startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        }
    }
}
