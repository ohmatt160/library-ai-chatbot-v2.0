import { Link, useLocation } from 'react-router';
import { MessageSquare, Search, ShieldCheck, Home } from 'lucide-react';
import { useAuthStore } from '../../store/auth';
import { useEffect } from 'react';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '../ui/sidebar';

export function AppSidebar() {
  const location = useLocation();
  const { user, isAuthenticated } = useAuthStore();
  const { isMobile, setOpenMobile } = useSidebar();

  const navItems = [
    {
      title: 'Home',
      url: '/',
      icon: Home,
    },
    {
      title: 'Chat',
      url: '/chat',
      icon: MessageSquare,
    },
    {
      title: 'Search Books',
      url: '/search',
      icon: Search,
    },
  ];

  const isAdmin = user?.user_type === 'Admin' || user?.user_type === 'admin';
  const adminItems = isAdmin ? [
    {
      title: 'Admin Dashboard',
      url: '/admin',
      icon: ShieldCheck,
    },
  ] : [];

  // Close mobile sidebar when location changes (user navigates)
  useEffect(() => {
    if (isMobile) {
      setOpenMobile(false);
    }
  }, [location.pathname, isMobile, setOpenMobile]);

  // Don't render if not authenticated
  if (!isAuthenticated) return null;
  return (
    <Sidebar>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild isActive={location.pathname === item.url}>
                    <Link to={item.url}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {adminItems.length > 0 && (
          <SidebarGroup>
            <SidebarGroupLabel>Admin</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {adminItems.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild isActive={location.pathname === item.url}>
                      <Link to={item.url}>
                        <item.icon className="h-4 w-4" />
                        <span>{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        )}
      </SidebarContent>
    </Sidebar>
  );
}
