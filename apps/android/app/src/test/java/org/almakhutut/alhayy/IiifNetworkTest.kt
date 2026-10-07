package org.almakhutut.alhayy

import org.almakhutut.alhayy.data.IiifHttpClient
import org.almakhutut.alhayy.data.IiifNetwork
import org.almakhutut.alhayy.data.IiifRequestException
import org.almakhutut.alhayy.data.IiifResponse
import org.junit.Assert.*
import org.junit.Test

class IiifNetworkTest {
    @Test fun rateLimitBlocksManifestAndImagesUntilRetryAfter() {
        var time = 1000L
        var calls = 0
        val client = IiifHttpClient(now = { time }, transport = { _, _ ->
            calls++
            if (calls == 1) IiifResponse(429, byteArrayOf(), "90") else IiifResponse(200, byteArrayOf(1))
        })
        val first = assertThrows(IiifRequestException::class.java) { client.get("https://example.org/manifest.json", 100) }
        assertEquals(91_000L, first.retryAt)
        assertThrows(IiifRequestException::class.java) { client.get("https://example.org/page.jpg", 100) }
        assertEquals(1, calls)
        time = 91_000
        assertArrayEquals(byteArrayOf(1), client.get("https://example.org/page.jpg", 100))
        assertEquals(2, calls)
    }
    @Test fun forbiddenIsReportedWithoutImmediateRetryAndInvalidSourcesAreRejected() {
        var calls = 0
        val client = IiifHttpClient(transport = { _, _ -> calls++; IiifResponse(403, byteArrayOf()) })
        assertEquals(403, assertThrows(IiifRequestException::class.java) { client.get("https://example.org/image.jpg", 100) }.status)
        assertEquals(1, calls)
        assertThrows(IllegalArgumentException::class.java) { client.get("http://example.org/image.jpg", 100) }
        assertEquals(1, calls)
    }
    @Test fun retryAfterDateAndBoundedPreviewPreserveOriginal() {
        assertEquals(60_000L, IiifHttpClient.retryDeadline("Thu, 01 Jan 1970 00:01:00 GMT", 1000))
        assertEquals(61_000L, IiifHttpClient.retryDeadline("invalid", 1000))
        val original = "https://gallica.bnf.fr/iiif/ark:/12148/book/f1/full/full/0/native.jpg"
        assertEquals("https://gallica.bnf.fr/iiif/ark:/12148/book/f1/full/1600,/0/native.jpg", IiifNetwork.preview(original))
        assertEquals("https://example.org/page.jpg", IiifNetwork.preview("https://example.org/page.jpg"))
        assertTrue(original.endsWith("/full/full/0/native.jpg"))
    }
}
