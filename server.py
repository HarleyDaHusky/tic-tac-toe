from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, join_room, emit
from tic_tac_toe import TicTacToe
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
games = {}
# track socket session -> { game_id, player_id } so we can act on disconnect
sessions = {}

@app.route('/')
def index():
    return send_from_directory(os.path.dirname(__file__), 'index.html')

@socketio.on('createGame')
def create_game(data):
    game_id = data['gameId']
    games[game_id] = TicTacToe()
    join_room(game_id)
    emit('gameCreated', {'gameId': game_id})

@socketio.on('joinGame')
def join_game(data):
    game_id = data['gameId']
    player_id = data['playerId']
    game = games.get(game_id)
    if game and game.add_player(player_id):
        join_room(game_id)
        # record this socket session so we can find the player on disconnect
        sid = request.sid
        sessions[sid] = {'game_id': game_id, 'player_id': player_id}
        emit('gameJoined', {'gameId': game_id})
        if len(game.players) == 2:
            # Send first_player info so only they see "Your turn!"
            emit('startGame', {'gameId': game_id, 'first_player': game.players[0]}, room=game_id)
    else:
        emit('error', {'message': 'Game not found or full'})

@socketio.on('makeMove')
def make_move(data):
    game_id = data['gameId']
    position = data['position']
    player_id = data['playerId']
    game = games.get(game_id)
    if game:
        result = game.make_move(player_id, position)
        # don't report a next_player if there's a winner or a draw
        next_player = game.players[game.turn] if len(game.players) == 2 and not result.get('winner') and not result.get('draw') else None
        socketio.emit(
            'moveMade',
            {
                'position': position,
                'player': player_id,
                'result': result,
                'next_player': next_player
            },
            room=game_id
        )
        # announce game over for winner or draw
        if result.get('winner'):
            socketio.emit('gameOver', {'winner': result['winner'], 'draw': False}, room=game_id)
        elif result.get('draw'):
            socketio.emit('gameOver', {'winner': None, 'draw': True}, room=game_id)

@socketio.on('disconnect')
def disconnect():
    sid = request.sid
    info = sessions.pop(sid, None)
    if not info:
        print('User disconnected (unknown session)')
        return
    game_id = info.get('game_id')
    player_id = info.get('player_id')
    game = games.get(game_id)
    opponent = None
    if game:
        # find the other player, if any
        for pid in game.players:
            if pid != player_id:
                opponent = pid
                break
        if opponent:
            # notify the room that opponent wins by forfeit
            socketio.emit(
                'gameOver',
                {
                    'winner': opponent,
                    'draw': False,
                    'forfeit': True,
                    'message': 'Opponent disconnected — win by forfeit'
                },
                room=game_id
            )
        # cleanup game state and any rematch votes
        games.pop(game_id, None)
        rematch_votes.pop(game_id, None) if 'rematch_votes' in globals() else None
    print(f'User disconnected: sid={sid}, player_id={player_id}, game_id={game_id}')

rematch_votes = {}

@socketio.on('rematchRequest')
def rematch_request(data):
    game_id = data['gameId']
    player_id = data['playerId']
    if game_id not in rematch_votes:
        rematch_votes[game_id] = set()
    rematch_votes[game_id].add(player_id)
    votes = len(rematch_votes[game_id])
    game = games.get(game_id)
    first_player = None
    if game and votes == 2:
        player_ids = list(rematch_votes[game_id])
        rematch_votes[game_id] = set()
        games[game_id] = TicTacToe()
        for pid in player_ids:
            games[game_id].add_player(pid)
        first_player = games[game_id].players[0]
        socketio.emit('startGame', {'gameId': game_id, 'first_player': first_player}, room=game_id)
    socketio.emit('rematchStatus', {'votes': votes, 'first_player': first_player}, room=game_id)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 3000))
    socketio.run(app, host='0.0.0.0', port=port)