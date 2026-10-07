package org.almakhutut.alhayy

import androidx.test.ext.junit.runners.AndroidJUnit4
import kotlinx.coroutines.runBlocking
import org.almakhutut.alhayy.data.ApiClient
import org.almakhutut.alhayy.data.ApiTransport
import org.almakhutut.alhayy.data.SourceSelection
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Uses Android's real JSON parser; the transport is a deterministic protocol fixture. */
@RunWith(AndroidJUnit4::class)
class ApiClientContractTest {
    private fun evidence(page: String = "p1", state: String = "machine") = JSONObject()
        .put("revision_id", "synthetic-revision").put("kind", "machine_reading")
        .put("state", state).put("text", "Synthetic uncertain reading")
        .put("provenance", JSONObject().put("source", JSONObject()
            .put("manuscript_id", "fixture").put("page_id", page).put("region_id", "r1"))
            .put("confidence", JSONObject.NULL).put("reviewer", JSONObject.NULL))

    @Test fun regionAndTaskAreSentWithoutPromotingUncertainText() = runBlocking<Unit> {
        var request: JSONObject? = null
        val client = ApiClient(object : ApiTransport {
            override fun request(url: String, body: String?): String {
                assertEquals("https://example.invalid/api/v1/ai-lab/ask", url)
                request = JSONObject(checkNotNull(body))
                return JSONObject().put("insufficient_evidence", false)
                    .put("evidence", JSONArray().put(evidence())).toString()
            }
        })
        val answer = client.askRegion("https://example.invalid/", SourceSelection("fixture", "p1", "r1"),
            "Read this region", "translate", "tr")
        assertEquals("r1", request!!.getJSONObject("source").getString("region_id"))
        assertEquals("p1", request!!.getJSONObject("source").getString("page_id"))
        assertEquals("translate", request!!.getString("task"))
        assertEquals("tr", request!!.getString("target_language"))
        assertEquals("machine", answer.evidence.single().state)
        assertNull(answer.evidence.single().confidence)
        assertNull(answer.evidence.single().reviewer)
    }

    @Test fun rejectsWrongPageAndUnattributedVerification() = runBlocking<Unit> {
        for (item in listOf(evidence(page = "p2"), evidence(state = "verified"))) {
            val client = ApiClient(object : ApiTransport {
                override fun request(url: String, body: String?) = JSONObject()
                    .put("insufficient_evidence", false).put("evidence", JSONArray().put(item)).toString()
            })
            try {
                client.askRegion("https://example.invalid", SourceSelection("fixture", "p1", "r1"),
                    "Read this", "read", null)
                fail("Invalid scientific source must be rejected")
            } catch (_: IllegalArgumentException) { /* expected */ }
        }
    }
}
