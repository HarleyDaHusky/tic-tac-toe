from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, join_room, emit
from tic_tac_toe import TicTacToe
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
games = {}
sessions = {}
rematch_votes = {}

@app.route('/')
def index():
    return send_from_directory(os.path.dirname(__file__), 'index.html')

@socketio.on('createGame')
def create_game(data):
    game_id = data['gameId']
    mode = data.get('mode', 'classic')
    
    if game_id in games:
        emit('error', {'message': 'Game ID already in use'})
        return
    
    games[game_id] = TicTacToe(mode=mode)
    join_room(game_id)
    emit('gameCreated', {'gameId': game_id, 'mode': mode})

@socketio.on('joinGame')
def join_game(data):
    game_id = data['gameId']
    player_id = data['playerId']
    game = games.get(game_id)
    
    if game and game.add_player(player_id):
        join_room(game_id)
        sid = request.sid
        sessions[sid] = {'game_id': game_id, 'player_id': player_id}
        emit('gameJoined', {'gameId': game_id})
        
        if len(game.players) == 2:
            if game.mode == 'wordfill':
                emit('startWordFill', {
                    'gameId': game_id,
                    'first_player': game.players[0],
                    'players': game.players,
                    'sequence': game.wordfill_sequence,
                    'current_index': 0
                }, room=game_id)
            else:
                emit('startGame', {
                    'gameId': game_id,
                    'first_player': game.players[0],
                    'players': game.players
                }, room=game_id)
    else:
        emit('error', {'message': 'Game not found or full'})

@socketio.on('placeWord')
def place_word(data):
    game_id = data['gameId']
    position = data['position']
    player_id = data['playerId']
    word = data.get('word', '')
    
    game = games.get(game_id)
    if game and game.mode == 'wordfill' and game.phase == 'wordfill':
        result = game.make_move(player_id, position, word=word)
        
        if result.get('error'):
            emit('error', {'message': result['error']})
            return
        
        socketio.emit('wordPlaced', {
            'position': position,
            'player': player_id,
            'word': word,
            'result': result,
            'next_player': result.get('next_player'),
            'first_player': game.players[0],
            'players': game.players
        }, room=game_id)
        
        if result.get('wordfill_complete'):
            socketio.emit('wordFillComplete', {
                'board': result['board'],
                'first_player': result['next_player'],
                'players': game.players
            }, room=game_id)

@socketio.on('makeMove')
def make_move(data):
    game_id = data['gameId']
    position = data['position']
    player_id = data['playerId']
    winner = data.get('winner')
    
    game = games.get(game_id)
    if game:
        result = game.make_move(player_id, position, winner=winner)
        
        if result.get('error'):
            emit('error', {'message': result['error']})
            return
        
        next_player = None
        if game.phase == 'game' and len(game.players) == 2 and not result.get('winner') and not result.get('draw'):
            next_player = game.players[game.turn]
        
        socketio.emit('moveMade', {
            'position': position,
            'player': player_id,
            'winner': winner,
            'result': result,
            'next_player': next_player,
            'phase': game.phase
        }, room=game_id)
        
        if result.get('winner'):
            socketio.emit('gameOver', {'winner': result['winner'], 'draw': False}, room=game_id)
        elif result.get('draw'):
            socketio.emit('gameOver', {'winner': None, 'draw': True}, room=game_id)

@socketio.on('disconnect')
def disconnect():
    sid = request.sid
    info = sessions.pop(sid, None)
    if not info:
        return
    game_id = info.get('game_id')
    player_id = info.get('player_id')
    game = games.get(game_id)
    opponent = None
    if game:
        for pid in game.players:
            if pid != player_id:
                opponent = pid
                break
        if opponent:
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
        games.pop(game_id, None)
        rematch_votes.pop(game_id, None) if 'rematch_votes' in globals() else None

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
        # Reverse the player order for rematch
        player_ids.reverse()  # Simple reversal
        # Reset game state
        rematch_votes[game_id] = set()
        games[game_id] = TicTacToe()
        # Add players in reversed order (second player becomes first)
        for pid in player_ids:
            games[game_id].add_player(pid)
        first_player = games[game_id].players[0]
        
        if game.mode == 'wordfill':
            socketio.emit('startWordFill', {
                'gameId': game_id,
                'first_player': first_player,
                'players': games[game_id].players,
                'sequence': games[game_id].wordfill_sequence,
                'current_index': 0
            }, room=game_id)
        else:
            socketio.emit('startGame', {
                'gameId': game_id,
                'first_player': first_player,
                'players': games[game_id].players
            }, room=game_id)
    socketio.emit('rematchStatus', {'votes': votes, 'first_player': first_player}, room=game_id)

@socketio.on('leaveGame')
def leave_game(data):
    game_id = data.get('gameId')
    player_id = data.get('playerId')

    game = games.get(game_id)
    if not game:
        return

    opponent = None
    for pid in game.players:
        if pid != player_id:
            opponent = pid
            break

    if opponent:
        socketio.emit(
            'gameOver',
            {
                'winner': opponent,
                'draw': False,
                'forfeit': True
            },
            room=game_id
        )

    games.pop(game_id, None)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 3000))
    socketio.run(app, host='0.0.0.0', port=port)
