#!/usr/bin/env python3

"""
Launcher for the Improved P1 Router Config Editor
"""

import sys
import os
import subprocess
import shutil
import json
import threading

# Add the parent directory to the path so we can import modules
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)  # Go up one level from download-and-launch
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added {project_root} to Python path")

def ensure_config_exists():
    """Make sure config.json exists in the expected location"""
    # Check for config file in expected location
    config_dir = os.path.join(os.getcwd(), "p1_router", "config")
    target_config = os.path.join(config_dir, "config.json")
    
    if not os.path.isdir("config"):
        os.makedirs("config", exist_ok=True)
    
    # If config doesn't exist in ./config/ but exists in p1_router/config/, copy it
    if not os.path.exists("config/config.json") and os.path.exists(target_config):
        print(f"Copying config from {target_config} to ./config/config.json")
        try:
            # Try to copy the full config file (which might be large)
            with open(target_config, 'r') as source:
                config_data = json.load(source)
            
            with open("config/config.json", 'w') as dest:
                json.dump(config_data, dest, indent=2)
            
            print(f"Successfully copied complete config with {len(config_data)} entries")
        except Exception as e:
            print(f"Error copying config: {e}. Will create minimal config instead.")
            shutil.copy(target_config, "config/config.json")
    
    # If still no config, create a minimal one
    if not os.path.exists("config/config.json"):
        print("Creating default config.json file")
        minimal_config = """[
  {
    "from": 100,
    "to": 269,
    "ip": "192.168.1.45",
    "universe": 0
  }
]"""
        with open("config/config.json", "w") as f:
            f.write(minimal_config)
    
    return os.path.exists("config/config.json")

