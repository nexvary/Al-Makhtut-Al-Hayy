package org.almakhutut.alhayy.ui

import android.content.Context
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Email
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Public
import androidx.compose.material.icons.filled.Share
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import org.almakhutut.alhayy.R
import org.almakhutut.alhayy.data.SocialLinks

@Composable
fun AboutScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    var error by remember { mutableStateOf(false) }

    Scaffold(topBar = { AppTopBar(stringResource(R.string.about), onBack) }) { padding ->
        Column(
            Modifier.fillMaxSize().padding(padding).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(stringResource(R.string.about_title), style = MaterialTheme.typography.headlineSmall)
            Text(stringResource(R.string.about_body))
            HorizontalDivider()
            LinkButton(context, stringResource(R.string.website), SocialLinks.WEBSITE, { Icon(Icons.Default.Public, null) }) { error = true }
            LinkButton(context, "Facebook", SocialLinks.FACEBOOK, { Icon(Icons.Default.Share, null) }) { error = true }
            LinkButton(context, stringResource(R.string.email), SocialLinks.EMAIL, { Icon(Icons.Default.Email, null) }) { error = true }
            LinkButton(context, "YouTube", SocialLinks.YOUTUBE, { Icon(Icons.Default.PlayArrow, null) }) { error = true }
            LinkButton(context, "X", SocialLinks.X, { Icon(Icons.Default.Share, null) }) { error = true }
            if (error) Text(stringResource(R.string.link_open_failed), color = MaterialTheme.colorScheme.error)
        }
    }
}

@Composable
private fun LinkButton(
    context: Context,
    label: String,
    link: String,
    icon: @Composable () -> Unit,
    onError: () -> Unit,
) {
    OutlinedButton(
        onClick = { if (!SocialLinks.open(context, link)) onError() },
        modifier = Modifier.fillMaxWidth().heightIn(min = 52.dp),
    ) {
        icon()
        Spacer(Modifier.width(8.dp))
        Text(label, modifier = Modifier.weight(1f))
    }
}
