import socket
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import time

class QuizClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Client")
        self.root.geometry("700x600")
        
        # Client state
        self.client_socket = None
        self.is_connected = False
        self.is_in_game = False
        self.client_name = ""
        self.receive_thread = None
        
        # Game state
        self.current_question = None
        self.scoreboard = []
        self.my_score = 0
        
        self.setup_gui()
        
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Connection frame
        conn_frame = ttk.LabelFrame(main_frame, text="Connection", padding="10")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Server IP
        ttk.Label(conn_frame, text="Server IP:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.ip_var = tk.StringVar(value="127.0.0.1")
        ip_entry = ttk.Entry(conn_frame, textvariable=self.ip_var, width=20)
        ip_entry.grid(row=0, column=1, padx=5)
        
        # Port
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.port_var = tk.StringVar(value="12345")
        port_entry = ttk.Entry(conn_frame, textvariable=self.port_var, width=15)
        port_entry.grid(row=0, column=3, padx=5)
        
        # Username
        ttk.Label(conn_frame, text="Username:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(conn_frame, textvariable=self.name_var, width=20)
        name_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Connect/Disconnect button
        self.connect_button = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_button.grid(row=1, column=2, columnspan=2, padx=10, pady=5)
        
        # Question frame
        question_frame = ttk.LabelFrame(main_frame, text="Question", padding="10")
        question_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(1, weight=1)
        
        # Question text
        self.question_label = tk.Label(question_frame, text="Waiting for question...", 
                                       wraplength=600, justify=tk.LEFT, font=("Arial", 11))
        self.question_label.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=10)
        
        # Answer choices frame
        choices_frame = ttk.Frame(question_frame)
        choices_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=10)
        
        self.answer_var = tk.StringVar()
        self.radio_a = ttk.Radiobutton(choices_frame, text="", variable=self.answer_var, value="A", state=tk.DISABLED)
        self.radio_a.grid(row=0, column=0, padx=5)
        self.choice_a_label = tk.Label(choices_frame, text="", wraplength=400, justify=tk.LEFT)
        self.choice_a_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        self.radio_b = ttk.Radiobutton(choices_frame, text="", variable=self.answer_var, value="B", state=tk.DISABLED)
        self.radio_b.grid(row=1, column=0, padx=5, pady=5)
        self.choice_b_label = tk.Label(choices_frame, text="", wraplength=400, justify=tk.LEFT)
        self.choice_b_label.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        self.radio_c = ttk.Radiobutton(choices_frame, text="", variable=self.answer_var, value="C", state=tk.DISABLED)
        self.radio_c.grid(row=2, column=0, padx=5, pady=5)
        self.choice_c_label = tk.Label(choices_frame, text="", wraplength=400, justify=tk.LEFT)
        self.choice_c_label.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Submit button
        self.submit_button = ttk.Button(question_frame, text="Submit Answer", command=self.submit_answer, state=tk.DISABLED)
        self.submit_button.grid(row=3, column=0, columnspan=3, pady=15)
        
        # Scoreboard frame
        scoreboard_frame = ttk.LabelFrame(main_frame, text="Scoreboard", padding="10")
        scoreboard_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.scoreboard_listbox = tk.Listbox(scoreboard_frame, height=5)
        self.scoreboard_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E))
        scoreboard_frame.columnconfigure(0, weight=1)
        
        # Activity log frame
        log_frame = ttk.LabelFrame(main_frame, text="Client Activity Log", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(3, weight=1)
        
        # Scrollbar for log
        log_scrollbar = ttk.Scrollbar(log_frame)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Activity log listbox
        self.log_listbox = tk.Listbox(log_frame, yscrollcommand=log_scrollbar.set, height=10)
        self.log_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.config(command=self.log_listbox.yview)
        
        self.log("Client initialized. Enter server details and connect.")
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.log_listbox.insert(tk.END, log_message)
        self.log_listbox.see(tk.END)
        print(log_message)  # Also print to console
        
    def toggle_connection(self):
        if not self.is_connected:
            self.connect()
        else:
            self.disconnect()
            
    def connect(self):
        try:
            server_ip = self.ip_var.get().strip()
            if not server_ip:
                messagebox.showerror("Error", "Please enter server IP address")
                return
                
            try:
                port = int(self.port_var.get())
                if port < 1 or port > 65535:
                    messagebox.showerror("Error", "Port must be between 1 and 65535")
                    return
            except ValueError:
                messagebox.showerror("Error", "Invalid port number")
                return
                
            client_name = self.name_var.get().strip()
            if not client_name:
                messagebox.showerror("Error", "Please enter a username")
                return
                
            # Create socket and connect
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(10)  # Increased timeout for network connections
            self.log(f"Attempting to connect to {server_ip}:{port}...")
            self.client_socket.connect((server_ip, port))
            self.client_socket.settimeout(None)
            
            # Send connection message with name
            self.client_name = client_name
            self.send_message({
                "type": "connect",
                "name": client_name
            })
            
            self.log(f"Connecting to {server_ip}:{port} as '{client_name}'...")
            
            self.is_connected = True
            self.connect_button.config(text="Disconnect")
            self.ip_var.set(server_ip)
            self.port_var.set(str(port))
            self.name_var.set(client_name)
            
            # Start receiving thread AFTER setting is_connected
            self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.receive_thread.start()
            
            self.log("Receive thread started, waiting for server response...")
            # Note: Connection will be confirmed when we receive connection_accepted message
                    
        except socket.timeout:
            error_msg = (
                f"Connection timeout after 10 seconds.\n\n"
                f"Troubleshooting:\n"
                f"1. Verify server IP: {server_ip}\n"
                f"2. Verify server is running on port {port}\n"
                f"3. Check if both computers are on the same network\n"
                f"4. Test connection: ping {server_ip}\n"
                f"5. Check Windows Firewall settings on server"
            )
            messagebox.showerror("Connection Timeout", error_msg)
            self.log(f"Connection timeout to {server_ip}:{port}")
            if self.client_socket:
                try:
                    self.client_socket.close()
                except:
                    pass
                self.client_socket = None
        except ConnectionRefusedError:
            error_msg = (
                f"Connection refused by {server_ip}:{port}\n\n"
                f"Possible causes:\n"
                f"1. Server is not running\n"
                f"2. Wrong port number\n"
                f"3. Firewall is blocking the connection\n"
                f"4. Server is not listening on this IP address"
            )
            messagebox.showerror("Connection Refused", error_msg)
            self.log(f"Connection refused from {server_ip}:{port}")
            if self.client_socket:
                try:
                    self.client_socket.close()
                except:
                    pass
                self.client_socket = None
        except OSError as e:
            error_code = getattr(e, 'winerror', getattr(e, 'errno', None))
            if error_code == 10051:  # Network is unreachable
                error_msg = (
                    f"Network unreachable: {server_ip}\n\n"
                    f"Possible causes:\n"
                    f"1. Wrong IP address\n"
                    f"2. Different network (not on same Wi-Fi)\n"
                    f"3. Network interface is down"
                )
            elif error_code == 10060:  # Connection timed out (Windows)
                error_msg = (
                    f"Connection timed out to {server_ip}:{port}\n\n"
                    f"Check:\n"
                    f"1. Server is running\n"
                    f"2. Firewall allows port {port}\n"
                    f"3. Both computers on same network"
                )
            else:
                error_msg = f"Connection error: {e}\n\nError code: {error_code}"
            messagebox.showerror("Connection Error", error_msg)
            self.log(f"Connection error to {server_ip}:{port} - {e} (code: {error_code})")
            if self.client_socket:
                try:
                    self.client_socket.close()
                except:
                    pass
                self.client_socket = None
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect: {e}\n\nServer IP: {server_ip}\nPort: {port}")
            self.log(f"Connection error: {e}")
            if self.client_socket:
                try:
                    self.client_socket.close()
                except:
                    pass
                self.client_socket = None
                
    def disconnect(self):
        self.is_connected = False
        self.is_in_game = False
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
            
        self.connect_button.config(text="Connect")
        self.log("Disconnected from server")
        
        # Enable connection inputs
        # Reset UI
        self.reset_question_ui()
        self.scoreboard_listbox.delete(0, tk.END)
        
    def send_message(self, message):
        if self.client_socket:
            try:
                data = json.dumps(message).encode('utf-8')
                self.client_socket.sendall(data)
            except Exception as e:
                self.log(f"Error sending message: {e}")
                self.disconnect()
                
    def receive_messages(self):
        buffer = b""  # Buffer for incomplete messages (bytes)
        while self.is_connected:
            try:
                if not self.client_socket:
                    break
                    
                data = self.client_socket.recv(4096)
                if not data:
                    break
                
                # Add to buffer
                buffer += data
                
                # Process all complete messages (separated by newline)
                while b'\n' in buffer:
                    # Split at first newline
                    line, buffer = buffer.split(b'\n', 1)
                    if line:
                        try:
                            message = json.loads(line.decode('utf-8'))
                            self.handle_message(message)
                        except (json.JSONDecodeError, UnicodeDecodeError) as e:
                            self.log(f"Error parsing message: {e}")
                    
            except ConnectionResetError:
                self.log("Connection reset by server")
                break
            except OSError:
                break
            except Exception as e:
                self.log(f"Error receiving message: {e}")
                break
                
        # Connection lost
        if self.is_connected:
            self.root.after(0, self.handle_disconnection)
            
    def handle_message(self, message):
        msg_type = message.get("type")
        
        if msg_type == "connection_accepted":
            msg = message.get("message", "Connected successfully")
            self.root.after(0, lambda: self.log(f"✓ {msg}"))
            # Connection confirmed, can disable inputs if needed (optional)
            
        elif msg_type == "connection_error":
            error_msg = message.get("message", "Connection error")
            self.root.after(0, lambda: messagebox.showerror("Connection Error", error_msg))
            self.root.after(0, lambda: self.log(f"Connection error: {error_msg}"))
            self.root.after(0, self.disconnect)
            
        elif msg_type == "scoreboard":
            scoreboard = message.get("scoreboard", [])
            self.root.after(0, lambda: self.update_scoreboard(scoreboard))
            
        elif msg_type == "question":
            question_data = {
                "question_number": message.get("question_number", 0),
                "total_questions": message.get("total_questions", 0),
                "question": message.get("question", ""),
                "A": message.get("A", ""),
                "B": message.get("B", ""),
                "C": message.get("C", "")
            }
            # Use a copy to avoid closure issues
            qd_copy = question_data.copy()
            self.root.after(0, lambda: self.display_question(qd_copy))
            
        elif msg_type == "answer_result":
            result_msg = message.get("message", "")
            your_answer = message.get("your_answer", "")
            correct_answer = message.get("correct_answer", "")
            your_score = message.get("your_score", 0)
            
            self.root.after(0, lambda: self.log(result_msg))
            self.root.after(0, lambda: self.show_answer_result(your_answer, correct_answer, result_msg, your_score))
            
        elif msg_type == "player_connected":
            player_name = message.get("player_name", "Unknown")
            connect_msg = message.get("message", f"{player_name} has joined")
            total_players = message.get("total_players", 0)
            self.root.after(0, lambda: self.log(f"{connect_msg} (Total players: {total_players})"))
            
        elif msg_type == "player_disconnected":
            player_name = message.get("player_name", "Unknown")
            disconnect_msg = message.get("message", f"{player_name} disconnected")
            self.root.after(0, lambda: self.log(disconnect_msg))
            
        elif msg_type == "game_end":
            reason = message.get("reason", "Game ended")
            final_scoreboard = message.get("final_scoreboard", [])
            winners = message.get("winners", [])
            
            self.root.after(0, lambda: self.handle_game_end(reason, final_scoreboard, winners))
            
        elif msg_type == "server_shutdown":
            self.root.after(0, lambda: self.log("Server is shutting down"))
            self.root.after(0, self.disconnect)
            
    def display_question(self, question_data):
        try:
            self.is_in_game = True
            self.current_question = question_data
            
            question_text = f"Question {question_data['question_number']}/{question_data['total_questions']}: {question_data['question']}"
            self.question_label.config(text=question_text)
            
            choice_a_text = f"A: {question_data['A']}"
            choice_b_text = f"B: {question_data['B']}"
            choice_c_text = f"C: {question_data['C']}"
            
            # Reset label colors to black
            self.choice_a_label.config(text=choice_a_text, fg="black")
            self.choice_b_label.config(text=choice_b_text, fg="black")
            self.choice_c_label.config(text=choice_c_text, fg="black")
            
            # Enable answer UI
            self.radio_a.config(state=tk.NORMAL)
            self.radio_b.config(state=tk.NORMAL)
            self.radio_c.config(state=tk.NORMAL)
            self.submit_button.config(state=tk.NORMAL)
            self.answer_var.set("")
            
            self.log(f"Question {question_data['question_number']}: {question_data['question']}")
        except Exception as e:
            self.log(f"Error displaying question: {e}")
        
    def submit_answer(self):
        if not self.is_in_game or not self.current_question:
            return
            
        answer = self.answer_var.get()
        if not answer:
            messagebox.showwarning("Warning", "Please select an answer")
            return
            
        # Disable UI immediately to prevent double submission
        self.disable_answer_ui()
        
        # Send answer with timestamp
        self.send_message({
            "type": "answer",
            "answer": answer,
            "timestamp": time.time()
        })
        
        self.log(f"Answer submitted: {answer}. Waiting for other players...")
        
    def disable_answer_ui(self):
        self.radio_a.config(state=tk.DISABLED)
        self.radio_b.config(state=tk.DISABLED)
        self.radio_c.config(state=tk.DISABLED)
        self.submit_button.config(state=tk.DISABLED)
    
    def show_answer_result(self, your_answer, correct_answer, result_msg, your_score):
        """Show the answer result and highlight correct/incorrect answers"""
        # Disable answer UI first
        self.disable_answer_ui()
        
        # Reset all colors first
        self.choice_a_label.config(fg="black")
        self.choice_b_label.config(fg="black")
        self.choice_c_label.config(fg="black")
        
        # Highlight the selected answer
        if your_answer == "A":
            self.choice_a_label.config(fg="red" if your_answer != correct_answer else "green")
        elif your_answer == "B":
            self.choice_b_label.config(fg="red" if your_answer != correct_answer else "green")
        elif your_answer == "C":
            self.choice_c_label.config(fg="red" if your_answer != correct_answer else "green")
        
        # Highlight correct answer in green (if different from selected)
        if correct_answer == "A" and your_answer != "A":
            self.choice_a_label.config(fg="green")
        elif correct_answer == "B" and your_answer != "B":
            self.choice_b_label.config(fg="green")
        elif correct_answer == "C" and your_answer != "C":
            self.choice_c_label.config(fg="green")
        
        # Show result message
        self.log(f"Your answer: {your_answer}, Correct answer: {correct_answer}")
        self.log(f"Your current score: {your_score} points")
        
    def reset_question_ui(self):
        self.question_label.config(text="Waiting for question...")
        self.choice_a_label.config(text="")
        self.choice_b_label.config(text="")
        self.choice_c_label.config(text="")
        self.answer_var.set("")
        self.disable_answer_ui()
        
    def update_scoreboard(self, scoreboard):
        self.scoreboard = scoreboard
        self.scoreboard_listbox.delete(0, tk.END)
        
        for entry in scoreboard:
            name = entry.get("name", "Unknown")
            score = entry.get("score", 0)
            if name == self.client_name:
                self.my_score = score
                self.scoreboard_listbox.insert(tk.END, f"{name}: {score} points (You)")
            else:
                self.scoreboard_listbox.insert(tk.END, f"{name}: {score} points")
                
    def handle_game_end(self, reason, final_scoreboard, winners):
        self.is_in_game = False
        self.log(f"Game ended: {reason}")
        
        # Update final scoreboard with rankings
        self.scoreboard_listbox.delete(0, tk.END)
        for entry in final_scoreboard:
            rank = entry.get("rank", 0)
            name = entry.get("name", "Unknown")
            score = entry.get("score", 0)
            if name == self.client_name:
                self.scoreboard_listbox.insert(tk.END, f"Rank {rank}: {name}: {score} points (You)")
            else:
                self.scoreboard_listbox.insert(tk.END, f"Rank {rank}: {name}: {score} points")
                
        # Show winner message
        if self.client_name in winners:
            winner_msg = f"Congratulations! You are a winner!\n\nFinal Rankings:\n"
        else:
            winner_msg = f"Game Over!\n\nFinal Rankings:\n"
            
        for entry in final_scoreboard:
            rank = entry.get("rank", 0)
            name = entry.get("name", "Unknown")
            score = entry.get("score", 0)
            winner_msg += f"Rank {rank}: {name} - {score} points\n"
            
        messagebox.showinfo("Game Ended", winner_msg)
        self.log("Final scoreboard displayed")
        
        self.reset_question_ui()
        
    def handle_disconnection(self):
        self.is_connected = False
        self.is_in_game = False
        self.connect_button.config(text="Connect")
        self.log("Connection lost")
        messagebox.showwarning("Disconnected", "Connection to server lost")
        self.reset_question_ui()
        
    def on_closing(self):
        if self.is_connected:
            self.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    client = QuizClient(root)
    root.protocol("WM_DELETE_WINDOW", client.on_closing)
    root.mainloop()

