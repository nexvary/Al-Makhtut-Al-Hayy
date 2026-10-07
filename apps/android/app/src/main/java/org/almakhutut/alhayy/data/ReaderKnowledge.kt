package org.almakhutut.alhayy.data

import org.json.JSONObject

data class SourceSelection(val manuscriptId: String, val pageId: String, val regionId: String? = null)
data class SourcedRepresentation(
    val revisionId: String,
    val kind: String,
    val state: String,
    val text: String?,
    val source: SourceSelection,
    val witnessId: String?,
    val confidence: Double?,
    val reviewer: String?,
    val timestamp: String?,
)
data class LabReading(val insufficientEvidence: Boolean, val evidence: List<SourcedRepresentation>)

interface ReaderKnowledgeClient {
    suspend fun layers(base: String, manuscriptId: String, pageId: String): List<SourcedRepresentation>
    suspend fun askRegion(base: String, source: SourceSelection, question: String, task: String, targetLanguage: String?): LabReading
}

internal fun JSONObject.optionalText(key: String): String? =
    if (isNull(key)) null else optString(key).takeIf { it.isNotBlank() }

internal fun JSONObject.toSourcedRepresentation(idKey: String): SourcedRepresentation {
    val provenance = getJSONObject("provenance")
    val anchor = provenance.getJSONObject("source")
    val state = getString("state")
    require(state in setOf("machine", "draft", "verified")) { "Unknown scientific review state" }
    val confidence = if (provenance.isNull("confidence")) null else provenance.getDouble("confidence")
    require(confidence == null || (confidence.isFinite() && confidence in 0.0..1.0)) { "Invalid confidence" }
    val source = SourceSelection(anchor.getString("manuscript_id"), anchor.getString("page_id"), anchor.optionalText("region_id"))
    require(source.manuscriptId.isNotBlank() && source.pageId.isNotBlank()) { "Missing source identity" }
    val reviewer = provenance.optionalText("reviewer")
    require(state != "verified" || reviewer != null) { "Verified text requires a reviewer" }
    return SourcedRepresentation(getString(idKey), getString("kind"), state, optionalText("text"), source,
        anchor.optionalText("witness_id"), confidence, reviewer, provenance.optionalText("timestamp"))
}
