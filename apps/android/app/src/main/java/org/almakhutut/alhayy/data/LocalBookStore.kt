package org.almakhutut.alhayy.data

import android.content.Context
import android.graphics.BitmapFactory
import android.util.AtomicFile
import android.graphics.pdf.PdfRenderer
import android.net.Uri
import android.os.ParcelFileDescriptor
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.UUID

class LocalBookStore(private val context: Context) {
    private val root = File(context.filesDir, "local-books").apply { mkdirs() }
    private val indexFile = AtomicFile(File(root, "library.json"))

    fun list(): List<LocalBook> = synchronized(indexLock) {
        if (!indexFile.baseFile.isFile && !File(root, "library.json.bak").isFile) {
            return@synchronized emptyList()
        }
        runCatching {
            val array = JSONArray(String(indexFile.readFully(), Charsets.UTF_8))
            (0 until array.length()).map { array.getJSONObject(it).toBook() }
        }.getOrDefault(emptyList()).sortedByDescending { it.createdAt }
    }

    suspend fun importPdf(uri: Uri, title: String): LocalBook = withContext(Dispatchers.IO) {
        val id = UUID.randomUUID().toString()
        val folder = File(root, id).apply { mkdirs() }
        var saved = false
        try {
        val target = File(folder, "book.pdf")
        context.contentResolver.openInputStream(uri).use { input ->
            requireNotNull(input) { "Unable to open PDF" }
            target.outputStream().use { output -> copyLimited(input, output) }
        }
        val count = ParcelFileDescriptor.open(target, ParcelFileDescriptor.MODE_READ_ONLY).use { pfd ->
            PdfRenderer(pfd).use { it.pageCount }
        }
        require(count > 0) { "PDF has no pages" }
        val book = LocalBook(
            id = id,
            title = title.ifBlank { "PDF" },
            kind = LocalBookKind.PDF,
            source = target.absolutePath,
            pageCount = count,
            createdAt = System.currentTimeMillis(),
        )
        currentCoroutineContext().ensureActive()
        save(book)
        saved = true
        book
        } finally {
            if (!saved) folder.deleteRecursively()
        }
    }

    suspend fun importImages(uris: List<Uri>, title: String): LocalBook = withContext(Dispatchers.IO) {
        require(uris.isNotEmpty()) { "No images selected" }
        require(uris.size <= 500) { "Import at most 500 images at a time" }
        val id = UUID.randomUUID().toString()
        val folder = File(root, id).apply { mkdirs() }
        var saved = false
        try {
        val pages = uris.mapIndexed { pageIndex, uri ->
            val mime = context.contentResolver.getType(uri).orEmpty()
            val extension = when {
                mime.contains("png") -> ".png"
                mime.contains("webp") -> ".webp"
                else -> ".jpg"
            }
            val number = (pageIndex + 1).toString().padStart(4, '0')
            val target = File(folder, "page-" + number + extension)
            context.contentResolver.openInputStream(uri).use { input ->
                requireNotNull(input) { "Unable to open image" }
                target.outputStream().use { output -> copyLimited(input, output) }
            }
            val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
            BitmapFactory.decodeFile(target.absolutePath, bounds)
            require(bounds.outWidth > 0 && bounds.outHeight > 0) { "Invalid image" }
            target.toURI().toString()
        }
        val book = LocalBook(
            id = id,
            title = title.ifBlank { "Images" },
            kind = LocalBookKind.IMAGES,
            source = folder.absolutePath,
            pages = pages,
            pageCount = pages.size,
            createdAt = System.currentTimeMillis(),
        )
        currentCoroutineContext().ensureActive()
        save(book)
        saved = true
        book
        } finally {
            if (!saved) folder.deleteRecursively()
        }
    }

    suspend fun importIiif(url: String, title: String): LocalBook = withContext(Dispatchers.IO) {
        val pages = IiifLoader().load(url)
        require(pages.isNotEmpty()) { "IIIF manifest contains no image pages" }
        val book = LocalBook(
            id = UUID.randomUUID().toString(),
            title = title.ifBlank { "IIIF" },
            kind = LocalBookKind.IIIF,
            source = url,
            pages = pages,
            pageCount = pages.size,
            createdAt = System.currentTimeMillis(),
        )
        currentCoroutineContext().ensureActive()
        save(book)
        book
    }

    fun delete(bookId: String): Boolean = synchronized(indexLock) {
        val current = list()
        val target = current.firstOrNull { it.id == bookId } ?: return@synchronized false
        if (target.kind != LocalBookKind.IIIF) File(root, bookId).deleteRecursively()
        writeAll(current.filterNot { it.id == bookId })
        true
    }

    private fun save(book: LocalBook) = synchronized(indexLock) {
        writeAll(list().filterNot { it.id == book.id } + book)
    }

    private fun writeAll(books: List<LocalBook>) {
        val array = JSONArray()
        books.forEach { array.put(it.toJson()) }
        val stream = indexFile.startWrite()
        try {
            stream.write(array.toString().toByteArray(Charsets.UTF_8))
            indexFile.finishWrite(stream)
        } catch (error: Exception) {
            indexFile.failWrite(stream)
            throw error
        }
    }

    private suspend fun copyLimited(input: java.io.InputStream, output: java.io.OutputStream) {
        val buffer = ByteArray(8192)
        var total = 0L
        while (true) {
            currentCoroutineContext().ensureActive()
            val read = input.read(buffer)
            if (read < 0) break
            total += read
            require(total <= 128L * 1024 * 1024) { "File exceeds 128 MiB import limit" }
            output.write(buffer, 0, read)
        }
    }

    companion object {
        private val indexLock = Any()
    }

    private fun LocalBook.toJson(): JSONObject = JSONObject()
        .put("id", id)
        .put("title", title)
        .put("kind", kind.name)
        .put("source", source)
        .put("pages", JSONArray(pages))
        .put("pageCount", pageCount)
        .put("createdAt", createdAt)

    private fun JSONObject.toBook(): LocalBook {
        val pageArray = optJSONArray("pages") ?: JSONArray()
        val pages = (0 until pageArray.length()).map { pageArray.getString(it) }
        return LocalBook(
            id = getString("id"),
            title = getString("title"),
            kind = LocalBookKind.valueOf(getString("kind")),
            source = getString("source"),
            pages = pages,
            pageCount = getInt("pageCount"),
            createdAt = getLong("createdAt"),
        )
    }
}
