import { useState } from 'react';
import { Link } from 'react-router';
import { Menu, Sun, Moon, User, LogOut, BookOpen } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useAuthStore } from '../../store/auth';
import { useMutation } from '@tanstack/react-query';
import { authApi } from '../../services/api';
import { toast } from 'sonner';
import { LoginModal } from '../auth/LoginModal';
import { RegisterModal } from '../auth/RegisterModal';
import { SystemHealth } from '../common/SystemHealth';
import { Button } from '../ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { useSidebar } from '../ui/sidebar';

interface HeaderProps {
  onMenuClick: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const { theme, setTheme } = useTheme();
  const { user, isAuthenticated, clearAuth } = useAuthStore();
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const { isMobile, toggleSidebar } = useSidebar();

  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      clearAuth();
      toast.success('Logged out successfully');
    },
    onError: () => {
      clearAuth(); // Clear auth even if API call fails
    },
  });

  const handleLogout = () => {
    logoutMutation.mutate();
  };

  const getDisplayName = () => {
    if (!user) return '';
    if (user.first_name || user.last_name) {
      return `${user.first_name || ''} ${user.last_name || ''}`.trim();
    }
    return user.username;
  };

  return (
    <>
      <header className="sticky top-0 z-50 w-full border-b border-border/50 backdrop-blur-xl bg-background/80 supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-16 items-center justify-between px-4 md:px-6 lg:px-8 mx-auto max-w-7xl">
          <div className="flex items-center gap-4">
            {/* Menu button - visible on all screens, uses sidebar toggle */}
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSidebar}
            >
              <Menu className="h-5 w-5" />
            </Button>
            <Link to="/" className="flex items-center gap-2">
              <BookOpen className="h-6 w-6" />
              <span className="font-semibold text-lg hidden sm:inline-block">
                Library AI
              </span>
            </Link>
          </div>

          <div className="flex items-center gap-2">
            <SystemHealth />

            {/* Theme Toggle */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            >
              <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
              <span className="sr-only">Toggle theme</span>
            </Button>

            {/* User Menu */}
            {isAuthenticated ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <User className="h-5 w-5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuLabel>
                    <div className="flex flex-col">
                      <span>{getDisplayName()}</span>
                      <span className="text-xs text-muted-foreground">{user?.email || user?.username}</span>
                      <span className="text-xs text-muted-foreground">{user?.user_type}</span>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout}>
                    <LogOut className="mr-2 h-4 w-4" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Button onClick={() => setShowLogin(true)}>Login</Button>
            )}
          </div>
        </div>
      </header>

      <LoginModal
        isOpen={showLogin}
        onClose={() => setShowLogin(false)}
        onSwitchToRegister={() => {
          setShowLogin(false);
          setShowRegister(true);
        }}
      />
      <RegisterModal
        isOpen={showRegister}
        onClose={() => setShowRegister(false)}
        onSwitchToLogin={() => {
          setShowRegister(false);
          setShowLogin(true);
        }}
      />
    </>
  );
}
