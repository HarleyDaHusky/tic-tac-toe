class TicTacToe:
    def __init__(self, mode='classic'):
        self.board = [''] * 9
        self.players = []
        self.turn = 0
        self.winner = None
        self.mode = mode  # 'classic' or 'wordfill'
        self.word_board = [''] * 9  # Store words during word fill phase
        self.phase = 'wordfill' if mode == 'wordfill' else 'game'  # 'wordfill' or 'game'
        self.wordfill_turn = 0  # Track turns during word fill phase
        # Word fill sequence: [0,1,1,2,2,3,3,4,4] (indices of players 0 and 1)
        self.wordfill_sequence = [0, 1, 1, 0, 0, 1, 1, 0, 0]  # Player indices for each tile (0-based)
        self.current_wordfill_index = 0  # Current position in sequence

    def add_player(self, player_id):
        if len(self.players) < 2 and player_id not in self.players:
            self.players.append(player_id)
            return True
        return False

    def make_move(self, player_id, position, word=None):
        # Handle word fill phase
        if self.mode == 'wordfill' and self.phase == 'wordfill':
            return self.handle_word_fill(player_id, position, word)
        # Handle regular game phase
        else:
            return self.handle_game_move(player_id, position)

    def handle_word_fill(self, player_id, position, word):
        # Validate position
        try:
            position = int(position)
        except (ValueError, TypeError):
            return {'error': f'Position must be an integer', 'winner': self.winner, 'phase': self.phase}

        if position < 0 or position >= len(self.board):
            return {'error': f'Invalid position {position}', 'winner': self.winner, 'phase': self.phase}

        # Check if it's the right player's turn
        expected_player_index = self.wordfill_sequence[self.current_wordfill_index]
        if self.players[expected_player_index] != player_id:
            return {'error': 'Not your turn in word fill phase', 'winner': self.winner, 'phase': self.phase}

        # Check if position is already filled
        if self.word_board[position] != '':
            return {'error': 'This tile already has a word', 'winner': self.winner, 'phase': self.phase}

        # Validate word
        if not word or not isinstance(word, str) or len(word.strip()) == 0:
            return {'error': 'Please enter a valid word', 'winner': self.winner, 'phase': self.phase}

        # Store the word
        self.word_board[position] = word.strip()
        
        # Move to next position in sequence
        self.current_wordfill_index += 1
        
        # Check if word fill phase is complete
        if self.current_wordfill_index >= len(self.wordfill_sequence):
            self.phase = 'game'
            self.turn = 0  # Start game with player 0
            return {
                'board': self.word_board,
                'winner': self.winner,
                'draw': False,
                'phase': self.phase,
                'wordfill_complete': True,
                'next_player': self.players[0]
            }
        
        # Determine next player for word fill
        next_player_index = self.wordfill_sequence[self.current_wordfill_index]
        
        return {
            'board': self.word_board,
            'winner': self.winner,
            'draw': False,
            'phase': self.phase,
            'wordfill_complete': False,
            'next_player': self.players[next_player_index],
            'filled_position': position,
            'word': word.strip()
        }

    def handle_game_move(self, player_id, position):
        try:
            position = int(position)
        except (ValueError, TypeError):
            return {'error': f'Position must be an integer', 'winner': self.winner}

        if position < 0 or position >= len(self.board):
            return {'error': f'Invalid position {position}', 'winner': self.winner}

        if self.winner or self.board[position] != '':
            return {'error': 'Invalid move', 'winner': self.winner}

        if len(self.players) < 2 or self.players[self.turn] != player_id:
            return {'error': 'Not your turn or waiting for opponent', 'winner': self.winner}

        # In wordfill mode, use the words as markers
        if self.mode == 'wordfill':
            # Use the word that was placed in this position
            self.board[position] = self.word_board[position]
        else:
            # Classic mode - use X and O
            self.board[position] = 'X' if self.turn == 0 else 'O'

        # Check for winner
        if self.check_winner():
            self.winner = player_id
            return {'board': self.board, 'winner': self.winner, 'draw': False, 'phase': self.phase}

        # Check for draw
        if self.check_draw():
            return {'board': self.board, 'winner': self.winner, 'draw': True, 'phase': self.phase}

        # Continue game
        self.turn = 1 - self.turn
        return {'board': self.board, 'winner': self.winner, 'draw': False, 'phase': self.phase}

    def check_winner(self):
        combos = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        for a,b,c in combos:
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                return True
        return False

    def check_draw(self):
        if self.check_winner():
            return False
        return all(cell != '' for cell in self.board)

    def get_game_state(self):
        """Return current game state for client"""
        return {
            'mode': self.mode,
            'phase': self.phase,
            'board': self.board if self.phase == 'game' else self.word_board,
            'players': self.players,
            'turn': self.turn if self.phase == 'game' else self.wordfill_sequence[self.current_wordfill_index] if self.current_wordfill_index < len(self.wordfill_sequence) else None,
            'wordfill_progress': self.current_wordfill_index if self.mode == 'wordfill' else None,
            'wordfill_sequence': self.wordfill_sequence if self.mode == 'wordfill' else None
        }