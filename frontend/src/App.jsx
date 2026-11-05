import React, { useState, useEffect, useRef } from 'react';
import ChatHeader from './components/ChatHeader';
import MessageBubble from './components/MessageBubble';
import ChatFooter from './components/ChatFooter';
import ConversationsSidebar from './components/ConversationsSidebar';
import AdminModal from './components/AdminModal';
import LanguageSelector from './components/LanguageSelector';
import FarmerProfileModal from './components/FarmerProfileModal';
import { useAudioRecorder } from './hooks/useAudioRecorder';
import { useAudioPlayer } from './hooks/useAudioPlayer';
import { sendVoiceQuery, sendTextQuery, submitFeedback } from './services/voiceApi';
import api from './services/api';
import { SUPPORTED_LANGUAGES } from './utils/constants';
import { Loader2, Sparkles, Sprout, AlertCircle, RefreshCw } from 'lucide-react';

export default function App() {
  const [selectedLang, setSelectedLang] = useState(SUPPORTED_LANGUAGES[0]); // Default Hindi (or Marathi if set)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isAdminOpen, setIsAdminOpen] = useState(false);
  const [isLangOpen, setIsLangOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  const [systemStatus, setSystemStatus] = useState(null);
  const [knowledgeStatus, setKnowledgeStatus] = useState(null);

  const [farmerContext, setFarmerContext] = useState({
    state: 'Maharashtra',
    district: 'Nagpur',
    cropName: 'Cotton (कापूस / कपास)',
    soilType: 'Black Soil (काली मिट्टी)',
    landSize: 2.5,
  });

  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const messagesEndRef = useRef(null);

  const {
    isRecording,
    audioBlob,
    recordingDuration,
    startRecording,
    stopRecording,
    resetRecording,
    error: micError,
  } = useAudioRecorder();

  const {
    isPlaying,
    playbackSpeed,
    playAudioFromBase64,
    togglePlayPause,
    changeSpeed,
  } = useAudioPlayer();

  const [activeAudioMsgId, setActiveAudioMsgId] = useState(null);

  // Initialize Starter Welcome Message
  const initWelcomeMessage = (lang) => {
    const greetings = {
      mr: "नमस्कार शेतकरी मित्र! मी किसानवाणी AI (Krishi Mitra) आहे. तुमच्या पिकावरील कीड, खत मात्रा, रोग किंवा सिंचनाबद्दल बोला किंवा टाइप करा.",
      hi: "नमस्ते किसान भाई! मैं किसानवाणी AI (कृषि मित्र) हूँ। अपनी फसल में कीट, रोग, खाद या सिंचाई के बारे में बोलकर या लिखकर पूछें।",
      en: "Hello Farmer Friend! I am KisanVani AI. Ask any question regarding crop pests, fertilizer doses, diseases, or irrigation."
    };

    const welcomeMsg = {
      id: 'welcome-msg',
      role: 'assistant',
      content: greetings[lang?.code] || greetings['hi'],
      language: lang?.code || 'hi',
      timestamp: Date.now(),
      sources: []
    };

    setMessages([welcomeMsg]);
  };

  // Fetch status and history on load
  const fetchStatusAndHistory = async () => {
    try {
      const [sysRes, knRes, convRes] = await Promise.all([
        api.get('/api/v1/system/status'),
        api.get('/api/v1/knowledge/status'),
        api.get('/api/v1/conversations').catch(() => ({ data: { conversations: [] } }))
      ]);
      setSystemStatus(sysRes.data);
      setKnowledgeStatus(knRes.data);
      if (convRes.data?.conversations) {
        setConversations(convRes.data.conversations);
      }
    } catch (e) {
      console.warn('Backend status fetch warning:', e);
    }
  };

  useEffect(() => {
    initWelcomeMessage(selectedLang);
    fetchStatusAndHistory();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Handle Voice Recording Submission
  useEffect(() => {
    if (audioBlob) {
      handleVoiceUpload(audioBlob);
    }
  }, [audioBlob]);

  const handleVoiceUpload = async (blob) => {
    setIsLoading(true);
    setErrorMsg(null);
    const durationStr = `${Math.floor(recordingDuration / 60)}:${recordingDuration % 60 < 10 ? '0' : ''}${recordingDuration % 60}`;

    const tempFarmerMsgId = `farmer-${Date.now()}`;
    const farmerMsg = {
      id: tempFarmerMsgId,
      role: 'farmer',
      isVoice: true,
      duration: durationStr,
      content: "🎤 Voice question recording...",
      timestamp: Date.now()
    };
    setMessages((prev) => [...prev, farmerMsg]);

    try {
      const response = await sendVoiceQuery(blob, {
        ...farmerContext,
        language: selectedLang.code,
        sessionId: activeSessionId
      });

      // Update farmer message with real transcript
      setMessages((prev) =>
        prev.map((m) =>
          m.id === tempFarmerMsgId ? { ...m, content: response.transcript } : m
        )
      );

      // Add AI response message
      const aiMsgId = `ai-${Date.now()}`;
      const aiMsg = {
        id: aiMsgId,
        role: 'assistant',
        content: response.answer_text,
        language: response.detected_language,
        audio_base64: response.audio_base64,
        sources: response.sources,
        is_grounded: response.is_grounded,
        timestamp: Date.now()
      };

      setMessages((prev) => [...prev, aiMsg]);
      fetchStatusAndHistory();

      // Automatically play response audio
      if (response.audio_base64) {
        setActiveAudioMsgId(aiMsgId);
        playAudioFromBase64(response.audio_base64, true);
      }
    } catch (err) {
      console.error('Voice processing error:', err);
      setErrorMsg(err.response?.data?.detail || 'Failed to process voice query. Please try again.');
    } finally {
      setIsLoading(false);
      resetRecording();
    }
  };

  const handleSendText = async (text) => {
    if (!text.trim() || isLoading) return;

    setIsLoading(true);
    setErrorMsg(null);

    const farmerMsg = {
      id: `farmer-${Date.now()}`,
      role: 'farmer',
      isVoice: false,
      content: text,
      timestamp: Date.now()
    };
    setMessages((prev) => [...prev, farmerMsg]);

    try {
      const response = await sendTextQuery(text, {
        ...farmerContext,
        language: selectedLang.code,
        sessionId: activeSessionId
      });

      const aiMsgId = `ai-${Date.now()}`;
      const aiMsg = {
        id: aiMsgId,
        role: 'assistant',
        content: response.answer_text,
        language: response.detected_language,
        audio_base64: response.audio_base64,
        sources: response.sources,
        is_grounded: response.is_grounded,
        timestamp: Date.now()
      };

      setMessages((prev) => [...prev, aiMsg]);
      fetchStatusAndHistory();

      if (response.audio_base64) {
        setActiveAudioMsgId(aiMsgId);
        playAudioFromBase64(response.audio_base64, true);
      }
    } catch (err) {
      console.error('Text processing error:', err);
      setErrorMsg(err.response?.data?.detail || 'Failed to get agricultural advisory.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTogglePlay = (msgId, audioB64) => {
    if (activeAudioMsgId === msgId) {
      togglePlayPause();
    } else {
      setActiveAudioMsgId(msgId);
      playAudioFromBase64(audioB64, true);
    }
  };

  const handleFeedback = async (msgId, isHelpful) => {
    try {
      await submitFeedback({
        session_id: activeSessionId || 'default-chat-session',
        message_index: 0,
        rating: isHelpful ? 5 : 1,
        is_helpful: isHelpful,
        crop_name: farmerContext.cropName,
      });
    } catch (e) {
      console.warn('Feedback error:', e);
    }
  };

  const handleNewChat = () => {
    setActiveSessionId(null);
    initWelcomeMessage(selectedLang);
  };

  const handleSelectSession = (sessionItem) => {
    setActiveSessionId(sessionItem.session_id);
    const historyMsgs = [
      {
        id: `f-${sessionItem.created_at}`,
        role: 'farmer',
        content: sessionItem.query_transcript || sessionItem.transcript || 'Voice query',
        timestamp: sessionItem.created_at
      },
      {
        id: `ai-${sessionItem.created_at}`,
        role: 'assistant',
        content: sessionItem.response_text || sessionItem.answer_text || '',
        language: sessionItem.detected_language,
        audio_base64: sessionItem.audio_base64,
        sources: sessionItem.sources || [],
        timestamp: sessionItem.created_at
      }
    ];
    setMessages(historyMsgs);
  };

  return (
    <div className="flex flex-col h-screen max-h-screen bg-stone-100 overflow-hidden font-sans">
      {/* WhatsApp-Style Chat Header */}
      <ChatHeader
        onToggleSidebar={() => setIsSidebarOpen(true)}
        onOpenAdmin={() => setIsAdminOpen(true)}
        onOpenLang={() => setIsLangOpen(true)}
        onOpenProfile={() => setIsProfileOpen(true)}
        currentLang={selectedLang}
        farmerContext={farmerContext}
      />

      {/* Main Chat Message Stream */}
      <main className="flex-1 overflow-y-auto px-3 sm:px-6 py-4 bg-[#efeae2] bg-opacity-90 relative">
        <div className="max-w-3xl mx-auto space-y-3 pb-2">
          {/* Security & Grounding Banner */}
          <div className="text-center my-2">
            <span className="bg-white/90 text-stone-600 text-[11px] px-3 py-1 rounded-full shadow-xs border border-stone-200/80 inline-flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-emerald-600" />
              Grounded in verified ICAR & KVK agricultural science
            </span>
          </div>

          {/* Error Alert */}
          {(errorMsg || micError) && (
            <div className="p-3 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2 shadow-xs">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
              <span>{errorMsg || micError}</span>
            </div>
          )}

          {/* Render All Chat Messages */}
          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              isPlaying={isPlaying}
              activeAudioMsgId={activeAudioMsgId}
              playbackSpeed={playbackSpeed}
              onTogglePlay={handleTogglePlay}
              onChangeSpeed={changeSpeed}
              onFeedback={handleFeedback}
            />
          ))}

          {/* Processing / Thinking State */}
          {isLoading && (
            <div className="flex justify-start mb-4 animate-in fade-in duration-200">
              <div className="bg-white text-stone-700 rounded-2xl rounded-tl-xs px-4 py-3 shadow-xs border border-stone-200 flex items-center space-x-2.5 text-xs">
                <Loader2 className="w-4 h-4 animate-spin text-emerald-600" />
                <span className="font-medium">KisanVani is analyzing your question and retrieving ICAR advisories...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* WhatsApp-Style Input / Recording Footer */}
      <ChatFooter
        isRecording={isRecording}
        recordingDuration={recordingDuration}
        onStartRecording={startRecording}
        onStopRecording={stopRecording}
        onSendText={handleSendText}
        isLoading={isLoading}
        selectedLang={selectedLang}
      />

      {/* Sidebar Drawer */}
      <ConversationsSidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        conversations={conversations}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onOpenProfile={() => setIsProfileOpen(true)}
        farmerContext={farmerContext}
      />

      {/* Admin & KVK Hub Modal */}
      <AdminModal
        isOpen={isAdminOpen}
        onClose={() => setIsAdminOpen(false)}
        systemStatus={systemStatus}
        knowledgeStatus={knowledgeStatus}
        onRefreshStatus={fetchStatusAndHistory}
      />

      {/* Language Selector Modal */}
      <LanguageSelector
        isOpen={isLangOpen}
        onClose={() => setIsLangOpen(false)}
        selectedLang={selectedLang}
        onSelectLang={(lang) => {
          setSelectedLang(lang);
          initWelcomeMessage(lang);
        }}
      />

      {/* Farmer Profile Modal */}
      <FarmerProfileModal
        isOpen={isProfileOpen}
        onClose={() => setIsProfileOpen(false)}
        context={farmerContext}
        onSaveContext={setFarmerContext}
      />
    </div>
  );
}
