package org.almakhutut.alhayy

import android.graphics.Bitmap
import androidx.activity.compose.setContent
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.runBlocking
import org.almakhutut.alhayy.data.IiifHttpClient
import org.almakhutut.alhayy.data.IiifPageLoader
import org.almakhutut.alhayy.data.IiifResponse
import org.almakhutut.alhayy.ui.AlMakhtutTheme
import org.almakhutut.alhayy.ui.IiifPageImage
import org.junit.BeforeClass
import org.junit.Rule
import org.junit.Test
import org.junit.Assert.*
import org.junit.runner.RunWith
import java.io.ByteArrayOutputStream
import java.util.UUID

@RunWith(AndroidJUnit4::class)
class IiifRecoveryTest {
    companion object { @JvmStatic @BeforeClass fun language() { selectTestLanguage() } }
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()
    private fun png(): ByteArray {
        val image = Bitmap.createBitmap(24, 36, Bitmap.Config.ARGB_8888)
        image.eraseColor(android.graphics.Color.CYAN)
        val output = ByteArrayOutputStream()
        image.compress(Bitmap.CompressFormat.PNG, 100, output); image.recycle()
        return output.toByteArray()
    }
    @Test fun rateLimitedImageCanRecoverAndReadCachedPageOffline() = runBlocking<Unit> {
        var calls = 0
        val bytes = png()
        val client = IiifHttpClient(transport = { url, _ ->
            assertTrue(url.endsWith("/full/1600,/0/native.jpg"))
            calls++
            if (calls == 1) IiifResponse(429, byteArrayOf(), "1") else IiifResponse(200, bytes)
        })
        val loader = IiifPageLoader(rule.activity, client)
        val source = "https://example.org/${UUID.randomUUID()}/full/full/0/native.jpg"
        rule.activity.runOnUiThread { rule.activity.setContent { AlMakhtutTheme { IiifPageImage(source, loader) } } }
        rule.waitUntil(10_000) { rule.onAllNodesWithTag("iiif-page-error").fetchSemanticsNodes().isNotEmpty() }
        rule.waitUntil(5000) { rule.onAllNodesWithTag("iiif-page-retry").filter(isEnabled()).fetchSemanticsNodes().isNotEmpty() }
        rule.onNodeWithTag("iiif-page-retry").performClick()
        rule.waitUntil(10_000) { rule.onAllNodesWithTag("page-image").fetchSemanticsNodes().isNotEmpty() }
        rule.onNodeWithTag("page-image").assertIsDisplayed()
        assertEquals(2, calls)
        val offline = IiifPageLoader(rule.activity, IiifHttpClient(transport = { _, _ -> error("Network must not be called for cached page") }))
        val bitmap = offline.load(source); assertEquals(24, bitmap.width); bitmap.recycle()
    }
    @Test fun deniedImageHasExplicitErrorAndRetryControl() {
        val loader = IiifPageLoader(rule.activity, IiifHttpClient(transport = { _, _ -> IiifResponse(403, byteArrayOf()) }))
        rule.activity.runOnUiThread { rule.activity.setContent { AlMakhtutTheme { IiifPageImage("https://example.org/${UUID.randomUUID()}.jpg", loader) } } }
        rule.waitUntil(10_000) { rule.onAllNodesWithTag("iiif-page-error").fetchSemanticsNodes().isNotEmpty() }
        rule.onNodeWithText("HTTP 403").assertIsDisplayed()
        rule.onNodeWithTag("iiif-page-retry").assertIsDisplayed().assertIsEnabled()
    }
}
