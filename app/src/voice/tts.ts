/** Text-to-speech using Web Speech API with event callbacks. */

let speechQueue: string[] = [];
let isSpeakingInternal = false;
let onSpeakingChangeCallback: ((speaking: boolean) => void) | null = null;

function notifySpeakingChange(speaking: boolean) {
  isSpeakingInternal = speaking;
  if (onSpeakingChangeCallback) {
    onSpeakingChangeCallback(speaking);
  }
}

function processQueue() {
  if (isSpeakingInternal || speechQueue.length === 0) {
    if (speechQueue.length === 0 && !isSpeakingInternal) {
      notifySpeakingChange(false);
    }
    return;
  }

  const text = speechQueue.shift();
  if (!text) return;

  notifySpeakingChange(true);

  if ('speechSynthesis' in window) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    
    utterance.onend = () => {
      isSpeakingInternal = false;
      setTimeout(() => {
        processQueue();
      }, 300);
    };

    utterance.onerror = () => {
      isSpeakingInternal = false;
      processQueue();
    };

    window.speechSynthesis.speak(utterance);
  } else {
    console.warn('Speech synthesis not supported');
    isSpeakingInternal = false;
    processQueue();
  }
}

export function speak(text: string): void {
  if (!text || text.trim() === '') return;
  speechQueue.push(text);
  processQueue();
}

export function speakSequential(texts: string[]): void {
  if (texts.length === 0) return;
  speechQueue.push(...texts);
  processQueue();
}

export function stopSpeaking(): void {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
  speechQueue = [];
  isSpeakingInternal = false;
  notifySpeakingChange(false);
}

export function onSpeakingChange(callback: (speaking: boolean) => void): () => void {
  onSpeakingChangeCallback = callback;
  return () => {
    onSpeakingChangeCallback = null;
  };
}

export function isSpeaking(): boolean {
  return isSpeakingInternal || speechQueue.length > 0;
}

export function isSupported(): boolean {
  return 'speechSynthesis' in window;
}
