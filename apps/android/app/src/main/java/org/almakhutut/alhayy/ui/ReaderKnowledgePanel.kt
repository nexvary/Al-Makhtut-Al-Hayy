package org.almakhutut.alhayy.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CancellationException
import org.almakhutut.alhayy.R
import org.almakhutut.alhayy.data.LabReading
import org.almakhutut.alhayy.data.ReaderKnowledgeClient
import org.almakhutut.alhayy.data.SourceSelection
import org.almakhutut.alhayy.data.SourcedRepresentation

internal data class PendingQuestion(val sequence: Int, val question: String, val task: String, val language: String?)

internal class ReaderKnowledgeState {
    var expanded by mutableStateOf(false)
    var refresh by mutableIntStateOf(0)
    var layers by mutableStateOf<List<SourcedRepresentation>>(emptyList())
    var loading by mutableStateOf(false)
    var layersFailed by mutableStateOf(false)
    var question by mutableStateOf("")
    var task by mutableStateOf("read")
    var language by mutableStateOf("ar")
    var menu by mutableStateOf(false)
    var pending by mutableStateOf<PendingQuestion?>(null)
    var result by mutableStateOf<LabReading?>(null)
    var busy by mutableStateOf(false)
    var failed by mutableStateOf(false)
}

// Owned by ReaderScreen, so scrolling a lazy item offscreen does not discard a question.
@Composable
internal fun rememberReaderKnowledge(base: String, source: SourceSelection, client: ReaderKnowledgeClient): ReaderKnowledgeState {
    val state = remember(base, source) { ReaderKnowledgeState() }
    with(state) {
        LaunchedEffect(state, refresh) {
            layers = emptyList()
            layersFailed = false
            if (base.isBlank()) return@LaunchedEffect
            loading = true
            try {
                layers = client.layers(base, source.manuscriptId, source.pageId)
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (_: Exception) {
                layersFailed = true
            } finally {
                loading = false
            }
        }
        LaunchedEffect(state, pending) {
            val request = pending ?: return@LaunchedEffect
            busy = true
            failed = false
            result = null
            try {
                result = client.askRegion(base, source, request.question, request.task, request.language)
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (_: Exception) {
                failed = true
            } finally {
                busy = false
            }
        }
    }
    return state
}

@Composable
internal fun ReaderKnowledgePanel(base: String, source: SourceSelection, state: ReaderKnowledgeState) {
    with(state) {
        val labels = mapOf(
            "read" to stringResource(R.string.lab_read),
            "confidence" to stringResource(R.string.lab_confidence),
            "alternatives" to stringResource(R.string.lab_alternatives),
            "explain" to stringResource(R.string.lab_explain),
            "translate" to stringResource(R.string.lab_translate),
        )
        Column(Modifier.fillMaxWidth().testTag("reader-knowledge"), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(stringResource(R.string.original_preserved), style = MaterialTheme.typography.bodySmall)
            OutlinedButton(onClick = { expanded = !expanded }, modifier = Modifier.testTag("living-layers-toggle")) {
                Text(stringResource(R.string.living_layer_history))
            }
            if (expanded) {
                when {
                    base.isBlank() -> Text(stringResource(R.string.knowledge_server_required))
                    loading -> Text(stringResource(R.string.loading))
                    layersFailed -> Text(stringResource(R.string.layers_unavailable))
                    layers.isEmpty() -> Text(stringResource(R.string.no_living_layers))
                }
                val scoped = layers.filter { it.source.regionId == source.regionId }
                scoped.forEach { SourcedTextCard(it) }
                if (!loading && !layersFailed && layers.isNotEmpty() && scoped.isEmpty()) {
                    Text(stringResource(R.string.no_living_layers))
                }
                TextButton(enabled = !loading && base.isNotBlank(), onClick = { refresh++ }) {
                    Text(stringResource(R.string.reload_layers))
                }
            }
            Text(stringResource(R.string.manuscript_lab), style = MaterialTheme.typography.titleMedium)
            Text(stringResource(R.string.lab_scope, source.pageId, source.regionId ?: stringResource(R.string.whole_page)),
                modifier = Modifier.testTag("lab-source"), style = MaterialTheme.typography.bodySmall)
            Box {
                OutlinedButton(onClick = { menu = true }, modifier = Modifier.testTag("lab-task")) { Text(labels.getValue(task)) }
                DropdownMenu(expanded = menu, onDismissRequest = { menu = false }) {
                    labels.forEach { (value, label) ->
                        DropdownMenuItem(text = { Text(label) }, onClick = { task = value; menu = false })
                    }
                }
            }
            if (task == "translate") {
                OutlinedTextField(value = language, onValueChange = { language = it.take(35) },
                    label = { Text(stringResource(R.string.translation_language)) }, modifier = Modifier.fillMaxWidth())
            }
            OutlinedTextField(value = question, onValueChange = { question = it.take(2000) },
                label = { Text(stringResource(R.string.ask_manuscript)) }, modifier = Modifier.fillMaxWidth().testTag("lab-question"))
            Button(enabled = !busy && base.isNotBlank() && question.trim().length >= 2 && (task != "translate" || language.isNotBlank()),
                modifier = Modifier.testTag("lab-submit"), onClick = {
                    pending = PendingQuestion((pending?.sequence ?: 0) + 1, question.trim(), task,
                        if (task == "translate") language.trim() else null)
                }) { Text(stringResource(if (busy) R.string.searching else R.string.search)) }
            if (base.isBlank()) Text(stringResource(R.string.knowledge_server_required))
            if (failed) Text(stringResource(R.string.search_failed))
            result?.let { answer ->
                if (answer.insufficientEvidence || answer.evidence.isEmpty()) {
                    Text(stringResource(R.string.insufficient_source_evidence), modifier = Modifier.testTag("lab-insufficient"))
                } else {
                    Text(stringResource(R.string.source_excerpts_notice))
                    answer.evidence.forEach { SourcedTextCard(it) }
                }
            }
        }
}
}

@Composable
internal fun SourcedTextCard(item: SourcedRepresentation, title: String? = null) {
    val stateLabel = when (item.state) {
        "verified" -> stringResource(R.string.verified)
        "draft" -> stringResource(R.string.draft)
        else -> stringResource(R.string.machine)
    }
    val kindLabel = title ?: when (item.kind) {
        "machine_reading" -> stringResource(R.string.lab_read)
        "draft_transcription" -> stringResource(R.string.draft)
        "verified_transcription" -> stringResource(R.string.verified)
        "critical_text" -> stringResource(R.string.critical_text)
        "modernized_text" -> stringResource(R.string.modern_text)
        "simplified_explanation" -> stringResource(R.string.lab_explain)
        "translation" -> stringResource(R.string.lab_translate)
        else -> stringResource(R.string.living_layer_history)
    }
    Card(Modifier.fillMaxWidth().testTag("sourced-${item.revisionId}")) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text("$kindLabel • $stateLabel", color = MaterialTheme.colorScheme.primary)
            item.text?.let { Text(it) }
            Text(stringResource(R.string.source_reference, item.source.manuscriptId, item.source.pageId,
                item.source.regionId ?: stringResource(R.string.whole_page)), style = MaterialTheme.typography.bodySmall)
            Text(stringResource(R.string.confidence_value, item.confidence?.toString() ?: stringResource(R.string.unknown_confidence)),
                style = MaterialTheme.typography.bodySmall)
            Text(stringResource(R.string.reviewer_value, item.reviewer ?: stringResource(R.string.not_reviewed)),
                style = MaterialTheme.typography.bodySmall)
            item.witnessId?.let { Text(stringResource(R.string.witness_value, it), style = MaterialTheme.typography.bodySmall) }
            Text(stringResource(R.string.revision_value, item.revisionId), style = MaterialTheme.typography.bodySmall)
            item.timestamp?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
        }
    }
}
