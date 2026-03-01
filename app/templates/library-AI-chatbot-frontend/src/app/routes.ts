import { createBrowserRouter } from 'react-router';
import { RootLayout } from './pages/RootLayout';
import { HomePage } from './pages/HomePage';
import { ChatPage } from './pages/ChatPage';
import { SearchPage } from './pages/SearchPage';
import { AdminPage } from './pages/AdminPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { MyBorrowRequestsPage } from './pages/MyBorrowRequestsPage';
import { AdminBorrowPage } from './pages/AdminBorrowPage';

export const router = createBrowserRouter([
  {
    path: '/',
    Component: RootLayout,
    children: [
      { index: true, Component: HomePage },
      { path: 'chat', Component: ChatPage },
      { path: 'search', Component: SearchPage },
      { path: 'my-borrows', Component: MyBorrowRequestsPage },
      { path: 'admin', Component: AdminPage },
      { path: 'admin/borrows', Component: AdminBorrowPage },
      { path: '*', Component: NotFoundPage },
    ],
  },
]);
