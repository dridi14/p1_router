#!/usr/bin/env python3

"""
Animation Tool Test Script
This script tests the core functionality of the animation tool.
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our modules
from animation.keyframe import AnimationController
from animation.playback import AnimationPlayer
from core.canvas import AnimationCanvas
from ui.timeline_widget import TimelineWidget
from ui.main_window import MainWindow


def test_animation_controller():
    """Test the AnimationController class."""
    print("Testing AnimationController...")
    
    controller = AnimationController()
    
    # Test adding keyframes
    controller.add_keyframe("test_property", 0, "value1")
    controller.add_keyframe("test_property", 10, "value2")
    
    # Test getting values
    assert controller.get_value("test_property", 0) == "value1"
    assert controller.get_value("test_property", 10) == "value2"
    assert controller.get_value("test_property", 5) == "value1"  # Should return value1 due to string interpolation
    
    # Test frame navigation
    controller.set_frame(5)
    assert controller.current_frame == 5
    
    controller.next_frame()
    assert controller.current_frame == 6
    
    controller.prev_frame()
    assert controller.current_frame == 5
    
    print("AnimationController tests passed!")


def test_animation_player():
    """Test the AnimationPlayer class."""
    print("Testing AnimationPlayer...")
    
    controller = AnimationController()
    update_count = [0]  # Use a list to store the count (mutable)
    
    def update_callback(frame):
        update_count[0] += 1
    
    player = AnimationPlayer(controller, update_callback)
    
    # Create a temporary root window for testing
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    player.set_root(root)
    
    # Test play/pause
    player.play()
    assert player.playing is True
    
    player.pause()
    assert player.playing is False
    
    # Test toggle
    player.toggle_play()
    assert player.playing is True
    
    player.toggle_play()
    assert player.playing is False
    
    # Test stop
    player.play()
    player.stop()
    assert player.playing is False
    assert controller.current_frame == 0
    
    # Clean up
    root.destroy()
    
    print("AnimationPlayer tests passed!")


def test_canvas():
    """Test the AnimationCanvas class."""
    print("Testing AnimationCanvas...")
    
    # Create a temporary root window for testing
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    canvas = AnimationCanvas(root, width=400, height=400, grid_size=16)
    
    # Test drawing pixels
    canvas._draw_pixel(0, 0, "#FF0000")
    canvas._draw_pixel(1, 1, "#00FF00")
    canvas._draw_pixel(2, 2, "#0000FF")
    
    # Test getting pixel values
    assert canvas.controller.get_value("pixel_0_0") == "#FF0000"
    assert canvas.controller.get_value("pixel_1_1") == "#00FF00"
    assert canvas.controller.get_value("pixel_2_2") == "#0000FF"
    
    # Test clearing pixels
    canvas._clear_pixel(1, 1)
    assert canvas.controller.get_value("pixel_1_1") is None
    
    # Test zoom
    canvas.set_zoom(2.0)
    assert canvas.zoom_factor == 2.0
    
    # Clean up
    root.destroy()
    
    print("AnimationCanvas tests passed!")


def run_tests():
    """Run all tests."""
    try:
        test_animation_controller()
        test_animation_player()
        test_canvas()
        print("\nAll tests passed successfully!")
        return True
    except Exception as e:
        print(f"\nTest failed: {e}")
        return False


def main():
    """Main entry point."""
    print("Animation Tool Test Script")
    print("=========================")
    
    success = run_tests()
    
    if success:
        print("\nAll tests passed! The animation tool is working correctly.")
        
        # Ask if user wants to launch the tool
        if messagebox.askyesno("Tests Passed", "All tests passed! Would you like to launch the animation tool?"):
            root = tk.Tk()
            app = MainWindow(root)
            root.mainloop()
    else:
        print("\nSome tests failed. Please check the output above for details.")
        messagebox.showerror("Tests Failed", "Some tests failed. Please check the console output for details.")


if __name__ == "__main__":
    main() 