# 🎮 Multiplayer Tic-Tac-Toe

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://tic-tac-toe-0wd2.onrender.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

### Two Game Modes

| Classic Mode | Crazy Mode |
|-------------|------------|
| Traditional X/O gameplay | Word-fill challenge phase |
| First to 3 in a row wins | Challenge tiles to claim them |
| Simple and quick matches | Rock Paper Scissors center tile |
| Perfect for beginners | Winner of challenge claims square |

### Real-time Multiplayer
- Instant moves with WebSocket technology
- Create/join games with custom Game ID
- See opponent's moves in real-time
- Rematch functionality
- Auto-forfeit on disconnect

### Modern UI
- Clean, responsive design
- Visual indicators for turns
- Player name display with color coding
- Mobile-friendly interface
- Interactive game board

### Game Features
- Turn-based gameplay
- Win/draw detection
- Visual feedback for selected cells
- Waiting indicators during challenges
- Comprehensive info modal with rules

## 🎯 How to Play

### Quick Start
1. Enter your name
2. Create a game or join with a friend's Game ID
3. Choose game mode (Classic or Crazy)
4. Share the Game ID with your opponent
5. Wait for opponent to join
6. Start playing!

### Crazy Mode Rules

**Phase 1 - Word Fill**
- Players take turns placing words in outer squares
- Center square is Rock Paper Scissors
- 8 words total, following specific turn sequence

**Phase 2 - Challenge**
- Click any filled square to challenge it
- Choose who wins the challenge
- Winner claims square with their symbol (X/O)
- First to 3 symbols in a row wins!

## 🛠️ Tech Stack

### Frontend
- HTML5/CSS3 - Structure and styling
- Vanilla JavaScript - Client logic
- Socket.IO Client - Real-time communication
- CSS Grid/Flexbox - Responsive design

### Backend
- Flask - Python web framework
- Flask-SocketIO - WebSocket support
- Custom Game Engine - Game logic and state
- Eventlet - Async networking

### Infrastructure
- Render - Cloud hosting
- Gunicorn - WSGI server
- Eventlet workers - Concurrent connections
