#!/usr/bin/env python3

"""
Animation Playback
Manages real-time animation playback.
"""

import time
import tkinter as tk
from typing import Callable, Optional, Any

from .keyframe import AnimationController


class AnimationPlayer:
    """
    Manages real-time animation playback.
    """
    
    def __init__(self, controller: AnimationController, update_callback: Callable[[int], None]):
        """
        Initialize the animation player.
        
        Args:
            controller: The animation controller
            update_callback: Function to call with current frame when updated
        """
        self.controller = controller
        self.update_callback = update_callback
        
        self.last_frame_time = 0
        self.playing = False
        self.root: Optional[tk.Tk] = None
        self.after_id: Optional[int] = None
    
    def set_root(self, root: tk.Tk) -> None:
        """
        Set the tkinter root for scheduling updates.
        
        Args:
            root: The tkinter root window
        """
        self.root = root
    
    def play(self) -> None:
        """Start animation playback."""
        if self.playing:
            return
        
        if not self.root:
            raise ValueError("Tkinter root not set. Call set_root() before play().")
        
        self.playing = True
        self.controller.playing = True
        self.last_frame_time = time.time()
        self._schedule_next_frame()
    
    def pause(self) -> None:
        """Pause animation playback."""
        self.playing = False
        self.controller.playing = False
        if self.after_id and self.root:
            self.root.after_cancel(self.after_id)
            self.after_id = None
    
    def stop(self) -> None:
        """Stop animation playback and reset to frame 0."""
        self.pause()
        self.controller.current_frame = 0
        self.update_callback(self.controller.current_frame)
    
    def toggle_play(self) -> bool:
        """
        Toggle playback state.
        
        Returns:
            The new playing state
        """
        if self.playing:
            self.pause()
        else:
            self.play()
        return self.playing
    
    def seek(self, frame: int) -> None:
        """
        Seek to a specific frame.
        
        Args:
            frame: Frame number
        """
        self.controller.set_frame(frame)
        self.update_callback(self.controller.current_frame)
    
    def _schedule_next_frame(self) -> None:
        """Schedule the next frame update."""
        if not self.playing or not self.root:
            return
        
        # Calculate time until next frame
        current_time = time.time()
        frame_duration = 1.0 / self.controller.fps
        elapsed = current_time - self.last_frame_time
        
        if elapsed >= frame_duration:
            # Time for a new frame
            self.controller.next_frame()
            self.update_callback(self.controller.current_frame)
            self.last_frame_time = current_time
            
            # If we reached the end and not looping, stop
            if (self.controller.current_frame >= self.controller.duration 
                    and not self.controller.loop):
                self.pause()
                return
        
        # Calculate delay until next frame
        delay = max(1, int((frame_duration - (time.time() - self.last_frame_time)) * 1000))
        self.after_id = self.root.after(delay, self._schedule_next_frame)


class KeyframeEditor:
    """
    Utility class for editing keyframes in the UI.
    """
    
    def __init__(self, controller: AnimationController):
        """
        Initialize the keyframe editor.
        
        Args:
            controller: The animation controller
        """
        self.controller = controller
    
    def add_keyframe(self, property_name: str, value: Any, easing: str = "linear") -> None:
        """
        Add a keyframe at the current frame.
        
        Args:
            property_name: Name of the property
            value: Value at the keyframe
            easing: Easing function name
        """
        self.controller.add_keyframe(
            property_name, 
            self.controller.current_frame, 
            value, 
            easing
        )
    
    def remove_current_keyframe(self, property_name: str) -> bool:
        """
        Remove the keyframe at the current frame.
        
        Args:
            property_name: Name of the property
            
        Returns:
            True if a keyframe was removed, False otherwise
        """
        return self.controller.remove_keyframe(property_name, self.controller.current_frame)
    
    def get_value(self, property_name: str) -> Any:
        """
        Get the current value of a property.
        
        Args:
            property_name: Name of the property
            
        Returns:
            The current value of the property
        """
        return self.controller.get_value(property_name)
    
    def has_keyframe_at_current_frame(self, property_name: str) -> bool:
        """
        Check if there is a keyframe at the current frame.
        
        Args:
            property_name: Name of the property
            
        Returns:
            True if a keyframe exists at the current frame, False otherwise
        """
        return self.controller.has_keyframe(property_name, self.controller.current_frame)
    
    def get_properties_with_keyframes_at_current_frame(self) -> list:
        """
        Get all properties that have keyframes at the current frame.
        
        Returns:
            List of property names
        """
        frame_keyframes = self.controller.get_keyframe_frames()
        return frame_keyframes.get(self.controller.current_frame, []) 