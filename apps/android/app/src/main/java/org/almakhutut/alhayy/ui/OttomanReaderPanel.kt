package org.almakhutut.alhayy.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import org.almakhutut.alhayy.R
import org.almakhutut.alhayy.data.*

internal data class DictionaryRequest(val sequence: Int, val query: String)
internal data class PracticeRequest(val sequence: Int, val id: String, val text: String, val step: Int)
internal class OttomanReaderState {
    var expanded by mutableStateOf(false)
    var refresh by mutableIntStateOf(0)
    var loading by mutableStateOf(false)
    var failed by mutableStateOf(false)
    var records by mutableStateOf<List<OttomanRevision>>(emptyList())
    var exercises by mutableStateOf<List<OttomanExercise>>(emptyList())
    var stage by mutableStateOf("transcription")
    var stageMenu by mutableStateOf(false)
    var query by mutableStateOf("")
    var lookup by mutableStateOf<DictionaryRequest?>(null)
    var dictionaryBusy by mutableStateOf(false)
    var dictionaryFailed by mutableStateOf(false)
    var definitions by mutableStateOf<List<DictionaryReading>?>(null)
    var exerciseId by mutableStateOf<String?>(null)
    var exerciseMenu by mutableStateOf(false)
    var answer by mutableStateOf("")
    var attempt by mutableStateOf<PracticeRequest?>(null)
    var practiceBusy by mutableStateOf(false)
    var practiceFailed by mutableStateOf(false)
    var feedback by mutableStateOf<ExerciseFeedback?>(null)
}

@Composable
internal fun rememberOttomanReader(base: String, source: SourceSelection, client: OttomanReaderClient): OttomanReaderState {
    val state = remember(base, source) { OttomanReaderState() }
    with(state) {
        LaunchedEffect(state, expanded, refresh) {
            if (!expanded || base.isBlank()) return@LaunchedEffect
            loading = true; failed = false
            try {
                coroutineScope {
                    val pipeline = async { client.pipeline(base, source) }
                    val lessons = async { client.exercises(base, source) }
                    records = pipeline.await(); exercises = lessons.await()
                }
            } catch (cancelled: CancellationException) { throw cancelled }
            catch (_: Exception) { failed = true }
            finally { loading = false }
        }
        LaunchedEffect(state, lookup) {
            val request = lookup ?: return@LaunchedEffect
            dictionaryBusy = true; dictionaryFailed = false; definitions = null
            try { definitions = client.dictionary(base, request.query) }
            catch (cancelled: CancellationException) { throw cancelled }
            catch (_: Exception) { dictionaryFailed = true }
            finally { dictionaryBusy = false }
        }
        LaunchedEffect(state, attempt, exerciseId) {
            val request = attempt ?: return@LaunchedEffect
            if (request.id != exerciseId) return@LaunchedEffect
            practiceBusy = true; practiceFailed = false
            try { feedback = client.attempt(base, source, request.id, request.text, request.step) }
            catch (cancelled: CancellationException) { throw cancelled }
            catch (_: Exception) { practiceFailed = true }
            finally { practiceBusy = false }
        }
    }
    return state
}

@Composable
internal fun ottomanStageLabel(stage: String): String = stringResource(when (stage) {
    "layout" -> R.string.ottoman_layout
    "htr" -> R.string.ottoman_htr
    "transcription" -> R.string.ottoman_transcription
    "transliteration" -> R.string.ottoman_transliteration
    "modernization" -> R.string.ottoman_modern_turkish
    "translation_ar" -> R.string.ottoman_arabic
    else -> R.string.ottoman_english
})

