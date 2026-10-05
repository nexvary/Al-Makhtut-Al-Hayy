package org.almakhutut.alhayy.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.URLEncoder

data class HeritageItem(val id: String, val title: String, val reading: SourcedRepresentation,
    val interpretive: Boolean = false, val interpretation: String? = null, val latitude: Double? = null, val longitude: Double? = null)
interface HeritageReaderClient {
    suspend fun entities(base: String, query: String): List<HeritageItem>
    suspend fun time(base: String, start: Int, end: Int): List<HeritageItem>
    suspend fun exhibitions(base: String): List<HeritageItem>
    suspend fun objects(base: String, exhibition: String): List<HeritageItem>
    suspend fun ask(base: String, question: String): List<HeritageItem>
}
class HeritageApiClient(private val transport: ApiTransport = UrlConnectionTransport()) : HeritageReaderClient {
    private fun segment(value: String) = URLEncoder.encode(value,"UTF-8").replace("+","%20")
    private fun item(value: JSONObject, museum: Boolean = false): HeritageItem {
        val title = value.optionalText("name") ?: value.getString("title")
        value.put("kind", "historical_objects").put("text", value.optionalText("description") ?: JSONObject.NULL)
        val reading = value.toSourcedRepresentation("id")
        val location = if (value.isNull("location")) null else value.getJSONObject("location")
        val lat = location?.getDouble("latitude"); val lon = location?.getDouble("longitude")
        require(lat == null || (lat.isFinite() && lat in -90.0..90.0))
        require(lon == null || (lon.isFinite() && lon in -180.0..180.0))
        val interpretive = value.optString("evidence_class") == "interpretive_reconstruction"
        if (museum) require(value.getString("evidence_class") in setOf("documented_evidence", "interpretive_reconstruction"))
        val notes = value.optionalText("interpretation_notes")
        require(!interpretive || notes != null)
        return HeritageItem(value.optionalText("entity_id") ?: value.optionalText("exhibition_id") ?: value.getString("object_id"),
            title,reading,interpretive,notes,lat,lon)
    }
    private suspend fun list(base: String, path: String): List<HeritageItem> = withContext(Dispatchers.IO) {
        val array = JSONArray(transport.request("${base.trimEnd('/')}/api/v1/$path")); ensureActive()
        (0 until array.length()).map { item(array.getJSONObject(it)) }
    }
    override suspend fun entities(base: String, query: String) = list(base,"heritage/entities?q=${segment(query)}")
    override suspend fun time(base: String, start: Int, end: Int) = list(base,"heritage/time-machine?start=$start&end=$end")
    override suspend fun exhibitions(base: String) = list(base,"museum/exhibitions")
    override suspend fun objects(base: String, exhibition: String) = withContext(Dispatchers.IO) {
        val result = JSONObject(transport.request("${base.trimEnd('/')}/api/v1/museum/exhibitions/${segment(exhibition)}")); ensureActive()
        val array = result.getJSONArray("objects")
        (0 until array.length()).map { item(array.getJSONObject(it),museum=true) }
    }
    override suspend fun ask(base: String, question: String) = withContext(Dispatchers.IO) {
        val result = JSONObject(transport.request("${base.trimEnd('/')}/api/v1/heritage/ask", JSONObject().put("question",question).toString())); ensureActive()
        val array = result.getJSONArray("evidence")
        (0 until array.length()).map { index ->
            val value = array.getJSONObject(index)
            require(value.getString("state") == "verified")
            val reading = value.toSourcedRepresentation("revision_id")
            HeritageItem(reading.revisionId,reading.source.manuscriptId,reading)
        }
    }
}
