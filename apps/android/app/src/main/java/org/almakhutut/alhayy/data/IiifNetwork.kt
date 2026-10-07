package org.almakhutut.alhayy.data

import java.net.HttpURLConnection
import java.net.URI
import java.net.URL
import java.time.ZonedDateTime
import java.time.format.DateTimeFormatter

class IiifRequestException(val status: Int, val retryAt: Long = 0) : Exception("IIIF HTTP $status")
internal data class IiifResponse(val status: Int, val body: ByteArray, val retryAfter: String? = null)

/** Shared per-host cooldown for metadata and page images; never retries a denial immediately. */
internal class IiifHttpClient(
    private val now: () -> Long = System::currentTimeMillis,
    private val transport: (String, Int) -> IiifResponse = ::request,
) {
    private val cooldowns = mutableMapOf<String, Long>()
    private val locks = mutableMapOf<String, Any>()
    fun get(url: String, limit: Int): ByteArray {
        val uri = URI(url)
        require(uri.scheme == "https" && !uri.host.isNullOrBlank() && uri.userInfo == null) { "IIIF URL must use HTTPS" }
        val host = uri.host.lowercase()
        val lock = synchronized(locks) { locks.getOrPut(host) { Any() } }
        return synchronized(lock) {
            val blocked = synchronized(cooldowns) { cooldowns[host] ?: 0L }
            if (blocked > now()) throw IiifRequestException(429, blocked)
            val response = transport(url, limit)
            if (response.status == 429 || response.status == 503) {
                val until = retryDeadline(response.retryAfter, now())
                synchronized(cooldowns) { cooldowns[host] = until }
                throw IiifRequestException(response.status, until)
            }
            if (response.status !in 200..299) throw IiifRequestException(response.status)
            require(response.body.size <= limit) { "IIIF response exceeds size limit" }
            response.body
        }
    }
    companion object {
        internal fun retryDeadline(value: String?, now: Long): Long {
            val seconds = value?.trim()?.toLongOrNull()?.takeIf { it >= 0 }
            if (seconds != null) return now + seconds.coerceAtLeast(1).coerceAtMost((Long.MAX_VALUE - now) / 1000) * 1000
            val date = runCatching { ZonedDateTime.parse(value, DateTimeFormatter.RFC_1123_DATE_TIME).toInstant().toEpochMilli() }.getOrNull()
            return date?.coerceAtLeast(now + 1000) ?: (now + 60_000)
        }
        private fun request(url: String, limit: Int): IiifResponse {
            val connection = URL(url).openConnection() as HttpURLConnection
            try {
                connection.connectTimeout = 15_000
                connection.readTimeout = 30_000
                connection.instanceFollowRedirects = true
                connection.setRequestProperty("User-Agent", "Al-Makhtut-Al-Hayy/0.1.5 (+https://nexvary.com/)")
                connection.setRequestProperty("Accept", "application/ld+json, application/json, image/jpeg, image/*;q=0.9")
                if (URI(url).host.equals("gallica.bnf.fr", ignoreCase = true)) {
                    connection.setRequestProperty("Referer", "https://gallica.bnf.fr/")
                }
                val status = connection.responseCode
                if (status !in 200..299) return IiifResponse(status, byteArrayOf(), connection.getHeaderField("Retry-After"))
                require(connection.contentLengthLong <= limit) { "IIIF response exceeds size limit" }
                val body = connection.inputStream.use { input ->
                    val output = java.io.ByteArrayOutputStream()
                    val buffer = ByteArray(8192)
                    while (true) {
                        val count = input.read(buffer)
                        if (count < 0) break
                        require(output.size() + count <= limit) { "IIIF response exceeds size limit" }
                        output.write(buffer, 0, count)
                    }
                    output.toByteArray()
                }
                return IiifResponse(status, body)
            } finally { connection.disconnect() }
        }
    }
}

internal object IiifNetwork {
    val client = IiifHttpClient()
    private val manifests = linkedMapOf<String, Pair<Long, String>>()
    @Synchronized fun manifest(url: String): String {
        manifests[url]?.takeIf { System.currentTimeMillis() - it.first < 15 * 60_000 }?.let { return it.second }
        val body = String(client.get(url, 2 * 1024 * 1024), Charsets.UTF_8)
        manifests[url] = System.currentTimeMillis() to body
        while (manifests.size > 3) manifests.remove(manifests.keys.first())
        return body
    }
    /** Reduce only recognized IIIF full-image requests; retain the stored original URL. */
    fun preview(url: String): String = url.replace(Regex("/full/(full|max)/0/(native|default)\\.jpg$"), "/full/1600,/0/$2.jpg")
}
