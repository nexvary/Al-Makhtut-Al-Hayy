package org.almakhutut.alhayy

import android.content.ContextWrapper
import android.content.Intent
import androidx.activity.compose.setContent
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.almakhutut.alhayy.data.SocialLinks
import org.almakhutut.alhayy.ui.AboutScreen
import org.almakhutut.alhayy.ui.AlMakhtutTheme
import org.junit.Assert.assertEquals
import org.junit.BeforeClass
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class AboutLinksTest {
    companion object {
        @JvmStatic @BeforeClass fun selectLanguage() { selectTestLanguage() }
    }
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()

    @Test fun everyAboutButtonOpensItsExactDestination() {
        val intents = mutableListOf<Intent>()
        val context = object : ContextWrapper(rule.activity) {
            override fun startActivity(intent: Intent) { intents += intent }
        }
        rule.activityRule.scenario.onActivity { activity ->
            activity.setContent {
                CompositionLocalProvider(LocalContext provides context) {
                    AlMakhtutTheme { AboutScreen(onBack = {}) }
                }
            }
        }
        val labels = listOf(rule.activity.getString(R.string.website), "Facebook",
            rule.activity.getString(R.string.email), "YouTube", "X")
        labels.zip(SocialLinks.all).forEach { (label, destination) ->
            rule.onNodeWithText(label).performScrollTo().assertIsDisplayed().performClick()
            rule.runOnIdle {
                assertEquals(Intent.ACTION_VIEW, intents.last().action)
                assertEquals(destination, intents.last().data.toString())
            }
        }
    }
}
