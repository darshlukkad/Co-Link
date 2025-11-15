# Slack UI Implementation Guide

This document outlines the complete Slack-like UI implementation for the CoLink frontend application.

## Overview

CoLink's frontend is built to closely match Slack's design system and user experience, providing a familiar and intuitive interface for team collaboration.

## Design System

### Colors

Our color palette is based on Slack's official design system:

#### Sidebar Colors
- **Purple**: `#4A154B` - Main sidebar background
- **Purple Dark**: `#3E0E40` - Hover states
- **Purple Darker**: `#350D36` - Active states
- **Purple Border**: `#682769` - Border accents
- **Purple Active**: `#1164A3` - Selected channel highlight

#### Accent Colors
- **Green**: `#007a5a` - Primary actions (Slack's signature green)
- **Green Dark**: `#005a42` - Hover states for primary actions
- **Blue**: `#1264a3` - Links and secondary actions
- **Red**: `#e01e5a` - Notifications and danger actions

#### UI Colors
- **Message Hover**: `#f8f8f8` - Message background on hover
- **Message Highlight**: `#fff4e0` - Highlighted/mentioned messages
- **Border**: `#e0e0e0` - General borders

### Typography

- **Font Family**: Lato (Google Fonts) with fallback to system fonts
- **Base Font Size**: 15px
- **Line Height**: 1.46668 (Slack's exact ratio)
- **Font Weights**:
  - Light: 300
  - Regular: 400
  - Bold: 700
  - Black: 900

### Spacing & Layout

- **Sidebar Width**: 260px (16rem)
- **Message Padding**: 12px vertical, 20px horizontal
- **Border Radius**:
  - Small elements: 4px
  - Medium elements: 6px
  - Large elements: 8px

## Components

### 1. Sidebar (`components/sidebar/sidebar.tsx`)

**Features:**
- Workspace header with logo
- Collapsible channel list
- Collapsible direct messages list
- Unread count badges
- Active channel highlighting
- User profile section with status
- Hover-activated logout button

**Design Details:**
- Background: Slack purple (`#4A154B`)
- Hover states use subtle purple-dark overlay
- Active channel uses blue highlight (`#1164A3`)
- Smooth transitions (75-100ms duration)

### 2. Chat Interface (`app/workspace/page.tsx`)

**Features:**
- Channel header with topic display
- Action buttons (search, file upload, calls, info)
- Infinite scroll message area
- Real-time message updates via WebSocket
- Thread panel (right sidebar)
- Empty state for new channels
- Loading skeleton

**Design Details:**
- Clean white background
- Subtle border separators
- Responsive design for mobile/tablet/desktop

### 3. Message Item (`components/chat/message-item.tsx`)

**Features:**
- User avatar with status indicator
- Username and timestamp
- Message content with formatting
- Hover-activated action toolbar
- Emoji reactions (grouped by emoji type)
- Thread reply count
- Edit indicator
- Delete state handling

**Design Details:**
- Hover background: `#f8f8f8`
- Action toolbar appears on hover with smooth animation
- Reactions displayed as pills with count badges
- Avatar uses consistent color generation per user

**Actions:**
- Add reaction (emoji picker)
- Reply in thread
- Edit message
- Delete message
- More actions menu

### 4. Message Input (`components/chat/message-input.tsx`)

**Features:**
- Auto-resizing textarea
- Rich formatting toolbar (bold, italic, strikethrough, code)
- File attachment button
- Emoji picker integration
- Mention button
- Enter to send, Shift+Enter for new line
- Typing indicators
- Focus ring in Slack green

**Design Details:**
- Border changes to Slack green on focus
- Send button activates with Slack green when message exists
- Toolbar buttons with hover states
- Clean, minimal design

### 5. Thread Panel (`components/chat/thread-panel.tsx`)

**Features:**
- Parent message display
- Thread replies list
- Reply count summary
- Dedicated reply input
- Close button
- Mobile-responsive (slide-in on mobile)

**Design Details:**
- Fixed width: 384px (24rem)
- Border-left separator
- Parent message in highlighted box
- Smooth slide-in animation

### 6. Emoji Picker (`components/ui/emoji-picker.tsx`)

**Features:**
- Full emoji library (emoji-picker-react)
- Search functionality
- Category tabs
- Skin tone selector
- Click-outside to close
- Lazy loading for performance

**Design Details:**
- Positioned above trigger button
- Shadow elevation
- Scale-in animation
- 320px width, 400px height

### 7. Avatar (`components/ui/avatar.tsx`)

**Features:**
- Image support
- Initials fallback
- Consistent color generation per user
- Status indicator (online/away/offline)
- Multiple sizes (sm, md, lg, xl)

**Design Details:**
- Rounded corners
- Status dot positioned bottom-right
- Colors: Green (online), Yellow (away), Gray (offline)

### 8. Login Page (`app/login/page.tsx`)

**Features:**
- SSO buttons (Google, GitHub)
- Email/password form
- Error state handling
- Loading states
- Large, bold typography

**Design Details:**
- Centered layout
- Slack-style branding
- Large logo badge
- Clean dividers
- Responsive design

### 9. Modals

#### Create Channel Modal
- Channel name input (auto-formats to lowercase with hyphens)
- Description textarea
- Private/Public toggle with icons
- Clear error messaging

#### Search Modal (Cmd+K)
- Global search across messages
- Keyboard navigation
- Quick access to channels/DMs

#### File Upload Modal
- Drag & drop support
- File preview
- Upload progress
- Size/type validation

#### User Profile Modal
- Avatar display
- User information
- Status management
- Activity indicators

## Utility Functions

### `lib/utils.ts`

**Key Functions:**
- `cn()` - Tailwind class merging
- `formatMessageTime()` - Slack-style time formatting
- `getInitials()` - Extract user initials
- `getAvatarColor()` - Consistent color generation
- `formatFileSize()` - Human-readable file sizes
- `parseMarkdown()` - Basic markdown parsing
- `debounce()` / `throttle()` - Performance optimization

### `lib/api-client.ts`

Complete REST API client with:
- Authentication (login, SSO, refresh, logout)
- User management
- Channel operations
- Direct messages
- Message CRUD
- Reactions
- Threads
- File uploads
- Search

### `lib/websocket-client.ts`

Real-time WebSocket client with:
- Auto-reconnection
- Channel subscriptions
- Message events
- Typing indicators
- Presence updates
- Reaction events

## State Management

### Zustand Stores

**Auth Store** (`stores/auth-store.ts`)
- User authentication state
- Login/logout actions

**Workspace Store** (`stores/workspace-store.ts`)
- Channels list
- Direct messages
- Active channel/DM selection

**Chat Store** (`stores/chat-store.ts`)
- Messages by channel
- Thread state
- Typing indicators
- Message CRUD operations

## Animations

### Custom Animations
- `fade-in`: 0.2s ease-out
- `scale-in`: 0.2s ease-out with scale transform
- `slide-in-right`: 0.3s ease-out
- `slide-out-right`: 0.3s ease-in

### Transition Durations
- Fast: 75ms (sidebar hovers)
- Normal: 100ms (buttons, links)
- Medium: 200ms (modals, dropdowns)
- Slow: 300ms (panels, drawers)

## Responsive Design

### Breakpoints
- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px

### Mobile Optimizations
- Collapsible sidebar (drawer)
- Stacked layout for threads
- Touch-optimized tap targets (min 44px)
- Reduced padding/margins
- Hidden non-essential toolbar buttons

## Accessibility

- Semantic HTML elements
- ARIA labels and roles (via Radix UI)
- Keyboard navigation support
- Focus management
- Screen reader support
- Color contrast compliance (WCAG AA)

## Performance Optimizations

1. **Code Splitting**: Dynamic imports for heavy components (emoji picker)
2. **Lazy Loading**: Images and emoji data
3. **Virtualization**: Planned for long message lists
4. **Debouncing**: Typing indicators, search input
5. **Throttling**: Scroll events, resize handlers
6. **Memoization**: React components where beneficial

## Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Environment Variables

Required environment variables (see `.env.local.example`):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8007
NEXT_PUBLIC_KEYCLOAK_URL=http://localhost:8080
NEXT_PUBLIC_KEYCLOAK_REALM=colink
```

## Getting Started

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Set Up Environment**:
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your configuration
   ```

3. **Run Development Server**:
   ```bash
   npm run dev
   ```

4. **Open Browser**:
   Navigate to http://localhost:3000

## Future Enhancements

### Planned Features
- [ ] Rich text editor (Tiptap)
- [ ] File preview (images, PDFs, videos)
- [ ] Voice/video calling (WebRTC)
- [ ] Browser notifications
- [ ] Dark mode
- [ ] Custom emojis
- [ ] Message scheduling
- [ ] Read receipts
- [ ] User mentions autocomplete
- [ ] Channel mentions
- [ ] Link previews
- [ ] Code syntax highlighting
- [ ] Message search within channel
- [ ] Internationalization (i18n)

### Performance Improvements
- [ ] Virtual scrolling for messages
- [ ] Service worker for offline support
- [ ] Progressive Web App (PWA)
- [ ] Optimistic UI updates
- [ ] Image optimization (Next.js Image)

## Design References

This implementation is based on:
- Slack's official design system (Slack Kit)
- Slack's web client (as of 2024)
- Slack's design guidelines: https://docs.slack.dev/surfaces/app-design/
- Community Figma resources: Slack UI Kit 2024

## Comparison with Slack

### What We Match
✅ Color palette and branding
✅ Typography (Lato font)
✅ Sidebar layout and behavior
✅ Message layout and hover actions
✅ Emoji reactions
✅ Thread panel
✅ Real-time updates
✅ Typing indicators
✅ Channel/DM organization
✅ Search functionality

### What We're Missing
⏳ Rich text editor (currently plain text)
⏳ File previews
⏳ Voice/video calls
⏳ Desktop notifications
⏳ Dark mode
⏳ Custom emojis
⏳ Advanced formatting (code blocks, quotes)

## Conclusion

The CoLink frontend provides a comprehensive, Slack-like experience that is:
- **Familiar**: Matches Slack's design patterns
- **Modern**: Built with Next.js 16 and React 19
- **Performant**: Optimized for speed and responsiveness
- **Accessible**: Follows WCAG guidelines
- **Extensible**: Clean architecture for future features

The implementation prioritizes user experience while maintaining code quality and scalability for enterprise use.
