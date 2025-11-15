# CoLink Frontend

A modern, Slack-like real-time messaging application built with Next.js 14, TypeScript, and Tailwind CSS.

## Features

- 🔐 **Authentication** - Login with email/password or SSO (Google, GitHub)
- 💬 **Real-time Messaging** - WebSocket-powered instant messaging
- 📺 **Channels** - Public and private channels with role-based access
- 💼 **Direct Messages** - One-on-one conversations
- 🎭 **Reactions** - Emoji reactions on messages
- 🧵 **Threads** - Threaded conversations
- 📎 **File Sharing** - Upload and share files
- 🔍 **Search** - Full-text search across messages and files
- 👥 **Presence** - See who's online in real-time
- ⌨️ **Typing Indicators** - Know when someone is typing
- 🎨 **Slack-like UI** - Familiar and intuitive interface

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **State Management:** Zustand
- **Data Fetching:** TanStack Query (React Query)
- **WebSocket:** Socket.io Client
- **UI Components:** Radix UI
- **Icons:** Lucide React
- **Form Handling:** React Hook Form + Zod

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend services running (see main repo README)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env.local
```

Edit `.env.local` with your configuration:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8007
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## Project Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── login/             # Login page
│   ├── workspace/         # Main workspace (authenticated)
│   └── page.tsx           # Home page (redirects)
├── components/            # React components
│   ├── ui/               # Base UI components
│   ├── chat/             # Chat-related components
│   ├── sidebar/          # Sidebar components
│   └── modals/           # Modal dialogs
├── lib/                   # Utility functions
│   ├── api-client.ts     # API client
│   ├── websocket-client.ts # WebSocket client
│   └── utils.ts          # Helpers
├── stores/               # Zustand stores
│   ├── auth-store.ts     # Authentication state
│   ├── workspace-store.ts # Workspace/channels state
│   └── chat-store.ts     # Messages/chat state
├── types/                # TypeScript types
│   └── index.ts          # Shared types
└── hooks/                # Custom React hooks
```

## Key Components

### Authentication (`app/login/page.tsx`)
- Email/password login
- SSO integration (Google, GitHub)
- Token management

### Main Layout (`app/workspace/layout.tsx`)
- Authentication guard
- WebSocket connection setup
- Sidebar + content layout

### Sidebar (`components/sidebar/sidebar.tsx`)
- Workspace selector
- Channels list
- Direct messages list
- User profile

### Chat Interface (`app/workspace/page.tsx`)
- Channel header
- Messages area with infinite scroll
- Message input with formatting
- Real-time updates

### Message Components
- `MessageItem` - Individual message with actions
- `MessageInput` - Rich text input with toolbar
- Reactions, threads, editing, deletion

## API Integration

The frontend integrates with CoLink backend services:

| Service | Endpoint | Purpose |
|---------|----------|---------|
| Users | `:8001` | User management |
| Messaging | `:8002` | Messages, threads, reactions |
| Files | `:8003` | File uploads/downloads |
| Search | `:8004` | Search messages/files |
| Admin | `:8005` | Moderation |
| Channels | `:8006` | Channels, DMs |
| Gateway | `:8007` | WebSocket (real-time) |
| Presence | `:8008` | Online status, typing |

## WebSocket Events

Real-time events handled:

- `message:new` - New message in channel
- `message:updated` - Message edited
- `message:deleted` - Message deleted
- `reaction:added` - Reaction added to message
- `reaction:removed` - Reaction removed
- `typing:start` - User started typing
- `typing:stop` - User stopped typing
- `presence:update` - User status changed

## State Management

Uses Zustand for simple, fast state management:

- **Auth Store** - User authentication state
- **Workspace Store** - Current workspace, channels, DMs
- **Chat Store** - Messages, threads, typing indicators

## Styling

Tailwind CSS with custom configuration matching Slack's design:

- **Primary Color:** `#007a5a` (Slack green)
- **Sidebar:** `#3f0e40` (Slack purple)
- **Hover States:** Subtle gray overlays
- **Borders:** Light gray for separation

## Scripts

```bash
# Development
npm run dev         # Start dev server

# Building
npm run build       # Build for production
npm start           # Start production server

# Linting
npm run lint        # Run ESLint
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | WebSocket server URL | `ws://localhost:8007` |
| `NEXT_PUBLIC_KEYCLOAK_URL` | Keycloak server URL | `http://localhost:8080` |
| `NEXT_PUBLIC_KEYCLOAK_REALM` | Keycloak realm name | `colink` |

## Performance Optimizations

- React Server Components for initial page load
- Client-side navigation with Next.js Link
- Optimistic UI updates
- Message pagination (infinite scroll)
- Image lazy loading
- Code splitting

## Accessibility

- Semantic HTML
- Keyboard navigation support
- ARIA labels and roles (via Radix UI)
- Focus management
- Screen reader support

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers

## Deployment

### Vercel (Recommended)

```bash
vercel deploy
```

### Docker

```bash
docker build -t colink-frontend .
docker run -p 3000:3000 colink-frontend
```

## Development Roadmap

- [ ] Rich text editor (Tiptap)
- [ ] File preview (images, PDFs, videos)
- [ ] Voice/video calling (WebRTC)
- [ ] Notifications (browser + push)
- [ ] Mobile responsiveness improvements
- [ ] Dark mode
- [ ] Custom emojis
- [ ] Message scheduling
- [ ] Read receipts
- [ ] User mentions autocomplete
- [ ] Channel mentions
- [ ] Link previews
- [ ] Code syntax highlighting
- [ ] Internationalization (i18n)

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

MIT License - see LICENSE file for details

---

Built with ❤️ using Next.js and TypeScript
