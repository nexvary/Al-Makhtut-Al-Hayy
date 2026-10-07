package org.almakhutut.alhayy

import androidx.activity.compose.setContent
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.almakhutut.alhayy.data.*
import org.almakhutut.alhayy.ui.*
import org.junit.Assert.*
import org.junit.BeforeClass
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class HeritageHubTest {
    companion object { @JvmStatic @BeforeClass fun selectLanguage() { selectTestLanguage() } }
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()
    private fun scroll(tag:String):SemanticsNodeInteraction {
        // Async results can change LazyColumn item positions after the first scroll.
        // Wait for a fresh, visible node rather than retaining a disposed semantics node.
        rule.waitUntil(5000) {
            try {
                rule.onNodeWithTag("heritage-list").performScrollToNode(hasTestTag(tag))
                rule.waitForIdle()
                rule.onNodeWithTag(tag).performScrollTo()
                rule.onNodeWithTag(tag).assertIsDisplayed()
                true
            } catch (_: AssertionError) { false }
        }
        return rule.onNodeWithTag(tag)
    }
    @Test fun sourceTimeAndInterpretiveMuseumAreReachableAndBackWorks() {
        val anchor=SourceSelection("synthetic","p2","region")
        val reading=SourcedRepresentation("revision","historical_objects","draft","Synthetic descriptive evidence",anchor,null,null,null,null)
        val entry=HeritageItem("entity","Synthetic entity",reading)
        var source:SourceSelection?=null
        val client=object:HeritageReaderClient {
            override suspend fun entities(base:String,query:String)=listOf(entry)
            override suspend fun time(base:String,start:Int,end:Int):List<HeritageItem>{assertEquals(1000,start);assertEquals(1300,end);return listOf(entry)}
            override suspend fun exhibitions(base:String)=listOf(entry.copy(id="exhibition",title="Synthetic exhibition"))
            override suspend fun objects(base:String,exhibition:String)=listOf(entry.copy(id="object",title="Synthetic object",interpretive=true,interpretation="Synthetic assumptions"))
            override suspend fun ask(base:String,question:String)=emptyList<HeritageItem>()
        }
        rule.activityRule.scenario.onActivity{activity->activity.setContent{
            var closed by remember{mutableStateOf(false)}
            AlMakhtutTheme{if(closed)Text("heritage-closed") else HeritageHubScreen("https://example.invalid",onBack={closed=true},onSource={source=it},suppliedClient=client)}
        }}
        scroll("heritage-query").performTextInput("fixture")
        scroll("heritage-search").performClick()
        scroll("heritage-source-entity").performClick()
        assertEquals(anchor,source)
        scroll("heritage-time").performClick()
        scroll("heritage-source-entity").assertIsDisplayed()
        scroll("heritage-museum").performClick()
        rule.onNodeWithTag("heritage-list").performScrollToNode(hasText(rule.activity.getString(R.string.heritage_enter)))
        rule.onNodeWithText(rule.activity.getString(R.string.heritage_enter)).performScrollTo().performClick()
        rule.onNodeWithTag("heritage-list").performScrollToNode(hasText(rule.activity.getString(R.string.heritage_interpretive)))
        rule.onNodeWithText(rule.activity.getString(R.string.heritage_interpretive)).assertIsDisplayed()
        rule.onNodeWithContentDescription(rule.activity.getString(R.string.back)).performClick()
        rule.onNodeWithText("heritage-closed").assertIsDisplayed()
    }
}
