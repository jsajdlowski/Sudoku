import pygame
import os
import socket
import pickle
from grid import Grid

class SudokuClient:
    def __init__(self):
        self.window_width = 800
        self.window_height = 590
        self.cell_size = 60
        self.grid_size = self.cell_size * 9
        self.side_panel_width = self.window_width - self.grid_size
        
        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (400,100)
        self.surface = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption('Sudoku')
        
        pygame.font.init()
        self.game_font = pygame.font.SysFont('Arial', 32)
        self.score_font = pygame.font.SysFont('Arial', 24)
        
        self.num_x_offset = 22
        self.num_y_offset = 14
        
        self.score_x = self.grid_size + 50
        self.score_y = 100
        self.score_width = self.side_panel_width - 80 
        self.score_height = 150
        
        self.player_indicator_x = self.grid_size + 60
        self.player_indicator_y = 20
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_addr = None
        self.grid = None
        self.player_number = None
        self.current_turn = 0
        self.selected_cell = None
        self.scores = {0: 0, 1: 0}



    def connect(self, host='localhost', port=5555):
        try:
            self.server_addr = (host, port)
            join_message = {'type': 'join'}
            self.socket.sendto(pickle.dumps(join_message), self.server_addr)
            
            data, _ = self.socket.recvfrom(4096)
            init_data = pickle.loads(data)
            
            self.grid = Grid(self.game_font)
            self.grid.grid = init_data['board']
            self.player_number = init_data['player_number']
            self.current_turn = init_data['current_turn']
            
            print(f"Connected as Player {self.player_number}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def handle_click(self, pos):
        if self.current_turn != self.player_number or self.is_game_complete():
            return
            
        x = pos[0] // self.grid.cell_size
        y = pos[1] // self.grid.cell_size
        if 0 <= x < 9 and 0 <= y < 9:
            if self.grid.get_cell(x, y) == 0:
                self.selected_cell = (x, y)

    def handle_number_input(self, number):
        if self.selected_cell and self.current_turn == self.player_number:
            x, y = self.selected_cell
            if self.grid.get_cell(x, y) == 0: 
                move_data = {
                    'type': 'move',
                    'x': x,
                    'y': y,
                    'value': number
                }
                self.socket.sendto(pickle.dumps(move_data), self.server_addr)
                self.selected_cell = None

    def draw_player_indicator(self):
        player_text = f"Player {self.player_number}"
        color = (0, 255, 0) if self.current_turn == self.player_number else (255, 255, 255)
        text_surface = self.game_font.render(player_text, False, color)
        self.surface.blit(text_surface, (self.player_indicator_x, self.player_indicator_y))

    def draw_score_table(self):
        score_rect = pygame.Rect(self.score_x+10, self.score_y, self.score_width, self.score_height)
        pygame.draw.rect(self.surface, (30, 30, 30), score_rect)

        title = self.score_font.render("SCORES", False, (255, 255, 255))
        title_x = self.score_x + (self.score_width - title.get_width()) // 2 +10
        self.surface.blit(title, (title_x, self.score_y + 10))
        
        for player in [0, 1]:
            if player == self.current_turn:
                color = (0, 255, 0)
            elif self.scores[player] < 0:
                color = (255, 0, 0)
            else:
                color = (255, 255, 255)
                
            text = f"Player {player}: {self.scores[player]}"
            score_text = self.score_font.render(text, False, color)
            self.surface.blit(score_text, (
                self.score_x + 20,
                self.score_y + 50 + player * 35
            ))

    def is_game_complete(self):
        for y in range(len(self.grid.grid)):
            for x in range(len(self.grid.grid[y])):
                if self.grid.get_cell(x, y) == 0:
                    return False
        return True

    def draw_game_result(self):
        if not hasattr(self, 'scores'):
            return
            
        if self.scores[0] > self.scores[1]:
            winner = 0
        elif self.scores[1] > self.scores[0]:
            winner = 1
        else:
            result = "It's a Tie!"
            color = (255, 255, 0)
        
        if 'winner' in locals():
            if self.player_number == winner:
                result = "You Won!"
            else:
                result = f"Player {winner} Wins!"
            color = (0, 255, 0)

        text_surface = self.game_font.render(result, False, color)
        text_rect = text_surface.get_rect(center=(self.window_width // 2, self.window_height // 2))
        bg_rect = pygame.Rect(text_rect.x - 20, text_rect.y - 20, 
                            text_rect.width + 40, text_rect.height + 40)
        pygame.draw.rect(self.surface, (50, 50, 50), bg_rect)
        
        self.surface.blit(text_surface, text_rect)


    def run(self):
        running = True
        incorrect_moves = {}
        game_ended = False
        end_time = None
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and not game_ended:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN and not game_ended:
                    if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, 
                                pygame.K_4, pygame.K_5, pygame.K_6, 
                                pygame.K_7, pygame.K_8, pygame.K_9]:
                        number = int(event.unicode)
                        self.handle_number_input(number)

            try:
                self.socket.settimeout(0.001)
                data, _ = self.socket.recvfrom(4096)
                if data:
                    update = pickle.loads(data)
                    if update.get('type') == 'game_end':
                        game_ended = True
                        end_time = pygame.time.get_ticks()
                        self.grid.grid = update['board']
                        self.scores = update['scores']
                        if 'correct_cells' in update:
                            self.grid.correct_cells = update['correct_cells']
                    elif update.get('type') == 'disconnect':
                        print("Server has disconnected. Exiting...")
                        running = False
                    else:
                        self.grid.grid = update['board']
                        self.current_turn = update['current_turn']
                        self.scores = update['scores']
                        if 'correct_cells' in update:
                            self.grid.correct_cells = update['correct_cells']
                        if 'incorrect_move' in update:
                            x, y = update['incorrect_move']['x'], update['incorrect_move']['y']
                            incorrect_moves[(x, y)] = update['incorrect_move']['value']
                        elif self.current_turn == self.player_number:
                            incorrect_moves = {}
            except socket.timeout:
                pass

            self.surface.fill((0,0,0))
            if self.grid:
                self.grid.draw_all(pygame, self.surface)
                
                for (x, y), value in incorrect_moves.items():
                    text_surface = self.game_font.render(str(value), False, (255, 0, 0))
                    self.surface.blit(text_surface, (x * self.grid.cell_size + self.num_x_offset, 
                                                y * self.grid.cell_size + self.num_y_offset))
                
                if self.selected_cell and not game_ended:
                    x, y = self.selected_cell
                    rect = pygame.Rect(x * self.grid.cell_size, y * self.grid.cell_size, 
                                    self.grid.cell_size, self.grid.cell_size)
                    pygame.draw.rect(self.surface, (0, 255, 0), rect, 3)
                
                self.draw_score_table()
                self.draw_player_indicator()
                
                if game_ended:
                    self.draw_game_result()
                    if pygame.time.get_ticks() - end_time > 5000:
                        running = False
                
            pygame.display.flip()

        disconnect_msg = {'type': 'disconnect'}
        self.socket.sendto(pickle.dumps(disconnect_msg), self.server_addr)
        self.socket.close()
    

if __name__ == "__main__":
    client = SudokuClient()
    if client.connect():
        client.run()

