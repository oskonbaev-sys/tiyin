package com.fr8masters.tiyin

import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

object Net {
    private val pool = Executors.newSingleThreadExecutor()

    fun post(path: String, body: JSONObject, bearer: String? = null): JSONObject? {
        val con = URL(Store.BASE + path).openConnection() as HttpURLConnection
        return try {
            con.requestMethod = "POST"
            con.connectTimeout = 15000
            con.readTimeout = 15000
            con.doOutput = true
            con.setRequestProperty("Content-Type", "application/json; charset=utf-8")
            if (bearer != null) con.setRequestProperty("Authorization", "Bearer $bearer")
            con.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
            val ok = con.responseCode in 200..299
            val stream = if (ok) con.inputStream else con.errorStream
            val text = stream?.bufferedReader()?.use { it.readText() } ?: "{}"
            if (ok) JSONObject(text) else null
        } catch (_: Exception) {
            null
        } finally {
            con.disconnect()
        }
    }

    fun async(block: () -> Unit) = pool.execute(block)
}