def launch_animation_tool():
    """Launch the animation tool in a separate window"""
    print("Launching Animation Tool...")
    
    # Path to the animation tool launcher
    animation_tool_path = os.path.join(script_dir, "animation_tool_launcher.py")
    
    # Check if animation_tool_launcher.py exists, if not create it
    if not os.path.exists(animation_tool_path):
        create_animation_tool_launcher()
    
    try:
        # Set up environment variables to ensure correct path
        env = os.environ.copy()
        env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")
        print(f"Setting PYTHONPATH to include {project_root}")
        
        # Launch the animation tool in a separate process
        process = subprocess.Popen(
            [sys.executable, animation_tool_path],
            env=env,
            # Redirect output for debugging
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Start a thread to monitor the output (helpful for debugging)
        def monitor_output():
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    print(f"Animation Tool: {line.strip()}")
        
        thread = threading.Thread(target=monitor_output, daemon=True)
        thread.start()
        
        return True
    except Exception as e:
        print(f"Error launching Animation Tool: {e}")
        return False

def create_animation_tool_launcher():
    """Create the animation tool launcher script if it doesn't exist"""
    launcher_code = """#!/usr/bin/env python3

\"\"\"
Animation Tool for P1 Router
\"\"\"

import sys
import os
import time
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# Add the parent directory to the path so we can import the animation engine
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)  # Go up one level from download-and-launch
p1_router_dir = os.path.join(project_root, "p1_router")

# Ensure both directories are in the path
for path in [project_root, p1_router_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)
        print(f"Added {path} to Python path")

# Import directly from the animation engine modules
try:
    # Import modules directly using absolute paths
    sys.path.append(os.path.join(p1_router_dir, "animation_engine"))
    from animation_engine.integration import create_animation_engine
    from animation_engine.shapes.primitives import create_rectangle, create_circle, create_triangle, create_line
    # Fixed imports - PlaybackState is in timeline, not keyframe
    from animation_engine.core.keyframe import EasingType, PropertyAnimator
    from animation_engine.core.timeline import PlaybackState
    from animation_engine.core.renderer import BlendMode
    from animation_engine.p1_router_connector import create_animation_engine_with_p1_router
    
    print("Successfully imported animation engine modules")
    ANIMATION_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"Error importing animation engine: {e}")
    print(f"Current sys.path: {sys.path}")
    print("Make sure the animation_engine module is installed in the p1_router package.")
    ANIMATION_ENGINE_AVAILABLE = False

class AnimationToolApp(tk.Tk):
    \"\"\"Animation Tool Application\"\"\"
    
    def __init__(self):
        super().__init__()
        
        self.title("P1 Router Animation Tool")
        self.geometry("1000x700")
        
        # Check if animation engine is available
        if not ANIMATION_ENGINE_AVAILABLE:
            messagebox.showerror("Error", "Animation engine not available. Make sure the animation_engine module is installed in the p1_router package.")
            self.destroy()
            return
        
        # Create the main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create the canvas for animation preview
        self.canvas_frame = ttk.LabelFrame(self.main_frame, text="Animation Preview")
        self.canvas_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=5, pady=5)
        
        self.canvas_width = 400
        self.canvas_height = 400
        self.canvas = tk.Canvas(self.canvas_frame, width=self.canvas_width, height=self.canvas_height, bg="black")
        self.canvas.pack(padx=10, pady=10)
        
        # Create the control panel
        self.control_frame = ttk.LabelFrame(self.main_frame, text="Animation Controls")
        self.control_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Create the shape panel
        self.shape_frame = ttk.LabelFrame(self.main_frame, text="Shapes")
        self.shape_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        # Configure grid weights
        self.main_frame.columnconfigure(0, weight=3)
        self.main_frame.columnconfigure(1, weight=2)
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
        # Initialize shape and animator dictionaries
        self.shapes = {}
        self.animators = {}
        
        # Add control buttons
        self.add_controls()
        
        # Add shape buttons
        self.add_shape_controls()
        
        # Initialize the animation engine
        self.init_animation_engine()
        
        # Add a protocol handler for window closing
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def add_controls(self):
        \"\"\"Add animation control buttons\"\"\"
        ttk.Button(self.control_frame, text="Play", command=self.play_animation).pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(self.control_frame, text="Pause", command=self.pause_animation).pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(self.control_frame, text="Stop", command=self.stop_animation).pack(fill=tk.X, padx=10, pady=5)
        
        # Add timeline slider
        ttk.Label(self.control_frame, text="Timeline:").pack(padx=10, pady=(10, 0), anchor=tk.W)
        self.timeline_slider = ttk.Scale(self.control_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.seek_animation)
        self.timeline_slider.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Add FPS control
        fps_frame = ttk.Frame(self.control_frame)
        fps_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(fps_frame, text="FPS:").pack(side=tk.LEFT)
        self.fps_var = tk.StringVar(value="30")
        fps_entry = ttk.Entry(fps_frame, textvariable=self.fps_var, width=5)
        fps_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(fps_frame, text="Set", command=self.set_fps).pack(side=tk.LEFT)
        
        # Add duration control
        duration_frame = ttk.Frame(self.control_frame)
        duration_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(duration_frame, text="Duration (frames):").pack(side=tk.LEFT)
        self.duration_var = tk.StringVar(value="120")
        duration_entry = ttk.Entry(duration_frame, textvariable=self.duration_var, width=5)
        duration_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(duration_frame, text="Set", command=self.set_duration).pack(side=tk.LEFT)
        
        # Add loop checkbox
        self.loop_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.control_frame, text="Loop Animation", variable=self.loop_var, command=self.set_loop).pack(padx=10, pady=5, anchor=tk.W)
        
        # Add output mode selection
        ttk.Separator(self.control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(self.control_frame, text="Output Mode:").pack(padx=10, pady=(10, 0), anchor=tk.W)
        
        self.output_mode = tk.StringVar(value="preview")
        ttk.Radiobutton(self.control_frame, text="Preview Only", variable=self.output_mode, value="preview", command=self.change_output_mode).pack(padx=20, pady=2, anchor=tk.W)
        ttk.Radiobutton(self.control_frame, text="Send to P1 Router", variable=self.output_mode, value="router", command=self.change_output_mode).pack(padx=20, pady=2, anchor=tk.W)
        
        # Add status label
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.control_frame, textvariable=self.status_var).pack(padx=10, pady=10)
    
    def add_shape_controls(self):
        \"\"\"Add shape creation buttons\"\"\"
        ttk.Button(self.shape_frame, text="Add Rectangle", command=self.add_rectangle).pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(self.shape_frame, text="Add Circle", command=self.add_circle).pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(self.shape_frame, text="Add Triangle", command=self.add_triangle).pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(self.shape_frame, text="Add Line", command=self.add_line).pack(fill=tk.X, padx=10, pady=5)
        
        # Add animation preset buttons
        ttk.Separator(self.shape_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(self.shape_frame, text="Animation Presets:").pack(padx=10, pady=(10, 0), anchor=tk.W)
        ttk.Button(self.shape_frame, text="Bouncing Ball", command=self.create_bouncing_ball).pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(self.shape_frame, text="Spinning Triangle", command=self.create_spinning_triangle).pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(self.shape_frame, text="Moving Line", command=self.create_moving_line).pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(self.shape_frame, text="Clear All", command=self.clear_shapes).pack(fill=tk.X, padx=10, pady=(20, 5))
    
    def init_animation_engine(self):
        \"\"\"Initialize the animation engine\"\"\"
        try:
            print("Initializing animation engine...")
            
            # Create a function to update the canvas
            def update_canvas(frame):
                print(f"Frame update callback called, frame shape: {frame.shape}")
                # This function will be called with each frame update
                # Convert the numpy array to a format that can be displayed on the canvas
                self.update_canvas_display(frame)
            
            # Create the animation engine in preview mode
            self.engine = create_animation_engine(self.canvas_width, self.canvas_height, update_canvas)
            
            # Configure the timeline
            self.engine.timeline.options.fps = 30
            self.engine.timeline.options.duration_frames = 120
            self.engine.timeline.options.loop = True
            
            # Add a state change callback to update UI
            def on_state_change(state):
                state_str = "Playing" if state == PlaybackState.PLAYING else "Paused" if state == PlaybackState.PAUSED else "Stopped"
                print(f"Animation state changed to: {state_str}")
                self.status_var.set(f"Animation {state_str}")
                
            self.engine.timeline.add_state_change_callback(on_state_change)
            
            # Add a frame change callback to update UI
            def on_frame_change(frame):
                print(f"Frame changed to: {frame}")
                # Update the timeline slider
                max_frame = self.engine.timeline.options.duration_frames
                percentage = (frame / max_frame) * 100 if max_frame > 0 else 0
                self.timeline_slider.set(percentage)
                
            self.engine.timeline.add_frame_callback(on_frame_change)
            
            # Start the animation engine
            self.engine.start()
            
            self.status_var.set("Animation engine initialized in preview mode")
            print("Animation engine initialized successfully")
        except Exception as e:
            self.status_var.set(f"Error: {e}")
            print(f"Error initializing animation engine: {e}")
            import traceback
            traceback.print_exc()
    
    def change_output_mode(self):
        \"\"\"Change the output mode between preview and router\"\"\"
        # Rest of the function code...
        pass

    def update_canvas_display(self, frame):
        \"\"\"Update the canvas with the current frame\"\"\"
        try:
            # Clear the canvas
            self.canvas.delete("all")
            
            # Get the frame dimensions
            height, width, _ = frame.shape
            print(f"Rendering frame with dimensions: {width}x{height}")
            
            # Keep track of non-zero pixels for debugging
            non_zero_pixels = 0
            
            # Draw each pixel as a rectangle (this is inefficient but simple for testing)
            # In a real implementation, you'd convert the numpy array to a PhotoImage
            for y in range(0, height, 4):  # Sample every 4th pixel for performance
                for x in range(0, width, 4):
                    r, g, b = frame[y, x][:3]  # Ensure we only get RGB values
                    if r > 0 or g > 0 or b > 0:  # Only draw non-black pixels
                        color = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
                        self.canvas.create_rectangle(x, y, x+4, y+4, fill=color, outline="")
                        non_zero_pixels += 1
            
            # Update the timeline slider if timeline is available
            if hasattr(self, 'engine') and hasattr(self.engine, 'timeline'):
                current_frame = self.engine.timeline.current_frame
                max_frame = self.engine.timeline.options.duration_frames
                percentage = (current_frame / max_frame) * 100 if max_frame > 0 else 0
                self.timeline_slider.set(percentage)
                
                # Add a frame number indicator on the canvas
                self.canvas.create_text(
                    10, 10, 
                    text=f"Frame: {current_frame}/{max_frame}", 
                    fill="white", 
                    anchor="nw"
                )
            
            print(f"Rendered {non_zero_pixels} active pixels")
            
        except Exception as e:
            print(f"Error updating canvas: {e}")
            import traceback
            traceback.print_exc()
    
    # Animation control methods
    def play_animation(self):
        \"\"\"Start playing the animation\"\"\"
        self.engine.play()
        self.status_var.set("Playing animation")
    
    def pause_animation(self):
        \"\"\"Pause the animation\"\"\"
        self.engine.pause()
        self.status_var.set("Animation paused")
    
    def stop_animation(self):
        \"\"\"Stop the animation\"\"\"
        self.engine.stop()
        self.status_var.set("Animation stopped")
    
    def seek_animation(self, value):
        \"\"\"Seek to a specific position in the animation\"\"\"
        try:
            frame = int((float(value) / 100) * self.engine.timeline.options.duration_frames)
            print(f"Seeking to frame {frame} of {self.engine.timeline.options.duration_frames}")
            
            # Pause the animation while seeking
            was_playing = self.engine.timeline.playback_state == PlaybackState.PLAYING
            if was_playing:
                self.engine.pause()
            
            # Seek to the new frame
            self.engine.seek(frame)
            
            # Force an update of the canvas
            if hasattr(self.engine.renderer, 'buffer'):
                self.update_canvas_display(self.engine.renderer.buffer.buffer)
            
            # Resume playback if it was playing before
            if was_playing:
                self.engine.play()
                
            # Update status
            self.status_var.set(f"Frame: {frame}")
        except Exception as e:
            print(f"Error in seek_animation: {e}")
            
    def set_fps(self):
        \"\"\"Set the animation frame rate\"\"\"
        # Function implementation...
        pass

    def set_duration(self):
        \"\"\"Set the animation duration\"\"\"
        # Function implementation...
        pass

    def set_loop(self):
        \"\"\"Set whether the animation should loop\"\"\"
        # Function implementation...
        pass

    # Shape creation methods
    def add_rectangle(self):
        \"\"\"Add a rectangle to the animation\"\"\"
        # Function implementation...
        pass

    def add_circle(self):
        \"\"\"Add a circle to the animation\"\"\"
        # Function implementation...
        pass

    def add_triangle(self):
        \"\"\"Add a triangle to the animation\"\"\"
        # Function implementation...
        pass

    def add_line(self):
        \"\"\"Add a line to the animation\"\"\"
        # Function implementation...
        pass
        
    def clear_shapes(self):
        \"\"\"Clear all shapes from the animation\"\"\"
        self.engine.clear_shapes()
        self.shapes.clear()
        self.animators.clear()
        
        # Reset the render callback
        for callback in list(self.engine.renderer._render_callbacks):
            self.engine.renderer.remove_render_callback(callback)
            
        self.engine.renderer.add_render_callback(self.engine._render_shapes)
        self.status_var.set("All shapes cleared")
        
    def create_bouncing_ball(self):
        \"\"\"Create a bouncing ball animation\"\"\"
        self.clear_shapes()
        
        # Create a circle for the ball
        ball = create_circle((self.canvas_width // 2, self.canvas_height // 2), 20, (255, 0, 0, 255))
        ball_id = self.engine.add_shape(ball)
        self.shapes[ball_id] = ball
        
        # Create an animator for the ball
        animator = PropertyAnimator()
        self.animators[ball_id] = animator
        
        # Create a rectangle for the ground
        ground = create_rectangle((0, self.canvas_height - 20), (self.canvas_width, 20), (0, 255, 0, 255))
        ground_id = self.engine.add_shape(ground)
        self.shapes[ground_id] = ground
        
        # Animate the ball's position
        # Start at the top
        animator.add_keyframe("position", 0, (self.canvas_width // 2, 20), EasingType.EASE_OUT)
        
        # Bounce several times with decreasing height
        for i in range(1, 6):
            # Fall down
            animator.add_keyframe(
                "position", 
                i * 20, 
                (self.canvas_width // 2, self.canvas_height - 40),  # Just above the ground
                EasingType.EASE_IN
            )
            
            # Bounce up (with decreasing height)
            bounce_height = (self.canvas_height - 60) * (0.7 ** i)
            animator.add_keyframe(
                "position", 
                i * 20 + 10, 
                (self.canvas_width // 2, self.canvas_height - 40 - bounce_height),
                EasingType.EASE_OUT
            )
        
        # End at rest on the ground
        animator.add_keyframe(
            "position", 
            120, 
            (self.canvas_width // 2, self.canvas_height - 40),
            EasingType.EASE_IN
        )
        
        # Override the render callback to apply the animation
        def render_shapes():
            # Apply animations to shapes
            for shape_id, animator in self.animators.items():
                if shape_id in self.shapes:
                    animator.apply_to_object(self.shapes[shape_id], self.engine.timeline.current_frame)
            
            # Let the engine render the shapes
            self.engine._render_shapes()
        
        # Replace the engine's render callback
        self.engine.renderer.remove_render_callback(self.engine._render_shapes)
        self.engine.renderer.add_render_callback(render_shapes)
        
        self.status_var.set("Bouncing ball animation created")
    
    def create_spinning_triangle(self):
        \"\"\"Create a spinning triangle animation\"\"\"
        # Function implementation...
        pass
        
    def create_moving_line(self):
        \"\"\"Create a moving line animation\"\"\"
        # Function implementation...
        pass
        
    def on_closing(self):
        \"\"\"Handle window closing\"\"\"
        if hasattr(self, 'engine'):
            self.engine.stop_engine()
        self.destroy()

def main():
    app = AnimationToolApp()
    app.mainloop()

if __name__ == "__main__":
    main()
"""
    
    # Write the launcher script
    with open(os.path.join(script_dir, "animation_tool_launcher.py"), "w") as f:
        f.write(launcher_code)

def launch_improved_editor():
    """Launch the improved configuration editor"""
    # First ensure we have a config file in the right place
    if not ensure_config_exists():
        print("ERROR: Could not create or find config.json")
        return False
    
    try:
        # Try to run the improved editor directly
        print("Launching Improved P1 Router Config Editor...")
        
        # Run the improved editor script
        import improved_config_editor
        app = improved_config_editor.ImprovedConfigEditor()
        
        # Add animation tool button to the editor
        add_animation_button(app)
        
        app.mainloop()
        
    except ImportError as e:
        print(f"Import error: {e}")
        # If direct import fails, try running as subprocess
        print("Launching as subprocess...")
        try:
            subprocess.run([sys.executable, "improved_config_editor.py"])
        except Exception as e:
            print(f"Error launching Improved Config Editor: {e}")
            return False
            
    return True

def add_animation_button(app):
    """Add a button to launch the animation tool to the config editor"""
    try:
        # Create a button to launch the animation tool
        import tkinter as tk
        from tkinter import ttk
        
        # Add a button to the toolbar or main frame
        animation_btn = ttk.Button(
            app.toolbar_frame if hasattr(app, 'toolbar_frame') else app,
            text="Animation Tool",
            command=launch_animation_tool
        )
        animation_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        print("Added Animation Tool button to the config editor")
    except Exception as e:
        print(f"Error adding animation button: {e}")

if __name__ == "__main__":
    launch_improved_editor() 