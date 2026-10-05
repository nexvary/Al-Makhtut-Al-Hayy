package org.almakhutut.alhayy

import android.content.ContentValues
import android.graphics.Bitmap
import android.provider.MediaStore
import androidx.activity.compose.setContent
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.almakhutut.alhayy.data.*
import org.almakhutut.alhayy.model.*
import org.almakhutut.alhayy.ui.AlMakhtutTheme
import org.almakhutut.alhayy.ui.ReaderScreen
import org.junit.Assert.*
import org.junit.BeforeClass
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.concurrent.CopyOnWriteArrayList

@RunWith(AndroidJUnit4::class)
class ReaderKnowledgeTest {
    companion object {
        @JvmStatic @BeforeClass fun selectLanguage() { selectTestLanguage() }
    }
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()
    private fun text(id: Int) = rule.activity.getString(id)
    private fun scrollTo(matcher: SemanticsMatcher): SemanticsNodeInteraction {
        rule.onNodeWithTag("remote-reader-list").performScrollToNode(matcher)
        return rule.onNode(matcher).performScrollTo()
    }
    private fun proof() {
        val bitmap = rule.onRoot().captureToImage().asAndroidBitmap()
        val values = ContentValues().apply {
            put(MediaStore.Images.Media.DISPLAY_NAME, "living-layers-native.png")
            put(MediaStore.Images.Media.MIME_TYPE, "image/png")
            put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/MakhtutUiProof")
            put(MediaStore.Images.Media.IS_PENDING, 1)
        }
        val resolver = rule.activity.contentResolver
        val uri = checkNotNull(resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values))
        checkNotNull(resolver.openOutputStream(uri)).use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
        bitmap.recycle()
        values.clear(); values.put(MediaStore.Images.Media.IS_PENDING, 0)
        resolver.update(uri, values, null, null)
    }

    @Test fun scopedLabHistoryPageChangeAndBackWorkOnCompactPhone() {
        val queries = CopyOnWriteArrayList<SourceSelection>()
        val client = object : ReaderKnowledgeClient {
            override suspend fun layers(base: String, manuscriptId: String, pageId: String) = listOf(
                SourcedRepresentation("revision-$pageId", "machine_reading", "machine", "Synthetic source $pageId",
                    SourceSelection(manuscriptId, pageId), null, null, null, "2026-01-01T00:00:00Z"))
            override suspend fun askRegion(base: String, source: SourceSelection, question: String,
                task: String, targetLanguage: String?): LabReading {
                queries.add(source)
                return LabReading(true, emptyList())
            }
        }
        val image = File(rule.activity.cacheDir, "knowledge-fixture.png")
        val bitmap = Bitmap.createBitmap(100, 140, Bitmap.Config.ARGB_8888)
        image.outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
        bitmap.recycle()
        val pages = (1..2).map { index -> Page("p$index", index, null, image.toURI().toString(), 100, 140,
            listOf(Region("r$index", "text_line", emptyList(), listOf(TextLayer("htr_raw", "Synthetic region $index", "machine", null))))) }
        val manuscript = Manuscript("fixture", "Synthetic manuscript", null, null, null, pages)
        rule.activityRule.scenario.onActivity { activity -> activity.setContent {
            var closed by remember { mutableStateOf(false) }
            AlMakhtutTheme {
                if (closed) Text("knowledge-reader-closed")
                else ReaderScreen(manuscript, "https://example.invalid", onBack = { closed = true }, knowledgeClient = client)
            }
        } }
        scrollTo(hasTestTag("living-layers-toggle")).performClick()
        scrollTo(hasText("Synthetic source p1")).assertIsDisplayed()
        scrollTo(hasText(rule.activity.getString(R.string.confidence_value, text(R.string.unknown_confidence)))).assertIsDisplayed()
        proof()
        scrollTo(hasTestTag("living-layers-toggle")).performClick()
        scrollTo(hasText("Synthetic region 1")).performClick()
        scrollTo(hasTestTag("lab-source")).assertTextContains("r1")
        scrollTo(hasTestTag("lab-question")).performTextInput("Read this region")
        scrollTo(hasText(text(R.string.next))).assertIsDisplayed()
        scrollTo(hasTestTag("lab-question")).assertTextContains("Read this region")
        scrollTo(hasTestTag("lab-submit")).performClick()
        rule.waitUntil(5_000) { queries.isNotEmpty() }
        assertEquals(SourceSelection("fixture", "p1", "r1"), queries.single())
        scrollTo(hasTestTag("lab-insufficient")).assertIsDisplayed()
        scrollTo(hasText(text(R.string.next))).performClick()
        scrollTo(hasTestTag("lab-source")).assertTextContains("p2")
        rule.onNodeWithTag("lab-insufficient").assertDoesNotExist()
        scrollTo(hasTestTag("lab-submit")).assertIsNotEnabled()
        rule.onNodeWithContentDescription(text(R.string.back)).performClick()
        rule.onNodeWithText("knowledge-reader-closed").assertIsDisplayed()
    }
}
