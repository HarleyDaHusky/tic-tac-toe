from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, join_room, emit
from tic_tac_toe import TicTacToe
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
games = {}
sessions = {}
rematch_votes = {}
rps_pending = {}  # game_id -> { position, challenger, choices: { player_id: 'rock'|'paper'|'scissors' } }

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
    joining_mode = data.get('mode')
    game = games.get(game_id)
    
    if not game:
        emit('error', {'message': 'Game not found'})
        return
    
    # Check if mode matches
    if game.mode != joining_mode:
        emit('error', {'message': f'Game mode mismatch! This game is in {game.mode} mode. Please switch to {game.mode} mode to join.'})
        return
    
    if game.add_player(player_id):
        join_room(game_id)
        sid = request.sid
        sessions[sid] = {'game_id': game_id, 'player_id': player_id}
        emit('gameJoined', {'gameId': game_id, 'mode': game.mode})
        
        # Check if we now have 2 players
        if len(game.players) == 2:
            if game.mode == 'wordfill':
                emit('startWordFill', {
                    'gameId': game_id,
                    'first_player': game.players[0],
                    'players': game.players,
                    'sequence': game.wordfill_sequence,
                    'current_index': 0
                }, room=game_id)
            else:  # classic mode
                socketio.emit('startGame', {
                    'gameId': game_id,
                    'first_player': game.players[0],
                    'players': game.players
                }, room=game_id)
    else:
        emit('error', {'message': 'Game is full or you are already in the game'})

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
        
        # Emit to ALL players in the room
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
    if not game:
        emit('error', {'message': 'Game not found'})
        return
        
    result = game.make_move(player_id, position, winner=winner)
    
    if result.get('error'):
        emit('error', {'message': result['error']})
        return
    
    # CASE 1: Challenge notification (no winner yet)
    if winner is None and result.get('challenge'):
        challenged_word = result['challenge']['word']
        if game.mode == 'wordfill' and position == 4:
            rps_pending[game_id] = {
                'position': position,
                'challenger': player_id,
                'choices': {}
            }
            socketio.emit('rpsChallenge', {
                'position': position,
                'player_id': player_id,
                'players': game.players
            }, room=game_id)
        else:
            socketio.emit('challengeNotification', {
                'player_id': player_id,
                'player_name': player_id,
                'position': position,
                'word': challenged_word
            }, room=game_id)
        return

    # CASE 2: Winner selection (actual move)
    next_player = None
    if game.phase == 'game' and len(game.players) == 2 and not result.get('winner') and not result.get('draw'):
        next_player = game.players[game.turn]
    socketio.emit('moveCompleted', {
        'position': position,
        'player': player_id,
        'winner': winner,
        'result': result,
        'next_player': next_player,
        'phase': game.phase
    }, room=game_id)
    game_winner = result.get('winner')
    game_draw = result.get('draw')
    if game_winner:
        socketio.emit('gameOver', {'winner': game_winner, 'draw': False}, room=game_id)
    elif game_draw:
        socketio.emit('gameOver', {'winner': None, 'draw': True}, room=game_id)


def _rps_winner(choice1, choice2):
    """Returns 0 if player1 wins, 1 if player2 wins, None if tie."""
    beats = {'rock': 'scissors', 'paper': 'rock', 'scissors': 'paper'}
    if choice1 == choice2:
        return None
    return 0 if beats[choice1] == choice2 else 1


@socketio.on('rpsChoice')
def rps_choice(data):
    game_id = data['gameId']
    player_id = data['playerId']
    choice = data.get('choice', '').lower()
    
    if choice not in ('rock', 'paper', 'scissors'):
        emit('error', {'message': 'Invalid RPS choice'})
        return
    
    game = games.get(game_id)
    rps = rps_pending.get(game_id)
    
    if not game or not rps:
        emit('error', {'message': 'No RPS challenge in progress'})
        return
    
    if player_id not in game.players:
        emit('error', {'message': 'You are not in this game'})
        return
    
    rps['choices'][player_id] = choice
    
    if len(rps['choices']) < 2:
        return
    
    # Both players have chosen - determine winner
    p0, p1 = game.players[0], game.players[1]
    c0, c1 = rps['choices'].get(p0), rps['choices'].get(p1)
    
    winner_idx = _rps_winner(c0, c1)
    
    if winner_idx is None:
        # Tie - replay
        rps['choices'] = {}
        socketio.emit('rpsTie', {'message': "It's a tie! Pick again"}, room=game_id)
        return
    
    winner_player = game.players[winner_idx]
    position = rps['position']
    challenger = rps['challenger']
    
    del rps_pending[game_id]
    
    result = game.make_move(challenger, position, winner=winner_idx)
    
    if result.get('error'):
        emit('error', {'message': result['error']})
        return
    
    next_player = None
    if game.phase == 'game' and len(game.players) == 2 and not result.get('winner') and not result.get('draw'):
        next_player = game.players[game.turn]
    
    socketio.emit('moveCompleted', {
        'position': position,
        'player': challenger,
        'winner': winner_idx,
        'result': result,
        'next_player': next_player,
        'phase': game.phase,
        'rps_result': {'player0': c0, 'player1': c1}
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
            forfeit_data = {
                'winner': opponent,
                'draw': False,
                'forfeit': True,
                'message': 'Opponent disconnected - win by forfeit'
            }
            socketio.emit('gameOver', forfeit_data, room=game_id)
        games.pop(game_id, None)
        rematch_votes.pop(game_id, None)
        rps_pending.pop(game_id, None)

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
        player_ids.reverse()
        # Reset game state
        rematch_votes[game_id] = set()
        games[game_id] = TicTacToe(mode=game.mode)
        # Add players in reversed order
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
        winner_name = opponent
        socketio.emit(
            'gameOver',
            {'winner': winner_name, 'draw': False, 'forfeit': True},
            room=game_id
        )

    games.pop(game_id, None)
    rps_pending.pop(game_id, None)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 3000))
    socketio.run(app, host='0.0.0.0', port=port)