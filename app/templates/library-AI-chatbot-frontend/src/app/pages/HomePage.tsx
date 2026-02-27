import { Link, useNavigate } from 'react-router';
import { MessageSquare, Search, BookOpen, Sparkles } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { useAuthStore } from '../store/auth';
import { LoginModal } from '../components/auth/LoginModal';
import { RegisterModal } from '../components/auth/RegisterModal';

export function HomePage() {
  const { token } = useAuthStore();
  const navigate = useNavigate();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [loginRedirectTo, setLoginRedirectTo] = useState<string | null>(null);
  const prevTokenRef = useRef(token);

  useEffect(() => {
    // Check if we just logged in (token went from null to not null)
    if (!prevTokenRef.current && token && loginRedirectTo) {
      navigate(loginRedirectTo);
      setLoginRedirectTo(null);
    }
    prevTokenRef.current = token;
  }, [token, loginRedirectTo, navigate]);

  const handleProtectedAction = (redirectPath: string) => {
    if (!token) {
      setLoginRedirectTo(redirectPath);
      setShowLoginModal(true);
    } else {
      navigate(redirectPath);
    }
  };
  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <div className="text-center space-y-4 py-12 px-4">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-primary/10 mb-4">
          <BookOpen className="h-10 w-10 text-primary" />
        </div>
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold">
          Welcome to Library AI
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Your intelligent assistant for discovering, searching, and exploring our library catalog
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
          <Button size="lg" onClick={() => handleProtectedAction('/chat')}>
            <MessageSquare className="mr-2 h-5 w-5" />
            Start Chatting
          </Button>
          <Button variant="outline" size="lg" onClick={() => handleProtectedAction('/search')}>
            <Search className="mr-2 h-5 w-5" />
            Search Books
          </Button>
        </div>
      </div>

      {/* Features */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="backdrop-blur-sm bg-card/80 border border-border/50 hover:shadow-lg transition-shadow">
          <CardHeader>
            <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-2">
              <MessageSquare className="h-6 w-6 text-primary" />
            </div>
            <CardTitle>AI Chat Assistant</CardTitle>
            <CardDescription>
              Get instant answers about books, recommendations, and library services
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" className="w-full" onClick={() => handleProtectedAction('/chat')}>
              Try Chat
            </Button>
          </CardContent>
        </Card>

        <Card className="backdrop-blur-sm bg-card/80 border border-border/50 hover:shadow-lg transition-shadow">
          <CardHeader>
            <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-2">
              <Search className="h-6 w-6 text-primary" />
            </div>
            <CardTitle>Advanced Search</CardTitle>
            <CardDescription>
              Search our catalog by title, author, subject, and more
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" className="w-full" onClick={() => handleProtectedAction('/search')}>
              Search Now
            </Button>
          </CardContent>
        </Card>

        <Card className="backdrop-blur-sm bg-card/80 border border-border/50 hover:shadow-lg transition-shadow">
          <CardHeader>
            <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-2">
              <Sparkles className="h-6 w-6 text-primary" />
            </div>
            <CardTitle>Smart Recommendations</CardTitle>
            <CardDescription>
              Get personalized book suggestions based on your interests
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" className="w-full" onClick={() => handleProtectedAction('/chat')}>
              Get Recommendations
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Stats */}
      <Card className="backdrop-blur-sm bg-card/80 border border-border/50">
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold mb-2">10,000+</div>
              <div className="text-muted-foreground">Books Available</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">24/7</div>
              <div className="text-muted-foreground">AI Assistance</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">1,000+</div>
              <div className="text-muted-foreground">Happy Users</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <LoginModal
        isOpen={showLoginModal}
        onClose={() => {
          setShowLoginModal(false);
          setLoginRedirectTo(null);
        }}
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
