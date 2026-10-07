package org.almakhutut.alhayy.data

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.withContext
import java.io.File
import java.security.MessageDigest

internal class IiifPageLoader(context: Context, private val client: IiifHttpClient = IiifNetwork.client) {
    private val cache = File(context.cacheDir, "iiif-pages").apply { mkdirs() }
    suspend fun load(original: String): Bitmap = withContext(Dispatchers.IO) {
        val preview = IiifNetwork.preview(original)
        val key = MessageDigest.getInstance("SHA-256").digest(preview.toByteArray()).joinToString("") { "%02x".format(it) }
        val target = File(cache, key)
        currentCoroutineContext().ensureActive()
        val bytes = if (target.isFile) target.readBytes() else client.get(preview, 16 * 1024 * 1024)
        currentCoroutineContext().ensureActive()
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeByteArray(bytes, 0, bytes.size, bounds)
        if (bounds.outWidth <= 0 || bounds.outHeight <= 0) {
            target.delete()
            error("IIIF image could not be decoded")
        }
        val options = BitmapFactory.Options()
        var sample = 1
        while (bounds.outWidth.toLong() * bounds.outHeight / sample / sample > 4_000_000 ||
            bounds.outWidth / sample > 4000 || bounds.outHeight / sample > 4000) sample *= 2
        options.inSampleSize = sample
        val bitmap = requireNotNull(BitmapFactory.decodeByteArray(bytes, 0, bytes.size, options))
        // Cache failure does not turn a successfully decoded page into a reader error.
        runCatching {
            synchronized(cacheLock) {
                if (!target.isFile) target.writeBytes(bytes)
                target.setLastModified(System.currentTimeMillis())
                val files = cache.listFiles().orEmpty().sortedBy { it.lastModified() }
                var size = files.sumOf { it.length() }
                for (file in files) {
                    if (size <= 64L * 1024 * 1024) break
                    val length = file.length()
                    if (file.delete()) size -= length
                }
            }
        }
        bitmap
    }
    companion object { private val cacheLock = Any() }
}
