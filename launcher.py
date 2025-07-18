import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk
import threading
import time

class P1RouterLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("P1 Router Control Panel")
        self.geometry("800x600")
        
        self.processes = {}
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title = ttk.Label(main_frame, text="P1 Router Control Panel", font=("Arial", 24))
        title.pack(pady=(0, 20))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # Router controls
        router_frame = ttk.LabelFrame(main_frame, text="Routing Engine")
        router_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(router_frame, text="Start Main Router", 
                  command=self.start_main_router).pack(side=tk.LEFT, padx=10, pady=10)
        ttk.Button(router_frame, text="Stop Main Router", 
                  command=lambda: self.stop_process("main_router")).pack(side=tk.LEFT, padx=10, pady=10)
        
        self.router_status = ttk.Label(router_frame, text="Status: Stopped")
        self.router_status.pack(side=tk.LEFT, padx=20)
        
        # Basic listener controls
        listener_frame = ttk.LabelFrame(main_frame, text="eHuB Listener")
        listener_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(listener_frame, text="Start Listener", 
                  command=self.start_listener).pack(side=tk.LEFT, padx=10, pady=10)
        ttk.Button(listener_frame, text="Stop Listener", 
                  command=lambda: self.stop_process("listener")).pack(side=tk.LEFT, padx=10, pady=10)
        
        self.listener_status = ttk.Label(listener_frame, text="Status: Stopped")
        self.listener_status.pack(side=tk.LEFT, padx=20)
        
        # Test UI controls
        test_frame = ttk.LabelFrame(main_frame, text="Testing Interfaces")
        test_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(test_frame, text="Launch Basic Tester", 
                  command=self.start_tester).pack(side=tk.LEFT, padx=10, pady=10)
        ttk.Button(test_frame, text="Launch Advanced Tester", 
                  command=self.start_testerv2).pack(side=tk.LEFT, padx=10, pady=10)
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Log")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log = tk.Text(log_frame, height=10)
        self.log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(control_frame, text="Start All", 
                  command=self.start_all).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="Stop All", 
                  command=self.stop_all).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="Exit", 
                  command=self.exit_app).pack(side=tk.RIGHT, padx=10)
    
    def log_message(self, message):
        """Add a message to the log with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log.see(tk.END)
    
    def start_main_router(self):
        """Start the main routing engine"""
        if "main_router" in self.processes and self.processes["main_router"].poll() is None:
            self.log_message("Main router is already running")
            return
            
        try:
            # Set up environment
            env = os.environ.copy()
            
            # Start process
            process = subprocess.Popen(
                [sys.executable, "-m", "p1_router.main"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            self.processes["main_router"] = process
            
            # Update status
            self.router_status.config(text="Status: Running")
            self.log_message("Started main router")
            
            # Monitor output in a separate thread
            threading.Thread(target=self.monitor_process_output, 
                           args=(process, "main_router", self.router_status), 
                           daemon=True).start()
        except Exception as e:
            self.log_message(f"Error starting main router: {str(e)}")
    
    def start_listener(self):
        """Start the basic eHuB listener"""
        if "listener" in self.processes and self.processes["listener"].poll() is None:
            self.log_message("Listener is already running")
            return
            
        try:
            process = subprocess.Popen(
                [sys.executable, "listener.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            self.processes["listener"] = process
            
            self.listener_status.config(text="Status: Running")
            self.log_message("Started eHuB listener")
            
            threading.Thread(target=self.monitor_process_output, 
                           args=(process, "listener", self.listener_status), 
                           daemon=True).start()
        except Exception as e:
            self.log_message(f"Error starting listener: {str(e)}")
    
    def start_tester(self):
        """Launch the basic test UI"""
        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "p1_router.tester"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes["tester"] = process
            self.log_message("Launched basic tester UI")
        except Exception as e:
            self.log_message(f"Error launching basic tester: {str(e)}")
    
    def start_testerv2(self):
        """Launch the advanced test UI with video support"""
        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "p1_router.testerv2"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes["testerv2"] = process
            self.log_message("Launched advanced tester UI with video support")
        except Exception as e:
            self.log_message(f"Error launching advanced tester: {str(e)}")
    
    def monitor_process_output(self, process, name, status_label):
        """Monitor the output of a process in real-time"""
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
            self.log_message(f"{name}: {line.strip()}")
        
        # Process finished
        returncode = process.wait()
        if returncode == 0:
            self.log_message(f"{name} exited normally")
        else:
            self.log_message(f"{name} exited with code {returncode}")
            
            # Get error output
            error = process.stderr.read()
            if error:
                self.log_message(f"{name} error: {error}")
        
        # Update status
        status_label.config(text="Status: Stopped")
    
    def stop_process(self, name):
        """Stop a running process"""
        if name in self.processes:
            process = self.processes[name]
            if process.poll() is None:  # Process is running
                process.terminate()
                self.log_message(f"Stopped {name}")
                if name == "main_router":
                    self.router_status.config(text="Status: Stopped")
                elif name == "listener":
                    self.listener_status.config(text="Status: Stopped")
            else:
                self.log_message(f"{name} is not running")
    
    def start_all(self):
        """Start all main components"""
        self.start_main_router()
        self.start_listener()
        self.log_message("Started all components")
    
    def stop_all(self):
        """Stop all running processes"""
        for name in list(self.processes.keys()):
            self.stop_process(name)
        self.log_message("Stopped all components")
    
    def exit_app(self):
        """Clean up and exit"""
        self.stop_all()
        self.destroy()


if __name__ == "__main__":
    app = P1RouterLauncher()
    app.mainloop() 