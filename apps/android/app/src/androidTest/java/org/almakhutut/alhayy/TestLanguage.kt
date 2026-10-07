package org.almakhutut.alhayy

import android.app.LocaleManager
import android.os.Build
import android.os.LocaleList
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.os.LocaleListCompat
import androidx.test.platform.app.InstrumentationRegistry

/** Set framework locales before Activity launch, without relying on active delegates. */
fun selectTestLanguage() {
    val instrumentation = InstrumentationRegistry.getInstrumentation()
    val tag = InstrumentationRegistry.getArguments().getString("language", "en")
    instrumentation.runOnMainSync {
        if (Build.VERSION.SDK_INT >= 33) {
            instrumentation.targetContext.getSystemService(LocaleManager::class.java)
                .applicationLocales = LocaleList.forLanguageTags(tag)
        } else {
            AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags(tag))
        }
    }
}
