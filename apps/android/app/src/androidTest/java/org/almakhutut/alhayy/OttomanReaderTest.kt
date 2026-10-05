package org.almakhutut.alhayy

import android.graphics.Bitmap
import androidx.activity.compose.setContent
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.almakhutut.alhayy.data.*
import org.almakhutut.alhayy.model.Manuscript
import org.almakhutut.alhayy.model.Page
import org.almakhutut.alhayy.ui.*
import org.junit.Assert.*
import org.junit.BeforeClass
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.util.concurrent.CopyOnWriteArrayList

@RunWith(AndroidJUnit4::class)
class OttomanReaderTest {
    companion object { @JvmStatic @BeforeClass fun selectLanguage() { selectTestLanguage() } }
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()
    private fun scroll(tag: String): SemanticsNodeInteraction {
        rule.onNodeWithTag("remote-reader-list").performScrollToNode(hasTestTag(tag))
        return rule.onNodeWithTag(tag).performScrollTo()
    }
    @Test fun independentStagesDictionaryAndProgressivePracticeKeepOriginalAndBack() {
        val requests = CopyOnWriteArrayList<Int>()
        val source = SourceSelection("synthetic", "p1")
        val reading = SourcedRepresentation("reviewed-fixture", "transcription", "verified", "Synthetic reviewed reading",
            source, null, null, "fixture-reviewer", null)
        val client = object : OttomanReaderClient {
            override suspend fun pipeline(base: String, source: SourceSelection) = listOf(OttomanRevision("transcription", reading, null))
            override suspend fun dictionary(base: String, query: String) = listOf(DictionaryReading(reading,
                "Synthetic dictionary spelling", "Synthetic Latin", "Synthetic Turkish", null, null, null))
            override suspend fun exercises(base: String, source: SourceSelection) = listOf(OttomanExercise("lesson", "Synthetic exercise", "Synthetic rights fixture"))
            override suspend fun attempt(base: String, source: SourceSelection, id: String, text: String, step: Int): ExerciseFeedback {
                requests.add(step)
                return ExerciseFeedback(text == "Synthetic attempt", 2,
                    if (step == 0) emptyList() else listOf("transcription" to "Synthetic revealed reading"))
            }
        }
        val knowledge = object : ReaderKnowledgeClient {
            override suspend fun layers(base: String, manuscriptId: String, pageId: String) = emptyList<SourcedRepresentation>()
            override suspend fun askRegion(base: String, source: SourceSelection, question: String, task: String, targetLanguage: String?) = LabReading(true, emptyList())
        }
        val image = File(rule.activity.cacheDir, "ottoman-fixture.png")
        val bitmap = Bitmap.createBitmap(100, 140, Bitmap.Config.ARGB_8888)
        image.outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }; bitmap.recycle()
        val manuscript = Manuscript("synthetic", "Synthetic Ottoman fixture", null, null, null,
            listOf(Page("p1", 1, null, image.toURI().toString(), 100, 140, emptyList())))
        rule.activityRule.scenario.onActivity { activity -> activity.setContent {
            var closed by remember { mutableStateOf(false) }
            AlMakhtutTheme {
                if (closed) Text("ottoman-closed")
                else ReaderScreen(manuscript, "https://example.invalid", onBack = { closed = true }, knowledgeClient = knowledge, ottomanClient = client)
            }
        } }
        scroll("ottoman-toggle").performClick()
        rule.onNodeWithTag("remote-reader-list").performScrollToNode(hasText("Synthetic reviewed reading"))
        rule.onNodeWithText("Synthetic reviewed reading").assertIsDisplayed()
        scroll("ottoman-word").performTextInput("fixture")
        scroll("ottoman-lookup").performClick()
        rule.onNodeWithTag("remote-reader-list").performScrollToNode(hasText("Synthetic dictionary spelling"))
        rule.onNodeWithText("Synthetic dictionary spelling").assertIsDisplayed()
        scroll("ottoman-exercise").performClick()
        rule.onNodeWithText("Synthetic exercise").performClick()
        scroll("ottoman-attempt").performTextInput("Synthetic attempt")
        scroll("ottoman-check").performClick()
        scroll("ottoman-feedback").assertIsDisplayed()
        assertEquals(listOf(0), requests.toList())
        rule.onNodeWithText("Synthetic revealed reading", substring = true).assertDoesNotExist()
        scroll("ottoman-reveal").performClick()
        rule.onNodeWithTag("remote-reader-list").performScrollToNode(hasText("Synthetic revealed reading", substring = true))
        rule.onNodeWithText("Synthetic revealed reading", substring = true).assertIsDisplayed()
        assertEquals(listOf(0, 1), requests.toList())
        rule.onNodeWithContentDescription(rule.activity.getString(R.string.back)).performClick()
        rule.onNodeWithText("ottoman-closed").assertIsDisplayed()
    }
}
