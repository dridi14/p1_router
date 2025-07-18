#!/usr/bin/env python3

"""
KeyframeManager - Manages frames for animation with keyframe support
"""

from typing import Dict, List, Any, Optional, Tuple, Callable

class KeyframeManager:
    """
    Manages frames for animation with keyframe support.
    Handles frame data, navigation, and animation properties.
    """
    
    def __init__(self):
        """Initialize the keyframe manager."""
        # Frame data: {frame_index: {(x, y): color}}
        self.frames = {}
        
        # Current state
        self.current_frame = 0
        self.fps = 12
        self.loop = True
        
        # Callback for frame changes
        self.frame_change_callback = None
        
        # Initialize with an empty first frame
        self.frames[0] = {}
    
    def set_frame_change_callback(self, callback: Callable[[int], None]):
        """
        Set a callback for when the current frame changes.
        
        Args:
            callback: Function to call with the new frame index
        """
        self.frame_change_callback = callback
    
    def set_frame(self, frame_idx: int) -> bool:
        """
        Set the current frame.
        
        Args:
            frame_idx: Frame index to set as current
            
        Returns:
            True if the frame was changed, False otherwise
        """
        # Ensure the frame exists
        if frame_idx not in self.frames:
            return False
        
        # Update current frame
        if self.current_frame != frame_idx:
            self.current_frame = frame_idx
            
            # Call the frame change callback
            if self.frame_change_callback:
                self.frame_change_callback(frame_idx)
            
            return True
        
        return False
    
    def add_frame(self) -> int:
        """
        Add a new frame after the current one.
        
        Returns:
            The index of the new frame
        """
        # Find the highest frame index
        max_frame = max(self.frames.keys()) if self.frames else -1
        new_frame_idx = max_frame + 1
        
        # Create a new empty frame
        self.frames[new_frame_idx] = {}
        
        # Set the new frame as the current frame
        self.set_frame(new_frame_idx)
        
        return new_frame_idx
    
    def remove_frame(self) -> bool:
        """
        Remove the current frame.
        
        Returns:
            True if the frame was removed, False otherwise
        """
        # Don't remove if it's the only frame
        if len(self.frames) <= 1:
            return False
        
        # Remove the current frame
        frame_idx = self.current_frame
        del self.frames[frame_idx]
        
        # Reindex frames if needed
        if frame_idx == max(self.frames.keys()) + 1:
            # No need to reindex in this case
            new_frame_idx = max(self.frames.keys())
        else:
            # Reindex all frames after this one
            new_frames = {}
            for idx, data in sorted(self.frames.items()):
                if idx < frame_idx:
                    new_frames[idx] = data
                else:
                    new_frames[idx - 1] = data
            self.frames = new_frames
            new_frame_idx = frame_idx - 1 if frame_idx > 0 else 0
        
        # Set current frame to the previous frame or the first frame
        self.set_frame(new_frame_idx)
        
        return True
    
    def duplicate_frame(self) -> int:
        """
        Duplicate the current frame.
        
        Returns:
            The index of the new frame
        """
        # Find the highest frame index
        max_frame = max(self.frames.keys()) if self.frames else -1
        new_frame_idx = max_frame + 1
        
        # Copy the current frame data
        current_data = self.frames.get(self.current_frame, {})
        self.frames[new_frame_idx] = {coord: color for coord, color in current_data.items()}
        
        # Set the new frame as the current frame
        self.set_frame(new_frame_idx)
        
        return new_frame_idx
    
    def next_frame(self) -> bool:
        """
        Go to the next frame.
        
        Returns:
            True if moved to the next frame, False if already at the last frame
        """
        # Find the next frame index
        frame_indices = sorted(self.frames.keys())
        current_idx = frame_indices.index(self.current_frame)
        
        if current_idx < len(frame_indices) - 1:
            # Move to the next frame
            next_frame = frame_indices[current_idx + 1]
            return self.set_frame(next_frame)
        elif self.loop and frame_indices:
            # Loop back to the first frame
            return self.set_frame(frame_indices[0])
        
        return False
    
    def prev_frame(self) -> bool:
        """
        Go to the previous frame.
        
        Returns:
            True if moved to the previous frame, False if already at the first frame
        """
        # Find the previous frame index
        frame_indices = sorted(self.frames.keys())
        current_idx = frame_indices.index(self.current_frame)
        
        if current_idx > 0:
            # Move to the previous frame
            prev_frame = frame_indices[current_idx - 1]
            return self.set_frame(prev_frame)
        elif self.loop and frame_indices:
            # Loop back to the last frame
            return self.set_frame(frame_indices[-1])
        
        return False
    
    def set_pixel(self, x: int, y: int, color: str):
        """
        Set a pixel in the current frame.
        
        Args:
            x: X coordinate
            y: Y coordinate
            color: Color in hex format (#RRGGBB)
        """
        # Ensure the current frame exists
        if self.current_frame not in self.frames:
            self.frames[self.current_frame] = {}
        
        # Set the pixel color
        self.frames[self.current_frame][(x, y)] = color
    
    def clear_pixel(self, x: int, y: int):
        """
        Clear a pixel in the current frame.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        # If the coordinate exists in the current frame, remove it
        if self.current_frame in self.frames and (x, y) in self.frames[self.current_frame]:
            del self.frames[self.current_frame][(x, y)]
    
    def get_frame_data(self) -> Dict[Tuple[int, int], str]:
        """
        Get the pixel data for the current frame.
        
        Returns:
            Dictionary mapping (x, y) coordinates to color values
        """
        return self.frames.get(self.current_frame, {})
    
    def clear_frame(self):
        """Clear all pixels from the current frame."""
        self.frames[self.current_frame] = {}
    
    def get_all_frames(self) -> Dict[int, Dict[Tuple[int, int], str]]:
        """
        Get all frame data.
        
        Returns:
            Dictionary mapping frame indices to frame data dictionaries
        """
        return self.frames
    
    def set_all_frames(self, frames_data: Dict[int, Dict[Tuple[int, int], str]]):
        """
        Set all frame data.
        
        Args:
            frames_data: Dictionary mapping frame indices to frame data dictionaries
        """
        self.frames = frames_data
        
        # Ensure the current frame exists
        if not self.frames:
            self.frames[0] = {}
            self.current_frame = 0
        elif self.current_frame not in self.frames:
            self.current_frame = min(self.frames.keys())
            
            # Call the frame change callback
            if self.frame_change_callback:
                self.frame_change_callback(self.current_frame) 