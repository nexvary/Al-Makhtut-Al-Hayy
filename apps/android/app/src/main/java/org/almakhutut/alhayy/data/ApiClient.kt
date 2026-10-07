package org.almakhutut.alhayy.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.withContext
import org.almakhutut.alhayy.model.Manuscript
import org.almakhutut.alhayy.model.toManuscript
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

interface ApiTransport {
    fun request(url: String, body: String? = null): String
}

class UrlConnectionTransport : ApiTransport {
    override fun request(url: String, body: String?): String {
        val connection = URL(url).openConnection() as HttpURLConnection
        try {
            connection.requestMethod = if (body == null) "GET" else "POST"
            connection.connectTimeout = 10_000
            connection.readTimeout = 30_000
            connection.setRequestProperty("Accept", "application/json")
            if (body != null) {
                connection.doOutput = true
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                connection.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
            }
            val code = connection.responseCode
            if (code !in 200..299) error("HTTP $code")
            val output = ByteArrayOutputStream()
            connection.inputStream.use { input ->
                val buffer = ByteArray(8192)
                while (true) {
                    val count = input.read(buffer)
                    if (count < 0) break
                    require(output.size() + count <= 2 * 1024 * 1024) { "Metadata response exceeds limit" }
                    output.write(buffer, 0, count)
                }
            }
            return output.toString(Charsets.UTF_8.name())
        } finally {
            connection.disconnect()
        }
    }
}

class ApiClient(private val transport: ApiTransport = UrlConnectionTransport()) : ReaderKnowledgeClient {
    private fun segment(value: String) = URLEncoder.encode(value, "UTF-8").replace("+", "%20")

    suspend fun manuscripts(baseUrl: String): List<Manuscript> = withContext(Dispatchers.IO) {
        val array = JSONArray(transport.request("${baseUrl.trimEnd('/')}/api/v1/manuscripts"))
        ensureActive()
        (0 until array.length()).map { array.getJSONObject(it).toManuscript() }
    }

    suspend fun manuscript(baseUrl: String, id: String): Manuscript = withContext(Dispatchers.IO) {
        val text = transport.request("${baseUrl.trimEnd('/')}/api/v1/manuscripts/${segment(id)}")
        ensureActive()
        JSONObject(text).toManuscript()
    }

    override suspend fun layers(base: String, manuscriptId: String, pageId: String): List<SourcedRepresentation> = withContext(Dispatchers.IO) {
        val result = JSONObject(transport.request("${base.trimEnd('/')}/api/v1/living/manuscripts/${segment(manuscriptId)}/pages/${segment(pageId)}/layers"))
        ensureActive()
        val array = result.getJSONArray("layers")
        (0 until array.length()).map { array.getJSONObject(it).toSourcedRepresentation("id") }.also { layers ->
            require(layers.all { it.source.manuscriptId == manuscriptId && it.source.pageId == pageId }) { "Wrong source page in layer response" }
        }
    }

    override suspend fun askRegion(base: String, source: SourceSelection, question: String, task: String, targetLanguage: String?): LabReading = withContext(Dispatchers.IO) {
        val anchor = JSONObject().put("manuscript_id", source.manuscriptId).put("page_id", source.pageId)
            .put("region_id", source.regionId ?: JSONObject.NULL)
        val body = JSONObject().put("source", anchor).put("question", question).put("task", task)
            .put("target_language", targetLanguage ?: JSONObject.NULL)
        val result = JSONObject(transport.request("${base.trimEnd('/')}/api/v1/ai-lab/ask", body.toString()))
        ensureActive()
        val array = result.getJSONArray("evidence")
        val evidence = (0 until array.length()).map { array.getJSONObject(it).toSourcedRepresentation("revision_id") }
        require(evidence.all { it.source == source }) { "Answer evidence belongs to another page or region" }
        LabReading(result.getBoolean("insufficient_evidence"), evidence)
    }

    // Keep the legacy API method for callers still using the original corpus endpoint.
    suspend fun ask(baseUrl: String, question: String): String = withContext(Dispatchers.IO) {
        val body = JSONObject().put("question", question).put("limit", 6)
        val result = JSONObject(transport.request("${baseUrl.trimEnd('/')}/api/v1/qa/ask", body.toString()))
        ensureActive()
        if (result.optBoolean("insufficient_evidence")) "لا توجد أدلة كافية داخل المخطوط للإجابة."
        else {
            val evidence = result.optJSONArray("evidence") ?: JSONArray()
            (0 until evidence.length()).joinToString("\n") { "• ${evidence.getJSONObject(it).optString("text")}" }
        }
    }
}
