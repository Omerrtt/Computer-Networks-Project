import socket
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import time
import time
import os
import time
import os
import traceback
import queue


class QuizServer:
    """
    Main Server Class for the Quiz Game.
    
    Architecture:
    - Main Thread: Handles all GUI (Tkinter) updates and Game Logic (scoring, state).
    - Accept Thread: Background thread that waits for new client connections.
    - Client Threads: One background thread per client to listen for incoming messages.
    - Queue System: A thread-safe queue connects Client Threads -> Main Thread. 
      Background threads put events in the queue, and the Main Thread processes them.
      This prevents "Freezing" and race conditions.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Server")
        self.root.geometry("800x600")
        
        # Server state
        self.server_socket = None
        self.is_listening = False
        self.is_game_active = False
        self.clients = {}  # {client_socket: {'name': str, 'address': tuple}}
        self.client_names = set()  # Track unique names
        
        # message queue for thread safety
        # This is CRITICAL for the architecture.
        # Tkinter (GUI) is not thread-safe. We cannot update the UI from background threads.
        # Instead, background threads put data into this queue, and the main thread reads it.
        self.queue = queue.Queue()
        
        # Start queue processing
        # This initiates the periodic check of the queue on the main thread.
        self.process_queue()
        
        # Game state
        self.questions = []
        self.current_question_index = 0
        self.num_questions = 0
        self.answers_received = {}  # {question_index: {client_name: {'answer': str, 'timestamp': float}}}
        self.scores = {}  # {client_name: score}
        
        self.setup_gui()
        
    def setup_gui(self):
        """
        Initializes the Tkinter GUI components.
        Sets up the layout for configuration, game controls, client list, and logs.
        """
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
        
        # Question file input
        ttk.Label(game_frame, text="Question File:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.question_file_var = tk.StringVar()
        self.question_file_var.trace_add('write', lambda *args: self.on_question_file_changed())
        question_file_entry = ttk.Entry(game_frame, textvariable=self.question_file_var, width=30)
        question_file_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Number of questions
        ttk.Label(game_frame, text="Number of Questions:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.num_questions_var = tk.StringVar(value="5")  # Default to 5 questions
        self.num_questions_var.trace_add('write', lambda *args: self.update_start_game_button())
        num_questions_entry = ttk.Entry(game_frame, textvariable=self.num_questions_var, width=15)
        num_questions_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Available questions info
        self.available_questions_label = ttk.Label(game_frame, text="Available Questions: 0")
        self.available_questions_label.grid(row=1, column=2, padx=10, pady=5)
        
        # Start game button
        self.start_game_button = ttk.Button(game_frame, text="Start Game", command=self.start_game, state=tk.DISABLED)
        self.start_game_button.grid(row=1, column=3, padx=10, pady=5)
        
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
        
    def on_question_file_changed(self):
        """Called when question file path changes"""
        question_file = self.question_file_var.get().strip()
        if question_file:
            # Check if file exists
            if os.path.exists(question_file):
                self.log(f"Question file found: {question_file}")
                questions = self.load_questions_from_file(question_file)
                if questions:
                    self.available_questions_label.config(text=f"Available Questions: {len(questions)}")
                    self.log(f"Question file loaded successfully: {len(questions)} questions found")
                else:
                    self.available_questions_label.config(text="Available Questions: 0")
                    self.log("Failed to load questions from file or file is empty")
            else:
                self.available_questions_label.config(text="Available Questions: 0")
                self.log(f"Question file not found: {question_file}")
        else:
            self.available_questions_label.config(text="Available Questions: 0")
        self.update_start_game_button()
    
    def load_questions_from_file(self, filename):
        """
        Load questions from a text file.
        Format: Each question spans 5 lines:
        - Line 1: Question text
        - Line 2: Choice A (can be "A - [text]" or just "[text]")
        - Line 3: Choice B (can be "B - [text]" or just "[text]")
        - Line 4: Choice C (can be "C - [text]" or just "[text]")
        - Line 5: Correct answer (can be "Answer: A" or just "A")
        """
        questions = []
        try:
            if not os.path.exists(filename):
                self.log(f"Question file not found: {filename}")
                return questions
                
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Remove empty lines and strip whitespace
            lines = [line.strip() for line in lines if line.strip()]
            
            # Each question is 5 lines
            if len(lines) % 5 != 0:
                self.log(f"Warning: File has {len(lines)} lines, which is not a multiple of 5. Some questions may be incomplete.")
            
            for i in range(0, len(lines), 5):
                if i + 4 < len(lines):
                    # Parse question text
                    question_text = lines[i]
                    
                    # Parse choice A (remove "A - " prefix if present)
                    choice_a = lines[i + 1]
                    if choice_a.startswith("A - "):
                        choice_a = choice_a[4:].strip()
                    elif choice_a.startswith("A:"):
                        choice_a = choice_a[2:].strip()
                    
                    # Parse choice B (remove "B - " prefix if present)
                    choice_b = lines[i + 2]
                    if choice_b.startswith("B - "):
                        choice_b = choice_b[4:].strip()
                    elif choice_b.startswith("B:"):
                        choice_b = choice_b[2:].strip()
                    
                    # Parse choice C (remove "C - " prefix if present)
                    choice_c = lines[i + 3]
                    if choice_c.startswith("C - "):
                        choice_c = choice_c[4:].strip()
                    elif choice_c.startswith("C:"):
                        choice_c = choice_c[2:].strip()
                    
                    # Parse correct answer (remove "Answer: " prefix if present)
                    correct_answer_line = lines[i + 4].upper().strip()
                    correct_answer = None
                    
                    if correct_answer_line.startswith("ANSWER:"):
                        correct_answer = correct_answer_line[7:].strip()
                    elif correct_answer_line.startswith("ANSWER"):
                        # Handle "ANSWER A" format
                        parts = correct_answer_line.split()
                        if len(parts) > 1:
                            correct_answer = parts[1].strip()
                    else:
                        correct_answer = correct_answer_line.strip()
                    
                    # Extract just the letter (A, B, or C)
                    if correct_answer:
                        # Remove any extra characters, keep only A, B, or C
                        correct_answer = correct_answer[0] if len(correct_answer) > 0 else None
                    
                    # Validate correct answer
                    if correct_answer not in ['A', 'B', 'C']:
                        self.log(f"Warning: Invalid correct answer '{lines[i + 4]}' (parsed as '{correct_answer}') for question {len(questions) + 1}. Skipping.")
                        continue
                    
                    question = {
                        'question': question_text,
                        'A': choice_a,
                        'B': choice_b,
                        'C': choice_c,
                        'correct': correct_answer
                    }
                    
                    questions.append(question)
                else:
                    self.log(f"Warning: Incomplete question at line {i + 1}. Skipping.")
            
            return questions
            
        except FileNotFoundError:
            self.log(f"Question file not found: {filename}")
            return questions
        except PermissionError:
            self.log(f"Permission denied: Cannot read {filename}")
            return questions
        except Exception as e:
            self.log(f"Error loading question file {filename}: {e}")
            return questions
        
    def log(self, message):
        """
        Thread-safe logging method.
        Updates the log listbox on the main thread using root.after().
        """
        def _log():
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_message = f"[{timestamp}] {message}"
            self.log_listbox.insert(tk.END, log_message)
            self.log_listbox.see(tk.END)
        self.root.after(0, _log)
        
    def toggle_server(self):
        """
        Toggles the server state between running (listening) and stopped.
        Triggered by the Start/Stop Server button.
        """
        if not self.is_listening:
            self.start_server()
        else:
            self.stop_server()
            
    def start_server(self):
        """
        Starts the server socket to listen for connections.
        Validates the port and binds the socket.
        """
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
            self.log(f"Clients should connect to: {local_ip}:{port}")
            
            # Start accepting connections
            # We run this in a SEPARATE thread (daemon=True) so the GUI doesn't freeze
            # while waiting for a client to connect.
            accept_thread = threading.Thread(target=self.accept_connections, daemon=True)
            accept_thread.start()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
        except OSError as e:
            messagebox.showerror("Error", f"Failed to start server: {e}")
            self.log(f"Error starting server: {e}")
            
    def stop_server(self):
        """
        Stops the server, closes the socket, and disconnects all clients.
        If a game is active, it force-ends the game first.
        """
        self.is_listening = False
        
        # If game is active, end it first (this will close all client connections)
        if self.is_game_active:
            self.end_game("Server is stopping")
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
                
        self.start_button.config(text="Start Server")
        self.log("Server stopped")
        
    def accept_connections(self):
        """
        Background loop to accept new incoming TCP connections.
        When a client connects, it spawns a new 'handle_client' thread for them.
        """
        while self.is_listening:
            try:
                if self.server_socket:
                    client_socket, address = self.server_socket.accept()
                    self.log(f"New connection attempt from {address}")
                    
                    # Handle client in a separate thread
                    # For EVERY client, we start a new dedicated thread.
                    # This allows the server to listen to multiple clients simultaneously.
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
                
    def process_queue(self):
        """
        Process events from the queue on the MAIN THREAD.
        This is the bridge between background threads and the GUI/Game Logic.
        """
        try:
            while True:
                # Process all available messages
                try:
                    event = self.queue.get_nowait()
                except queue.Empty:
                    break
                    
                event_type = event[0]
                
                if event_type == "connect":
                    client_socket, address, client_name = event[1], event[2], event[3]
                    self._handle_connect_event(client_socket, address, client_name)
                    
                elif event_type == "disconnect":
                    client_socket = event[1]
                    self._handle_disconnect_event(client_socket)
                    
                elif event_type == "message":
                    client_socket, message = event[1], event[2]
                    self._handle_message_event(client_socket, message)
                    
        except Exception as e:
            self.log(f"Error processing queue: {e}")
            traceback.print_exc()
            
        # Schedule next check
        self.root.after(50, self.process_queue)
        
    def _handle_connect_event(self, client_socket, address, client_name):
        """
        Handles a 'connect' event from the queue.
        Executed on the Main Thread.
        Validates the username and adds the client to the active list.
        """
        # Check if name is taken
        if client_name in self.client_names:
            self.send_message(client_socket, {
                "type": "connection_error",
                "message": f"Name '{client_name}' is already in use."
            })
            client_socket.close()
            return
            
        # Accept connection
        self.client_names.add(client_name)
        self.clients[client_socket] = {
            'name': client_name,
            'address': address
        }
        self.scores[client_name] = 0
        
        self.send_message(client_socket, {
            "type": "connection_accepted",
            "message": f"Welcome {client_name}! Waiting for game to start."
        })
        
        self.log(f"Client '{client_name}' connected from {address}")
        self.update_clients_list()
        
        # Send current scoreboard
        self.send_scoreboard()
        
        # Notify others
        if len(self.clients) > 1:
            self.broadcast_message({
                "type": "player_connected",
                "player_name": client_name,
                "message": f"{client_name} has joined the game",
                "total_players": len(self.clients)
            }, exclude_socket=client_socket)
            
        self.update_start_game_button()

    def _handle_disconnect_event(self, client_socket):
        """
        Handles a 'disconnect' event from the queue.
        Executed on the Main Thread.
        Removes the client from lists and notifies other players.
        """
        if client_socket in self.clients:
            client_name = self.clients[client_socket]['name']
            address = self.clients[client_socket]['address']
            
            # Clean up
            self.client_names.discard(client_name)
            del self.clients[client_socket]
            
            if client_name in self.scores:
                del self.scores[client_name]
                
            self.log(f"Client '{client_name}' disconnected")
            
            self.update_clients_list()
            self.update_start_game_button()
            
            # Notify others
            self.broadcast_message({
                "type": "player_disconnected",
                "player_name": client_name,
                "message": f"{client_name} has disconnected"
            })
            
            try:
                client_socket.close()
            except:
                pass
                
    def _handle_message_event(self, client_socket, message):
        """
        Handles a 'message' event from the queue.
        Executed on the Main Thread.
        """
        self.handle_client_message(client_socket, message)

    def handle_client(self, client_socket, address):
        """
        Thread that strictly listens and puts events in queue.
        
        IMPORTANT: This run in a background thread.
        It does NOT update the GUI directly.
        It does NOT modify game state directly.
        It only puts messages into self.queue for the Main Thread to handle.
        """
        try:
            # First message is always the connect message
            try:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    client_socket.close()
                    return
                message = json.loads(data)
            except:
                client_socket.close()
                return
                
            if message.get("type") == "connect":
                client_name = message.get("name", "").strip()
                if not client_name:
                    client_socket.close()
                    return
                    
                # We can't check game active or duplicate name here safely
                # So we pass it to main thread
                if self.is_game_active:
                     self.send_message(client_socket, {
                        "type": "connection_error",
                        "message": "Game is already in progress."
                    })
                     client_socket.close()
                     return

                # Check duplicate name safely? No, do in main thread.
                # Just put in queue
                self.queue.put(("connect", client_socket, address, client_name))
            else:
                client_socket.close()
                return

            # Main listen loop
            while True:
                try:
                    data = client_socket.recv(1024).decode('utf-8')
                    if not data:
                        break
                    
                    message = json.loads(data)
                    self.queue.put(("message", client_socket, message))
                    
                except json.JSONDecodeError:
                    continue
                except ConnectionResetError:
                    break
                    
        except Exception as e:
            pass # Just disconnect
        finally:
            self.queue.put(("disconnect", client_socket, None))
            


                
    def handle_client_message(self, client_socket, message):
        """
        Processes a specific message type (e.g., 'answer') from a client.
        Executed on the Main Thread.
        """
        msg_type = message.get("type")
        client_name = self.clients.get(client_socket, {}).get('name', 'Unknown')
        
        if msg_type == "answer":
            if not self.is_game_active:
                return
                
            answer = message.get("answer", "").upper()
            if answer not in ['A', 'B', 'C']:
                return
                
            # Record answer logic - NO LOCK NEEDED as we are on MAIN THREAD
            # Since process_queue calls this, we are strictly sequential here.
            # No race conditions between clients answering at the same time.
            if self.current_question_index not in self.answers_received:
                self.answers_received[self.current_question_index] = {}
                
            if client_name not in self.answers_received[self.current_question_index]:
                self.answers_received[self.current_question_index][client_name] = {
                    'answer': answer,
                    'timestamp': time.time()  # Use server time
                }
                self.log(f"Received answer '{answer}' from {client_name}")
                
                # Check if all players answered
                if len(self.answers_received[self.current_question_index]) == len(self.clients):
                    self.process_question_answers()

    def update_clients_list(self):
        """Updates the listbox showing connected clients."""
        def _update():
            self.clients_listbox.delete(0, tk.END)
            # No lock needed - running on main thread
            for client_info in self.clients.values():
                self.clients_listbox.insert(tk.END, client_info['name'])
        self.root.after(0, _update)
                
    def update_start_game_button(self):
        """Update the start game button state - must be called from GUI thread"""
        def update():
            num_questions = self.num_questions_var.get().strip()
            question_file = self.question_file_var.get().strip()
            
            # Check if question file exists and is valid
            file_valid = False
            if question_file:
                questions = self.load_questions_from_file(question_file)
                file_valid = len(questions) > 0
            
            can_start = (
                len(self.clients) >= 2 and
                num_questions and
                num_questions.isdigit() and
                int(num_questions) > 0 and
                file_valid and
                not self.is_game_active and
                self.is_listening
            )
            self.start_game_button.config(state=tk.NORMAL if can_start else tk.DISABLED)
            if can_start:
                self.log(f"Start Game button enabled: {len(self.clients)} players, {num_questions} questions, file loaded")
        
        # Ensure we're on the GUI thread
        if threading.current_thread() == threading.main_thread():
            update()
        else:
            self.root.after(0, update)
        
    def start_game(self):
        """
        Starts the quiz game.
        Loads questions, validates requirements (2+ players), and broadcasts the first question.
        """
        try:
            # Get question file path
            question_file = self.question_file_var.get().strip()
            if not question_file:
                messagebox.showerror("Error", "Please select a question file")
                return
            
            # Check if file exists
            if not os.path.exists(question_file):
                messagebox.showerror("Error", f"Question file not found: {question_file}")
                self.log(f"Error: Question file not found: {question_file}")
                return
            
            # Load questions from file
            self.questions = self.load_questions_from_file(question_file)
            
            if not self.questions:
                messagebox.showerror("Error", "No questions available in the file or file could not be read")
                self.log("Error: No questions loaded from file")
                return
                    
            self.log(f"Loaded {len(self.questions)} questions from file: {question_file}")
                
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
            
            # Start game monitoring loop
            self.monitor_game_state()
            
            # Send first question
            self.send_next_question()
            
        except Exception as e:
            self.log(f"Error starting game: {e}")
            messagebox.showerror("Error", f"Failed to start game: {e}")
            
    def send_next_question(self):
        """
        Retrieves the next question and broadcasts it to all clients.
        If no questions remain, ends the game.
        """
        # Check player count first
        if len(self.clients) < 2:
            self.end_game("Less than 2 players remaining")
            return
            
        if self.current_question_index >= self.num_questions:
            self.end_game("All questions answered")
            return
            
        # Get question (reuse if needed)
        # Verify index is within bounds to prevent crashes, using modulo for endless loops if intended
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
        self.log(f"Broadcasting question {self.current_question_index + 1} to {len(self.clients)} clients...")
        client_count = len(self.clients)
        self.broadcast_message(question_message)
        self.log(f"Question broadcast completed to {client_count} clients")
        
    def process_question_answers(self):
        """
        Evaluates answers for the current question.
        Calculates scores (including speed bonuses) and sends results to clients.
        Triggers the next question after processing.
        """
        if self.current_question_index not in self.answers_received:
            return
        
        # Check if we have enough players before processing
        if len(self.clients) < 2:
            self.end_game("Less than 2 players remaining")
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
        
        # Check player count before moving to next question
        if len(self.clients) < 2:
            self.end_game("Less than 2 players remaining")
            return
        
        # Move to next question
        self.current_question_index += 1
        
        # Send next question
        self.send_next_question()
        
    def send_scoreboard(self):
        """Broadcasts the current scoreboard to all connected clients."""
        scoreboard = []
        for name, score in sorted(self.scores.items(), key=lambda x: (-x[1], x[0])):
            scoreboard.append({"name": name, "score": score})
            
        self.broadcast_message({
            "type": "scoreboard",
            "scoreboard": scoreboard
        })

    def monitor_game_state(self):
        """
        Periodic task to check game health (e.g., minimum player count).
        Runs every 1 second via root.after().
        """
        """Monitor game state every 1 second"""
        if not self.is_game_active:
            return

        # Check for insufficient players
        # Check for insufficient players
        # No lock needed - running on main thread via queue or root.after
        player_count = len(self.clients)
        
        if player_count < 2:
            self.log("Monitor detected fewer than 2 players. Ending game...")
            # Use root.after to ensure end_game runs on main thread (though end_game itself is thread-safe now)
            # But technically monitor_game_state IS running on main thread via root.after below
            self.end_game("Less than 2 players remaining")
            return

        # Schedule next check
        self.root.after(1000, self.monitor_game_state)
        
    def end_game(self, reason):
        # Set game as inactive FIRST so new connections can be accepted AND to prevent multiple threads
        self.is_game_active = False
        
        # Start end_game in a separate thread to avoid freezing GUI with sleep
        threading.Thread(target=self._end_game_worker, args=(reason,), daemon=True).start()

    def _end_game_worker(self, reason):
        """
        Background worker to handle game end logic (calculating final ranks).
        Started in a thread to avoid blocking if we wanted to add delays/animations later.
        """
        self.log(f"Game ended: {reason}")
        self.log(f"is_game_active set to False - new connections can now be accepted")
        
        # Capture state safely (no lock needed, main thread)
        scores_copy = self.scores.copy()
        clients_snapshot = list(self.clients.items()) # List of (socket, info_dict)
        
        # Calculate rankings using local copy
        sorted_scores = sorted(scores_copy.items(), key=lambda x: (-x[1], x[0]))
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
        
        # Broadcast to remaining clients
        remaining_names = [info['name'] for sock, info in clients_snapshot]
        self.log(f"Sending game_end message to {len(clients_snapshot)} remaining clients: {remaining_names}")
        
        if len(clients_snapshot) == 0:
            self.log("No clients remaining, skipping game_end message")
        else:
            message = {
                "type": "game_end",
                "reason": reason,
                "final_scoreboard": rankings,
                "winners": winner_names
            }
            
            for client_socket, info in clients_snapshot:
                try:
                    self.send_message(client_socket, message)
                    self.log(f"Sent game_end message to {info['name']}")
                except Exception as e:
                    self.log(f"Error sending game_end to {info['name']}: {e}")
            
            self.log(f"game_end message sent phase completed")
            
            # Wait a bit for messages to be sent before closing connections
            time.sleep(1.0)
        
        # Close all client connections
        for client_socket, _ in clients_snapshot:
            try:
                client_socket.close()
            except:
                pass
                
        # Clear client data
        # Clear client data
        self.clients.clear()
        self.client_names.clear()
        self.scores.clear()
        
        # Reset game state but keep server listening (if server is still listening)
        # Reset game state
        self.current_question_index = 0
        self.answers_received = {}
        # Keep scores empty as they were cleared above

            
        self.update_clients_list()
        self.update_start_game_button()
        
        if self.is_listening:
            self.log("Game ended. All connections closed. Server is still listening and ready for new connections.")
        else:
            self.log("Game ended. All connections closed.")
        
    def send_message(self, client_socket, message):
        try:
            data = json.dumps(message).encode('utf-8')
            # Send message with newline separator
            full_message = data + b'\n'
            client_socket.sendall(full_message)
        except Exception as e:
            self.log(f"Error sending message: {e}")
            
    def broadcast_message(self, message, exclude_socket=None):
        """Broadcast message to all clients, optionally excluding one"""

        # No lock needed - running on main thread via queue
        clients_to_remove = []
        msg_type = message.get("type", "unknown")
        for client_socket in self.clients.keys():
            if client_socket == exclude_socket:
                continue  # Skip excluded client
            try:
                client_name = self.clients[client_socket]['name']
                self.send_message(client_socket, message)
                if msg_type == "game_end":
                    self.log(f"Sent game_end message to {client_name}")
            except Exception as e:
                self.log(f"Error sending {msg_type} to {self.clients.get(client_socket, {}).get('name', 'Unknown')}: {e}")
                clients_to_remove.append(client_socket)
                
        for client_socket in clients_to_remove:
            try:
                client_socket.close()
            except:
                pass
            
            if client_socket in self.clients:
                del self.clients[client_socket]
            self.log(f"Removed unresponsive client during broadcast")
                
    def on_closing(self):
        if self.is_listening:
            self.stop_server()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    server = QuizServer(root)
    root.protocol("WM_DELETE_WINDOW", server.on_closing)
    root.mainloop()

