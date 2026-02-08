from flask import Flask, send_from_directory
from flask_socketio import SocketIO, join_room, emit
from tic_tac_toe import TicTacToe
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
games = {}

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
        # Send info about whose turn is next
        next_player = game.players[game.turn] if len(game.players) == 2 and not result.get('winner') else None
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
        if result.get('winner'):
            socketio.emit('gameOver', {'winner': result['winner']}, room=game_id)
            # REMOVE or comment out this line:
            # del games[game_id]

@socketio.on('disconnect')
def disconnect():
    print('User disconnected')

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