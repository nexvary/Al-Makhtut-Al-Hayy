package org.almakhutut.alhayy.ui

import android.speech.tts.TextToSpeech
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import org.almakhutut.alhayy.data.ApiClient
import org.almakhutut.alhayy.model.Manuscript
import org.almakhutut.alhayy.model.Region
import java.util.Locale

@Composable
fun ReaderScreen(manuscript: Manuscript, apiBase: String, onBack: () -> Unit) {
    var pageIndex by remember { mutableIntStateOf(0) }
    var selected by remember { mutableStateOf<Region?>(null) }
    var question by remember { mutableStateOf("") }
    var answer by remember { mutableStateOf("") }
    val scope = rememberCoroutineScope()
    val page = manuscript.pages.getOrNull(pageIndex)
    val context = LocalContext.current
    val tts = remember { TextToSpeech(context) {} }
    DisposableEffect(Unit) { onDispose { tts.shutdown() } }

    Column(Modifier.fillMaxSize().padding(12.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = onBack) { Text("رجوع") }
            Text(
                manuscript.title,
                style = MaterialTheme.typography.titleLarge,
                modifier = Modifier.semantics { heading() },
            )
        }

        if (page == null) {
            Text("لا توجد صفحات.")
            return@Column
        }

        Spacer(Modifier.height(8.dp))
        ZoomablePage(page, selected?.id)

        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Button(
                enabled = pageIndex > 0,
                onClick = { pageIndex--; selected = null },
            ) { Text("السابق") }
            Text("${pageIndex + 1} / ${manuscript.pages.size}")
            Button(
                enabled = pageIndex < manuscript.pages.lastIndex,
                onClick = { pageIndex++; selected = null },
            ) { Text("التالي") }
        }

        LazyColumn(Modifier.weight(1f)) {
            items(page.regions, key = { it.id }) { region ->
                RegionCard(region, region.id == selected?.id) { selected = region }
            }
        }

        selected?.let { region ->
            val speech = preferredText(region)
            if (speech.isNotBlank()) {
                Button(onClick = {
                    tts.language = Locale("ar")
                    tts.speak(speech, TextToSpeech.QUEUE_FLUSH, null, "region-${region.id}")
                }) { Text("🔊 استمع") }
            }
        }

        OutlinedTextField(
            value = question,
            onValueChange = { question = it },
            label = { Text("اسأل المخطوط") },
            modifier = Modifier.fillMaxWidth(),
        )
        Button(
            enabled = question.length >= 2,
            onClick = {
                answer = "جارٍ البحث…"
                scope.launch {
                    answer = runCatching { ApiClient().ask(apiBase, question) }
                        .getOrElse { "تعذر البحث: ${it.message}" }
                }
            },
        ) { Text("بحث") }
        if (answer.isNotBlank()) Text(answer)
    }
}

@Composable
private fun RegionCard(region: Region, selected: Boolean, onClick: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp).clickable(onClick = onClick),
        colors = CardDefaults.cardColors(
            containerColor = if (selected) MaterialTheme.colorScheme.secondary.copy(alpha = .18f)
            else MaterialTheme.colorScheme.surface,
        ),
    ) {
        Column(Modifier.padding(10.dp)) {
            region.layers.forEach { layer ->
                Text(
                    when (layer.status) {
                        "verified" -> "موثّق • ${layer.kind}"
                        "draft" -> "مسودة • ${layer.kind}"
                        else -> "آلي • ${layer.kind}"
                    },
                    color = MaterialTheme.colorScheme.primary,
                    style = MaterialTheme.typography.labelMedium,
                )
                Text(layer.text)
            }
        }
    }
}

private fun preferredText(region: Region): String {
    val order = listOf("simplified_arabic", "normalized_arabic", "verified_transcription", "htr_raw")
    order.forEach { kind -> region.layers.firstOrNull { it.kind == kind }?.text?.let { return it } }
    return region.layers.firstOrNull()?.text.orEmpty()
}
