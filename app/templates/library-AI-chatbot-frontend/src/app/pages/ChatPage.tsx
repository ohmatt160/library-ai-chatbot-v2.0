import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { ChatInterface } from '../components/chat/ChatInterface';
import { SatisfactionSurvey } from '../components/admin/SatisfactionSurvey';
import { useAuthStore } from '../store/auth';
import { LoginModal } from '../components/auth/LoginModal';
import { RegisterModal } from '../components/auth/RegisterModal';
import { Button } from '../components/ui/button';
import { Star } from 'lucide-react';

export function ChatPage() {
  const { token } = useAuthStore();
  const navigate = useNavigate();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [showSurvey, setShowSurvey] = useState(false);
  const [sessionId, setSessionId] = useState('');

  useEffect(() => {
    if (!token) {
      setShowLoginModal(true);
    }
  }, [token]);

  const handleLoginSuccess = () => {
    setShowLoginModal(false);
  };

  const handleLoginClose = () => {
    setShowLoginModal(false);
    navigate('/');
  };

  const handleEndSession = (sid: string) => {
    setSessionId(sid);
    setShowSurvey(true);
  };

  const handleSurveyComplete = () => {
    setShowSurvey(false);
  };
  return (
    <div className="h-full flex flex-col">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1>AI Chat Assistant</h1>
          <p className="text-muted-foreground">
            Ask questions, get book recommendations, or search our catalog
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => {
            const sid = `session_${Date.now()}`;
            setSessionId(sid);
            setShowSurvey(true);
          }}
        >
          <Star className="mr-2 h-4 w-4" />
          Feedback
        </Button>
      </div>
      <div className="flex-1 min-h-0">
        {showSurvey ? (
          <div className="max-w-2xl mx-auto py-8">
            <SatisfactionSurvey 
              sessionId={sessionId || `session_${Date.now()}`} 
              onComplete={handleSurveyComplete} 
            />
          </div>
        ) : token ? (
          <ChatInterface onEndSession={handleEndSession} />
        ) : null}
      </div>
      <LoginModal
        isOpen={showLoginModal}
        onClose={handleLoginClose}
        onSwitchToRegister={() => {
          setShowLoginModal(false);
          setShowRegisterModal(true);
        }}
      />
      <RegisterModal
        isOpen={showRegisterModal}
        onClose={() => setShowRegisterModal(false)}
        onSwitchToLogin={() => {
          setShowRegisterModal(false);
          setShowLoginModal(true);
        }}
      />
    </div>
  );
}
