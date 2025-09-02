# tic-tac-toe
A simple Tic-Tac-Toe Project

<h2>Full Stack Overview</h2>

<table>
  <tr>
    <th>Layer</th>
    <th>Technology</th>
    <th>Description</th>
  </tr>
  <tr>
    <td><b>Frontend</b></td>
    <td>HTML, CSS, JavaScript<br><code>Socket.IO client</code></td>
    <td>
      <ul>
        <li>Game UI, board, status, turn indicator, rematch button</li>
        <li>Real-time communication with server</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td><b>Backend</b></td>
    <td>Python<br><code>Flask</code>, <code>Flask-SocketIO</code></td>
    <td>
      <ul>
        <li>Serves static files</li>
        <li>Handles game logic and events</li>
        <li>Real-time multiplayer via WebSockets</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td><b>Game Logic</b></td>
    <td><code>tic_tac_toe.py</code></td>
    <td>
      <ul>
        <li>Board state, moves, win detection, player management</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td><b>Communication</b></td>
    <td>WebSockets<br><code>Socket.IO</code></td>
    <td>
      <ul>
        <li>Live game state updates</li>
        <li>Lobby management</li>
        <li>Rematch requests</li>
      </ul>
    </td>
  </tr>
</table>
