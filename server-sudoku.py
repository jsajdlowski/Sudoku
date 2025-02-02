import socket
import pickle
from grid import Grid
import pygame
import signal
import sys

class SudokuServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind((host, port))
        
        pygame.font.init()
        self.game_font = pygame.font.SysFont('Arial', 50)
        self.clients = {}
        self.reset_game_state()
        print(f"Server started on {host}:{port}")

    def reset_game_state(self):
        self.grid = Grid(self.game_font)
        self.grid.remove_numbers(10)
        self.clients = {}
        self.current_turn = 0
        self.scores = {0: 0, 1: 0}
        self.correct_cells = set()
        print("Game state reset - Ready for new players")

    def is_game_complete(self):
        if not self.grid:
            return False
        for y in range(9):
            for x in range(9):
                if self.grid.get_cell(x, y) == 0:
                    return False
        return True

    def handle_client(self, client_socket, addr):
        try:
            player_number = len(self.clients)
            init_data = {
                'board': self.grid.get_board(),
                'player_number': player_number,
                'current_turn': self.current_turn,
                'scores': self.scores,
                'correct_cells': self.correct_cells
            }
            client_socket.send(pickle.dumps(init_data))
            self.clients.append(client_socket)
            
            while True:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    move_data = pickle.loads(data)
                    if player_number == self.current_turn:
                        x, y, value = move_data['x'], move_data['y'], move_data['value']
                        if self.grid.solution[y][x] == value:
            
                            self.grid.set_cell(x, y, value)
                            self.scores[player_number] += 1
                            self.correct_cells.add((x, y))
                            
          
                            if self.is_game_complete():
                                game_end_data = {
                                    'type': 'game_end',
                                    'board': self.grid.get_board(),
                                    'scores': self.scores,
                                    'correct_cells': self.correct_cells
                                }
   
                                for client in self.clients:
                                    client.send(pickle.dumps(game_end_data))

                                self.reset_game_state()
                            else:
                                update_data = {
                                    'type': 'update',
                                    'board': self.grid.get_board(),
                                    'current_turn': (self.current_turn + 1) % 2,
                                    'scores': self.scores,
                                    'correct_cells': self.correct_cells
                                }
                                for client in self.clients:
                                    if client != client_socket:
                                        client.send(pickle.dumps(update_data))
                                self.current_turn = (self.current_turn + 1) % 2
                        else:
                            self.scores[player_number] -= 1
                            incorrect_update = {
                                'board': self.grid.get_board(),
                                'current_turn': (self.current_turn + 1) % 2,
                                'scores': self.scores,
                                'correct_cells': self.correct_cells,
                                'incorrect_move': {
                                    'x': x,
                                    'y': y,
                                    'value': value
                                }
                            }
                            client_socket.send(pickle.dumps(incorrect_update))
                            other_update = {
                                'board': self.grid.get_board(),
                                'current_turn': (self.current_turn + 1) % 2,
                                'scores': self.scores,
                                'correct_cells': self.correct_cells
                            }
                            for client in self.clients:
                                if client != client_socket:
                                    client.send(pickle.dumps(other_update))
                            self.current_turn = (self.current_turn + 1) % 2
                    
                except:
                    break
                    
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            client_socket.close()
            
            if len(self.clients) == 0:
                self.reset_game_state()

    def signal_handler(self, sig, frame):
        print("\nShutting down server...")
        disconnect_message = {'type': 'disconnect'}
        for client_addr in self.clients:
            self.server.sendto(pickle.dumps(disconnect_message), client_addr)
        self.server.close()
        sys.exit(0)
        
    def start(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        print("Starting server...")
        while True:
            try:
                data, addr = self.server.recvfrom(1024)
                if not data:
                    continue
                
                message = pickle.loads(data)
                if message.get('type') == 'join':
                    if len(self.clients) < 2:
                        player_number = len(self.clients)
                        self.clients[addr] = player_number
                        self.scores[player_number] = 0
                        
                        if player_number == 0:
                            self.current_turn = 0
                        
                        init_data = {
                            'type': 'init',
                            'board': self.grid.get_board(),
                            'player_number': player_number,
                            'current_turn': self.current_turn,
                            'scores': self.scores,
                            'correct_cells': self.correct_cells
                        }
                        self.server.sendto(pickle.dumps(init_data), addr)
                        print(f"Player {player_number + 1} connected from {addr}")
                    else:
                        active_clients = {}
                        for client_addr in self.clients:
                            try:
                                ping_data = {'type': 'ping'}
                                self.server.sendto(pickle.dumps(ping_data), client_addr)
                                active_clients[client_addr] = self.clients[client_addr]
                            except:
                                continue
                        
                        if len(active_clients) < 2:
                            self.clients = active_clients
                            self.reset_game_state()
                            player_number = len(self.clients)
                            self.clients[addr] = player_number
                            init_data = {
                                'type': 'init',
                                'board': self.grid.get_board(),
                                'player_number': player_number,
                                'current_turn': self.current_turn,
                                'scores': self.scores,
                                'correct_cells': self.correct_cells
                            }
                            self.server.sendto(pickle.dumps(init_data), addr)
                            print(f"Player {player_number + 1} connected from {addr}")
                        else:
                            print(f"Rejected connection from {addr}: Game full")
                
                elif message.get('type') == 'move':
                    if addr in self.clients:
                        player_number = self.clients[addr]
                        if player_number == self.current_turn:
                            self.handle_move(message, addr)
                
                elif message.get('type') == 'disconnect':
                    if addr in self.clients:
                        del self.clients[addr]
                        if len(self.clients) == 0:
                            self.reset_game_state()
                        print(f"Player disconnected from {addr}")
            
            except Exception as e:
                print(f"Error in server: {e}")

    def handle_move(self, message, addr):
        if addr in self.clients:
            player_number = self.clients[addr]
            if player_number == self.current_turn:
                x, y, value = message['x'], message['y'], message['value']
                if self.grid.solution[y][x] == value:
                    self.grid.set_cell(x, y, value)
                    self.scores[player_number] += 1
                    self.correct_cells.add((x, y))
                    
                    if self.is_game_complete():
                        game_end_data = {
                            'type': 'game_end',
                            'board': self.grid.get_board(),
                            'scores': self.scores,
                            'correct_cells': self.correct_cells
                        }
                        for client_addr in self.clients:
                            self.server.sendto(pickle.dumps(game_end_data), client_addr)
                        self.reset_game_state()
                    else:
                        update_data = {
                            'type': 'update',
                            'board': self.grid.get_board(),
                            'current_turn': (self.current_turn + 1) % 2,
                            'scores': self.scores,
                            'correct_cells': self.correct_cells
                        }
                        for client_addr in self.clients:
                            self.server.sendto(pickle.dumps(update_data), client_addr)
                        self.current_turn = (self.current_turn + 1) % 2
                else:
                    self.scores[player_number] -= 1
                    incorrect_update = {
                        'type': 'incorrect',
                        'board': self.grid.get_board(),
                        'current_turn': (self.current_turn + 1) % 2,
                        'scores': self.scores,
                        'correct_cells': self.correct_cells,
                        'incorrect_move': {
                            'x': x,
                            'y': y,
                            'value': value
                        }
                    }
                    self.server.sendto(pickle.dumps(incorrect_update), addr)
                    
                    other_update = {
                        'type': 'update',
                        'board': self.grid.get_board(),
                        'current_turn': (self.current_turn + 1) % 2,
                        'scores': self.scores,
                        'correct_cells': self.correct_cells
                    }
                    for client_addr in self.clients:
                        if client_addr != addr:
                            self.server.sendto(pickle.dumps(other_update), client_addr)
                    self.current_turn = (self.current_turn + 1) % 2

if __name__ == "__main__":
    server = SudokuServer()
    server.start()