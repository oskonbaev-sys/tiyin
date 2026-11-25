package com.fr8masters.tiyin

import android.annotation.SuppressLint
import android.content.Intent
import android.graphics.Bitmap
import android.net.Uri
import android.os.Bundle
import android.webkit.CookieManager
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import androidx.activity.result.contract.ActivityResultContracts
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var refresh: SwipeRefreshLayout
    private var fileCallback: ValueCallback<Array<Uri>>? = null

    // Выбор чека/скриншота для вкладки AI (<input type="file">)
    private val pickFile = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { r ->
        fileCallback?.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(r.resultCode, r.data))
        fileCallback = null
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        setSupportActionBar(findViewById(R.id.toolbar))
        Store.fitSystemBars(findViewById(R.id.root))

        webView = findViewById(R.id.webview)
        refresh = findViewById(R.id.refresh)

        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            cacheMode = WebSettings.LOAD_DEFAULT
            mediaPlaybackRequiresUserGesture = false
        }
        CookieManager.getInstance().setAcceptCookie(true)
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true)

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(
                view: WebView,
                request: WebResourceRequest
            ): Boolean {
                val uri = request.url
                if (uri.host == HOST) return false
                // Внешние ссылки (t.me и т.д.) открываем в браузере/Telegram
                try {
                    startActivity(Intent(Intent.ACTION_VIEW, uri))
                } catch (_: Exception) {
                }
                return true
            }

            override fun onPageStarted(view: WebView, url: String?, favicon: Bitmap?) {
                refresh.isRefreshing = true
            }

            override fun onPageFinished(view: WebView, url: String?) {
                refresh.isRefreshing = false
            }
        }

        webView.webChromeClient = object : WebChromeClient() {
            override fun onShowFileChooser(
                view: WebView,
                callback: ValueCallback<Array<Uri>>,
                params: FileChooserParams
            ): Boolean {
                fileCallback?.onReceiveValue(null)
                fileCallback = callback
                return try {
                    pickFile.launch(params.createIntent())
                    true
                } catch (_: Exception) {
                    fileCallback = null
                    false
                }
            }
        }

        refresh.setOnRefreshListener { webView.reload() }

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) {
                    webView.goBack()
                } else {
                    finish()
                }
            }
        })

        if (savedInstanceState != null) {
            webView.restoreState(savedInstanceState)
        } else {
            val key = Store.key(this)
            if (key == null) {
                startActivity(Intent(this, LoginActivity::class.java)); finish(); return
            }
            webView.loadUrl("$START_URL/#app_token=" + Uri.encode(key))
        }
    }

    override fun onCreateOptionsMenu(menu: android.view.Menu): Boolean {
        if (BuildConfig.AUTO_RECORD) menu.add(0, 1, 0, R.string.settings_menu)
        else menu.add(0, 3, 0, R.string.auto_macrodroid)
        menu.add(0, 4, 1, R.string.privacy)
        menu.add(0, 2, 2, R.string.logout)
        return true
    }

    override fun onOptionsItemSelected(item: android.view.MenuItem): Boolean {
        when (item.itemId) {
            1 -> startActivity(Intent(this, SettingsActivity::class.java))
            4 -> try {
                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(Store.PRIVACY_URL)))
            } catch (_: Exception) {}
            3 -> try {
                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://t.me/${Store.BOT}?start=macro")))
            } catch (_: Exception) {}
            2 -> {
                Store.logout(this)
                CookieManager.getInstance().removeAllCookies(null)
                webView.clearCache(true)
                webView.evaluateJavascript("try{localStorage.removeItem('tiyin_app_token')}catch(e){}", null)
                startActivity(Intent(this, LoginActivity::class.java))
                finish()
            }
        }
        return true
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        webView.saveState(outState)
    }

    override fun onPause() {
        super.onPause()
        CookieManager.getInstance().flush()
    }

    companion object {
        private const val HOST = "tiyin.fr8mastersllc.com"
        private const val START_URL = "https://$HOST"
    }
}
