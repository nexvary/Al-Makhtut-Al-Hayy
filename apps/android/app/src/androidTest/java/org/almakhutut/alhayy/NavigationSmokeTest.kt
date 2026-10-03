package org.almakhutut.alhayy

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onFirst
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class NavigationSmokeTest {
    @get:Rule
    val rule = createAndroidComposeRule<MainActivity>()

    private fun text(id: Int): String =
        InstrumentationRegistry.getInstrumentation().targetContext.getString(id)

    @Test
    fun opensEveryMainTabAndBackReturnsHome() {
        rule.onNodeWithText(text(R.string.app_name)).assertIsDisplayed()

        rule.onAllNodesWithText(text(R.string.add_book)).onFirst().performClick()
        rule.onNodeWithText(text(R.string.import_pdf)).assertIsDisplayed()
        rule.onNodeWithContentDescription(text(R.string.back)).performClick()
        rule.onNodeWithText(text(R.string.app_name)).assertIsDisplayed()

        rule.onAllNodesWithText(text(R.string.about)).onFirst().performClick()
        rule.onNodeWithText(text(R.string.about_title)).assertIsDisplayed()
        rule.onNodeWithContentDescription(text(R.string.back)).performClick()
        rule.onNodeWithText(text(R.string.app_name)).assertIsDisplayed()

        rule.onAllNodesWithText(text(R.string.settings)).onFirst().performClick()
        rule.onNodeWithText(text(R.string.language)).assertIsDisplayed()

        rule.activityRule.scenario.onActivity {
            it.onBackPressedDispatcher.onBackPressed()
        }
        rule.onNodeWithText(text(R.string.app_name)).assertIsDisplayed()
    }
}
