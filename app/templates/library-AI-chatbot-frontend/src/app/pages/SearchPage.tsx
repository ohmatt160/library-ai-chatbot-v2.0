import { useEffect } from 'react';
import { useNavigate } from 'react-router';
import { BookSearch } from '../components/search/BookSearch';
import { useAuthStore } from '../store/auth';
import { LoginModal } from '../components/auth/LoginModal';
import { RegisterModal } from '../components/auth/RegisterModal';
import { useState } from 'react';

export function SearchPage() {
  const { token } = useAuthStore();
  const navigate = useNavigate();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);

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
  return (
    <div>
      <div className="mb-6">
        <h1>Search Books</h1>
        <p className="text-muted-foreground">
          Find books in our library catalog by title, author, or subject
        </p>
      </div>
      {token && <BookSearch />}
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
