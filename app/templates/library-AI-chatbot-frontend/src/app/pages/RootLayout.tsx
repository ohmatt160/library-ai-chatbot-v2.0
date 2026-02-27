import { Outlet } from 'react-router';
import { useState } from 'react';
import { Header } from '../components/layout/Header';
import { AppSidebar } from '../components/layout/AppSidebar';
import { SidebarProvider, SidebarInset } from '../components/ui/sidebar';

export function RootLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <SidebarProvider defaultOpen={false} open={sidebarOpen} onOpenChange={setSidebarOpen}>
      <div className="flex min-h-screen w-full bg-gradient-to-br from-[var(--gradient-from)] to-[var(--gradient-to)]">
        <AppSidebar />
        <SidebarInset className="flex-1 flex flex-col">
          <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
          <main className="flex-1 p-4 md:p-6 lg:p-8">
            <div className="container mx-auto max-w-7xl">
              <Outlet />
            </div>
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}
