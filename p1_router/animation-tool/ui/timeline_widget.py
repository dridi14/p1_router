#!/usr/bin/env python3

"""
TimelineWidget - A widget for displaying and navigating animation frames
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Any, Optional, Callable

from animation.keyframe import AnimationController


class TimelineWidget(ttk.Frame):
    """
    Timeline widget for displaying and navigating animation frames.
    Allows adding, selecting, and manipulating keyframes.
    """
    
    def __init__(
        self, 
        master: Any, 
        animation_controller: Optional[AnimationController] = None,
        frame_callback: Optional[Callable[[int], None]] = None,
        **kwargs
    ):
        """
        Initialize the timeline widget.
        
        Args:
            master: The parent widget
            animation_controller: The animation controller (if not provided, a new one is created)
            frame_callback: Function to call when a frame is selected
            **kwargs: Additional keyword arguments for the Frame constructor
        """
        super().__init__(master, **kwargs)
        
        # Timeline properties
        self.controller = animation_controller or AnimationController()
        self.frame_callback = frame_callback
        self.hover_frame = None
        
        # UI properties
        self.frame_width = 15  # Width of a frame in the timeline
        self.timeline_height = 50  # Height of the timeline
        self.visible_frames = 20  # Number of frames visible at once
        
        # Keyframe colors
        self.keyframe_colors = {
            "position": "#ff6666",  # Red
            "color": "#66ff66",     # Green
            "scale": "#6666ff",     # Blue
            "rotation": "#ffff66",  # Yellow
            "opacity": "#ff66ff",   # Pink
            "default": "#ffcc66"    # Orange (default)
        }
        
        # Set up the UI
        self._setup_ui()
        self._setup_bindings()
        
        # Add some sample keyframes for testing
        if not self.controller.tracks:
            print("Adding sample keyframes for testing...")
            # Add a sample property with keyframes at frames 0, 5, and 10
            self.controller.add_keyframe("sample_property", 0, "value1")
            self.controller.add_keyframe("sample_property", 5, "value2")
            self.controller.add_keyframe("sample_property", 10, "value3")
            
            # Add pixel keyframes
            self.controller.add_keyframe("pixel_0_0", 0, "#FF0000")
            self.controller.add_keyframe("pixel_1_1", 5, "#00FF00")
            self.controller.add_keyframe("pixel_2_2", 10, "#0000FF")
            
            # Verify keyframes were added
            keyframes = self.controller.get_all_keyframes()
            print(f"Keyframes after adding: {keyframes}")
            frames = self.controller.get_keyframe_frames()
            print(f"Frames with keyframes: {frames}")
            
            # Force a timeline update
            self.update_timeline()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Container frame with border
        self.container = ttk.Frame(self, borderwidth=1, relief="sunken")
        self.container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Timeline canvas
        self.canvas = tk.Canvas(
            self.container, 
            height=self.timeline_height,
            background="white",
            highlightthickness=0
        )
        self.canvas.pack(side=tk.TOP, fill=tk.X, expand=True)
        
        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self.container, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.configure(xscrollcommand=self.scrollbar.set)
        
        # Frame navigation controls
        controls = ttk.Frame(self)
        controls.pack(fill=tk.X, expand=True, padx=5, pady=5)
        
        # Play controls
        self.play_button = ttk.Button(controls, text="▶", width=3, command=self.play)
        self.play_button.pack(side=tk.LEFT, padx=2)
        
        self.stop_button = ttk.Button(controls, text="■", width=3, command=self.stop)
        self.stop_button.pack(side=tk.LEFT, padx=2)
        
        # FPS control
        ttk.Label(controls, text="FPS:").pack(side=tk.LEFT, padx=(10, 2))
        self.fps_var = tk.StringVar(value=str(self.controller.fps))
        fps_spinbox = ttk.Spinbox(controls, from_=1, to=60, width=5, textvariable=self.fps_var)
        fps_spinbox.pack(side=tk.LEFT)
        self.fps_var.trace_add("write", lambda *args: self._update_fps())
        
        # Frame navigation
        ttk.Button(controls, text="<<", width=3, command=self.prev_frame).pack(side=tk.LEFT, padx=(10, 2))
        self.frame_var = tk.StringVar(value=str(self.controller.current_frame + 1))
        self.frame_entry = ttk.Entry(controls, textvariable=self.frame_var, width=5)
        self.frame_entry.pack(side=tk.LEFT, padx=2)
        self.frame_entry.bind("<Return>", self._on_frame_entry)
        self.frame_count_label = ttk.Label(controls, text=f"of {self.controller.duration}")
        self.frame_count_label.pack(side=tk.LEFT, padx=2)
        ttk.Button(controls, text=">>", width=3, command=self.next_frame).pack(side=tk.LEFT, padx=2)
        
        # Add frame buttons
        ttk.Button(controls, text="+", width=3, command=self.add_frame).pack(side=tk.LEFT, padx=(10, 2))
        ttk.Button(controls, text="-", width=3, command=self.remove_frame).pack(side=tk.LEFT)
        
        # Duration control
        ttk.Label(controls, text="Duration:").pack(side=tk.LEFT, padx=(10, 2))
        self.duration_var = tk.StringVar(value=str(self.controller.duration))
        duration_spinbox = ttk.Spinbox(controls, from_=1, to=1000, width=5, textvariable=self.duration_var)
        duration_spinbox.pack(side=tk.LEFT)
        self.duration_var.trace_add("write", lambda *args: self._update_duration())
        
        # Loop control
        self.loop_var = tk.BooleanVar(value=self.controller.loop)
        ttk.Checkbutton(controls, text="Loop", variable=self.loop_var, command=self._update_loop).pack(side=tk.LEFT, padx=(10, 0))
        
        # Keyframe controls
        keyframe_frame = ttk.Frame(self)
        keyframe_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)
        
        ttk.Label(keyframe_frame, text="Keyframe:").pack(side=tk.LEFT)
        ttk.Button(keyframe_frame, text="Add", width=6, command=self._add_keyframe_placeholder).pack(side=tk.LEFT, padx=2)
        ttk.Button(keyframe_frame, text="Remove", width=6, command=self._remove_keyframe_placeholder).pack(side=tk.LEFT, padx=2)
        
        # Easing selection
        ttk.Label(keyframe_frame, text="Easing:").pack(side=tk.LEFT, padx=(10, 2))
        self.easing_var = tk.StringVar(value="linear")
        easing_combo = ttk.Combobox(keyframe_frame, values=[
            "linear", "ease_in_quad", "ease_out_quad", "ease_in_out_quad",
            "ease_in_cubic", "ease_out_cubic", "ease_in_out_cubic",
            "ease_in_sine", "ease_out_sine", "ease_in_out_sine",
            "ease_in_back", "ease_out_back", "ease_in_out_back",
            "ease_in_bounce", "ease_out_bounce", "ease_in_out_bounce"
        ], textvariable=self.easing_var, state="readonly", width=15)
        easing_combo.pack(side=tk.LEFT)
        
        # Draw initial timeline
        self.update_timeline()
        
    def _setup_bindings(self):
        """Set up mouse and keyboard bindings."""
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Motion>", self._on_canvas_hover)
        self.canvas.bind("<Shift-Button-1>", self._on_canvas_shift_click)
        self.canvas.bind("<Control-Button-1>", self._on_canvas_ctrl_click)
    
    def update_timeline(self):
        """Update the timeline display."""
        self.canvas.delete("all")
        
        # Calculate canvas dimensions
        width = max(
            self.controller.duration * self.frame_width + 50,
            self.winfo_width()
        )
        
        # Configure canvas scrolling
        self.canvas.config(scrollregion=(0, 0, width, self.timeline_height))
        
        # Get keyframes
        keyframe_frames = self.controller.get_keyframe_frames()
        
        # Debug: Print keyframes
        print(f"Timeline update - Keyframes: {keyframe_frames}")
        print(f"Current frame: {self.controller.current_frame}, Duration: {self.controller.duration}")
        
        # Draw frame markers
        for frame_idx in range(self.controller.duration + 1):
            x = frame_idx * self.frame_width + 10
            
            # Draw frame marker
            if frame_idx == self.controller.current_frame:
                # Current frame
                self.canvas.create_rectangle(
                    x, 5, x + self.frame_width - 2, self.timeline_height - 5,
                    fill="#ffcc66", outline="#cc9933", width=2,
                    tags=("frame", f"frame_{frame_idx}")
                )
            else:
                # Regular frame
                self.canvas.create_rectangle(
                    x, 5, x + self.frame_width - 2, self.timeline_height - 5,
                    fill="white", outline="#dddddd",
                    tags=("frame", f"frame_{frame_idx}")
                )
            
            # Draw keyframe indicator(s)
            if frame_idx in keyframe_frames:
                properties = keyframe_frames[frame_idx]
                if len(properties) > 0:
                    # Use the color of the first property, or default
                    color = self.keyframe_colors.get(properties[0], self.keyframe_colors["default"])
                    
                    # Draw keyframe diamond
                    center_x = x + self.frame_width // 2
                    self.canvas.create_polygon(
                        center_x, 8,
                        center_x + 5, 13,
                        center_x, 18,
                        center_x - 5, 13,
                        fill=color, outline="#333333",
                        tags=("keyframe", f"keyframe_{frame_idx}")
                    )
                    
                    # If there are multiple properties, indicate with a dot
                    if len(properties) > 1:
                        self.canvas.create_text(
                            center_x, 13,
                            text=str(len(properties)),
                            font=("Arial", 6),
                            fill="white",
                            tags=("keyframe_count", f"keyframe_count_{frame_idx}")
                        )
            
            # Draw frame number (for every 5th frame)
            if frame_idx % 5 == 0:
                self.canvas.create_text(
                    x + self.frame_width // 2, self.timeline_height - 15,
                    text=str(frame_idx + 1),  # 1-indexed for display
                    font=("Arial", 8),
                    tags=("label", f"label_{frame_idx}")
                )
        
        # Draw playhead
        x = self.controller.current_frame * self.frame_width + 10 + self.frame_width // 2
        self.canvas.create_line(
            x, 0, x, self.timeline_height,
            fill="#ff3333", width=2,
            tags="playhead"
        )
        
        # Ensure current frame is visible
        self._ensure_frame_visible(self.controller.current_frame)
        
        # Update frame display
        self.frame_var.set(str(self.controller.current_frame + 1))
        self.frame_count_label.config(text=f"of {self.controller.duration}")
    
    def _ensure_frame_visible(self, frame_idx):
        """Ensure the given frame is visible in the timeline."""
        x1 = frame_idx * self.frame_width
        x2 = x1 + self.frame_width
        
        # Convert to canvas coordinates (0 to 1)
        canvas_width = self.canvas.winfo_width()
        if canvas_width > 1:  # Avoid division by zero
            x1_frac = x1 / canvas_width
            x2_frac = x2 / canvas_width
            
            # Check if frame is outside current view
            current_view = self.canvas.xview()
            if x1_frac < current_view[0] or x2_frac > current_view[1]:
                # Scroll to make frame visible
                self.canvas.xview_moveto(max(0, x1_frac - 0.1))
    
    def _update_fps(self):
        """Update the frames per second value."""
        try:
            fps = int(self.fps_var.get())
            if fps > 0:
                self.controller.set_fps(fps)
        except ValueError:
            # Revert to current value
            self.fps_var.set(str(self.controller.fps))
    
    def _update_duration(self):
        """Update the animation duration."""
        try:
            duration = int(self.duration_var.get())
            if duration > 0:
                self.controller.set_duration(duration)
                self.update_timeline()
        except ValueError:
            # Revert to current value
            self.duration_var.set(str(self.controller.duration))
    
    def _update_loop(self):
        """Update the loop setting."""
        self.controller.set_loop(self.loop_var.get())
    
    def _on_canvas_click(self, event):
        """Handle clicks on the timeline canvas."""
        # Calculate which frame was clicked
        frame_idx = max(0, min(self.controller.duration, (event.x - 10) // self.frame_width))
        
        # Set as current frame
        self.set_current_frame(frame_idx)
    
    def _on_canvas_shift_click(self, event):
        """Handle shift+click to select a range of frames."""
        # Placeholder for future implementation
        pass
    
    def _on_canvas_ctrl_click(self, event):
        """Handle ctrl+click to toggle keyframe at the clicked frame."""
        # Calculate which frame was clicked
        frame_idx = max(0, min(self.controller.duration, (event.x - 10) // self.frame_width))
        
        # Toggle keyframe for the current property (placeholder)
        self._toggle_keyframe_placeholder(frame_idx)
    
    def _on_canvas_hover(self, event):
        """Handle mouse hover over the timeline canvas."""
        # Calculate which frame is being hovered over
        frame_idx = max(0, min(self.controller.duration, (event.x - 10) // self.frame_width))
        
        if frame_idx != self.hover_frame:
            self.hover_frame = frame_idx
            
            # Show frame info in a tooltip (future implementation)
    
    def _on_frame_entry(self, event):
        """Handle manual frame number entry."""
        try:
            frame = int(self.frame_var.get()) - 1  # Convert from 1-indexed display to 0-indexed internal
            self.set_current_frame(frame)
        except ValueError:
            # Revert to current frame if invalid
            self.frame_var.set(str(self.controller.current_frame + 1))
    
    def set_current_frame(self, frame_idx):
        """
        Set the current frame and update the display.
        
        Args:
            frame_idx: The frame index to set as current
        """
        # Ensure frame is in valid range
        frame_idx = max(0, min(frame_idx, self.controller.duration))
        
        # Update controller
        self.controller.set_frame(frame_idx)
        
        # Update display
        self.update_timeline()
        
        # Call the frame change callback if provided
        if self.frame_callback:
            self.frame_callback(frame_idx)
    
    def add_frame(self):
        """Add a new frame after the current one."""
        # Get current frame
        current_frame = self.controller.current_frame
        
        # Create a new frame after the current one
        new_frame = current_frame + 1
        
        # Shift all keyframes after the current frame
        keyframes = self.controller.get_all_keyframes()
        
        # First, increase duration to accommodate the new frame
        self.controller.set_duration(self.controller.duration + 1)
        
        # Move keyframes from later frames one frame forward
        for property_name, frames in keyframes.items():
            # Sort frames in reverse order to avoid overwriting
            for frame in sorted([int(f) for f in frames.keys() if int(f) > current_frame], reverse=True):
                keyframe = frames[frame]
                # Add keyframe at the next frame
                self.controller.add_keyframe(
                    property_name,
                    frame + 1,
                    keyframe.value,
                    keyframe.easing
                )
        
        # Set current frame to the new frame
        self.controller.set_frame(new_frame)
        
        # Update display
        self.update_timeline()
    
    def remove_frame(self):
        """Remove the current frame (reduce duration)."""
        if self.controller.duration <= 1:
            return  # Cannot remove the only frame
            
        # Get current frame
        current_frame = self.controller.current_frame
        
        # Get all keyframes
        keyframes = self.controller.get_all_keyframes()
        
        # Remove keyframes at the current frame
        for property_name, frames in keyframes.items():
            if current_frame in frames:
                self.controller.remove_keyframe(property_name, current_frame)
        
        # Shift all keyframes after the current frame
        for property_name, frames in keyframes.items():
            # Sort frames to process them in order
            for frame in sorted([int(f) for f in frames.keys() if int(f) > current_frame]):
                keyframe = frames[frame]
                # Add keyframe at the previous frame
                self.controller.add_keyframe(
                    property_name,
                    frame - 1,
                    keyframe.value,
                    keyframe.easing
                )
                # Remove the original keyframe
                self.controller.remove_keyframe(property_name, frame)
        
        # Decrease duration by 1
        self.controller.set_duration(self.controller.duration - 1)
        
        # Update controller frame if needed
        if current_frame >= self.controller.duration:
            self.controller.set_frame(self.controller.duration - 1)
        
        # Update display
        self.update_timeline()
    
    def prev_frame(self):
        """Go to the previous frame."""
        if self.controller.current_frame > 0:
            self.set_current_frame(self.controller.current_frame - 1)
    
    def next_frame(self):
        """Go to the next frame."""
        if self.controller.current_frame < self.controller.duration:
            self.set_current_frame(self.controller.current_frame + 1)
    
    def play(self):
        """Start animation playback."""
        self.controller.play()
        self.play_button.config(text="❚❚")  # Change to pause symbol
        
        # Animation playback is handled externally through the AnimationPlayer
    
    def stop(self):
        """Stop animation playback."""
        self.controller.stop()
        self.play_button.config(text="▶")  # Change to play symbol
        
        # Update to show frame 0
        self.update_timeline()
    
    def _toggle_keyframe_placeholder(self, frame_idx):
        """
        Placeholder for toggling a keyframe at the given frame.
        In a real implementation, this would toggle keyframes for the selected property.
        """
        # Set the current frame to the clicked frame
        self.set_current_frame(frame_idx)
        
        # In a real implementation, we would:
        # 1. Check if a keyframe exists at this frame for the selected property
        # 2. If exists, remove it
        # 3. If doesn't exist, add a keyframe with current value
        
        # For now, just update the display
        self.update_timeline()
    
    def _add_keyframe_placeholder(self):
        """
        Placeholder for adding a keyframe at the current frame.
        In a real implementation, this would add a keyframe for the selected property.
        """
        # In a real implementation, we would add a keyframe for the selected property
        # with the current value and the selected easing function
        
        # For now, just update the display
        self.update_timeline()
    
    def _remove_keyframe_placeholder(self):
        """
        Placeholder for removing a keyframe at the current frame.
        In a real implementation, this would remove a keyframe for the selected property.
        """
        # In a real implementation, we would remove the keyframe for the selected property
        # at the current frame
        
        # For now, just update the display
        self.update_timeline()
    
    def set_controller(self, controller: AnimationController):
        """
        Set a new animation controller.
        
        Args:
            controller: The animation controller to use
        """
        self.controller = controller
        self.update_timeline()
    
    def get_controller(self) -> AnimationController:
        """
        Get the current animation controller.
        
        Returns:
            The current animation controller
        """
        return self.controller 