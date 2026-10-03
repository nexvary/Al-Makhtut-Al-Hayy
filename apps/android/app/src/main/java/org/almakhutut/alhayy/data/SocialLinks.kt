package org.almakhutut.alhayy.data

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import java.net.URI

object SocialLinks {
    const val WEBSITE = "https://nexvary.com/"
    const val FACEBOOK = "https://www.facebook.com/share/14p9krEn5ij/"
    const val EMAIL = "mailto:info@nexvary.com"
    const val YOUTUBE = "https://www.youtube.com/@NexvaryInc"
    const val X = "https://x.com/Nexvary"

    val all: List<String> = listOf(WEBSITE, FACEBOOK, EMAIL, YOUTUBE, X)

    fun isSupported(value: String): Boolean = runCatching {
        val uri = URI(value)
        uri.scheme in setOf("https", "mailto") && !uri.schemeSpecificPart.isNullOrBlank()
    }.getOrDefault(false)

    fun open(context: Context, value: String): Boolean {
        if (!isSupported(value)) return false
        return try {
            context.startActivity(
                Intent(Intent.ACTION_VIEW, Uri.parse(value)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
            )
            true
        } catch (_: ActivityNotFoundException) {
            false
        }
    }
}
