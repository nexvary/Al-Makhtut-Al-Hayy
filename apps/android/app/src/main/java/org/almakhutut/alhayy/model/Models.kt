package org.almakhutut.alhayy.model

import org.json.JSONArray
import org.json.JSONObject

data class TextLayer(
    val kind: String,
    val text: String,
    val status: String,
    val confidence: Double?,
)

data class Point(val x: Float, val y: Float)

data class Region(
    val id: String,
    val type: String,
    val polygon: List<Point>,
    val layers: List<TextLayer>,
)

data class Page(
    val id: String,
    val sequence: Int,
    val label: String?,
    val image: String,
    val imageWidth: Int?,
    val imageHeight: Int?,
    val regions: List<Region>,
)

data class Manuscript(
    val id: String,
    val title: String,
    val author: String?,
    val sourceUrl: String?,
    val license: String?,
    val pages: List<Page>,
)

private fun JSONArray.objects(): List<JSONObject> =
    (0 until length()).map { getJSONObject(it) }

fun JSONObject.toManuscript(): Manuscript {
    val pages = optJSONArray("pages")?.objects()?.map { page ->
        val regions = page.optJSONArray("regions")?.objects()?.map { region ->
            val polygonArray = region.optJSONArray("polygon")
            val polygon = if (polygonArray == null) emptyList() else
                (0 until polygonArray.length()).map { i ->
                    val p = polygonArray.getJSONObject(i)
                    Point(p.optDouble("x").toFloat(), p.optDouble("y").toFloat())
                }
            val layerArray = region.optJSONArray("layers")
            val layers = if (layerArray == null) emptyList() else
                (0 until layerArray.length()).map { i ->
                    val item = layerArray.getJSONObject(i)
                    TextLayer(
                        kind = item.optString("kind"),
                        text = item.optString("text"),
                        status = item.optString("status"),
                        confidence = if (item.isNull("confidence")) null else item.optDouble("confidence"),
                    )
                }
            Region(
                id = region.optString("id"),
                type = region.optString("region_type", "text_line"),
                polygon = polygon,
                layers = layers,
            )
        }.orEmpty()
        Page(
            id = page.optString("id"),
            sequence = page.optInt("sequence"),
            label = page.optString("folio_label").ifBlank { null },
            image = page.optString("image"),
            imageWidth = page.optInt("image_width").takeIf { it > 0 },
            imageHeight = page.optInt("image_height").takeIf { it > 0 },
            regions = regions,
        )
    }.orEmpty()
    return Manuscript(
        id = optString("id"),
        title = optString("title"),
        author = optString("author").ifBlank { null },
        sourceUrl = optString("source_url").ifBlank { null },
        license = optString("license").ifBlank { null },
        pages = pages,
    )
}
