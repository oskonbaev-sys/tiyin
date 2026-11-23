package com.fr8masters.tiyin

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.View
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.widget.SwitchCompat

/** Настройки автозаписи: только статус и кнопки, ничего вводить не нужно. */
class SettingsActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)
        title = getString(R.string.settings_title)

        findViewById<Button>(R.id.btn_access).setOnClickListener { Store.openAccess(this) }
        findViewById<Button>(R.id.btn_restricted).setOnClickListener {
            startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                Uri.fromParts("package", packageName, null)))
        }
        findViewById<Button>(R.id.btn_bot).setOnClickListener {
            try {
                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://t.me/${Store.BOT}?start=android")))
            } catch (_: Exception) {}
        }
        findViewById<SwitchCompat>(R.id.sw_enabled).apply {
            isChecked = Store.enabled(this@SettingsActivity)
            setOnCheckedChangeListener { _, v -> Store.setEnabled(this@SettingsActivity, v) }
        }
    }

    override fun onResume() {
        super.onResume()
        val linked = Store.key(this) != null
        val access = Store.hasAccess(this)
        val status = findViewById<TextView>(R.id.status)
        status.setText(when {
            !linked -> R.string.st_not_linked
            !access -> R.string.st_no_access
            else -> R.string.st_ok
        })
        findViewById<View>(R.id.btn_bot).visibility = if (linked) View.GONE else View.VISIBLE
        findViewById<View>(R.id.btn_access).visibility = if (linked && !access) View.VISIBLE else View.GONE
        // Android 13+: у приложений не из Play Market доступ к уведомлениям сначала заблокирован
        findViewById<View>(R.id.restricted_box).visibility =
            if (linked && !access && Build.VERSION.SDK_INT >= 33) View.VISIBLE else View.GONE
    }
}