@Composable
internal fun OttomanReaderPanel(base: String, state: OttomanReaderState) {
    with(state) {
        Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(onClick = { expanded = !expanded }, modifier = Modifier.testTag("ottoman-toggle")) {
                Text(stringResource(R.string.ottoman_lab))
            }
            if (!expanded) return@Column
            Text(stringResource(R.string.ottoman_separation), style = MaterialTheme.typography.bodySmall)
            if (base.isBlank()) { Text(stringResource(R.string.knowledge_server_required)); return@Column }
            if (loading) Text(stringResource(R.string.loading))
            if (failed) Text(stringResource(R.string.layers_unavailable))
            Box {
                OutlinedButton(onClick = { stageMenu = true }, modifier = Modifier.testTag("ottoman-stage")) { Text(ottomanStageLabel(stage)) }
                DropdownMenu(expanded = stageMenu, onDismissRequest = { stageMenu = false }) {
                    listOf("layout", "htr", "transcription", "transliteration", "modernization", "translation_ar", "translation_en").forEach { value ->
                        DropdownMenuItem(text = { Text(ottomanStageLabel(value)) }, onClick = { stage = value; stageMenu = false })
                    }
                }
            }
            val readings = records.filter { it.stage == stage }
            if (!loading && !failed && readings.isEmpty()) Text(stringResource(R.string.no_living_layers))
            readings.forEach { item ->
                SourcedTextCard(item.reading, ottomanStageLabel(item.stage))
                item.inputRevision?.let { Text(stringResource(R.string.ottoman_upstream, it), style = MaterialTheme.typography.bodySmall) }
            }
            TextButton(enabled = !loading, onClick = { refresh++ }) { Text(stringResource(R.string.reload_layers)) }
            HorizontalDivider()
            Text(stringResource(R.string.ottoman_dictionary), style = MaterialTheme.typography.titleMedium)
            OutlinedTextField(query, { query = it.take(200) }, label = { Text(stringResource(R.string.ottoman_word)) },
                modifier = Modifier.fillMaxWidth().testTag("ottoman-word"))
            Button(enabled = query.isNotBlank() && !dictionaryBusy, onClick = {
                lookup = DictionaryRequest((lookup?.sequence ?: 0) + 1, query.trim())
            }, modifier = Modifier.testTag("ottoman-lookup")) { Text(stringResource(R.string.search)) }
            if (dictionaryBusy) Text(stringResource(R.string.searching))
            if (dictionaryFailed) Text(stringResource(R.string.search_failed))
            definitions?.let { entries ->
                if (entries.isEmpty()) Text(stringResource(R.string.no_living_layers))
                entries.forEach { entry ->
                    SourcedTextCard(entry.reading.copy(text = entry.spelling), stringResource(R.string.ottoman_dictionary))
                    listOf(entry.transliteration, entry.modernTurkish, entry.arabic, entry.english).forEachIndexed { index, value ->
                        value?.let { Text("${ottomanStageLabel(listOf("transliteration", "modernization", "translation_ar", "translation_en")[index])}: $it") }
                    }
                    Text(stringResource(R.string.ottoman_origin, entry.origin ?: stringResource(R.string.not_reviewed)))
                }
            }
            HorizontalDivider()
            Text(stringResource(R.string.ottoman_academy), style = MaterialTheme.typography.titleMedium)
            Text(stringResource(R.string.ottoman_practice_notice), style = MaterialTheme.typography.bodySmall)
            if (!loading && !failed && exercises.isEmpty()) Text(stringResource(R.string.ottoman_no_exercises))
            if (exercises.isNotEmpty()) {
                Box {
                    OutlinedButton(onClick = { exerciseMenu = true }, modifier = Modifier.testTag("ottoman-exercise")) {
                        Text(exercises.firstOrNull { it.id == exerciseId }?.title ?: stringResource(R.string.ottoman_choose_exercise))
                    }
                    DropdownMenu(exerciseMenu, onDismissRequest = { exerciseMenu = false }) {
                        exercises.forEach { exercise -> DropdownMenuItem(text = { Text(exercise.title) }, onClick = {
                            exerciseId = exercise.id; exerciseMenu = false; answer = ""; feedback = null; attempt = null; practiceFailed = false
                        }) }
                    }
                }
                exercises.firstOrNull { it.id == exerciseId }?.let { exercise ->
                    Text(exercise.rights, style = MaterialTheme.typography.bodySmall)
                    OutlinedTextField(answer, { answer = it.take(10000) }, label = { Text(stringResource(R.string.ottoman_attempt)) },
                        modifier = Modifier.fillMaxWidth().testTag("ottoman-attempt"))
                    Button(enabled = !practiceBusy, onClick = {
                        attempt = PracticeRequest((attempt?.sequence ?: 0) + 1, exercise.id, answer, feedback?.revealed?.size ?: 0)
                    }, modifier = Modifier.testTag("ottoman-check")) { Text(stringResource(R.string.ottoman_check)) }
                    TextButton(enabled = !practiceBusy && (feedback?.revealed?.size ?: 0) < (feedback?.availableSteps ?: 4), onClick = {
                        attempt = PracticeRequest((attempt?.sequence ?: 0) + 1, exercise.id, answer, (feedback?.revealed?.size ?: 0) + 1)
                    }, modifier = Modifier.testTag("ottoman-reveal")) { Text(stringResource(R.string.ottoman_reveal)) }
                    if (practiceBusy) Text(stringResource(R.string.loading))
                    if (practiceFailed) Text(stringResource(R.string.search_failed))
                    feedback?.let { result ->
                        Text(stringResource(if (result.exact) R.string.ottoman_match else R.string.ottoman_not_match), modifier = Modifier.testTag("ottoman-feedback"))
                        result.revealed.forEach { (stage, text) -> Text("${ottomanStageLabel(stage)}: $text") }
                    }
                }
            }
        }
    }
}
