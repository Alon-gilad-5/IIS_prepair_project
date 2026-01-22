import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { speak, speakSequential, stopSpeaking } from '../voice/tts';
import { startRecognition, stopRecognition, isSupported as sttSupported } from '../voice/stt';
import { useToast } from '../components/Toast';
import './InterviewRoom.css';

interface Message {
  id: string;
  role: 'interviewer' | 'user';
  content: string;
  timestamp: Date;
}

function InterviewRoom() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { showToast } = useToast();
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [transcript, setTranscript] = useState('');
  const [userCode, setUserCode] = useState('');
  const [showWhiteboard, setShowWhiteboard] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [progress, setProgress] = useState({ turn_index: 0, total: 0 });
  const [timer, setTimer] = useState(0);
  const [voiceOn, setVoiceOn] = useState(true);
  const [currentQuestion, setCurrentQuestion] = useState<any>(null);
  
  const stopRecognitionRef = useRef<(() => void) | null>(null);
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const addMessage = (role: 'interviewer' | 'user', content: string) => {
    const newMessage: Message = {
      id: `${Date.now()}-${Math.random()}`,
      role,
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!sessionId) {
      navigate('/');
      return;
    }

    const storedVoiceOn = localStorage.getItem('voiceOn');
    if (storedVoiceOn !== null) {
      setVoiceOn(storedVoiceOn === 'true');
    }

    timerIntervalRef.current = setInterval(() => {
      setTimer((prev) => prev + 1);
    }, 1000);

    loadInitialQuestion();

    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
      stopSpeaking();
      if (stopRecognitionRef.current) {
        stopRecognitionRef.current();
      }
    };
  }, [sessionId, navigate]);

  const loadInitialQuestion = async () => {
    const storedFirstQuestion = localStorage.getItem('firstQuestion');
    const storedTotalQuestions = localStorage.getItem('totalQuestions');

    if (storedFirstQuestion) {
      try {
        const firstQuestion = JSON.parse(storedFirstQuestion);
        setCurrentQuestion(firstQuestion);
        
        const total = storedTotalQuestions ? parseInt(storedTotalQuestions, 10) : 0;
        setProgress({ turn_index: 0, total });

        // Add welcome message and first question
        addMessage('interviewer', "Welcome! Let's begin the interview. I'll be asking you a series of questions. Take your time to answer each one thoughtfully.");
        
        setTimeout(() => {
          addMessage('interviewer', firstQuestion.text);
          if (voiceOn) {
            setIsSpeaking(true);
            speakSequential([
              "Welcome! Let's begin the interview. I'll be asking you a series of questions.",
              firstQuestion.text
            ]);
            // Estimate speaking time and reset isSpeaking
            setTimeout(() => setIsSpeaking(false), 8000);
          }
        }, 500);

        localStorage.removeItem('firstQuestion');
        localStorage.removeItem('totalQuestions');
      } catch (error) {
        console.error('Failed to load first question:', error);
      }
    }
  };

  const handleStartRecording = () => {
    if (!sttSupported()) {
      showToast('Speech recognition not supported. Please type your answer.', 'warning');
      return;
    }

    stopSpeaking();
    setIsSpeaking(false);
    setIsRecording(true);
    
    stopRecognitionRef.current = startRecognition(
      (text) => setTranscript(text),
      (error) => {
        showToast(`Recognition error: ${error}`, 'error');
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
    if (!sessionId) return;
    
    const answer = transcript.trim();
    if (!answer && !userCode.trim()) {
      showToast('Please provide an answer', 'warning');
      return;
    }

    // Add user's response to chat
    addMessage('user', answer || userCode);

    setIsProcessing(true);
    handleStopRecording();

    try {
      const result = await api.nextInterview(
        sessionId,
        answer,
        userCode.trim() || undefined
      );

      if (result.is_done) {
        addMessage('interviewer', "Thank you for completing the interview! Let me prepare your feedback...");
        if (voiceOn) {
          speak("Thank you for completing the interview! Let me prepare your feedback.");
        }
        setTimeout(() => navigate(`/done/${sessionId}`), 2000);
      } else {
        // Build interviewer response
        const responses: string[] = [];
        
        if (result.interviewer_message) {
          responses.push(result.interviewer_message);
          addMessage('interviewer', result.interviewer_message);
        }
        
        if (result.followup_question?.text) {
          responses.push(result.followup_question.text);
          setTimeout(() => {
            addMessage('interviewer', result.followup_question!.text);
          }, 1000);
        }
        
        if (result.next_question?.text) {
          responses.push(result.next_question.text);
          setCurrentQuestion(result.next_question);
          setTimeout(() => {
            addMessage('interviewer', result.next_question!.text);
          }, responses.length > 1 ? 2000 : 1000);
        }

        setTranscript('');
        setUserCode('');
        setShowWhiteboard(false);
        setProgress(result.progress);

        // Speak all responses
        if (voiceOn && responses.length > 0) {
          setIsSpeaking(true);
          speakSequential(responses);
          setTimeout(() => setIsSpeaking(false), responses.length * 4000);
        }
      }
    } catch (error: any) {
      showToast(error.message || 'Failed to process answer', 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleToggleVoice = () => {
    const newVoiceOn = !voiceOn;
    setVoiceOn(newVoiceOn);
    localStorage.setItem('voiceOn', String(newVoiceOn));
    if (!newVoiceOn) {
      stopSpeaking();
      setIsSpeaking(false);
    }
    showToast(newVoiceOn ? 'Voice enabled' : 'Voice disabled', 'info');
  };

  const handleRepeatLast = () => {
    const lastInterviewerMessage = [...messages].reverse().find(m => m.role === 'interviewer');
    if (lastInterviewerMessage && voiceOn) {
      setIsSpeaking(true);
      speak(lastInterviewerMessage.content);
      setTimeout(() => setIsSpeaking(false), 4000);
    }
  };

  const handleEndInterview = async () => {
    if (!sessionId) return;

    handleStopRecording();
    stopSpeaking();

    try {
      await api.endInterview(sessionId);
      showToast('Interview ended', 'success');
      navigate(`/done/${sessionId}`);
    } catch (error: any) {
      showToast(error.message || 'Failed to end interview', 'error');
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="interview-room conversation-mode">
      <div className="conversation-container">
        {/* Header */}
        <div className="conversation-header">
          <div className="header-left">
            <div className="interviewer-avatar">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2a5 5 0 015 5v2a5 5 0 01-10 0V7a5 5 0 015-5z"/>
                <path d="M12 14c-5 0-9 2-9 5v3h18v-3c0-3-4-5-9-5z"/>
              </svg>
            </div>
            <div className="header-info">
              <h2>AI Interviewer</h2>
              <span className={`status ${isSpeaking ? 'speaking' : isProcessing ? 'thinking' : 'listening'}`}>
                {isSpeaking ? 'Speaking...' : isProcessing ? 'Thinking...' : 'Listening'}
              </span>
            </div>
          </div>
          <div className="header-right">
            <span className="timer">{formatTime(timer)}</span>
            <span className="progress-text">Q{progress.turn_index}/{progress.total}</span>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="chat-container" ref={chatContainerRef}>
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.role}`}>
              <div className="message-bubble">
                {message.content}
              </div>
            </div>
          ))}
          
          {isProcessing && (
            <div className="message interviewer">
              <div className="message-bubble typing">
                <span className="dot"></span>
                <span className="dot"></span>
                <span className="dot"></span>
              </div>
            </div>
          )}
        </div>

        {/* Voice Controls */}
        <div className="voice-controls">
          {/* Live transcript display */}
          {(isRecording || transcript) && (
            <div className="live-transcript">
              <div className="transcript-label">
                {isRecording && <span className="recording-dot"></span>}
                {isRecording ? 'Listening...' : 'Your response:'}
              </div>
              <div className="transcript-text">
                {transcript || '(Speak now...)'}
              </div>
            </div>
          )}

          <div className="control-buttons">
            {/* Main mic button */}
            <button
              className={`btn-mic ${isRecording ? 'recording' : ''}`}
              onClick={isRecording ? handleStopRecording : handleStartRecording}
              disabled={isProcessing || isSpeaking}
            >
              {isRecording ? (
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <rect x="6" y="6" width="12" height="12" rx="2"/>
                </svg>
              ) : (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/>
                  <path d="M19 10v2a7 7 0 01-14 0v-2"/>
                  <line x1="12" y1="19" x2="12" y2="23"/>
                  <line x1="8" y1="23" x2="16" y2="23"/>
                </svg>
              )}
            </button>

            {/* Submit button */}
            <button
              className="btn-submit"
              onClick={handleSubmit}
              disabled={isProcessing || (!transcript.trim() && !userCode.trim())}
            >
              {isProcessing ? 'Processing...' : 'Send'}
            </button>

            {/* Secondary controls */}
            <div className="secondary-controls">
              <button
                className={`btn-icon ${voiceOn ? 'active' : ''}`}
                onClick={handleToggleVoice}
                title={voiceOn ? 'Mute voice' : 'Enable voice'}
              >
                {voiceOn ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                    <path d="M19.07 4.93a10 10 0 010 14.14M15.54 8.46a5 5 0 010 7.07"/>
                  </svg>
                ) : (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                    <line x1="23" y1="9" x2="17" y2="15"/>
                    <line x1="17" y1="9" x2="23" y2="15"/>
                  </svg>
                )}
              </button>

              <button
                className="btn-icon"
                onClick={handleRepeatLast}
                disabled={!voiceOn || isSpeaking}
                title="Repeat last message"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="1 4 1 10 7 10"/>
                  <path d="M3.51 15a9 9 0 102.13-9.36L1 10"/>
                </svg>
              </button>

              {currentQuestion?.type === 'code' && (
                <button
                  className="btn-icon code"
                  onClick={() => setShowWhiteboard(true)}
                  title="Open code whiteboard"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="16 18 22 12 16 6"/>
                    <polyline points="8 6 2 12 8 18"/>
                  </svg>
                </button>
              )}

              <button
                className="btn-icon danger"
                onClick={handleEndInterview}
                title="End interview"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
              </button>
            </div>
          </div>

          {/* Text input fallback */}
          <div className="text-input-fallback">
            <input
              type="text"
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              placeholder="Or type your answer here..."
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSubmit()}
              disabled={isRecording || isProcessing}
            />
          </div>
        </div>
      </div>

      {/* Code Whiteboard Modal */}
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
    </div>
  );
}

export default InterviewRoom;
