import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { speak, stopSpeaking } from '../voice/tts';
import { startRecognition, stopRecognition, isSupported as sttSupported } from '../voice/stt';
import './InterviewRoom.css';

function InterviewRoom() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [question, setQuestion] = useState<any>(null);
  const [transcript, setTranscript] = useState('');
  const [userCode, setUserCode] = useState('');
  const [showWhiteboard, setShowWhiteboard] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState({ turn_index: 0, total: 0 });
  const [timer, setTimer] = useState(0);
  const stopRecognitionRef = useRef<(() => void) | null>(null);
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!sessionId) {
      navigate('/');
      return;
    }

    // Start timer
    timerIntervalRef.current = setInterval(() => {
      setTimer((prev) => prev + 1);
    }, 1000);

    // Load initial question
    loadQuestion();

    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
      stopSpeaking();
      if (stopRecognitionRef.current) {
        stopRecognitionRef.current();
      }
    };
  }, [sessionId]);

  const loadQuestion = async () => {
    // For MVP, we'll get the first question from the session start
    // In a full implementation, this would come from the API
  };

  const handleStartRecording = () => {
    if (!sttSupported()) {
      alert('Speech recognition not supported. Please use text input.');
      return;
    }

    setIsRecording(true);
    stopRecognitionRef.current = startRecognition(
      (text) => setTranscript(text),
      (error) => {
        alert(`Recognition error: ${error}`);
        setIsRecording(false);
      }
    );
  };

  const handleStopRecording = () => {
    if (stopRecognitionRef.current) {
      stopRecognitionRef.current();
      stopRecognitionRef.current = null;
    }
    setIsRecording(false);
  };

  const handleSubmit = async () => {
    if (!sessionId || (!transcript.trim() && !userCode.trim())) {
      alert('Please provide an answer');
      return;
    }

    setIsProcessing(true);
    handleStopRecording();

    try {
      const result = await api.nextInterview(
        sessionId,
        transcript,
        userCode.trim() || undefined
      );

      if (result.is_done) {
        navigate(`/done/${sessionId}`);
      } else {
        setQuestion(result.next_question);
        setTranscript('');
        setUserCode('');
        setShowWhiteboard(false);
        setProgress(result.progress);

        // Speak next question if available
        if (result.next_question?.text) {
          speak(result.next_question.text);
        }
      }
    } catch (error: any) {
      alert(`Error: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRepeatQuestion = () => {
    if (question?.text) {
      speak(question.text);
    }
  };

  const handleEndInterview = async () => {
    if (!sessionId) return;

    handleStopRecording();
    stopSpeaking();

    try {
      await api.endInterview(sessionId);
      navigate(`/done/${sessionId}`);
    } catch (error: any) {
      alert(`Error ending interview: ${error.message}`);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="interview-room">
      <div className="container">
        <div className="header">
          <div className="timer">Time: {formatTime(timer)}</div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{
                width: `${progress.total > 0 ? (progress.turn_index / progress.total) * 100 : 0}%`,
              }}
            />
            <span>
              Question {progress.turn_index} of {progress.total}
            </span>
          </div>
        </div>

        {question && (
          <div className="question-section">
            <h2>Question</h2>
            <p>{question.text}</p>
            <button className="btn btn-secondary" onClick={handleRepeatQuestion}>
              Repeat Question
            </button>
            {question.type === 'code' && (
              <button
                className="btn btn-code"
                onClick={() => setShowWhiteboard(true)}
              >
                🖊️ Open Code Whiteboard
              </button>
            )}
          </div>
        )}

        <div className="transcript-section">
          <label>Your Answer</label>
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder={sttSupported() ? 'Click mic to record or type here...' : 'Type your answer here...'}
            rows={10}
          />
        </div>

        {showWhiteboard && (
          <div className="whiteboard-overlay" onClick={() => setShowWhiteboard(false)}>
            <div className="whiteboard-modal" onClick={(e) => e.stopPropagation()}>
              <div className="whiteboard-header">
                <h3>Code Whiteboard</h3>
                <button className="close-btn" onClick={() => setShowWhiteboard(false)}>
                  ✕
                </button>
              </div>
              <textarea
                className="whiteboard-editor"
                value={userCode}
                onChange={(e) => setUserCode(e.target.value)}
                placeholder="Type your code solution here..."
                autoFocus
                spellCheck={false}
              />
              <div className="whiteboard-footer">
                <button className="btn btn-secondary" onClick={() => setShowWhiteboard(false)}>
                  Close
                </button>
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    setShowWhiteboard(false);
                    handleSubmit();
                  }}
                  disabled={!userCode.trim() && !transcript.trim()}
                >
                  Submit Code
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="controls">
          <button
            className={`btn ${isRecording ? 'btn-danger' : 'btn-primary'}`}
            onClick={isRecording ? handleStopRecording : handleStartRecording}
            disabled={isProcessing}
          >
            {isRecording ? '⏹️ Stop Recording' : '🎤 Start Recording'}
          </button>

          <button
            className="btn btn-secondary"
            onClick={handleSubmit}
            disabled={isProcessing || !transcript.trim()}
          >
            {isProcessing ? 'Processing...' : 'Submit Answer'}
          </button>

          <button className="btn btn-tertiary" onClick={handleEndInterview}>
            End Interview
          </button>
        </div>
      </div>
    </div>
  );
}

export default InterviewRoom;
