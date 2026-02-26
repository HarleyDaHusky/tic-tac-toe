class TicTacToe:
    def __init__(self, mode='classic'):
        self.board = [''] * 9
        self.players = []
        self.turn = 0
        self.winner = None
        self.mode = mode
        self.word_board = [''] * 9
        self.phase = 'wordfill' if mode == 'wordfill' else 'game'
        self.wordfill_turn = 0
        self.outer_positions = [0, 1, 2, 3, 5, 6, 7, 8]
        self.wordfill_sequence = [0, 1, 1, 0, 0, 1, 1, 0]
        self.current_wordfill_index = 0
        # Center square starts as RPS but can be claimed
        self.word_board[4] = "RPS"
        self.board[4] = "RPS"

    def add_player(self, player_id):
        if len(self.players) < 2 and player_id not in self.players:
            self.players.append(player_id)
            return True
        return False

    def make_move(self, player_id, position, word=None, winner=None):
        if self.mode == 'wordfill' and self.phase == 'wordfill':
            return self.handle_word_fill(player_id, position, word)
        else:
            return self.handle_game_move(player_id, position, winner)

    def handle_word_fill(self, player_id, position, word):
        try:
            position = int(position)
        except (ValueError, TypeError):
            return {'error': 'Position must be an integer', 'winner': self.winner, 'phase': self.phase}

        if position < 0 or position >= len(self.board):
            return {'error': f'Invalid position {position}', 'winner': self.winner, 'phase': self.phase}

        # Don't allow filling the center in word fill phase
        if position == 4:
            return {'error': 'The center square is Rock Paper Scissors and cannot be edited', 'winner': self.winner, 'phase': self.phase}

        if self.current_wordfill_index >= len(self.wordfill_sequence):
            return {'error': 'Word fill phase is complete', 'winner': self.winner, 'phase': self.phase}
            
        expected_player_index = self.wordfill_sequence[self.current_wordfill_index]
        if self.players[expected_player_index] != player_id:
            return {'error': 'Not your turn in word fill phase', 'winner': self.winner, 'phase': self.phase}

        if self.word_board[position] != '':
            return {'error': 'This tile already has a word', 'winner': self.winner, 'phase': self.phase}

        if not word or not isinstance(word, str) or len(word.strip()) == 0:
            return {'error': 'Please enter a valid word', 'winner': self.winner, 'phase': self.phase}

        self.word_board[position] = word.strip()
        self.current_wordfill_index += 1
        
        if self.current_wordfill_index >= len(self.wordfill_sequence):
            self.phase = 'game'
            self.turn = 0
            return {
                'board': self.word_board,
                'winner': self.winner,
                'draw': False,
                'phase': self.phase,
                'wordfill_complete': True,
                'next_player': self.players[0],
                'current_wordfill_index': self.current_wordfill_index
            }
        
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
            return {'error': 'Position must be an integer', 'winner': self.winner}

        if position < 0 or position >= len(self.board):
            return {'error': f'Invalid position {position}', 'winner': self.winner}

        if self.winner:
            return {'error': 'Game already over', 'winner': self.winner}

        # Check if cell is already taken by X or O
        if self.board[position] == 'X' or self.board[position] == 'O':
            return {'error': 'Invalid move - cell already taken', 'winner': self.winner}

        if len(self.players) < 2:
            return {'error': 'Waiting for opponent', 'winner': self.winner}

        # Check if it's the correct player's turn
        if self.players[self.turn] != player_id:
            return {'error': 'Not your turn', 'winner': self.winner}

        # Get the word from word_board if in wordfill mode
        selected_word = None
        if self.mode == 'wordfill':
            selected_word = self.word_board[position]
            print(f"[DEBUG] Word at position {position}: {selected_word}")

        # CASE 1: This is just a challenge notification (no winner yet)
        if winner is None and self.mode == 'wordfill':
            print(f"[DEBUG] Challenge started on position {position} with word: {selected_word}")
            
            # DON'T place a symbol or switch turns yet
            # Just return challenge info
            result = {
                'board': self.board,  # Board unchanged
                'winner': self.winner,
                'draw': False,
                'phase': self.phase,
                'challenge': {
                    'player_id': player_id,
                    'position': position,
                    'word': selected_word
                }
            }
            print(f"[DEBUG] Returning challenge result")
            return result

        # CASE 2: This is an actual move with a winner
        # Set the symbol based on winner
        if self.mode == 'wordfill' and winner is not None:
            self.board[position] = 'X' if winner == 0 else 'O'
            print(f"[DEBUG] Tile {position} set to {self.board[position]} by winner {winner}")
        else:
            # Classic mode
            player_index = 0 if self.players[0] == player_id else 1
            self.board[position] = 'X' if player_index == 0 else 'O'
            print(f"[DEBUG] Tile {position} set to {self.board[position]} by player {player_id} (index {player_index})")

        # Switch turns for the next player
        self.turn = 1 - self.turn

        # Check for winner
        if self.check_winner():
            self.winner = player_id
            return {'board': self.board, 'winner': self.winner, 'draw': False, 'phase': self.phase}

        # Check for draw
        if self.check_draw():
            return {'board': self.board, 'winner': self.winner, 'draw': True, 'phase': self.phase}

        return {'board': self.board, 'winner': self.winner, 'draw': False, 'phase': self.phase}

    def check_winner(self):
        combos = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        for a,b,c in combos:
            if self.board[a] and self.board[b] and self.board[c]:
                if self.board[a] == self.board[b] == self.board[c]:
                    # Make sure we're not comparing RPS to X/O
                    if self.board[a] != 'RPS':
                        return True
        return False

    def check_draw(self):
        if self.check_winner():
            return False
        # Count X and O, ignore RPS
        filled_cells = sum(1 for cell in self.board if cell == 'X' or cell == 'O')
        return filled_cells == 9

    def get_game_state(self):
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