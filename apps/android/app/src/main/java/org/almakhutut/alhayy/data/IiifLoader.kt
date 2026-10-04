package org.almakhutut.alhayy.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class IiifLoader {
    suspend fun load(url: String): List<String> = withContext(Dispatchers.IO) {
        require(url.startsWith("https://")) { "IIIF URL must use HTTPS" }
        val text = requestManifest(url)
        parse(JSONObject(text))
    }

    private fun requestManifest(url: String): String {
        var lastCode = -1
        val userAgents = listOf(
            "Al-Makhtut-Al-Hayy/0.1.1 (Android; IIIF client; +https://nexvary.com/)",
            "Mozilla/5.0 (Linux; Android 15) AppleWebKit/537.36 Chrome/140 Mobile Safari/537.36",
        )
        userAgents.forEach { userAgent ->
            val connection = URL(url).openConnection() as HttpURLConnection
            try {
                connection.connectTimeout = 15_000
                connection.readTimeout = 30_000
                connection.instanceFollowRedirects = true
                connection.setRequestProperty("Accept", "application/ld+json, application/json;q=0.9, */*;q=0.1")
                connection.setRequestProperty("User-Agent", userAgent)
                connection.setRequestProperty("Referer", "https://gallica.bnf.fr/")
                connection.setRequestProperty("Accept-Language", "ar,en;q=0.8,fr;q=0.6")
                lastCode = connection.responseCode
                if (lastCode in 200..299) {
                    return connection.inputStream.bufferedReader(Charsets.UTF_8).use { it.readText() }
                }
                if (lastCode !in listOf(403, 429)) error("IIIF HTTP $lastCode")
            } finally {
                connection.disconnect()
            }
        }
        error(if (lastCode == 403) "IIIF_ACCESS_DENIED" else "IIIF HTTP $lastCode")
    }

    internal fun parse(manifest: JSONObject): List<String> {
        val v3Items = manifest.optJSONArray("items")
        if (v3Items != null) {
            return (0 until v3Items.length()).mapNotNull { i ->
                val canvas = v3Items.optJSONObject(i) ?: return@mapNotNull null
                val pages = canvas.optJSONArray("items") ?: return@mapNotNull null
                val annotationPage = pages.optJSONObject(0) ?: return@mapNotNull null
                val annotations = annotationPage.optJSONArray("items") ?: return@mapNotNull null
                val body = annotations.optJSONObject(0)?.optJSONObject("body") ?: return@mapNotNull null
                val services = body.optJSONArray("service")
                val service = services?.optJSONObject(0)?.optString("id")
                    ?: body.optJSONObject("service")?.optString("id")
                when {
                    body.optString("id").startsWith("https://") -> body.optString("id")
                    !service.isNullOrBlank() -> service.trimEnd('/') + "/full/max/0/default.jpg"
                    else -> null
                }
            }
        }

        val sequences = manifest.optJSONArray("sequences")
        val canvases = sequences?.optJSONObject(0)?.optJSONArray("canvases")
        if (canvases != null) {
            return (0 until canvases.length()).mapNotNull { i ->
                val canvas = canvases.optJSONObject(i) ?: return@mapNotNull null
                val images = canvas.optJSONArray("images") ?: return@mapNotNull null
                val resource = images.optJSONObject(0)?.optJSONObject("resource") ?: return@mapNotNull null
                val service = resource.optJSONObject("service")?.optString("@id")
                when {
                    resource.optString("@id").startsWith("https://") -> resource.optString("@id")
                    !service.isNullOrBlank() -> {
                        val legacy = resource.optJSONObject("service")
                            ?.optString("@context").orEmpty().contains("/image/1/")
                        service.trimEnd('/') + "/full/full/0/" +
                            (if (legacy) "native.jpg" else "default.jpg")
                    }
                    else -> null
                }
            }
        }
        return emptyList()
    }
}
