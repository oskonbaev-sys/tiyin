package com.fr8masters.tiyin

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONObject

/** Открывается по ссылке из бота (tiyin://link?t=...): сам получает ключ и ведёт к переключателю доступа. */
class LinkActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val token = intent?.data?.getQueryParameter("t")
        if (token.isNullOrBlank()) { done(); return }

        Net.async {
            val res = Net.post("/api/android/claim", JSONObject().put("token", token))
            val key = res?.optString("key").orEmpty()
            runOnUiThread {
                if (key.isNotEmpty()) {
                    Store.setKey(this, key)
                    if (!Store.hasAccess(this)) {
                        Toast.makeText(this, R.string.toggle_hint, Toast.LENGTH_LONG).show()
                        Store.openAccess(this)
                    }
                } else {
                    Toast.makeText(this, R.string.link_failed, Toast.LENGTH_LONG).show()
                }
                done()
            }
        }
    }

    private fun done() {
        startActivity(Intent(this, SettingsActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP))
        finish()
    }
}
