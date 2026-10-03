package org.almakhutut.alhayy

import org.almakhutut.alhayy.data.SocialLinks
import org.almakhutut.alhayy.ui.supportedLanguages
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class NavigationAndLinksTest {
    @Test
    fun everyInternalScreenHasBackContract() {
        AppScreen.entries.filter { it != AppScreen.HOME }.forEach {
            assertTrue(it.hasInternalBack)
        }
        assertFalse(AppScreen.HOME.hasInternalBack)
    }

    @Test
    fun allSocialLinksHaveSupportedSchemes() {
        assertTrue(SocialLinks.all.all(SocialLinks::isSupported))
    }

    @Test
    fun requestedLanguageSetIsComplete() {
        assertEquals(
            setOf("ar", "en", "tr", "es", "de", "it", "fr", "ur", "fa", "ru"),
            supportedLanguages.map { it.tag }.toSet(),
        )
    }
}
