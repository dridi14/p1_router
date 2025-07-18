#!/usr/bin/env python3

"""
SimpleTimeline - A simplified timeline widget for animation keyframes
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Any, Optional, Callable, Tuple

class SimpleTimeline(ttk.Frame):
    """
    A simplified timeline widget for displaying and manipulating animation frames.
    Provides frame navigation, playback controls, and keyframe visualization.
    """
    
    def __init__(
        self, 
        master: Any, 
        frame_callback: Optional[Callable[[int], None]] = None,
        **kwargs
    ):
        """
        Initialize the simple timeline widget.
        
        Args:
            master: The parent widget
            frame_callback: Function to call when a frame is selected
            **kwargs: Additional keyword arguments for the Frame constructor
        """
        super().__init__(master, **kwargs)
        
        # Timeline properties
        self.fps = 12
        self.current_frame = 0
        self.total_frames = 10  # Default number of frames
        self.is_playing = False
        self.loop = True
        self.after_id = None
        
        # UI properties
        self.frame_width = 16  # Width of a frame in the timeline
        self.timeline_height = 50  # Height of the timeline
        self.visible_frames = 20  # Number of frames visible at once
        
        # Callback
        self.frame_callback = frame_callback
        
        # Set up the UI
        self._setup_ui()
        self._setup_bindings()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Main container
        self.container = ttk.Frame(self)
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Timeline canvas
        self.canvas_frame = ttk.Frame(self.container)
        self.canvas_frame.pack(fill=tk.X, expand=True)
        
        self.canvas = tk.Canvas(
            self.canvas_frame, 
            height=self.timeline_height,
            background="white",
            highlightthickness=1,
            highlightbackground="#cccccc"
        )
        self.canvas.pack(side=tk.TOP, fill=tk.X, expand=True)
        
        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.configure(xscrollcommand=self.scrollbar.set)
        
        # Controls frame
        self.controls = ttk.Frame(self.container)
        self.controls.pack(fill=tk.X, expand=True, pady=5)
        
        # Left controls - Frame navigation
        self.nav_frame = ttk.Frame(self.controls)
        self.nav_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Button(self.nav_frame, text="<<", width=3, command=self.prev_frame).pack(side=tk.LEFT, padx=2)
        
        # Frame entry and label
        self.frame_var = tk.StringVar(value="1")
        self.frame_entry = ttk.Entry(self.nav_frame, textvariable=self.frame_var, width=4)
        self.frame_entry.pack(side=tk.LEFT, padx=2)
        self.frame_entry.bind("<Return>", self._on_frame_entry)
        self.frame_entry.bind("<FocusOut>", self._on_frame_entry)
        
        self.frame_count_var = tk.StringVar(value=f"/ {self.total_frames}")
        self.frame_count_label = ttk.Label(self.nav_frame, textvariable=self.frame_count_var)
        self.frame_count_label.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(self.nav_frame, text=">>", width=3, command=self.next_frame).pack(side=tk.LEFT, padx=2)
        
        # Center controls - Playback
        self.playback_frame = ttk.Frame(self.controls)
        self.playback_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        self.play_button = ttk.Button(self.playback_frame, text="▶", width=3, command=self.play)
        self.play_button.pack(side=tk.LEFT, padx=2)
        
        self.stop_button = ttk.Button(self.playback_frame, text="■", width=3, command=self.stop)
        self.stop_button.pack(side=tk.LEFT, padx=2)
        
        # FPS control
        ttk.Label(self.playback_frame, text="FPS:").pack(side=tk.LEFT, padx=(10, 2))
        self.fps_var = tk.StringVar(value="12")
        fps_spinbox = ttk.Spinbox(
            self.playback_frame, 
            from_=1, 
            to=60, 
            width=4,
            textvariable=self.fps_var,
            command=self._update_fps
        )
        fps_spinbox.pack(side=tk.LEFT)
        self.fps_var.trace_add("write", lambda *args: self._update_fps())
        
        # Right controls - Frame management - REMOVED - Now in left panel

        # Loop control
        self.loop_var = tk.BooleanVar(value=self.loop)
        ttk.Checkbutton(
            self.playback_frame, 
            text="Loop", 
            variable=self.loop_var, 
            command=self._update_loop
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # Draw initial timeline
        self.update_timeline()
        
    def _setup_bindings(self):
        """Set up mouse and keyboard bindings."""
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Motion>", self._on_canvas_hover)
    
    def update_timeline(self):
        """Update the timeline display."""
        self.canvas.delete("all")
        
        # Calculate canvas dimensions
        width = max(
            self.total_frames * self.frame_width + 50,
            self.winfo_width()
        )
        
        # Configure canvas scrolling
        self.canvas.config(scrollregion=(0, 0, width, self.timeline_height))
        
        # Draw frame markers
        for frame_idx in range(self.total_frames):
            x = frame_idx * self.frame_width + 10
            
            # Draw frame marker
            if frame_idx == self.current_frame:
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
            
            # Draw frame number (for every 5th frame)
            if frame_idx % 5 == 0:
                self.canvas.create_text(
                    x + self.frame_width // 2, self.timeline_height - 15,
                    text=str(frame_idx + 1),  # 1-indexed for display
                    font=("Arial", 8),
                    tags="frame_number"
                )
        
        # Ensure current frame is visible
        self._ensure_frame_visible(self.current_frame)
        
        # Update the frame counter
        self.frame_var.set(str(self.current_frame + 1))  # 1-indexed for display
        self.frame_count_var.set(f"/ {self.total_frames}")
    
    def _ensure_frame_visible(self, frame_idx):
        """
        Ensure that the specified frame is visible in the timeline view.
        
        Args:
            frame_idx: Frame index to make visible
        """
        # Calculate frame position
        frame_x = frame_idx * self.frame_width + 10
        frame_width = self.frame_width
        
        # Get current scroll region
        try:
            scroll_region = self.canvas.cget("scrollregion").split()
            if len(scroll_region) == 4:
                scroll_left, _, scroll_right, _ = map(float, scroll_region)
            else:
                scroll_left, scroll_right = 0, self.canvas.winfo_width()
        except (tk.TclError, ValueError):
            # No valid scrollregion, use canvas dimensions
            scroll_left, scroll_right = 0, self.canvas.winfo_width()
        
        # Get current visible region
        visible_left = self.canvas.canvasx(0)
        visible_right = visible_left + self.canvas.winfo_width()
        
        # If the frame is not fully visible, scroll to it
        if frame_x < visible_left:
            # Scroll left to show the frame
            if scroll_right > scroll_left:  # Avoid division by zero
                self.canvas.xview_moveto((frame_x - 10) / (scroll_right - scroll_left))
        elif frame_x + frame_width > visible_right:
            # Scroll right to show the frame
            if scroll_right > scroll_left:  # Avoid division by zero
                self.canvas.xview_moveto((frame_x + frame_width - self.canvas.winfo_width() + 10) / (scroll_right - scroll_left))
    
    def _on_canvas_click(self, event):
        """
        Handle click on the timeline.
        
        Args:
            event: Click event
        """
        # Calculate which frame was clicked
        x = self.canvas.canvasx(event.x)
        frame_idx = int((x - 10) / self.frame_width)
        
        # Clamp to valid frame range
        frame_idx = max(0, min(frame_idx, self.total_frames - 1))
        
        # Set as current frame
        self.set_current_frame(frame_idx)
    
    def _on_canvas_hover(self, event):
        """
        Handle mouse hover on the timeline.
        
        Args:
            event: Motion event
        """
        # Currently not used, but could show frame number or tooltip
        pass
    
    def _on_frame_entry(self, event):
        """
        Handle frame entry field input.
        
        Args:
            event: Key or focus event
        """
        try:
            # Get frame number (1-indexed)
            frame_num = int(self.frame_var.get())
            
            # Convert to 0-indexed and clamp to valid range
            frame_idx = max(0, min(frame_num - 1, self.total_frames - 1))
            
            # Set as current frame
            self.set_current_frame(frame_idx)
        except ValueError:
            # Reset to current frame if entry is invalid
            self.frame_var.set(str(self.current_frame + 1))
    
    def _update_fps(self):
        """Update the FPS setting."""
        try:
            # Parse FPS value
            fps = int(self.fps_var.get())
            self.fps = max(1, min(fps, 60))  # Clamp to 1-60
            
            # If currently playing, restart with new FPS
            if self.is_playing:
                self.stop()
                self.play()
        except ValueError:
            # Reset to current FPS if entry is invalid
            self.fps_var.set(str(self.fps))
    
    def _update_loop(self):
        """Update the loop setting."""
        self.loop = self.loop_var.get()
    
    def set_current_frame(self, frame_idx):
        """
        Set the current frame and update the display.
        
        Args:
            frame_idx: Frame index to set as current
        """
        # Clamp to valid frame range
        frame_idx = max(0, min(frame_idx, self.total_frames - 1))
        
        # Update current frame
        if self.current_frame != frame_idx:
            self.current_frame = frame_idx
            
            # Update UI
            self.update_timeline()
            
            # Call the frame callback
            if self.frame_callback:
                self.frame_callback(frame_idx)
    
    def add_frame(self):
        """Add a new frame after the current one."""
        # Increase total frames
        self.total_frames += 1
        
        # Update UI
        self.update_timeline()
        
        # Return the new frame index
        return self.total_frames - 1
    
    def delete_frame(self):
        """Delete the current frame."""
        # Don't delete if it's the only frame
        if self.total_frames <= 1:
            return False
        
        # Decrease total frames
        self.total_frames -= 1
        
        # Adjust current frame if needed
        if self.current_frame >= self.total_frames:
            self.current_frame = self.total_frames - 1
        
        # Update UI
        self.update_timeline()
        
        # Return success
        return True
    
    def duplicate_frame(self):
        """Duplicate the current frame."""
        # Increase total frames
        self.total_frames += 1
        
        # Move to the new frame (which is right after the current one)
        new_frame_idx = self.current_frame + 1
        self.current_frame = new_frame_idx
        
        # Update UI
        self.update_timeline()
        
        # Return the new frame index
        return new_frame_idx
    
    def next_frame(self):
        """Go to the next frame."""
        if self.current_frame < self.total_frames - 1:
            # Move to next frame
            self.set_current_frame(self.current_frame + 1)
            return True
        elif self.loop:
            # Loop back to first frame
            self.set_current_frame(0)
            return True
        return False
    
    def prev_frame(self):
        """Go to the previous frame."""
        if self.current_frame > 0:
            # Move to previous frame
            self.set_current_frame(self.current_frame - 1)
            return True
        elif self.loop:
            # Loop back to last frame
            self.set_current_frame(self.total_frames - 1)
            return True
        return False
    
    def play(self):
        """Start animation playback."""
        if self.is_playing:
            return
        
        self.is_playing = True
        self._play_next_frame()
    
    def _play_next_frame(self):
        """Play the next frame in the animation."""
        if not self.is_playing:
            return
        
        # Move to next frame
        if not self.next_frame() and not self.loop:
            # Stop at end if not looping
            self.stop()
            return
        
        # Schedule next frame
        delay = int(1000 / self.fps)  # milliseconds
        self.after_id = self.after(delay, self._play_next_frame)
    
    def stop(self):
        """Stop animation playback."""
        self.is_playing = False
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
    
    def set_frame_count(self, count: int):
        """
        Set the total number of frames.
        
        Args:
            count: Total number of frames
        """
        # Set total frames
        self.total_frames = max(1, count)
        
        # Adjust current frame if needed
        if self.current_frame >= self.total_frames:
            self.current_frame = self.total_frames - 1
        
        # Update UI
        self.update_timeline()
    
    def set_keyframes(self, keyframe_frames: Dict[int, List[str]]):
        """
        Set keyframe markers in the timeline.
        
        Args:
            keyframe_frames: Dictionary mapping frame indices to lists of property names
        """
        # Remove existing keyframe markers
        self.canvas.delete("keyframe")
        
        # Add keyframe markers
        for frame_idx, properties in keyframe_frames.items():
            if frame_idx < self.total_frames and properties:
                x = frame_idx * self.frame_width + 10
                center_x = x + self.frame_width // 2
                
                # Draw keyframe diamond
                self.canvas.create_polygon(
                    center_x, 8,
                    center_x + 5, 13,
                    center_x, 18,
                    center_x - 5, 13,
                    fill="#ff9900", outline="#996600",
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