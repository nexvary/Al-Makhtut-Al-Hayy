package org.almakhutut.alhayy.data

enum class LocalBookKind {
    PDF,
    IMAGES,
    IIIF,
}

data class LocalBook(
    val id: String,
    val title: String,
    val kind: LocalBookKind,
    val source: String,
    val pages: List<String> = emptyList(),
    val pageCount: Int,
    val createdAt: Long,
)
