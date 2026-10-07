package org.almakhutut.alhayy.data

import android.content.Context
import java.io.File

class OfflineCache(private val context: Context) {
    fun put(manuscriptId: String, json: String) {
        file(manuscriptId).writeText(json)
    }

    fun get(manuscriptId: String): String? =
        file(manuscriptId).takeIf(File::isFile)?.readText()

    fun listIds(): List<String> =
        directory().listFiles()?.mapNotNull {
            it.name.removeSuffix(".json").takeIf(String::isNotBlank)
        }.orEmpty()

    private fun directory(): File =
        File(context.filesDir, "offline-manuscripts").apply { mkdirs() }

    private fun file(id: String): File =
        File(directory(), id.replace(Regex("[^A-Za-z0-9._-]"), "_") + ".json")
}
