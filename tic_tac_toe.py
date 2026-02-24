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
        # Word fill sequence for 8 outer squares (skipping center index 4)
        # Positions to fill in order: 0,1,2,3,5,6,7,8 (all except center)
        self.outer_positions = [0, 1, 2, 3, 5, 6, 7, 8]
        # Player sequence for these 8 positions: [0,1,1,0,0,1,1,0] (following the pattern but one less)
        self.wordfill_sequence = [0, 1, 1, 0, 0, 1, 1, 0]  # Player indices for each outer tile
        self.current_wordfill_index = 0  # Current position in sequence
        # Mark center as already filled with RPS
        self.word_board[4] = "RPS"

    def add_player(self, player_id):
        if len(self.players) < 2 and player_id not in self.players:
            self.players.append(player_id)
            return True
        return False

    def make_move(self, player_id, position, word=None, winner=None):
        # Handle word fill phase
        if self.mode == 'wordfill' and self.phase == 'wordfill':
            return self.handle_word_fill(player_id, position, word)
        # Handle regular game phase
        else:
            return self.handle_game_move(player_id, position, winner)

    def handle_word_fill(self, player_id, position, word):
        # Validate position
        try:
            position = int(position)
        except (ValueError, TypeError):
            return {'error': f'Position must be an integer', 'winner': self.winner, 'phase': self.phase}

        if position < 0 or position >= len(self.board):
            return {'error': f'Invalid position {position}', 'winner': self.winner, 'phase': self.phase}

        # Don't allow filling the center
        if position == 4:
            return {'error': 'The center square is Rock Paper Scissors and cannot be edited', 'winner': self.winner, 'phase': self.phase}

        # Check if it's the right player's turn
        if self.current_wordfill_index >= len(self.wordfill_sequence):
            return {'error': 'Word fill phase is complete', 'winner': self.winner, 'phase': self.phase}
            
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
        
        # Check if word fill phase is complete (all 8 outer squares filled)
        if self.current_wordfill_index >= len(self.wordfill_sequence):
            self.phase = 'game'
            self.turn = 0  # Start game with player 0
            return {
                'board': self.word_board,
                'winner': self.winner,
                'draw': False,
                'phase': self.phase,
                'wordfill_complete': True,
                'next_player': self.players[0],
                'current_wordfill_index': self.current_wordfill_index
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
            'word': word.strip(),
            'current_wordfill_index': self.current_wordfill_index
        }

    def handle_game_move(self, player_id, position, winner=None):
        try:
            position = int(position)
        except (ValueError, TypeError):
            return {'error': f'Position must be an integer', 'winner': self.winner}

        if position < 0 or position >= len(self.board):
            return {'error': f'Invalid position {position}', 'winner': self.winner}

        if self.winner or self.board[position] != '':
            return {'error': 'Invalid move', 'winner': self.winner}

        if len(self.players) < 2:
            return {'error': 'Waiting for opponent', 'winner': self.winner}

        # In wordfill mode, use the winner parameter to determine which player gets the square
        if self.mode == 'wordfill' and winner is not None:
            # Use the winner's symbol (X for player 0, O for player 1)
            self.board[position] = 'X' if winner == 0 else 'O'
        else:
            # Regular turn-based play
            if self.players[self.turn] != player_id:
                return {'error': 'Not your turn', 'winner': self.winner}
            self.board[position] = 'X' if self.turn == 0 else 'O'
            self.turn = 1 - self.turn

        # Check for winner
        if self.check_winner():
            self.winner = self.players[0] if self.board.count('X') > self.board.count('O') else self.players[1]
            return {'board': self.board, 'winner': self.winner, 'draw': False, 'phase': self.phase}

        # Check for draw
        if self.check_draw():
            return {'board': self.board, 'winner': self.winner, 'draw': True, 'phase': self.phase}

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
            'wordfill_sequence': self.wordfill_sequence if self.mode == 'wordfill' else None,
            'outer_positions': self.outer_positions if self.mode == 'wordfill' else None
        }