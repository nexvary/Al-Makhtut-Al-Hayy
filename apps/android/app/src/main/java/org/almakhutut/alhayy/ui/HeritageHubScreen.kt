package org.almakhutut.alhayy.ui

import android.content.Intent
import android.net.Uri
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CancellationException
import org.almakhutut.alhayy.R
import org.almakhutut.alhayy.data.*

internal data class HeritageRequest(val sequence: Int, val task: String, val query: String, val start: Int, val end: Int)

class HeritageHubState {
    var query by mutableStateOf("")
    var start by mutableStateOf("1000")
    var end by mutableStateOf("1300")
    internal var request by mutableStateOf<HeritageRequest?>(null)
    var results by mutableStateOf<List<HeritageItem>>(emptyList())
    var busy by mutableStateOf(false)
    var failed by mutableStateOf(false)
}

@Composable
fun HeritageHubScreen(base: String, onBack: () -> Unit, onSource: (SourceSelection) -> Unit,
    suppliedClient: HeritageReaderClient? = null, sourceStatus: String = "", retainedState: HeritageHubState? = null) {
    BackHandler(onBack = onBack)
    val defaultClient = remember { HeritageApiClient() }
    val client = suppliedClient ?: defaultClient
    val context = LocalContext.current
    val localState = remember(base) { HeritageHubState() }
    val state = retainedState ?: localState
    with(state) {
    LaunchedEffect(base, request) {
        val current = request ?: return@LaunchedEffect
        busy = true; failed = false; results = emptyList()
        try {
            results = when (current.task) {
                "time" -> client.time(base,current.start,current.end)
                "museum" -> client.exhibitions(base)
                "objects" -> client.objects(base,current.query)
                "ask" -> client.ask(base,current.query)
                else -> client.entities(base,current.query)
            }
        } catch (cancelled: CancellationException) { throw cancelled }
        catch (_: Exception) { failed = true }
        finally { busy = false }
    }
    fun send(task: String, text: String = query) {
        request = HeritageRequest((request?.sequence ?: 0)+1,task,text,start.toIntOrNull() ?: 1000,end.toIntOrNull() ?: 1300)
    }
    Scaffold(topBar = { AppTopBar(stringResource(R.string.heritage_hub),onBack) }) { padding ->
        LazyColumn(Modifier.fillMaxSize().padding(padding).imePadding().testTag("heritage-list"),
            contentPadding = PaddingValues(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            item {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (sourceStatus.isNotBlank()) Text(sourceStatus)
                    Text(stringResource(R.string.heritage_notice), style = MaterialTheme.typography.bodySmall)
                    OutlinedTextField(query,{query=it.take(2000)}, label={Text(stringResource(R.string.heritage_query))},modifier=Modifier.fillMaxWidth().testTag("heritage-query"))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(enabled=!busy && base.isNotBlank() && query.length<=200,onClick={send("entities")}, modifier=Modifier.testTag("heritage-search")){Text(stringResource(R.string.search))}
                        OutlinedButton(enabled=!busy && base.isNotBlank() && query.trim().length>=2,onClick={send("ask")},modifier=Modifier.testTag("heritage-ask")){Text(stringResource(R.string.heritage_ask))}
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedTextField(start,{start=it.take(6)},label={Text(stringResource(R.string.heritage_start))},modifier=Modifier.weight(1f))
                        OutlinedTextField(end,{end=it.take(6)},label={Text(stringResource(R.string.heritage_end))},modifier=Modifier.weight(1f))
                    }
                    Button(enabled=!busy && base.isNotBlank() && start.toIntOrNull()?.let { it in -10000..3000 } == true && end.toIntOrNull()?.let { it in -10000..3000 } == true && (start.toIntOrNull() ?: 0)<=(end.toIntOrNull() ?: 0),onClick={send("time")},modifier=Modifier.testTag("heritage-time")){Text(stringResource(R.string.heritage_time))}
                    OutlinedButton(enabled=!busy && base.isNotBlank(),onClick={send("museum")},modifier=Modifier.testTag("heritage-museum")){Text(stringResource(R.string.heritage_museum))}
                    if(base.isBlank()) Text(stringResource(R.string.knowledge_server_required))
                    if(busy) Text(stringResource(R.string.loading))
                    if(failed) Text(stringResource(R.string.search_failed))
                    if(request!=null && !busy && !failed && results.isEmpty()) Text(stringResource(R.string.insufficient_source_evidence))
                }
            }
            items(results,key={it.id}) { item ->
                Column(verticalArrangement=Arrangement.spacedBy(8.dp)) {
                    SourcedTextCard(item.reading,item.title)
                    if(item.interpretive) Text(stringResource(R.string.heritage_interpretive),color=MaterialTheme.colorScheme.secondary)
                    item.interpretation?.let{Text(it)}
                    if(request?.task=="museum") Button(onClick={send("objects",item.id)}){Text(stringResource(R.string.heritage_enter))}
                    OutlinedButton(onClick={onSource(item.reading.source)},modifier=Modifier.testTag("heritage-source-${item.id}")){Text(stringResource(R.string.heritage_original))}
                    if(item.latitude!=null && item.longitude!=null) {
                        Text("${item.latitude}, ${item.longitude}")
                        TextButton(onClick={
                            val url="https://www.openstreetmap.org/?mlat=${item.latitude}&mlon=${item.longitude}#map=10/${item.latitude}/${item.longitude}"
                            try {context.startActivity(Intent(Intent.ACTION_VIEW,Uri.parse(url)))} catch (_: android.content.ActivityNotFoundException) {failed=true}
                        }){Text(stringResource(R.string.heritage_map))}
                    }
                }
            }
        }
    }
}
}
