package org.almakhutut.alhayy.data

import android.content.Context
import android.graphics.pdf.PdfRenderer
import android.net.Uri
import android.os.ParcelFileDescriptor
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.UUID

class LocalBookStore(private val context: Context) {
    private val root = File(context.filesDir, "local-books").apply { mkdirs() }
    private val indexFile = File(root, "library.json")

    fun list(): List<LocalBook> {
        if (!indexFile.isFile) return emptyList()
        return runCatching {
            val array = JSONArray(indexFile.readText())
            (0 until array.length()).map { array.getJSONObject(it).toBook() }
        }.getOrDefault(emptyList()).sortedByDescending { it.createdAt }
    }

    suspend fun importPdf(uri: Uri, title: String): LocalBook = withContext(Dispatchers.IO) {
        val id = UUID.randomUUID().toString()
        val folder = File(root, id).apply { mkdirs() }
        val target = File(folder, "book.pdf")
        context.contentResolver.openInputStream(uri).use { input ->
            requireNotNull(input) { "Unable to open PDF" }
            target.outputStream().use { output -> input.copyTo(output) }
        }
        val count = ParcelFileDescriptor.open(target, ParcelFileDescriptor.MODE_READ_ONLY).use { pfd ->
            PdfRenderer(pfd).use { it.pageCount }
        }
        val book = LocalBook(
            id = id,
            title = title.ifBlank { "PDF" },
            kind = LocalBookKind.PDF,
            source = target.absolutePath,
            pageCount = count,
            createdAt = System.currentTimeMillis(),
        )
        save(book)
        book
    }

    suspend fun importImages(uris: List<Uri>, title: String): LocalBook = withContext(Dispatchers.IO) {
        require(uris.isNotEmpty()) { "No images selected" }
        val id = UUID.randomUUID().toString()
        val folder = File(root, id).apply { mkdirs() }
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
                target.outputStream().use { output -> input.copyTo(output) }
            }
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
        save(book)
        book
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
        save(book)
        book
    }

    fun delete(bookId: String): Boolean {
        val current = list()
        val target = current.firstOrNull { it.id == bookId } ?: return false
        if (target.kind != LocalBookKind.IIIF) File(root, bookId).deleteRecursively()
        writeAll(current.filterNot { it.id == bookId })
        return true
    }

    private fun save(book: LocalBook) {
        writeAll(list().filterNot { it.id == book.id } + book)
    }

    private fun writeAll(books: List<LocalBook>) {
        val array = JSONArray()
        books.forEach { array.put(it.toJson()) }
        indexFile.writeText(array.toString())
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
