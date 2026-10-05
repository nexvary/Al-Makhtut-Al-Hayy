package org.almakhutut.alhayy.ui

import android.speech.tts.TextToSpeech
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import org.almakhutut.alhayy.R
import org.almakhutut.alhayy.data.ApiClient
import org.almakhutut.alhayy.data.ReaderKnowledgeClient
import org.almakhutut.alhayy.data.SourceSelection
import org.almakhutut.alhayy.model.Manuscript
import org.almakhutut.alhayy.model.Region
import java.util.Locale

@Composable
fun ReaderScreen(manuscript: Manuscript, apiBase: String, onBack: () -> Unit, knowledgeClient: ReaderKnowledgeClient? = null) {
    BackHandler(onBack = onBack)
    var pageIndex by remember { mutableIntStateOf(0) }
    var selected by remember { mutableStateOf<Region?>(null) }
    val defaultClient = remember { ApiClient() }
    val client = knowledgeClient ?: defaultClient
    val page = manuscript.pages.getOrNull(pageIndex)
    val source = page?.let { SourceSelection(manuscript.id, it.id, selected?.id) }
    val knowledge = source?.let { rememberReaderKnowledge(apiBase, it, client) }
    val context = LocalContext.current
    val tts = remember { TextToSpeech(context) {} }
    DisposableEffect(Unit) { onDispose { tts.shutdown() } }

    Scaffold(topBar = { AppTopBar(manuscript.title, onBack) }) { padding ->
        LazyColumn(Modifier.fillMaxSize().padding(padding).imePadding().padding(12.dp)
            .testTag("remote-reader-list")) {
            item {
            Text(
                manuscript.title,
                style = MaterialTheme.typography.titleLarge,
                modifier = Modifier.semantics { heading() },
            )

            if (page == null) {
                Text(stringResource(R.string.no_pages))
                return@item
            }

            Spacer(Modifier.height(8.dp))
            ZoomablePage(page, selected?.id)

            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Button(
                    enabled = pageIndex > 0,
                    onClick = { pageIndex--; selected = null },
                ) { Text(stringResource(R.string.previous)) }
                Text(stringResource(R.string.page_of, pageIndex + 1, manuscript.pages.size))
                Button(
                    enabled = pageIndex < manuscript.pages.lastIndex,
                    onClick = { pageIndex++; selected = null },
                ) { Text(stringResource(R.string.next)) }
            }

            }
            items(page?.regions.orEmpty(), key = { it.id }) { region ->
                RegionCard(region, region.id == selected?.id) { selected = region }
            }
            item {

            selected?.let { region ->
                val speech = preferredText(region)
                if (speech.isNotBlank()) {
                    Button(onClick = {
                        tts.language = Locale("ar")
                        tts.speak(speech, TextToSpeech.QUEUE_FLUSH, null, "region-" + region.id)
                    }) { Text(stringResource(R.string.listen)) }
                }
            }

            page?.let {
                ReaderKnowledgePanel(apiBase, checkNotNull(source), checkNotNull(knowledge))
            }
            }
        }
    }
}

@Composable
private fun RegionCard(region: Region, selected: Boolean, onClick: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp).clickable(onClick = onClick),
        colors = CardDefaults.cardColors(
            containerColor = if (selected) {
                MaterialTheme.colorScheme.secondary.copy(alpha = .18f)
            } else {
                MaterialTheme.colorScheme.surface
            },
        ),
    ) {
        Column(Modifier.padding(10.dp)) {
            region.layers.forEach { layer ->
                val label = when (layer.status) {
                    "verified" -> stringResource(R.string.verified)
                    "draft" -> stringResource(R.string.draft)
                    else -> stringResource(R.string.machine)
                }
                Text(
                    label + " • " + layer.kind,
                    color = MaterialTheme.colorScheme.primary,
                    style = MaterialTheme.typography.labelMedium,
                )
                Text(layer.text)
            }
        }
    }
}

private fun preferredText(region: Region): String {
    val order = listOf(
        "simplified_arabic",
        "normalized_arabic",
        "verified_transcription",
        "htr_raw",
    )
    order.forEach { kind ->
        region.layers.firstOrNull { it.kind == kind }?.text?.let { return it }
    }
    return region.layers.firstOrNull()?.text.orEmpty()
}
