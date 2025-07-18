#!/usr/bin/env python3

"""
Keyframe Management
Classes for creating, managing and interpolating keyframes.
"""

from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass

from .easing import EASING_FUNCTIONS


@dataclass
class Keyframe:
    """
    A keyframe representing a value at a specific frame.
    """
    frame: int
    value: Any
    easing: str = "linear"  # The easing function name to use


class KeyframeTrack:
    """
    Manages a sequence of keyframes for a single property.
    Handles interpolation between keyframes.
    """
    
    def __init__(self, property_name: str):
        """
        Initialize a keyframe track.
        
        Args:
            property_name: Name of the property being animated
        """
        self.property_name = property_name
        self.keyframes: List[Keyframe] = []
    
    def add_keyframe(self, frame: int, value: Any, easing: str = "linear") -> None:
        """
        Add a keyframe to the track.
        
        Args:
            frame: Frame number
            value: Value at the keyframe
            easing: Easing function name to use for interpolation
        """
        # Create new keyframe
        keyframe = Keyframe(frame, value, easing)
        
        # Find the right position to insert the keyframe
        index = 0
        while index < len(self.keyframes) and self.keyframes[index].frame < frame:
            index += 1
        
        # Check if a keyframe already exists at this frame
        if index < len(self.keyframes) and self.keyframes[index].frame == frame:
            # Replace the keyframe
            self.keyframes[index] = keyframe
        else:
            # Insert the keyframe
            self.keyframes.insert(index, keyframe)
    
    def remove_keyframe(self, frame: int) -> bool:
        """
        Remove a keyframe at the specified frame.
        
        Args:
            frame: Frame number of the keyframe to remove
            
        Returns:
            True if a keyframe was removed, False otherwise
        """
        for i, keyframe in enumerate(self.keyframes):
            if keyframe.frame == frame:
                self.keyframes.pop(i)
                return True
        return False
    
    def get_keyframe(self, frame: int) -> Optional[Keyframe]:
        """
        Get the keyframe at the specified frame.
        
        Args:
            frame: Frame number
            
        Returns:
            The keyframe at the specified frame, or None if not found
        """
        for keyframe in self.keyframes:
            if keyframe.frame == frame:
                return keyframe
        return None
    
    def get_value_at_frame(self, frame: int) -> Any:
        """
        Get the interpolated value at the specified frame.
        
        Args:
            frame: Frame number
            
        Returns:
            The interpolated value at the specified frame
        """
        # If there are no keyframes, return None
        if not self.keyframes:
            return None
        
        # If there's only one keyframe, return its value
        if len(self.keyframes) == 1:
            return self.keyframes[0].value
        
        # If the frame is before the first keyframe, return the first keyframe's value
        if frame <= self.keyframes[0].frame:
            return self.keyframes[0].value
        
        # If the frame is after the last keyframe, return the last keyframe's value
        if frame >= self.keyframes[-1].frame:
            return self.keyframes[-1].value
        
        # Find the keyframes surrounding the frame
        prev_keyframe = None
        next_keyframe = None
        
        for i in range(len(self.keyframes) - 1):
            if self.keyframes[i].frame <= frame < self.keyframes[i + 1].frame:
                prev_keyframe = self.keyframes[i]
                next_keyframe = self.keyframes[i + 1]
                break
        
        # Interpolate between the keyframes
        return self._interpolate(frame, prev_keyframe, next_keyframe)
    
    def _interpolate(self, frame: int, prev_keyframe: Keyframe, next_keyframe: Keyframe) -> Any:
        """
        Interpolate between two keyframes.
        
        Args:
            frame: Current frame number
            prev_keyframe: Previous keyframe
            next_keyframe: Next keyframe
            
        Returns:
            The interpolated value
        """
        # Calculate the progress between the keyframes (0 to 1)
        t = (frame - prev_keyframe.frame) / (next_keyframe.frame - prev_keyframe.frame)
        
        # Apply easing function
        easing_func = EASING_FUNCTIONS.get(prev_keyframe.easing, EASING_FUNCTIONS["linear"])
        t = easing_func(t)
        
        # Handle different value types
        if isinstance(prev_keyframe.value, (int, float)) and isinstance(next_keyframe.value, (int, float)):
            # Numeric interpolation
            return prev_keyframe.value + t * (next_keyframe.value - prev_keyframe.value)
        elif isinstance(prev_keyframe.value, tuple) and isinstance(next_keyframe.value, tuple):
            # Tuple interpolation (e.g., for coordinates, colors)
            if len(prev_keyframe.value) != len(next_keyframe.value):
                return prev_keyframe.value  # Cannot interpolate tuples of different lengths
            
            result = []
            for i in range(len(prev_keyframe.value)):
                if isinstance(prev_keyframe.value[i], (int, float)) and isinstance(next_keyframe.value[i], (int, float)):
                    # Numeric component interpolation
                    result.append(prev_keyframe.value[i] + t * (next_keyframe.value[i] - prev_keyframe.value[i]))
                else:
                    # Non-numeric component, no interpolation
                    result.append(prev_keyframe.value[i])
            return tuple(result)
        elif isinstance(prev_keyframe.value, str) and isinstance(next_keyframe.value, str):
            # String interpolation (for color hex values)
            if prev_keyframe.value.startswith("#") and next_keyframe.value.startswith("#"):
                # Color interpolation
                return self._interpolate_color(prev_keyframe.value, next_keyframe.value, t)
            return prev_keyframe.value if t < 0.5 else next_keyframe.value
        else:
            # Default: no interpolation, just switch at the halfway point
            return prev_keyframe.value if t < 0.5 else next_keyframe.value
    
    def _interpolate_color(self, color1: str, color2: str, t: float) -> str:
        """
        Interpolate between two color hex strings.
        
        Args:
            color1: First color hex string (#RRGGBB)
            color2: Second color hex string (#RRGGBB)
            t: Interpolation factor (0 to 1)
            
        Returns:
            Interpolated color hex string
        """
        # Parse the hex colors
        try:
            r1 = int(color1[1:3], 16)
            g1 = int(color1[3:5], 16)
            b1 = int(color1[5:7], 16)
            
            r2 = int(color2[1:3], 16)
            g2 = int(color2[3:5], 16)
            b2 = int(color2[5:7], 16)
            
            # Interpolate
            r = int(r1 + t * (r2 - r1))
            g = int(g1 + t * (g2 - g1))
            b = int(b1 + t * (b2 - b1))
            
            # Clamp values
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            # Return hex string
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            # Handle invalid colors
            return color1


