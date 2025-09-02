class TicTacToe:
    def __init__(self):
        self.board = [''] * 9
        self.players = []
        self.turn = 0
        self.winner = None

    def add_player(self, player_id):
        if len(self.players) < 2 and player_id not in self.players:
            self.players.append(player_id)
            return True
        return False

    def make_move(self, player_id, position):
        # Ensure position is an integer
        # test2
        try:
            position = int(position)
        except (ValueError, TypeError):
            print(f"[DEBUG] Invalid position type: {position}")
            return {'error': f'Position must be an integer, got {position}', 'winner': self.winner}
        if position < 0 or position >= len(self.board):
            print(f"[DEBUG] Position out of range: {position}")
            return {'error': f'Invalid position {position}', 'winner': self.winner}
        # Return immediately if invalid position or board access
        if self.winner or self.board[position] != '':
            print(f"[DEBUG] Invalid move at position {position}, board: {self.board}")
            return {'error': 'Invalid move', 'winner': self.winner}
        if len(self.players) < 2 or self.players[self.turn] != player_id:
            print(f"[DEBUG] Not enough players or not player's turn: {self.players}, turn: {self.turn}, player_id: {player_id}")
            return {'error': 'Not your turn or waiting for opponent', 'winner': self.winner}
        print(f"[DEBUG] Making move at position {position} for player {player_id}")
        self.board[position] = 'X' if self.turn == 0 else 'O'
        if self.check_winner():
            self.winner = player_id
        self.turn = 1 - self.turn
        return {'board': self.board, 'winner': self.winner}

    def check_winner(self):
        combos = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        for a,b,c in combos:
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                return True
        return False