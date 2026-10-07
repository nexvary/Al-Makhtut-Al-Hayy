package org.almakhutut.alhayy

import android.content.ContentValues
import android.os.Build
import android.provider.MediaStore
import androidx.compose.ui.graphics.asAndroidBitmap
import android.graphics.Bitmap
import android.graphics.pdf.PdfDocument
import android.net.Uri
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.runBlocking
import org.almakhutut.alhayy.data.IiifLoader
import org.almakhutut.alhayy.data.LocalBookStore
import org.json.JSONObject
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.BeforeClass
import org.junit.After
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

@RunWith(AndroidJUnit4::class)
class OfflineReaderTest {
    companion object {
        @JvmStatic @BeforeClass fun selectLanguage() { selectTestLanguage() }
    }

    @get:Rule val rule = createAndroidComposeRule<MainActivity>()
    private val ids = mutableListOf<String>()
    private fun text(id: Int) = rule.activity.getString(id)
    private fun store() = LocalBookStore(rule.activity)
    private fun proof(name: String) {
        rule.waitForIdle()
        val screenshot = rule.onRoot().captureToImage().asAndroidBitmap()
        if (Build.VERSION.SDK_INT >= 29) {
            // Public test output survives Gradle uninstalling fixture APKs after the suite.
            val values = ContentValues().apply {
                put(MediaStore.Images.Media.DISPLAY_NAME, "$name.png")
                put(MediaStore.Images.Media.MIME_TYPE, "image/png")
                put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/MakhtutUiProof")
                put(MediaStore.Images.Media.IS_PENDING, 1)
            }
            val resolver = rule.activity.contentResolver
            val uri = checkNotNull(resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values))
            checkNotNull(resolver.openOutputStream(uri)).use {
                check(screenshot.compress(Bitmap.CompressFormat.PNG, 100, it))
            }
            values.clear()
            values.put(MediaStore.Images.Media.IS_PENDING, 0)
            resolver.update(uri, values, null, null)
        } else {
            val folder = File(rule.activity.getExternalFilesDir(null), "ui-proof").apply { mkdirs() }
            File(folder, "$name.png").outputStream().use {
                check(screenshot.compress(Bitmap.CompressFormat.PNG, 100, it))
            }
        }
        screenshot.recycle()
    }

    @After fun cleanup() { ids.forEach { store().delete(it) } }

    @Test fun importsPdfAndReadsBothPagesWithoutBackend() = runBlocking<Unit> {
        val file = File(rule.activity.cacheDir, "offline-test.pdf")
        val document = PdfDocument()
        try {
            repeat(2) { index ->
                val page = document.startPage(PdfDocument.PageInfo.Builder(200, 300, index + 1).create())
                page.canvas.drawColor(android.graphics.Color.WHITE)
                document.finishPage(page)
            }
            file.outputStream().use { document.writeTo(it) }
        } finally {
            document.close()
        }
        val book = store().importPdf(Uri.fromFile(file), "Offline PDF fixture")
        ids += book.id
        assertEquals(2, book.pageCount)
        rule.activityRule.scenario.recreate()
        rule.onNodeWithText(book.title).performScrollTo().performClick()
        rule.waitUntil(10_000) { rule.onAllNodesWithTag("page-image").fetchSemanticsNodes().isNotEmpty() }
        rule.onNodeWithTag("page-image").performTouchInput {
            pinch(Offset(width * .4f, height * .4f), Offset(width * .6f, height * .6f),
                Offset(width * .2f, height * .2f), Offset(width * .8f, height * .8f))
        }
        rule.onNodeWithContentDescription(text(R.string.next)).assertIsDisplayed().performClick()
        rule.onNodeWithText(rule.activity.getString(R.string.page_of, 2, 2)).assertIsDisplayed()
        proof("offline-pdf-page-2")
        rule.onNodeWithContentDescription(text(R.string.previous)).performClick()
        rule.onNodeWithText(rule.activity.getString(R.string.page_of, 1, 2)).assertIsDisplayed()
        rule.onNodeWithContentDescription(text(R.string.back)).performClick()
        rule.onNodeWithText(text(R.string.app_name)).assertIsDisplayed()
    }

    @Test fun importsMultipleImagesAndSystemBackReturnsHome() = runBlocking<Unit> {
        val files = (1..2).map { index ->
            File(rule.activity.cacheDir, "offline-image-$index.png").also { file ->
                val bitmap = Bitmap.createBitmap(20, 30, Bitmap.Config.ARGB_8888)
                file.outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
                bitmap.recycle()
            }
        }
        val book = store().importImages(files.map(Uri::fromFile), "Offline image fixture")
        ids += book.id
        assertEquals(2, LocalBookStore(rule.activity).list().first { it.id == book.id }.pages.size)
        rule.activityRule.scenario.recreate()
        rule.onNodeWithText(book.title).performScrollTo().performClick()
        rule.onNodeWithContentDescription(text(R.string.next)).performClick()
        rule.onNodeWithText(rule.activity.getString(R.string.page_of, 2, 2)).assertIsDisplayed()
        rule.activityRule.scenario.onActivity { it.onBackPressedDispatcher.onBackPressed() }
        rule.onNodeWithText(text(R.string.app_name)).assertIsDisplayed()
    }

    @Test fun invalidPdfLeavesNoPartialBook() = runBlocking<Unit> {
        val root = File(rule.activity.filesDir, "local-books")
        val before = root.listFiles()?.map { it.name }?.toSet().orEmpty()
        val invalid = File(rule.activity.cacheDir, "invalid.pdf").apply { writeText("not a PDF") }
        assertTrue(runCatching { store().importPdf(Uri.fromFile(invalid), "Invalid fixture") }.isFailure)
        assertEquals(before, root.listFiles()?.map { it.name }?.toSet().orEmpty())
    }

    @Test fun addBookControlsRemainReachableOnCompactPhone() {
        rule.onAllNodesWithText(text(R.string.add_book)).onFirst().performClick()
        rule.onNodeWithText(text(R.string.open_iiif)).performScrollTo().assertIsDisplayed()
        proof("add-book-scrolled")
        rule.onNodeWithContentDescription(text(R.string.back)).assertIsDisplayed().performClick()
        rule.onNodeWithText(text(R.string.app_name)).assertIsDisplayed()
    }

    @Test fun parsesBothIiifVersionsWithoutNetwork() {
        val v2 = JSONObject("""{"sequences":[{"canvases":[{"images":[{"resource":{"@id":"https://example.org/page.jpg"}}]}]}]}""")
        val v3 = JSONObject("""{"items":[{"items":[{"items":[{"body":{"id":"https://example.org/page.jpg"}}]}]}]}""")
        assertEquals(listOf("https://example.org/page.jpg"), IiifLoader().parse(v2))
        assertEquals(listOf("https://example.org/page.jpg"), IiifLoader().parse(v3))
        val legacy = JSONObject("""{"sequences":[{"canvases":[{"images":[{"resource":{"@id":"https://example.org/full/full/0/native.jpg","service":{"@id":"https://example.org","@context":"http://iiif.io/api/image/1/context.json"}}}]}]}]}""")
        assertEquals(listOf("https://example.org/full/full/0/native.jpg"), IiifLoader().parse(legacy))
    }
}