class AnimationController:
    """
    Manages keyframe tracks for multiple properties and handles animation playback.
    """
    
    def __init__(self):
        """Initialize the animation controller."""
        self.tracks: Dict[str, KeyframeTrack] = {}
        self.current_frame = 0
        self.fps = 12
        self.playing = False
        self.duration = 120  # Default duration in frames
        self.loop = True
    
    def add_keyframe(self, property_name: str, frame: int, value: Any, easing: str = "linear") -> None:
        """
        Add a keyframe for a property.
        
        Args:
            property_name: Name of the property being animated
            frame: Frame number
            value: Value at the keyframe
            easing: Easing function name to use
        """
        # Ensure the track exists
        if property_name not in self.tracks:
            self.tracks[property_name] = KeyframeTrack(property_name)
        
        # Add the keyframe
        self.tracks[property_name].add_keyframe(frame, value, easing)
        
        # Update duration if needed
        if frame > self.duration:
            self.duration = frame
    
    def remove_keyframe(self, property_name: str, frame: int) -> bool:
        """
        Remove a keyframe for a property.
        
        Args:
            property_name: Name of the property
            frame: Frame number
            
        Returns:
            True if a keyframe was removed, False otherwise
        """
        if property_name in self.tracks:
            return self.tracks[property_name].remove_keyframe(frame)
        return False
    
    def get_value(self, property_name: str, frame: Optional[int] = None) -> Any:
        """
        Get the value of a property at a specific frame.
        
        Args:
            property_name: Name of the property
            frame: Frame number, or None to use the current frame
            
        Returns:
            The property value at the specified frame, or None if not found
        """
        if frame is None:
            frame = self.current_frame
        
        if property_name in self.tracks:
            return self.tracks[property_name].get_value_at_frame(frame)
        
        return None
    
    def get_all_values(self, frame: Optional[int] = None) -> Dict[str, Any]:
        """
        Get all property values at a specific frame.
        
        Args:
            frame: Frame number, or None to use the current frame
            
        Returns:
            Dictionary of property name -> value
        """
        if frame is None:
            frame = self.current_frame
            
        values = {}
        for property_name, track in self.tracks.items():
            values[property_name] = track.get_value_at_frame(frame)
        
        return values
    
    def get_all_keyframes(self) -> Dict[str, Dict[int, Keyframe]]:
        """
        Get all keyframes organized by property and frame.
        
        Returns:
            Dictionary of property_name -> {frame -> keyframe}
        """
        keyframes = {}
        for property_name, track in self.tracks.items():
            keyframes[property_name] = {keyframe.frame: keyframe for keyframe in track.keyframes}
        
        return keyframes
    
    def has_keyframe(self, property_name: str, frame: int) -> bool:
        """
        Check if a keyframe exists for a property at a specific frame.
        
        Args:
            property_name: Name of the property
            frame: Frame number
            
        Returns:
            True if a keyframe exists, False otherwise
        """
        if property_name in self.tracks:
            return self.tracks[property_name].get_keyframe(frame) is not None
        return False
    
    def get_keyframe_frames(self) -> Dict[int, List[str]]:
        """
        Get all frames that have keyframes and the properties they affect.
        
        Returns:
            Dictionary of frame -> list of property names
        """
        keyframe_frames = {}
        
        print(f"Tracks in controller: {len(self.tracks)}")
        for property_name, track in self.tracks.items():
            print(f"Track {property_name} has {len(track.keyframes)} keyframes")
            for keyframe in track.keyframes:
                if keyframe.frame not in keyframe_frames:
                    keyframe_frames[keyframe.frame] = []
                keyframe_frames[keyframe.frame].append(property_name)
        
        return keyframe_frames
    
    def next_frame(self) -> int:
        """
        Advance to the next frame.
        
        Returns:
            The new current frame
        """
        self.current_frame += 1
        
        # Handle looping
        if self.current_frame > self.duration:
            if self.loop:
                self.current_frame = 0
            else:
                self.current_frame = self.duration
                self.playing = False
        
        return self.current_frame
    
    def prev_frame(self) -> int:
        """
        Go to the previous frame.
        
        Returns:
            The new current frame
        """
        self.current_frame -= 1
        
        # Handle bounds
        if self.current_frame < 0:
            if self.loop:
                self.current_frame = self.duration
            else:
                self.current_frame = 0
        
        return self.current_frame
    
    def set_frame(self, frame: int) -> int:
        """
        Set the current frame.
        
        Args:
            frame: Frame number
            
        Returns:
            The new current frame
        """
        self.current_frame = max(0, min(frame, self.duration))
        return self.current_frame
    
    def play(self) -> None:
        """Start playback."""
        self.playing = True
    
    def pause(self) -> None:
        """Pause playback."""
        self.playing = False
    
    def stop(self) -> None:
        """Stop playback and reset to frame 0."""
        self.playing = False
        self.current_frame = 0
    
    def toggle_play(self) -> bool:
        """
        Toggle playback state.
        
        Returns:
            The new playing state
        """
        self.playing = not self.playing
        return self.playing
    
    def set_fps(self, fps: int) -> None:
        """
        Set the playback framerate.
        
        Args:
            fps: Frames per second
        """
        self.fps = max(1, fps)
    
    def set_duration(self, duration: int) -> None:
        """
        Set the animation duration.
        
        Args:
            duration: Duration in frames
        """
        self.duration = max(1, duration)
    
    def set_loop(self, loop: bool) -> None:
        """
        Set whether the animation should loop.
        
        Args:
            loop: Whether to loop
        """
        self.loop = loop 