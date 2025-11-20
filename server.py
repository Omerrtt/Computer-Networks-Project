import socket
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import time

# Embedded questions
EMBEDDED_QUESTIONS = [
    {
        'question': 'How many times has Diego Maradona participated in World Cups as team captain?',
        'A': '3',
        'B': '4',
        'C': '5',
        'correct': 'A'
    },
    {
        'question': 'Which of the following is NOT a country on the Asian continent?',
        'A': 'Pakistan',
        'B': 'Laos',
        'C': 'Tonga',
        'correct': 'C'
    },
    {
        'question': 'What is the name of the 2nd Robin in Batman comics?',
        'A': 'Dick Grayson',
        'B': 'Jason Todd',
        'C': 'Tim Drake',
        'correct': 'B'
    },
    {
        'question': 'Who is the painter of "Saturn Devouring His Son"?',
        'A': 'Pablo Picasso',
        'B': 'Claude Monet',
        'C': 'Francisco Goya',
        'correct': 'C'
    },
    {
        'question': 'Which of the following is widely described as the world\'s largest soda lake?',
        'A': 'Dead Sea',
        'B': 'Lake Van in Turkey',
        'C': 'Lake Turkana in Kenya',
        'correct': 'B'
    },
    {
        'question': 'Which of these games was created by a Turkish developer?',
        'A': 'Mount & Blade',
        'B': 'Europa Universalis',
        'C': 'Kingdom Come Deliverance',
        'correct': 'A'
    },
    {
        'question': 'Which ocean is the largest by area?',
        'A': 'Indian Ocean',
        'B': 'Atlantic Ocean',
        'C': 'Pacific Ocean',
        'correct': 'C'
    },
    {
        'question': 'What does "CPU" stand for?',
        'A': 'Central Processing Unit',
        'B': 'Core Parallel Unit',
        'C': 'Central Program Utility',
        'correct': 'A'
    },
    {
        'question': 'Who wrote what is widely considered the first modern science fiction novel?',
        'A': 'H. G. Wells',
        'B': 'Isaac Asimov',
        'C': 'Mary Shelley',
        'correct': 'C'
    },
    {
        'question': 'Which of these is a real moon of Jupiter?',
        'A': 'Titan',
        'B': 'Thebe',
        'C': 'Triton',
        'correct': 'B'
    }
]

