package org.almakhutut.alhayy

import android.graphics.Bitmap
import androidx.activity.compose.setContent
import androidx.appcompat.app.AppCompatDelegate
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.core.os.LocaleListCompat
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.almakhutut.alhayy.model.Manuscript
import org.almakhutut.alhayy.model.Page
import org.almakhutut.alhayy.model.Region
import org.almakhutut.alhayy.model.TextLayer
import org.almakhutut.alhayy.ui.AlMakhtutTheme
import org.almakhutut.alhayy.ui.ReaderScreen
import org.junit.BeforeClass
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

@RunWith(AndroidJUnit4::class)
class RemoteReaderTest {
    companion object {
        @JvmStatic @BeforeClass fun selectLanguage() {
            val tag = InstrumentationRegistry.getArguments().getString("language", "en")
            InstrumentationRegistry.getInstrumentation().runOnMainSync {
                AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags(tag))
            }
        }
    }
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()
    private fun text(id: Int) = rule.activity.getString(id)

    @Test fun remotePagesAndQuestionRemainReachableAndBackClosesReader() {
        val image = File(rule.activity.cacheDir, "remote-page.png")
        val bitmap = Bitmap.createBitmap(100, 140, Bitmap.Config.ARGB_8888)
        image.outputStream().use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
        bitmap.recycle()
        val pages = (1..2).map { index ->
            Page("p$index", index, null, image.toURI().toString(), 100, 140,
                listOf(Region("r$index", "text_line", emptyList(),
                    listOf(TextLayer("htr_raw", "Machine fixture $index", "machine", null)))))
        }
        val manuscript = Manuscript("fixture", "Remote fixture", null, null, null, pages)
        rule.activityRule.scenario.onActivity { activity ->
            activity.setContent {
                var closed by remember { mutableStateOf(false) }
                AlMakhtutTheme {
                    if (closed) Text("reader-closed")
                    else ReaderScreen(manuscript, "", onBack = { closed = true })
                }
            }
        }
        rule.onNodeWithText(text(R.string.next)).performScrollTo().performClick()
        rule.onNodeWithText(rule.activity.getString(R.string.page_of, 2, 2))
            .performScrollTo().assertIsDisplayed()
        rule.onNodeWithText("Machine fixture 2").performScrollTo().assertIsDisplayed()
        rule.onNodeWithText(text(R.string.ask_manuscript)).performScrollTo().assertIsDisplayed()
        rule.onNodeWithContentDescription(text(R.string.back)).assertIsDisplayed().performClick()
        rule.onNodeWithText("reader-closed").assertIsDisplayed()
    }
}
