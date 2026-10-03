export function canSpeak(): boolean {
  return "speechSynthesis" in window && "SpeechSynthesisUtterance" in window;
}

export function speakArabic(text: string): void {
  if (!canSpeak()) throw new Error("Text-to-speech is not supported in this browser");
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "ar";
  utterance.rate = 0.9;
  window.speechSynthesis.speak(utterance);
}
