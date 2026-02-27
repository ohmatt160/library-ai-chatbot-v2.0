# Library AI Chatbot Frontend

A modern, production-ready React + TypeScript frontend for the Library AI Chatbot system.

## Features

### 🎨 Design & Theme

- **Light Blue & Black Color Scheme** (`#E3F2FD` and `#1A1A1A`)
- **Dark Mode Support** with system detection
- **Glassmorphism Effects** on cards and components
- **Gradient Backgrounds** that change with theme
- **Responsive Design** (mobile-first approach)

### 🔐 Authentication

- Login/Register modals with validation
- JWT token storage in localStorage
- Auto-redirect after successful login
- Profile dropdown with logout functionality
- Protected admin routes

### 💬 Chat Interface

- Real-time message bubbles (user on right, bot on left)
- Animated typing indicator with dots
- **Markdown support** for bot responses
- Suggested follow-up questions as clickable chips
- Thumbs up/down feedback buttons
- Message timestamps
- Auto-scroll to bottom
- File attachment UI (placeholder)
- Session management

### 📚 Book Search

- Search bar with advanced filters (author, subject)
- Grid/List view toggle
- Book cards displaying:
  - Title, Author, ISBN
  - Location and availability status
  - Reserve button (requires authentication)
- Real-time search with query caching
- Responsive design

### 👨‍💼 Admin Dashboard

- **User Management Table** with search and pagination
- **Activity Logs** with filtering
- **Metrics & Analytics**:
  - Total users and activities
  - Average response time
  - Top intents chart
  - Daily activity chart
- Dark mode compatible charts
- Real-time data updates

### ⚙️ Additional Features

- System health indicator with response time
- Toast notifications for user feedback
- Error boundaries for graceful error handling
- Keyboard shortcuts:
  - `Enter` to send message
  - `Escape` to cancel/clear input
- Loading skeletons for better UX
- React Query for API caching and optimization
- Zustand for global state management

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast builds
- **Tailwind CSS** v4 for styling
- **shadcn/ui** components
- **React Query** (@tanstack/react-query) for API caching
- **Zustand** for state management
- **React Router** for navigation
- **Recharts** for admin metrics visualization
- **date-fns** for time formatting
- **React Markdown** for chat message formatting
- **Motion** (Framer Motion) for animations
- **Axios** for API calls
- **next-themes** for theme management

## Project Structure

```
src/
├── app/
│   ├── components/
│   │   ├── auth/           # Login & Register modals
│   │   ├── chat/           # Chat interface components
│   │   ├── search/         # Book search components
│   │   ├── admin/          # Admin dashboard components
│   │   ├── layout/         # Header, Sidebar
│   │   ├── common/         # Shared components
│   │   └── ui/             # shadcn/ui components
│   ├── hooks/              # Custom React hooks
│   ├── pages/              # Page components
│   ├── providers/          # Context providers
│   ├── services/           # API service layer
│   ├── store/              # Zustand stores
│   ├── types/              # TypeScript types
│   ├── routes.ts           # Router configuration
│   └── App.tsx             # Main app component
└── styles/
    ├── fonts.css
    ├── index.css
    ├── tailwind.css
    └── theme.css           # Custom color scheme
```

## API Integration

The application connects to a backend API at `http://localhost:5000/api` with the following endpoints:

### Authentication

- `POST /register` - Create new account
- `POST /login` - User login
- `POST /logout` - User logout
- `GET /profile` - Get user profile
- `GET /session` - Get session info

### Chat

- `POST /chat` - Send message
- `POST /feedback` - Send message feedback
- `GET /activity` - Get user activity

### Search

- `GET /search/books?q={query}&author={author}&subject={subject}` - Search books

### Admin (requires admin role)

- `GET /admin/users` - Get all users
- `GET /admin/activities` - Get all activities
- `GET /admin/metrics` - Get system metrics

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Backend API running on `http://localhost:5000`

### Installation

1. Install dependencies:

```bash
npm install
# or
pnpm install
```

2. Start the development server:

```bash
npm run dev
```

3. Open your browser to the URL shown in the terminal (typically `http://localhost:5173`)

### Backend Setup

Make sure your backend API is running on `http://localhost:5000` before using the application.

## Usage

### For Users

1. **Register/Login**: Click the "Login" button in the header to create an account or log in
2. **Chat**: Navigate to the Chat page to interact with the AI assistant
3. **Search**: Use the Search page to find books in the catalog
4. **Reserve Books**: Click "Reserve" on available books (requires login)

### For Admins

1. Log in with an admin account
2. Access the Admin Dashboard from the sidebar
3. View user management, activity logs, and system metrics

## Keyboard Shortcuts

- `Enter` - Send message in chat
- `Escape` - Clear/cancel current input
- Theme automatically detects system preferences

## Environment Variables

The API base URL is currently hardcoded to `http://localhost:5000/api`. To change this, update the `BASE_URL` constant in `/src/app/services/api.ts`.

## Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Notes

- The application uses localStorage to persist authentication tokens
- Theme preference is saved and persists across sessions
- All API calls include automatic token injection via axios interceptors
- Error handling is implemented at both component and application levels

## Future Enhancements

- File attachment support for chat
- Email notifications
- Advanced search filters (date range, categories)
- User preferences and settings page
- Multi-language support
- Offline mode with service workers