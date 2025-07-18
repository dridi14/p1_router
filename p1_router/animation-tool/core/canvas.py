#!/usr/bin/env python3

"""
AnimationCanvas - The core canvas component for drawing and rendering animations
"""

import tkinter as tk
from tkinter import ttk
import math
from typing import Tuple, Dict, List, Optional, Any, Callable

from core.keyframe_manager import KeyframeManager

class AnimationCanvas(tk.Canvas):
    """
    Main canvas for drawing and rendering LED wall animations.
    Handles pixel drawing, rendering, and interaction.
    """
    
    def __init__(
        self, 
        master: Any, 
        width: int = 800, 
        height: int = 800, 
        grid_size: int = 128,
        **kwargs
    ):
        """
        Initialize the animation canvas.
        
        Args:
            master: Parent widget
            width: Canvas width in pixels
            height: Canvas height in pixels
            grid_size: Number of grid cells in each dimension (width/height)
            **kwargs: Additional arguments for the Canvas constructor
        """
        # Initialize the canvas
        super().__init__(master, width=width, height=height, **kwargs)
        self.configure(background="black")
        
        # Canvas properties
        self.grid_size = grid_size
        self.cell_size = min(width, height) // grid_size
        self.zoom_factor = 1.0
        
        # Initialize the keyframe manager
        self.keyframe_manager = KeyframeManager()
        self.keyframe_manager.set_frame_change_callback(self._on_frame_change)
        
        # Animation playback
        self.is_playing = False
        self.after_id = None
        
        # Drawing state
        self.current_color = "#FFFFFF"  # Default: white
        self.current_tool = "brush"
        self.show_grid = True
        
        # Selection and interaction state
        self.is_drawing = False
        self.last_x = 0
        self.last_y = 0
        self.selected_pixels = set()
        
        # Initialize the canvas
        self._setup_events()
        self.draw_grid()
        
    def _setup_events(self):
        """Set up event bindings for the canvas."""
        # Mouse events
        self.bind("<ButtonPress-1>", self._on_mouse_down)
        self.bind("<B1-Motion>", self._on_mouse_drag)
        self.bind("<ButtonRelease-1>", self._on_mouse_up)
        
        # Keyboard events
        self.bind("<Key>", self._on_key_press)
        
        # Set focus to receive keyboard events
        self.focus_set()
        
    def _on_mouse_down(self, event):
        """Handle mouse button press."""
        self.is_drawing = True
        x, y = self._screen_to_grid(event.x, event.y)
        self.last_x, self.last_y = x, y
        
        # Different behavior based on current tool
        if self.current_tool == "brush":
            self._draw_pixel(x, y, self.current_color)
        elif self.current_tool == "eraser":
            self._clear_pixel(x, y)
        elif self.current_tool == "select":
            self._start_selection(x, y)
            
    def _on_mouse_drag(self, event):
        """Handle mouse drag."""
        if not self.is_drawing:
            return
            
        x, y = self._screen_to_grid(event.x, event.y)
        
        # If position unchanged, do nothing
        if x == self.last_x and y == self.last_y:
            return
            
        # Handle line drawing between last point and current point
        if self.current_tool in ["brush", "eraser"]:
            self._draw_line(self.last_x, self.last_y, x, y)
        elif self.current_tool == "select":
            self._update_selection(x, y)
            
        self.last_x, self.last_y = x, y
        
    def _on_mouse_up(self, event):
        """Handle mouse button release."""
        self.is_drawing = False
        
        if self.current_tool == "select":
            self._finalize_selection()
            
    def _on_key_press(self, event):
        """Handle keyboard input."""
        key = event.keysym
        
        # Tool shortcuts
        if key == "b":
            self.set_tool("brush")
        elif key == "e":
            self.set_tool("eraser")
        elif key == "s":
            self.set_tool("select")
        elif key == "g":
            self.toggle_grid()
        elif key == "space":
            self._toggle_playback()
            
    def _screen_to_grid(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """
        Convert screen coordinates to grid coordinates.
        
        Args:
            screen_x: X coordinate on the canvas
            screen_y: Y coordinate on the canvas
            
        Returns:
            Tuple of (grid_x, grid_y)
        """
        cell_size = self.cell_size * self.zoom_factor
        grid_x = int(screen_x / cell_size)
        grid_y = int(screen_y / cell_size)
        
        # Clamp to grid bounds
        grid_x = max(0, min(grid_x, self.grid_size - 1))
        grid_y = max(0, min(grid_y, self.grid_size - 1))
        
        return grid_x, grid_y
        
    def _grid_to_screen(self, grid_x: int, grid_y: int) -> Tuple[int, int, int, int]:
        """
        Convert grid coordinates to screen rectangle coordinates.
        
        Args:
            grid_x: X coordinate on the grid
            grid_y: Y coordinate on the grid
            
        Returns:
            Tuple of (x1, y1, x2, y2) screen coordinates for the grid cell
        """
        cell_size = self.cell_size * self.zoom_factor
        x1 = grid_x * cell_size
        y1 = grid_y * cell_size
        x2 = x1 + cell_size
        y2 = y1 + cell_size
        
        return x1, y1, x2, y2
    
    def _draw_pixel(self, x: int, y: int, color: str):
        """
        Draw a single pixel at the given grid coordinates.
        
        Args:
            x: X coordinate on the grid
            y: Y coordinate on the grid
            color: Color to draw in hex format (#RRGGBB)
        """
        # Store pixel in current frame
        self.keyframe_manager.set_pixel(x, y, color)
        
        # Draw the pixel on the canvas
        self._draw_pixel_on_canvas(x, y, color)
    
    def _draw_pixel_on_canvas(self, x: int, y: int, color: str):
        """
        Draw a pixel on the canvas without adding to frame data.
        
        Args:
            x: X coordinate on the grid
            y: Y coordinate on the grid
            color: Color to draw in hex format (#RRGGBB)
        """
        x1, y1, x2, y2 = self._grid_to_screen(x, y)
        
        # Create unique tag for this pixel
        tag = f"pixel_{x}_{y}"
        
        # Remove existing pixel at this position if any
        self.delete(tag)
        
        # Draw new pixel
        self.create_rectangle(
            x1, y1, x2, y2,
            fill=color, outline="", 
            tags=(tag, "pixel")
        )
    
    def _clear_pixel(self, x: int, y: int):
        """
        Clear a pixel at the given grid coordinates.
        
        Args:
            x: X coordinate on the grid
            y: Y coordinate on the grid
        """
        # Remove pixel from current frame
        self.keyframe_manager.clear_pixel(x, y)
        
        # Remove from canvas
        tag = f"pixel_{x}_{y}"
        self.delete(tag)
    
    def _draw_line(self, x1: int, y1: int, x2: int, y2: int):
        """
        Draw a line between two grid points using Bresenham's line algorithm.
        
        Args:
            x1, y1: Starting grid coordinates
            x2, y2: Ending grid coordinates
        """
        # Bresenham's line algorithm
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        while x1 != x2 or y1 != y2:
            if self.current_tool == "brush":
                self._draw_pixel(x1, y1, self.current_color)
            else:  # eraser
                self._clear_pixel(x1, y1)
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
    
    def _start_selection(self, x: int, y: int):
        """Start a new selection at the given coordinates."""
        self.selection_start = (x, y)
        self.selection_current = (x, y)
        self.selected_pixels.clear()
        
        # Draw selection rectangle
        self._update_selection_visual()
    
    def _update_selection(self, x: int, y: int):
        """Update the current selection with new end coordinates."""
        self.selection_current = (x, y)
        self._update_selection_visual()
    
    def _update_selection_visual(self):
        """Update the visual representation of the selection."""
        # Clear previous selection visual
        self.delete("selection")
        
        # Draw new selection rectangle
        start_x, start_y = self.selection_start
        current_x, current_y = self.selection_current
        
        min_x = min(start_x, current_x)
        min_y = min(start_y, current_y)
        max_x = max(start_x, current_x)
        max_y = max(start_y, current_y)
        
        # Convert to screen coordinates
        x1, y1, _, _ = self._grid_to_screen(min_x, min_y)
        _, _, x2, y2 = self._grid_to_screen(max_x, max_y)
        
        # Draw selection rectangle
        self.create_rectangle(
            x1, y1, x2, y2,
            outline="white", dash=(4, 4),
            tags="selection"
        )
    
    def _finalize_selection(self):
        """Finalize the current selection."""
        # Get selection bounds
        start_x, start_y = self.selection_start
        current_x, current_y = self.selection_current
        
        min_x = min(start_x, current_x)
        min_y = min(start_y, current_y)
        max_x = max(start_x, current_x)
        max_y = max(start_y, current_y)
        
        # Populate selected pixels set
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                self.selected_pixels.add((x, y))
    
    def _on_frame_change(self, frame_idx):
        """
        Handle frame changes from the keyframe manager.
        
        Args:
            frame_idx: The new current frame index
        """
        self.redraw()
    
    def _toggle_playback(self):
        """Toggle animation playback."""
        if self.is_playing:
            self.stop_animation()
        else:
            self.play_animation()
    
    def draw_grid(self):
        """Draw grid lines on the canvas."""
        self.delete("grid")
        
        if not self.show_grid:
            return
            
        # Calculate cell size with zoom
        cell_size = self.cell_size * self.zoom_factor
        
        # Draw horizontal grid lines
        for i in range(self.grid_size + 1):
            y = i * cell_size
            self.create_line(
                0, y, self.winfo_width(), y,
                fill="#333333", tags="grid"
            )
            
        # Draw vertical grid lines
        for i in range(self.grid_size + 1):
            x = i * cell_size
            self.create_line(
                x, 0, x, self.winfo_height(),
                fill="#333333", tags="grid"
            )
    
    def set_tool(self, tool_name: str):
        """
        Set the current drawing tool.
        
        Args:
            tool_name: Name of the tool ("brush", "eraser", "select", etc.)
        """
        self.current_tool = tool_name
    
    def set_color(self, color: str):
        """
        Set the current drawing color.
        
        Args:
            color: Color in hex format (#RRGGBB)
        """
        self.current_color = color
    
    def set_zoom(self, zoom_factor: float):
        """
        Set the zoom level and redraw the canvas.
        
        Args:
            zoom_factor: Zoom factor (1.0 = 100%)
        """
        self.zoom_factor = max(0.1, min(10.0, zoom_factor))
        self.redraw()
    
    def toggle_grid(self):
        """Toggle grid visibility."""
        self.show_grid = not self.show_grid
        self.redraw()
    
    def clear_frame(self):
        """Clear the current frame."""
        # Clear frame data
        self.keyframe_manager.clear_frame()
        
        # Clear canvas
        self.delete("pixel")
    
    def set_frame(self, frame_idx: int) -> bool:
        """
        Set the current frame and update the display.
        
        Args:
            frame_idx: Frame index to switch to
            
        Returns:
            True if the frame was changed, False otherwise
        """
        return self.keyframe_manager.set_frame(frame_idx)
    
    def add_frame(self) -> int:
        """
        Add a new frame after the current one.
        
        Returns:
            The index of the new frame
        """
        new_frame = self.keyframe_manager.add_frame()
        self.redraw()
        return new_frame
    
    def remove_frame(self) -> bool:
        """
        Remove the current frame.
        
        Returns:
            True if the frame was removed, False otherwise
        """
        result = self.keyframe_manager.remove_frame()
        self.redraw()
        return result
    
    def duplicate_frame(self) -> int:
        """
        Duplicate the current frame.
        
        Returns:
            The index of the new frame
        """
        new_frame = self.keyframe_manager.duplicate_frame()
        self.redraw()
        return new_frame
    
    def next_frame(self) -> bool:
        """
        Go to the next frame.
        
        Returns:
            True if moved to the next frame, False if already at the last frame
        """
        return self.keyframe_manager.next_frame()
    
    def prev_frame(self) -> bool:
        """
        Go to the previous frame.
        
        Returns:
            True if moved to the previous frame, False if already at the first frame
        """
        return self.keyframe_manager.prev_frame()
    
    def play_animation(self):
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
        if not self.next_frame():
            # Loop back to first frame
            self.set_frame(0)
        
        # Schedule next frame
        delay = int(1000 / self.keyframe_manager.fps)  # milliseconds
        self.after_id = self.after(delay, self._play_next_frame)
    
    def stop_animation(self):
        """Stop animation playback."""
        self.is_playing = False
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
    
    def redraw(self):
        """Redraw the entire canvas based on the current frame."""
        # Clear the canvas
        self.delete("all")
        
        # Draw the grid
        self.draw_grid()
        
        # Draw the pixels for the current frame
        frame_data = self.keyframe_manager.get_frame_data()
        for (x, y), color in frame_data.items():
            self._draw_pixel_on_canvas(x, y, color)
        
        # Redraw selection if active
        if hasattr(self, 'selection_start') and hasattr(self, 'selection_current'):
            self._update_selection_visual()
    
    # Compatibility with MainWindow
    @property
    def frames(self):
        """Get all frames data (compatibility property)."""
        return self.keyframe_manager.frames
    
    @frames.setter
    def frames(self, value):
        """Set all frames data (compatibility property)."""
        self.keyframe_manager.set_all_frames(value)
    
    @property
    def current_frame(self):
        """Get current frame index (compatibility property)."""
        return self.keyframe_manager.current_frame
    
    @current_frame.setter
    def current_frame(self, value):
        """Set current frame index (compatibility property)."""
        self.keyframe_manager.set_frame(value)
    
    @property
    def fps(self):
        """Get FPS setting (compatibility property)."""
        return self.keyframe_manager.fps
    
    @fps.setter
    def fps(self, value):
        """Set FPS setting (compatibility property)."""
        self.keyframe_manager.fps = value
    
    def get_frame_data(self):
        """
        Get the current frame data.
        
        Returns:
            Dictionary of pixel coordinates to colors
        """
        return self.keyframe_manager.get_frame_data()
    
    def get_all_frames(self):
        """
        Get all frames data.
        
        Returns:
            Dictionary of frame index to pixel data
        """
        return self.keyframe_manager.get_all_frames()
    
    def set_all_frames(self, frames_data):
        """
        Set all frames data.
        
        Args:
            frames_data: Dictionary of frame index to pixel data
        """
        self.keyframe_manager.set_all_frames(frames_data)
        self.redraw() 