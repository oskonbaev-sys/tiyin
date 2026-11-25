package com.fr8masters.tiyin

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONObject

/** Вход по одноразовому коду из бота (/login). После входа Telegram не нужен. */
class LoginActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (Store.key(this) != null) { openApp(); return }
        setContentView(R.layout.activity_login)
        Store.fitSystemBars(findViewById(R.id.login_root))

        val code = findViewById<EditText>(R.id.code)
        val btn = findViewById<Button>(R.id.btn_login)
        val err = findViewById<TextView>(R.id.error)
        val progress = findViewById<ProgressBar>(R.id.progress)

        findViewById<Button>(R.id.btn_get_code).setOnClickListener {
            try {
                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://t.me/${Store.BOT}")))
            } catch (_: Exception) {}
        }

        btn.setOnClickListener {
            val c = code.text.toString().trim()
            if (c.length < 4) { err.setText(R.string.code_short); return@setOnClickListener }
            err.text = ""
            btn.isEnabled = false
            progress.visibility = View.VISIBLE
            Net.async {
                val res = Net.post("/api/app/login", JSONObject().put("code", c))
                val token = res?.optString("token").orEmpty()
                runOnUiThread {
                    progress.visibility = View.GONE
                    btn.isEnabled = true
                    if (token.isNotEmpty()) {
                        Store.setKey(this, token)
                        openApp()
                    } else {
                        err.setText(R.string.code_bad)
                    }
                }
            }
        }
    }

    private fun openApp() {
        startActivity(Intent(this, MainActivity::class.java))
        finish()
    }
}
