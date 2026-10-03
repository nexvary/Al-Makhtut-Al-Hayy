package org.almakhutut.alhayy.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.almakhutut.alhayy.model.Manuscript
import org.almakhutut.alhayy.model.toManuscript
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

class ApiClient {
    suspend fun manuscripts(baseUrl: String): List<Manuscript> = withContext(Dispatchers.IO) {
        val text = request("${baseUrl.trimEnd('/')}/api/v1/manuscripts")
        val array = JSONArray(text)
        (0 until array.length()).map { array.getJSONObject(it).toManuscript() }
    }

    suspend fun manuscript(baseUrl: String, id: String): Manuscript = withContext(Dispatchers.IO) {
        val encoded = URLEncoder.encode(id, "UTF-8")
        val text = request("${baseUrl.trimEnd('/')}/api/v1/manuscripts/$encoded")
        JSONObject(text).toManuscript()
    }

    suspend fun ask(baseUrl: String, question: String): String = withContext(Dispatchers.IO) {
        val body = JSONObject().put("question", question).put("limit", 6).toString()
        val connection = (
            URL("${baseUrl.trimEnd('/')}/api/v1/qa/ask").openConnection() as HttpURLConnection
        )
        connection.requestMethod = "POST"
        connection.connectTimeout = 10_000
        connection.readTimeout = 30_000
        connection.doOutput = true
        connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
        connection.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
        val code = connection.responseCode
        val stream = if (code in 200..299) connection.inputStream else connection.errorStream
        val text = stream.bufferedReader().use { it.readText() }
        connection.disconnect()
        if (code !in 200..299) error("HTTP $code: $text")
        val json = JSONObject(text)
        val evidence = json.optJSONArray("evidence") ?: JSONArray()
        if (json.optBoolean("insufficient_evidence")) {
            "لا توجد أدلة كافية داخل المخطوط للإجابة."
        } else {
            buildString {
                appendLine("الأدلة:")
                for (index in 0 until evidence.length()) {
                    appendLine("• ${evidence.getJSONObject(index).optString("text")}")
                }
            }.trim()
        }
    }

    private fun request(url: String): String {
        val connection = (URL(url).openConnection() as HttpURLConnection)
        connection.requestMethod = "GET"
        connection.connectTimeout = 10_000
        connection.readTimeout = 30_000
        val code = connection.responseCode
        val stream = if (code in 200..299) connection.inputStream else connection.errorStream
        val text = stream.bufferedReader().use { it.readText() }
        connection.disconnect()
        if (code !in 200..299) error("HTTP $code: $text")
        return text
    }
}
