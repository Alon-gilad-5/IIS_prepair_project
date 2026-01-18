/** Speech-to-text using Web Speech Recognition API. */

type RecognitionCallback = (transcript: string) => void;
type ErrorCallback = (error: string) => void;

let recognition: any = null;

if ('webkitSpeechRecognition' in window) {
  const SpeechRecognition = (window as any).webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-US';
}

export function startRecognition(
  onTranscript: RecognitionCallback,
  onError?: ErrorCallback
): () => void {
  if (!recognition) {
    if (onError) {
      onError('Speech recognition not supported. Please use text input instead.');
    }
    return () => {}; // No-op stop function
  }

  let finalTranscript = '';

  recognition.onresult = (event: any) => {
    let interimTranscript = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalTranscript += transcript + ' ';
      } else {
        interimTranscript += transcript;
      }
    }
    onTranscript(finalTranscript + interimTranscript);
  };

  recognition.onerror = (event: any) => {
    if (onError) {
      onError(`Recognition error: ${event.error}`);
    }
  };

  recognition.onend = () => {
    // Restart if needed
    // recognition.start();
  };

  recognition.start();

  return () => {
    if (recognition) {
      recognition.stop();
    }
  };
}

export function stopRecognition(): void {
  if (recognition) {
    recognition.stop();
  }
}

export function isSupported(): boolean {
  return recognition !== null;
}