class QuizServer:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Server")
        self.root.geometry("800x600")
        
        # Server state
        self.server_socket = None
        self.is_listening = False
        self.is_game_active = False
        self.clients = {}  # {client_socket: {'name': str, 'address': tuple, 'thread': threading.Thread}}
        self.client_names = set()  # Track unique names
        self.lock = threading.Lock()
        
        # Game state
        self.questions = []
        self.current_question_index = 0
        self.num_questions = 0
        self.answers_received = {}  # {question_index: {client_name: {'answer': str, 'timestamp': float}}}
        self.scores = {}  # {client_name: score}
        
        self.setup_gui()
        
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Server Configuration", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Port input
        ttk.Label(config_frame, text="Port:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.port_var = tk.StringVar(value="12345")
        port_entry = ttk.Entry(config_frame, textvariable=self.port_var, width=15)
        port_entry.grid(row=0, column=1, padx=5)
        
        # Start/Stop server button
        self.start_button = ttk.Button(config_frame, text="Start Server", command=self.toggle_server)
        self.start_button.grid(row=0, column=2, padx=10)
        
        # Game configuration frame
        game_frame = ttk.LabelFrame(main_frame, text="Game Configuration", padding="10")
        game_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Number of questions
        ttk.Label(game_frame, text="Number of Questions:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.num_questions_var = tk.StringVar(value="5")  # Default to 5 questions
        num_questions_entry = ttk.Entry(game_frame, textvariable=self.num_questions_var, width=15)
        num_questions_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Available questions info
        ttk.Label(game_frame, text=f"Available Questions: {len(EMBEDDED_QUESTIONS)}").grid(row=0, column=2, padx=10)
        
        # Start game button
        self.start_game_button = ttk.Button(game_frame, text="Start Game", command=self.start_game, state=tk.DISABLED)
        self.start_game_button.grid(row=0, column=3, padx=10)
        
        # Connected clients frame
        clients_frame = ttk.LabelFrame(main_frame, text="Connected Clients", padding="10")
        clients_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(2, weight=1)
        
        # Clients listbox
        self.clients_listbox = tk.Listbox(clients_frame, height=5)
        self.clients_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        clients_frame.columnconfigure(0, weight=1)
        clients_frame.rowconfigure(0, weight=1)
        
        # Activity log frame
        log_frame = ttk.LabelFrame(main_frame, text="Server Activity Log", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(3, weight=2)
        
        # Scrollbar for log
        log_scrollbar = ttk.Scrollbar(log_frame)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Activity log listbox
        self.log_listbox = tk.Listbox(log_frame, yscrollcommand=log_scrollbar.set, height=15)
        self.log_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.config(command=self.log_listbox.yview)
        
        self.log("Server initialized. Configure and start the server.")
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.log_listbox.insert(tk.END, log_message)
        self.log_listbox.see(tk.END)
        print(log_message)  # Also print to console
        
    def toggle_server(self):
        if not self.is_listening:
            self.start_server()
        else:
            self.stop_server()
            
    def start_server(self):
        try:
            port = int(self.port_var.get())
            if port < 1 or port > 65535:
                messagebox.showerror("Error", "Port must be between 1 and 65535")
                return
                
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('', port))
            self.server_socket.listen(5)
            self.is_listening = True
            
            # Get local IP address
            try:
                # Connect to a remote address to get local IP
                temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                temp_socket.connect(("8.8.8.8", 80))
                local_ip = temp_socket.getsockname()[0]
                temp_socket.close()
            except:
                local_ip = "Unable to determine"
            
            self.start_button.config(text="Stop Server")
            self.port_var.set(str(port))
            self.log(f"Server started and listening on port {port}")
            self.log(f"Server IP Address: {local_ip}")
            self.log(f"Clients can connect using IP: {local_ip} and Port: {port}")
            
            # Start accepting connections
            accept_thread = threading.Thread(target=self.accept_connections, daemon=True)
            accept_thread.start()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
        except OSError as e:
            messagebox.showerror("Error", f"Failed to start server: {e}")
            self.log(f"Error starting server: {e}")
            
    def stop_server(self):
        self.is_listening = False
        if self.server_socket:
            try:
                # Close all client connections
                with self.lock:
                    clients_to_close = list(self.clients.keys())
                for client_socket in clients_to_close:
                    try:
                        self.send_message(client_socket, {"type": "server_shutdown"})
                        client_socket.close()
                    except:
                        pass
                        
                self.server_socket.close()
            except:
                pass
                
        self.start_button.config(text="Start Server")
        self.log("Server stopped")
        
    def accept_connections(self):
        while self.is_listening:
            try:
                if self.server_socket:
                    client_socket, address = self.server_socket.accept()
                    self.log(f"New connection attempt from {address}")
                    
                    # Handle client in a separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
            except OSError:
                # Server socket closed
                break
            except Exception as e:
                self.log(f"Error accepting connection: {e}")
                
    def handle_client(self, client_socket, address):
        try:
            # Receive client name
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                return
                
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                self.log(f"Invalid message format from {address}")
                client_socket.close()
                return
                
            if message.get("type") == "connect":
                client_name = message.get("name", "").strip()
                
                if not client_name:
                    self.send_message(client_socket, {
                        "type": "connection_error",
                        "message": "Name cannot be empty"
                    })
                    client_socket.close()
                    self.log(f"Connection rejected from {address}: Empty name")
                    return
                    
                # Check if game is active
                if self.is_game_active:
                    self.send_message(client_socket, {
                        "type": "connection_error",
                        "message": "Game is already in progress. Cannot accept new connections."
                    })
                    client_socket.close()
                    self.log(f"Connection rejected from {address}: Game in progress")
                    return
                    
                # Check for duplicate name
                with self.lock:
                    if client_name in self.client_names:
                        self.send_message(client_socket, {
                            "type": "connection_error",
                            "message": f"Name '{client_name}' is already in use. Please choose a different name."
                        })
                        client_socket.close()
                        self.log(f"Connection rejected from {address}: Duplicate name '{client_name}'")
                        return
                        
                    # Accept connection
                    self.client_names.add(client_name)
                    self.clients[client_socket] = {
                        'name': client_name,
                        'address': address,
                        'thread': threading.current_thread()
                    }
                    self.scores[client_name] = 0
                    
                self.send_message(client_socket, {
                    "type": "connection_accepted",
                    "message": f"Welcome {client_name}! Waiting for game to start."
                })
                
                self.log(f"Client '{client_name}' connected from {address}")
                self.update_clients_list()
                
                # Send current scoreboard to new client first
                self.send_scoreboard()
                
                # Notify other clients about the new connection (with delay to ensure they're ready)
                if len(self.clients) > 1:  # Only if there are other clients
                    player_name_copy = client_name
                    total_players_copy = len(self.clients)
                    self.root.after(200, lambda: self.broadcast_message({
                        "type": "player_connected",
                        "player_name": player_name_copy,
                        "message": f"{player_name_copy} has joined the game",
                        "total_players": total_players_copy
                    }, exclude_socket=client_socket))
                
                # Update start game button (but don't auto-start)
                self.update_start_game_button()
                
                # Keep connection alive and handle messages
                while self.is_listening:
                    try:
                        data = client_socket.recv(1024).decode('utf-8')
                        if not data:
                            break
                            
                        message = json.loads(data)
                        self.handle_client_message(client_socket, message)
                        
                    except json.JSONDecodeError:
                        self.log(f"Invalid message from {self.clients.get(client_socket, {}).get('name', 'Unknown')}")
                        break
                    except ConnectionResetError:
                        break
                        
        except Exception as e:
            self.log(f"Error handling client {address}: {e}")
        finally:
            # Client disconnected
            self.disconnect_client(client_socket)
            
    def handle_client_message(self, client_socket, message):
        msg_type = message.get("type")
        client_name = self.clients.get(client_socket, {}).get('name', 'Unknown')
        
        if msg_type == "answer":
            if not self.is_game_active:
                return
                
            answer = message.get("answer", "").upper()
            if answer not in ['A', 'B', 'C']:
                return
                
            # Record answer with server timestamp
            with self.lock:
                if self.current_question_index not in self.answers_received:
                    self.answers_received[self.current_question_index] = {}
                    
                if client_name not in self.answers_received[self.current_question_index]:
                    self.answers_received[self.current_question_index][client_name] = {
                        'answer': answer,
                        'timestamp': time.time()  # Use server time for accuracy
                    }
                    self.log(f"Received answer '{answer}' from {client_name}")
                    
                    # Check if all players answered
                    if len(self.answers_received[self.current_question_index]) == len(self.clients):
                        self.process_question_answers()
                        
    def disconnect_client(self, client_socket):
        with self.lock:
            if client_socket in self.clients:
                client_name = self.clients[client_socket]['name']
                address = self.clients[client_socket]['address']
                
                self.client_names.discard(client_name)
                del self.clients[client_socket]
                
                if client_name in self.scores:
                    del self.scores[client_name]
                    
                self.log(f"Client '{client_name}' disconnected from {address}")
                
                try:
                    client_socket.close()
                except:
                    pass
                    
                # Notify other clients
                if self.is_game_active:
                    self.broadcast_message({
                        "type": "player_disconnected",
                        "player_name": client_name,
                        "message": f"{client_name} has disconnected"
                    })
                    
                    # Check if game should end
                    if len(self.clients) < 2:
                        self.end_game("Less than 2 players remaining")
                else:
                    self.send_scoreboard()
                    
                self.update_clients_list()
                self.update_start_game_button()
                
    def update_clients_list(self):
        self.clients_listbox.delete(0, tk.END)
        with self.lock:
            for client_info in self.clients.values():
                self.clients_listbox.insert(tk.END, client_info['name'])
                
    def update_start_game_button(self):
        """Update the start game button state - must be called from GUI thread"""
        def update():
            num_questions = self.num_questions_var.get().strip()
            can_start = (
                len(self.clients) >= 2 and
                num_questions and
                num_questions.isdigit() and
                int(num_questions) > 0 and
                not self.is_game_active and
                self.is_listening
            )
            self.start_game_button.config(state=tk.NORMAL if can_start else tk.DISABLED)
            if can_start:
                self.log(f"Start Game button enabled: {len(self.clients)} players, {num_questions} questions")
        
        # Ensure we're on the GUI thread
        if threading.current_thread() == threading.main_thread():
            update()
        else:
            self.root.after(0, update)
        
    def start_game(self):
        try:
            # Load embedded questions
            self.questions = EMBEDDED_QUESTIONS.copy()
            
            if not self.questions:
                messagebox.showerror("Error", "No questions available")
                return
                    
            self.log(f"Loaded {len(self.questions)} embedded questions")
                
            # Get number of questions
            try:
                self.num_questions = int(self.num_questions_var.get())
                if self.num_questions < 1:
                    messagebox.showerror("Error", "Number of questions must be at least 1")
                    return
            except ValueError:
                messagebox.showerror("Error", "Invalid number of questions")
                return
                
            # Check client count
            if len(self.clients) < 2:
                messagebox.showerror("Error", "At least 2 players must be connected")
                return
                
            # Start game
            self.is_game_active = True
            self.current_question_index = 0
            self.answers_received = {}
            self.scores = {name: 0 for name in self.scores}
            
            self.log(f"Game started with {len(self.clients)} players. {self.num_questions} questions will be asked.")
            self.update_start_game_button()
            
            # Send initial scoreboard
            self.send_scoreboard()
            
            # Send first question with a small delay to ensure all clients are ready
            self.root.after(300, self.send_next_question)
            
        except Exception as e:
            self.log(f"Error starting game: {e}")
            messagebox.showerror("Error", f"Failed to start game: {e}")
            
    def send_next_question(self):
        if self.current_question_index >= self.num_questions:
            self.end_game("All questions answered")
            return
            
        if len(self.clients) < 2:
            self.end_game("Less than 2 players remaining")
            return
            
        # Get question (reuse if needed)
        question = self.questions[self.current_question_index % len(self.questions)]
        
        self.log(f"Question {self.current_question_index + 1}/{self.num_questions}: {question['question']}")
        
        # Reset answers for this question
        self.answers_received[self.current_question_index] = {}
        
        # Broadcast question to all connected clients
        question_message = {
            "type": "question",
            "question_number": self.current_question_index + 1,
            "total_questions": self.num_questions,
            "question": question['question'],
            "A": question['A'],
            "B": question['B'],
            "C": question['C']
        }
        self.log(f"Broadcasting question {self.current_question_index + 1} to {len(self.clients)} clients...")
        with self.lock:
            client_count = len(self.clients)
        self.broadcast_message(question_message)
        self.log(f"Question broadcast completed to {client_count} clients")
        
    def process_question_answers(self):
        if self.current_question_index not in self.answers_received:
            return
            
        question = self.questions[self.current_question_index % len(self.questions)]
        correct_answer = question['correct']
        answers = self.answers_received[self.current_question_index]
        
        # Find first correct answer
        first_correct = None
        first_correct_time = float('inf')
        
        for client_name, answer_data in answers.items():
            if answer_data['answer'] == correct_answer:
                timestamp = answer_data.get('timestamp', 0)
                if timestamp < first_correct_time:
                    first_correct_time = timestamp
                    first_correct = client_name
                    
        # Calculate scores
        bonus_points = len(self.clients) - 1 if first_correct else 0
        
        # Update scores
        for client_name, answer_data in answers.items():
            answer = answer_data['answer']
            if answer == correct_answer:
                points = 1
                if client_name == first_correct:
                    points += bonus_points
                    self.scores[client_name] += points
                    self.log(f"{client_name} answered correctly FIRST and received {points} points (1 + {bonus_points} bonus)")
                else:
                    self.scores[client_name] += points
                    self.log(f"{client_name} answered correctly and received {points} point")
            else:
                self.scores[client_name] += 0
                self.log(f"{client_name} answered incorrectly ({answer}). Correct answer: {correct_answer}")
                
        # Send personalized results to each client
        for client_name, answer_data in answers.items():
            answer = answer_data['answer']
            if answer == correct_answer:
                if client_name == first_correct:
                    message = f"Correct! You answered first and received {1 + bonus_points} points (1 + {bonus_points} bonus)!"
                else:
                    message = f"Correct! You received 1 point."
            else:
                message = f"Incorrect. Your answer was {answer}. The correct answer is {correct_answer}. You received 0 points."
                
            # Find client socket
            client_socket = None
            for sock, info in self.clients.items():
                if info['name'] == client_name:
                    client_socket = sock
                    break
                    
            if client_socket:
                self.send_message(client_socket, {
                    "type": "answer_result",
                    "message": message,
                    "your_answer": answer,
                    "correct_answer": correct_answer,
                    "your_score": self.scores[client_name]
                })
                
        # Send updated scoreboard to all
        self.send_scoreboard()
        
        # Move to next question
        self.current_question_index += 1
        
        # Wait a bit before sending next question
        import time
        time.sleep(2)
        
        self.send_next_question()
        
    def send_scoreboard(self):
        scoreboard = []
        for name, score in sorted(self.scores.items(), key=lambda x: (-x[1], x[0])):
            scoreboard.append({"name": name, "score": score})
            
        self.broadcast_message({
            "type": "scoreboard",
            "scoreboard": scoreboard
        })
        
    def end_game(self, reason):
        self.is_game_active = False
        self.log(f"Game ended: {reason}")
        
        # Calculate rankings
        sorted_scores = sorted(self.scores.items(), key=lambda x: (-x[1], x[0]))
        rankings = []
        current_rank = 1
        
        for i, (name, score) in enumerate(sorted_scores):
            if i > 0 and sorted_scores[i-1][1] != score:
                current_rank = i + 1
            rankings.append({"rank": current_rank, "name": name, "score": score})
            
        # Find winners
        winners = [r for r in rankings if r['rank'] == 1]
        winner_names = [w['name'] for w in winners]
        
        self.log(f"Final rankings:")
        for ranking in rankings:
            self.log(f"  {ranking['rank']}. {ranking['name']}: {ranking['score']} points")
            
        # Send final results
        self.broadcast_message({
            "type": "game_end",
            "reason": reason,
            "final_scoreboard": rankings,
            "winners": winner_names
        })
        
        # Wait a bit for messages to be sent, then close connections
        time.sleep(1)
        
        # Close all client connections
        with self.lock:
            clients_to_close = list(self.clients.keys())
        for client_socket in clients_to_close:
            try:
                client_socket.close()
            except:
                pass
                
        # Clear client data
        with self.lock:
            self.clients.clear()
            self.client_names.clear()
            self.scores.clear()
            
        self.update_clients_list()
        self.update_start_game_button()
        self.log("All connections closed. Server ready for new connections.")
        
    def send_message(self, client_socket, message):
        try:
            data = json.dumps(message).encode('utf-8')
            # Send message with newline separator
            client_socket.sendall(data + b'\n')
            # Debug log for question messages
            if message.get("type") == "question":
                client_name = self.clients.get(client_socket, {}).get('name', 'Unknown')
                self.log(f"Sent question to {client_name}: {message.get('question', '')[:50]}...")
        except Exception as e:
            self.log(f"Error sending message: {e}")
            # Try to get client name for better error reporting
            try:
                client_name = self.clients.get(client_socket, {}).get('name', 'Unknown')
                self.log(f"Failed to send message to {client_name}")
            except:
                pass
            
    def broadcast_message(self, message, exclude_socket=None):
        """Broadcast message to all clients, optionally excluding one"""
        with self.lock:
            clients_to_remove = []
            for client_socket in self.clients.keys():
                if client_socket == exclude_socket:
                    continue  # Skip excluded client
                try:
                    self.send_message(client_socket, message)
                except:
                    clients_to_remove.append(client_socket)
                    
            for client_socket in clients_to_remove:
                self.disconnect_client(client_socket)
                
    def on_closing(self):
        if self.is_listening:
            self.stop_server()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    server = QuizServer(root)
    root.protocol("WM_DELETE_WINDOW", server.on_closing)
    root.mainloop()

