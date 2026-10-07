package org.almakhutut.alhayy.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

class IiifLoader {
    suspend fun load(url: String): List<String> = withContext(Dispatchers.IO) {
        require(url.startsWith("https://")) { "IIIF URL must use HTTPS" }
        val text = requestManifest(url)
        parse(JSONObject(text))
    }

    private fun requestManifest(url: String): String = IiifNetwork.manifest(url)

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
