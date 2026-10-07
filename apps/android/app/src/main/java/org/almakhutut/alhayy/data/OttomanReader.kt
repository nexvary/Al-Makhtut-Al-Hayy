package org.almakhutut.alhayy.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.URLEncoder

data class OttomanRevision(val stage: String, val reading: SourcedRepresentation, val inputRevision: String?)
data class OttomanExercise(val id: String, val title: String, val rights: String)
data class DictionaryReading(val reading: SourcedRepresentation, val spelling: String, val transliteration: String?,
    val modernTurkish: String?, val arabic: String?, val english: String?, val origin: String?)
data class ExerciseFeedback(val exact: Boolean, val availableSteps: Int, val revealed: List<Pair<String, String>>)

interface OttomanReaderClient {
    suspend fun pipeline(base: String, source: SourceSelection): List<OttomanRevision>
    suspend fun dictionary(base: String, query: String): List<DictionaryReading>
    suspend fun exercises(base: String, source: SourceSelection): List<OttomanExercise>
    suspend fun attempt(base: String, source: SourceSelection, id: String, text: String, step: Int): ExerciseFeedback
}

class OttomanApiClient(private val transport: ApiTransport = UrlConnectionTransport()) : OttomanReaderClient {
    private fun segment(value: String) = URLEncoder.encode(value, "UTF-8").replace("+", "%20")
    private fun page(base: String, source: SourceSelection) = "${base.trimEnd('/')}/api/v1/ottoman/manuscripts/${segment(source.manuscriptId)}/pages/${segment(source.pageId)}"
    override suspend fun pipeline(base: String, source: SourceSelection) = withContext(Dispatchers.IO) {
        val array = JSONObject(transport.request(page(base, source))).getJSONArray("revisions")
        ensureActive()
        (0 until array.length()).map { index ->
            val item = array.getJSONObject(index)
            val stage = item.getString("stage")
            require(stage in setOf("layout", "htr", "transcription", "transliteration", "modernization", "translation_ar", "translation_en"))
            item.put("kind", stage)
            val reading = item.toSourcedRepresentation("id")
            require(reading.source.manuscriptId == source.manuscriptId && reading.source.pageId == source.pageId)
            require(stage != "htr" || reading.state == "machine")
            OttomanRevision(stage, reading, item.optionalText("input_revision_id"))
        }.filter { it.reading.source.regionId == source.regionId }
    }
    override suspend fun dictionary(base: String, query: String) = withContext(Dispatchers.IO) {
        val array = JSONArray(transport.request("${base.trimEnd('/')}/api/v1/ottoman/dictionary?q=${segment(query)}"))
        ensureActive()
        (0 until array.length()).map { index ->
            val item = array.getJSONObject(index).put("kind", "dictionary").put("text", JSONObject.NULL)
            val reading = item.toSourcedRepresentation("id")
            val origin = item.optionalText("linguistic_origin")
            require(origin == null || (reading.state == "verified" && item.getJSONObject("provenance").getJSONArray("evidence").length() > 0))
            DictionaryReading(reading, item.getString("spelling"), item.optionalText("transliteration"),
                item.optionalText("modern_turkish"), item.optionalText("arabic"), item.optionalText("english"), origin)
        }
    }
    override suspend fun exercises(base: String, source: SourceSelection) = withContext(Dispatchers.IO) {
        val array = JSONArray(transport.request("${page(base, source)}/exercises"))
        ensureActive()
        (0 until array.length()).map { index -> array.getJSONObject(index).let {
            OttomanExercise(it.getString("id"), it.getString("title"), it.getString("rights_note"))
        } }
    }
    override suspend fun attempt(base: String, source: SourceSelection, id: String, text: String, step: Int) = withContext(Dispatchers.IO) {
        val body = JSONObject().put("text", text).put("reveal_step", step)
        val result = JSONObject(transport.request("${page(base, source)}/exercises/${segment(id)}/attempt", body.toString()))
        ensureActive()
        val array = result.getJSONArray("revealed")
        val available = result.getInt("available_steps")
        require(available in 1..4 && array.length() <= step && array.length() <= available)
        val revealed = (0 until array.length()).map { index ->
            val item = array.getJSONObject(index)
            val anchor = item.getJSONObject("provenance").getJSONObject("source")
            require(anchor.getString("manuscript_id") == source.manuscriptId && anchor.getString("page_id") == source.pageId)
            Pair(item.getString("stage"), item.getString("text"))
        }
        ExerciseFeedback(result.getBoolean("exact_match"), available, revealed)
    }
}
