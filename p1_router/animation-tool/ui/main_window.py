#!/usr/bin/env python3

"""
MainWindow - The main UI window for the Animation Tool
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox, simpledialog
import json
import threading
import time
import math
import random
import pickle
from typing import Dict, List, Any, Optional, Tuple

# Import our modules
from core.canvas import AnimationCanvas
from ui.timeline_widget import TimelineWidget
from ui.simple_timeline import SimpleTimeline

# Add parent directory to path to import LED wall modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import LED wall modules
from models.decoder import EntityState
from artnet_sender.sender import create_and_send_dmx_packet
from config.config_loader import load_config_tables


class MainWindow:
    """
    Main window for the Animation Tool application.
    Contains the canvas, tools, timeline, and properties panels.
    """
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the main window.
        
        Args:
            root: The tkinter root window
        """
        self.root = root
        self.root.title("P1 Router Animation Tool")
        self.root.geometry("1200x800")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Application state
        self.project_path = None
        self.is_modified = False
        
        # Set up the UI
        self._setup_ui()
        self._setup_bindings()
        
        # Initialize state
        self._update_title()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Create main container frame
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create menu
        self._setup_menu()
        
        # Top toolbar
        self._setup_toolbar()
        
        # Main content area - split into left panel and right panel
        self.content_paned = ttk.PanedWindow(self.main_container, orient=tk.HORIZONTAL)
        self.content_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left panel - Tools and properties
        self.left_panel = ttk.Frame(self.content_paned, width=200)
        self.content_paned.add(self.left_panel, weight=1)
        
        # Right panel - Canvas and timeline
        self.right_panel = ttk.Frame(self.content_paned)
        self.content_paned.add(self.right_panel, weight=4)
        
        # Set up the left panel (tools and properties)
        self._setup_left_panel()
        
        # Set up the right panel (canvas and timeline)
        self._setup_right_panel()
        
        # Status bar
        self.status_bar = ttk.Frame(self.main_container, relief=tk.SUNKEN, borderwidth=1)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.position_label = ttk.Label(self.status_bar, text="")
        self.position_label.pack(side=tk.RIGHT, padx=5)
    
    def _setup_menu(self):
        """Set up the application menu."""
        self.menu_bar = tk.Menu(self.root)
        
        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="New Project", command=self.new_project, accelerator="Ctrl+N")
        self.file_menu.add_command(label="Open Project", command=self.open_project, accelerator="Ctrl+O")
        self.file_menu.add_command(label="Save Project", command=self.save_project, accelerator="Ctrl+S")
        self.file_menu.add_command(label="Save Project As...", command=self.save_project_as, accelerator="Ctrl+Shift+S")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Export Frames", command=self.export_frames)
        self.file_menu.add_command(label="Export GIF", command=self.export_gif)
        self.file_menu.add_command(label="Export LED Data", command=self.export_led_data)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.on_close)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        
        # Edit menu
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        self.edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Cut", command=self.cut, accelerator="Ctrl+X")
        self.edit_menu.add_command(label="Copy", command=self.copy, accelerator="Ctrl+C")
        self.edit_menu.add_command(label="Paste", command=self.paste, accelerator="Ctrl+V")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Select All", command=self.select_all, accelerator="Ctrl+A")
        self.edit_menu.add_command(label="Deselect", command=self.deselect, accelerator="Esc")
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        
        # View menu
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.show_grid_var = tk.BooleanVar(value=True)
        self.view_menu.add_checkbutton(label="Show Grid", variable=self.show_grid_var, 
                                      command=self.toggle_grid)
        
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="+")
        self.view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="-")
        self.view_menu.add_command(label="Reset Zoom", command=self.reset_zoom, accelerator="0")
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        
        # Animation menu
        self.animation_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.animation_menu.add_command(label="Add Frame", command=self.add_frame, accelerator="Ins")
        self.animation_menu.add_command(label="Delete Frame", command=self.delete_frame, accelerator="Del")
        self.animation_menu.add_command(label="Duplicate Frame", command=self.duplicate_frame, accelerator="Ctrl+D")
        self.animation_menu.add_separator()
        self.animation_menu.add_command(label="Play Animation", command=self.play_animation, accelerator="Space")
        self.animation_menu.add_command(label="Stop Animation", command=self.stop_animation, accelerator="Esc")
        self.menu_bar.add_cascade(label="Animation", menu=self.animation_menu)
        
        # Help menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="About", command=self.show_about)
        self.help_menu.add_command(label="Help", command=self.show_help)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        
        self.root.config(menu=self.menu_bar)
    
    def _setup_toolbar(self):
        """Set up the top toolbar."""
        self.toolbar = ttk.Frame(self.main_container)
        self.toolbar.pack(fill=tk.X, padx=10, pady=5)
        
        # File operations
        ttk.Button(self.toolbar, text="New", command=self.new_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.toolbar, text="Open", command=self.open_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.toolbar, text="Save", command=self.save_project).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Tool selection
        ttk.Button(self.toolbar, text="Brush", command=lambda: self.set_tool("brush")).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.toolbar, text="Eraser", command=lambda: self.set_tool("eraser")).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.toolbar, text="Select", command=lambda: self.set_tool("select")).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.toolbar, text="Shape", command=lambda: self.set_tool("shape")).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Color picker
        self.color_button = tk.Button(
            self.toolbar, 
            bg="#FFFFFF", 
            width=3, 
            command=self.choose_color
        )
        self.color_button.pack(side=tk.LEFT, padx=2)
        
        # Animation controls
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        ttk.Button(self.toolbar, text="▶", width=3, command=self.play_animation).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.toolbar, text="■", width=3, command=self.stop_animation).pack(side=tk.LEFT, padx=2)
        
        # Frame rate control
        ttk.Label(self.toolbar, text="FPS:").pack(side=tk.LEFT, padx=(10, 2))
        self.fps_var = tk.StringVar(value="12")
        fps_spinbox = ttk.Spinbox(self.toolbar, from_=1, to=60, width=5, textvariable=self.fps_var)
        fps_spinbox.pack(side=tk.LEFT)
        
        # Export to LED Wall button - Add this new section
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        self.led_wall_button = ttk.Button(
            self.toolbar, 
            text="Send to LED Wall", 
            command=self.send_to_led_wall,
            style="Accent.TButton"  # Custom style for emphasis
        )
        self.led_wall_button.pack(side=tk.LEFT, padx=10)
        
        # Create custom button style
        style = ttk.Style()
        style.configure("Accent.TButton", background="#ff6600", foreground="white", font=("Arial", 9, "bold"))

    def _setup_left_panel(self):
        """Set up the left panel with tools and properties."""
        # Tool properties panel
        self.tool_properties = ttk.LabelFrame(self.left_panel, text="Tool Properties")
        self.tool_properties.pack(fill=tk.X, expand=False, padx=5, pady=5)
        
        # Brush size control
        brush_frame = ttk.Frame(self.tool_properties)
        brush_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(brush_frame, text="Brush Size:").pack(side=tk.LEFT)
        self.brush_size_var = tk.IntVar(value=1)
        ttk.Spinbox(brush_frame, from_=1, to=20, width=5, textvariable=self.brush_size_var).pack(side=tk.LEFT, padx=5)
        
        # Color picker
        color_frame = ttk.Frame(self.tool_properties)
        color_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(color_frame, text="Color:").pack(side=tk.LEFT)
        self.selected_color_var = tk.StringVar(value="#FFFFFF")
        self.color_display = tk.Button(
            color_frame, 
            bg=self.selected_color_var.get(), 
            width=6, 
            command=self.choose_color
        )
        self.color_display.pack(side=tk.LEFT, padx=5)
        
        # Shape properties panel (initially hidden)
        self.shape_properties = ttk.LabelFrame(self.left_panel, text="Shape Properties")
        
        shape_type_frame = ttk.Frame(self.shape_properties)
        shape_type_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(shape_type_frame, text="Shape:").pack(side=tk.LEFT)
        self.shape_type_var = tk.StringVar(value="rectangle")
        ttk.Combobox(shape_type_frame, values=["rectangle", "circle", "triangle"], 
                    textvariable=self.shape_type_var, state="readonly", width=10).pack(side=tk.LEFT, padx=5)
        
        shape_fill_frame = ttk.Frame(self.shape_properties)
        shape_fill_frame.pack(fill=tk.X, padx=5, pady=5)
        self.shape_fill_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(shape_fill_frame, text="Fill Shape", variable=self.shape_fill_var).pack(side=tk.LEFT)
        
        # Keyframe management panel (make it more compact)
        self.keyframe_panel = ttk.LabelFrame(self.left_panel, text="Frame Management")
        self.keyframe_panel.pack(fill=tk.X, expand=False, padx=5, pady=5)
        
        # Compact layout for frame management
        frame_buttons = ttk.Frame(self.keyframe_panel)
        frame_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(frame_buttons, text="Add Frame", width=12, command=self.add_frame).grid(row=0, column=0, padx=2, pady=2)
        ttk.Button(frame_buttons, text="Delete Frame", width=12, command=self.delete_frame).grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(frame_buttons, text="Duplicate", width=12, command=self.duplicate_frame).grid(row=1, column=0, padx=2, pady=2)
        
        # Add preset shapes panel
        self.preset_panel = ttk.LabelFrame(self.left_panel, text="Preset Shapes")
        self.preset_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create notebook for single-frame vs multi-frame presets
        preset_notebook = ttk.Notebook(self.preset_panel)
        preset_notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Single frame presets tab
        single_frame_tab = ttk.Frame(preset_notebook)
        preset_notebook.add(single_frame_tab, text="Shapes")
        
        # Multi-frame presets tab
        multi_frame_tab = ttk.Frame(preset_notebook)
        preset_notebook.add(multi_frame_tab, text="Animations")
        
        # Custom presets tab
        custom_presets_tab = ttk.Frame(preset_notebook)
        preset_notebook.add(custom_presets_tab, text="Custom")
        
        # Create scrollable canvas for single frame presets
        preset_canvas = tk.Canvas(single_frame_tab, highlightthickness=0)
        preset_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        preset_scrollbar = ttk.Scrollbar(single_frame_tab, orient=tk.VERTICAL, command=preset_canvas.yview)
        preset_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        preset_canvas.configure(yscrollcommand=preset_scrollbar.set)
        
        preset_frame = ttk.Frame(preset_canvas)
        preset_canvas.create_window((0, 0), window=preset_frame, anchor=tk.NW)
        
        # Define the single frame preset buttons
        presets = [
            {"name": "Rectangle", "icon": "⬛", "func": self._add_rectangle_preset},
            {"name": "Circle", "icon": "⚫", "func": self._add_circle_preset},
            {"name": "Diamond", "icon": "◆", "func": self._add_diamond_preset},
            {"name": "Triangle", "icon": "▲", "func": self._add_triangle_preset},
            {"name": "Cross", "icon": "✚", "func": self._add_cross_preset},
            {"name": "X", "icon": "❌", "func": self._add_x_preset},
            {"name": "H. Line", "icon": "—", "func": self._add_horizontal_line_preset},
            {"name": "V. Line", "icon": "|", "func": self._add_vertical_line_preset},
            {"name": "Gradient H", "icon": "🌈", "func": self._add_horizontal_gradient_preset},
            {"name": "Gradient V", "icon": "🌈", "func": self._add_vertical_gradient_preset},
            {"name": "Checkerboard", "icon": "🏁", "func": self._add_checkerboard_preset},
            {"name": "Random Dots", "icon": "⋮⋮", "func": self._add_random_dots_preset},
            {"name": "Star", "icon": "★", "func": self._add_star_preset},
            {"name": "Heart", "icon": "♥", "func": self._add_heart_preset}
        ]
        
        # Add single frame preset buttons to the frame
        for i, preset in enumerate(presets):
            row, col = divmod(i, 2)
            frame = ttk.Frame(preset_frame)
            frame.grid(row=row, column=col, padx=3, pady=3, sticky=tk.W)
            
            btn = ttk.Button(
                frame, 
                text=f"{preset['icon']} {preset['name']}", 
                command=preset['func'],
                width=12
            )
            btn.pack(side=tk.TOP)
        
        # Update scroll region for single frame presets
        def _update_scroll_region(event):
            preset_canvas.configure(scrollregion=preset_canvas.bbox(tk.ALL))
        preset_frame.bind("<Configure>", _update_scroll_region)
        
        # Create scrollable canvas for multi-frame presets
        anim_canvas = tk.Canvas(multi_frame_tab, highlightthickness=0)
        anim_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        anim_scrollbar = ttk.Scrollbar(multi_frame_tab, orient=tk.VERTICAL, command=anim_canvas.yview)
        anim_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        anim_canvas.configure(yscrollcommand=anim_scrollbar.set)
        
        anim_frame = ttk.Frame(anim_canvas)
        anim_canvas.create_window((0, 0), window=anim_frame, anchor=tk.NW)
        
        # Define the multi-frame preset buttons
        anim_presets = [
            {"name": "Ripple", "icon": "◎", "func": self._add_ripple_animation},
            {"name": "Wipe Right", "icon": "▶", "func": self._add_wipe_right_animation},
            {"name": "Wipe Left", "icon": "◀", "func": self._add_wipe_left_animation},
            {"name": "Wipe Down", "icon": "▼", "func": self._add_wipe_down_animation},
            {"name": "Wipe Up", "icon": "▲", "func": self._add_wipe_up_animation},
            {"name": "Pulse", "icon": "❂", "func": self._add_pulse_animation},
            {"name": "Rainbow", "icon": "🌈", "func": self._add_rainbow_animation},
            {"name": "Sparkle", "icon": "✨", "func": self._add_sparkle_animation},
            {"name": "Snake", "icon": "〰️", "func": self._add_snake_animation},
            {"name": "Spin", "icon": "↻", "func": self._add_spin_animation}
        ]
        
        # Add multi-frame preset buttons
        for i, preset in enumerate(anim_presets):
            frame = ttk.Frame(anim_frame)
            frame.pack(fill=tk.X, padx=3, pady=3)
            
            btn = ttk.Button(
                frame, 
                text=f"{preset['icon']} {preset['name']}", 
                command=preset['func'],
                width=20
            )
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Update scroll region for multi-frame presets
        def _update_anim_scroll_region(event):
            anim_canvas.configure(scrollregion=anim_canvas.bbox(tk.ALL))
        anim_frame.bind("<Configure>", _update_anim_scroll_region)
        
        # Add multi-frame option section
        options_frame = ttk.Frame(multi_frame_tab)
        options_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(options_frame, text="Animation Frames:").grid(row=0, column=0, padx=3, pady=3, sticky=tk.W)
        self.anim_frames_var = tk.StringVar(value="10")
        ttk.Spinbox(options_frame, from_=2, to=60, width=6, textvariable=self.anim_frames_var).grid(row=0, column=1, padx=3, pady=3)
        
        # Add append/replace option
        self.anim_mode_var = tk.StringVar(value="replace")
        ttk.Label(options_frame, text="Mode:").grid(row=1, column=0, padx=3, pady=3, sticky=tk.W)
        ttk.Radiobutton(options_frame, text="Replace All", variable=self.anim_mode_var, value="replace").grid(row=1, column=1, padx=3, pady=3, sticky=tk.W)
        ttk.Radiobutton(options_frame, text="Append", variable=self.anim_mode_var, value="append").grid(row=2, column=1, padx=3, pady=3, sticky=tk.W)
        
        # Add transition option
        self.transition_var = tk.BooleanVar(value=True)
        transition_frame = ttk.Frame(options_frame)
        transition_frame.grid(row=3, column=0, columnspan=2, padx=3, pady=3, sticky=tk.W)
        ttk.Checkbutton(transition_frame, text="Create Transition", variable=self.transition_var).pack(side=tk.LEFT)
        ttk.Label(transition_frame, text="Frames:").pack(side=tk.LEFT, padx=(10, 2))
        self.transition_frames_var = tk.StringVar(value="5")
        ttk.Spinbox(transition_frame, from_=1, to=30, width=4, textvariable=self.transition_frames_var).pack(side=tk.LEFT)
        
        # Setup custom presets tab
        custom_canvas = tk.Canvas(custom_presets_tab, highlightthickness=0)
        custom_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        custom_scrollbar = ttk.Scrollbar(custom_presets_tab, orient=tk.VERTICAL, command=custom_canvas.yview)
        custom_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        custom_canvas.configure(yscrollcommand=custom_scrollbar.set)
        
        custom_frame = ttk.Frame(custom_canvas)
        custom_canvas.create_window((0, 0), window=custom_frame, anchor=tk.NW)
        
        # Custom presets container (will be populated when loading presets)
        self.custom_presets_container = ttk.Frame(custom_frame)
        self.custom_presets_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Custom presets buttons
        custom_buttons_frame = ttk.Frame(custom_frame)
        custom_buttons_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(
            custom_buttons_frame, 
            text="Save Current Animation as Preset", 
            command=self.save_animation_preset
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            custom_buttons_frame, 
            text="Refresh Presets", 
            command=self.load_custom_presets
        ).pack(side=tk.LEFT, padx=5)
        
        # Update scroll region for custom presets
        def _update_custom_scroll_region(event):
            custom_canvas.configure(scrollregion=custom_canvas.bbox(tk.ALL))
        custom_frame.bind("<Configure>", _update_custom_scroll_region)
        
        # Load custom presets
        self.custom_presets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "presets")
        os.makedirs(self.custom_presets_dir, exist_ok=True)
        self.load_custom_presets()

    def _setup_right_panel(self):
        """Set up the right panel with canvas and timeline."""
        # Canvas container with scrollbars
        canvas_frame = ttk.Frame(self.right_panel)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas with scrollbars
        canvas_container = ttk.Frame(canvas_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbars for the canvas
        h_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        v_scrollbar = ttk.Scrollbar(canvas_container)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Animation canvas
        self.canvas = AnimationCanvas(
            canvas_container,
            width=800,
            height=600,
            grid_size=16,  # 16x16 grid
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set,
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure scrollbars
        h_scrollbar.config(command=self.canvas.xview)
        v_scrollbar.config(command=self.canvas.yview)
        
        # Timeline widget
        timeline_frame = ttk.Frame(self.right_panel)
        timeline_frame.pack(fill=tk.X, expand=False, padx=5, pady=5)
        
        # Create the SimpleTimeline widget
        self.timeline = SimpleTimeline(timeline_frame, frame_callback=self.on_timeline_frame_change)
        self.timeline.pack(fill=tk.X, expand=True)
        
        # Legacy Timeline widget for compatibility (hidden)
        self.legacy_timeline = TimelineWidget(timeline_frame)
        
        # Set up synchronization between canvas and timeline
        self._setup_canvas_timeline_sync()

    def _setup_canvas_timeline_sync(self):
        """Set up synchronization between canvas and timeline."""
        # Set initial frame count based on canvas
        frames_count = len(self.canvas.frames)
        if frames_count > 0:
            self.timeline.set_frame_count(frames_count)
        
        # Sync current frame
        self.timeline.set_current_frame(self.canvas.current_frame)

    def _setup_bindings(self):
        """Set up key and event bindings."""
        # File operations
        self.root.bind("<Control-n>", lambda e: self.new_project())
        self.root.bind("<Control-o>", lambda e: self.open_project())
        self.root.bind("<Control-s>", lambda e: self.save_project())
        self.root.bind("<Control-S>", lambda e: self.save_project_as())
        
        # Edit operations
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-a>", lambda e: self.select_all())
        self.root.bind("<Escape>", lambda e: self.deselect())
        
        # View operations
        self.root.bind("<plus>", lambda e: self.zoom_in())
        self.root.bind("<minus>", lambda e: self.zoom_out())
        self.root.bind("<0>", lambda e: self.reset_zoom())
        
        # Animation operations
        self.root.bind("<space>", lambda e: self.toggle_animation())
        self.root.bind("<Left>", lambda e: self.prev_frame())
        self.root.bind("<Right>", lambda e: self.next_frame())
        self.root.bind("<Insert>", lambda e: self.add_frame())
        self.root.bind("<Delete>", lambda e: self.delete_frame())
        self.root.bind("<Control-d>", lambda e: self.duplicate_frame())
        
        # Update mouse position display
        self.canvas.bind("<Motion>", self._update_mouse_position)
    
    def _update_title(self):
        """Update the window title based on the current project."""
        title = "P1 Router Animation Tool"
        if self.project_path:
            filename = os.path.basename(self.project_path)
            title += f" - {filename}"
        if self.is_modified:
            title += " *"
        self.root.title(title)
    
    def _update_mouse_position(self, event):
        """Update the status bar with the current mouse position."""
        x, y = self.canvas._screen_to_grid(event.x, event.y)
        self.position_label.config(text=f"Position: ({x}, {y})")
    
    def set_tool(self, tool_name):
        """Set the current drawing tool."""
        self.canvas.set_tool(tool_name)
        self.status_label.config(text=f"Tool: {tool_name.capitalize()}")
        
        # Show/hide shape properties panel based on selected tool
        if tool_name == "shape":
            if not self.shape_properties.winfo_viewable():
                self.shape_properties.pack(fill=tk.X, expand=False, padx=5, pady=5, after=self.tool_properties)
        else:
            if self.shape_properties.winfo_viewable():
                self.shape_properties.pack_forget()
    
    def choose_color(self):
        """Open a color picker dialog and set the selected color."""
        color = colorchooser.askcolor(self.selected_color_var.get(), title="Select Color")[1]
        if color:
            self.selected_color_var.set(color)
            self.color_display.config(bg=color)
            self.color_button.config(bg=color)
            self.canvas.set_color(color)
    
    def on_timeline_frame_change(self, frame_idx):
        """
        Handle frame change events from the timeline.
        
        Args:
            frame_idx: The new frame index
        """
        # Update canvas frame
        self.canvas.set_frame(frame_idx)
        
    def add_frame(self):
        """Add a new frame after the current one."""
        # Add frame in canvas
        new_frame = self.canvas.add_frame()
        
        # Update timeline
        self.timeline.set_frame_count(len(self.canvas.frames))
        self.timeline.set_current_frame(new_frame)
        
        # Update UI
        self._update_title()
        
        return new_frame
        
    def delete_frame(self):
        """Delete the current frame."""
        # Don't delete if it's the only frame
        if len(self.canvas.frames) <= 1:
            messagebox.showinfo("Cannot Delete", "Cannot delete the only frame.")
            return False
        
        # Ask for confirmation
        if messagebox.askyesno("Delete Frame", "Are you sure you want to delete this frame?"):
            # Delete the frame
            result = self.canvas.remove_frame()
            
            # Update timeline
            if result:
                self.timeline.set_frame_count(len(self.canvas.frames))
                self.timeline.set_current_frame(self.canvas.current_frame)
                
                # Update UI
                self._update_title()
            
            return result
        
        return False
        
    def duplicate_frame(self):
        """Duplicate the current frame."""
        # Duplicate frame in canvas
        new_frame = self.canvas.duplicate_frame()
        
        # Update timeline
        self.timeline.set_frame_count(len(self.canvas.frames))
        self.timeline.set_current_frame(new_frame)
        
        # Update UI
        self._update_title()
        
        return new_frame
        
    def prev_frame(self):
        """Go to the previous frame."""
        result = self.canvas.prev_frame()
        if result:
            self.timeline.set_current_frame(self.canvas.current_frame)
        return result
        
    def next_frame(self):
        """Go to the next frame."""
        result = self.canvas.next_frame()
        if result:
            self.timeline.set_current_frame(self.canvas.current_frame)
        return result
        
    def play_animation(self):
        """Start animation playback."""
        self.canvas.play_animation()
        self.timeline.play()
        
    def stop_animation(self):
        """Stop animation playback."""
        self.canvas.stop_animation()
        self.timeline.stop()
        
    def toggle_animation(self):
        """Toggle animation playback on/off."""
        if self.canvas.is_playing:
            self.stop_animation()
        else:
            self.play_animation()
    
    def show_about(self):
        """Show the about dialog."""
        messagebox.showinfo(
            "About P1 Router Animation Tool",
            "P1 Router Animation Tool v1.0\n"
            "A tool for creating LED wall animations.\n\n"
            "© 2025 P1 Router Team"
        )
    
    def show_help(self):
        """Show the help dialog."""
        messagebox.showinfo(
            "Help",
            "Keyboard shortcuts:\n"
            "Ctrl+N: New project\n"
            "Ctrl+O: Open project\n"
            "Ctrl+S: Save project\n"
            "Ctrl+Shift+S: Save project as\n\n"
            "B: Brush tool\n"
            "E: Eraser tool\n"
            "S: Selection tool\n"
            "G: Toggle grid\n\n"
            "Left/Right: Previous/Next frame\n"
            "Space: Play/Pause animation\n"
        )
    
    def on_close(self):
        """Handle window close event."""
        if self.is_modified:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "There are unsaved changes. Do you want to save before closing?"
            )
            
            if response is None:  # Cancel
                return
            elif response:  # Yes
                if not self.save_project():
                    return  # Don't close if save failed
        
        self.root.destroy() 

    def _on_frame_entry(self, event):
        """Handle manual frame number entry."""
        try:
            frame = int(self.frame_var.get()) - 1  # Convert from 1-indexed display to 0-indexed internal
            max_frame = max(self.canvas.frames.keys()) if self.canvas.frames else 0
            
            # Ensure frame is within valid range
            frame = max(0, min(frame, max_frame))
            
            # Set the current frame
            self.canvas.set_frame(frame)
            
            # Update UI
            self.frame_var.set(str(frame + 1))  # 1-indexed for display
            self.status_label.config(text=f"Frame {frame + 1}")
        except ValueError:
            # Revert to current frame if invalid
            self.frame_var.set(str(self.canvas.current_frame + 1)) 

    def _update_loop(self):
        """Update the loop setting."""
        self.loop = self.loop_var.get()
    
    def new_project(self):
        """Create a new animation project."""
        if self.is_modified:
            if not messagebox.askyesno("Unsaved Changes", 
                                    "There are unsaved changes. Do you want to continue?"):
                return
        
        # Reset project state
        self.project_path = None
        self.is_modified = False
        
        # Reset canvas
        self.canvas.frames = {0: {}}
        self.canvas.current_frame = 0
        self.canvas.redraw()
        
        # Reset timeline
        self.timeline.set_frame_count(1)
        self.timeline.set_current_frame(0)
        
        # Update UI
        self._update_title()
        self.status_label.config(text="New project created")
    
    def open_project(self):
        """Open an existing animation project."""
        if self.is_modified:
            if not messagebox.askyesno("Unsaved Changes", 
                                    "There are unsaved changes. Do you want to continue?"):
                return
        
        filepath = filedialog.askopenfilename(
            title="Open Animation Project",
            filetypes=[("LED Animation Files", "*.ledanim"), ("All Files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'r') as f:
                project_data = json.load(f)
            
            # Convert string keys (from JSON) to integer keys for frames
            frames = {}
            for frame_idx_str, pixel_data in project_data["frames"].items():
                # Convert string representation of coordinates back to tuples
                frame_idx = int(frame_idx_str)
                frames[frame_idx] = {}
                
                for pos_str, color in pixel_data.items():
                    # Parse string representation of coordinates
                    try:
                        x, y = map(int, pos_str.split(","))
                        frames[frame_idx][(x, y)] = color
                    except (ValueError, TypeError):
                        # Skip invalid coordinates
                        continue
            
            # Update canvas properties
            self.canvas.fps = project_data.get("fps", 12)
            
            # Load data into canvas
            self.canvas.set_all_frames(frames)
            self.canvas.set_frame(0)
            
            # Update timeline
            self.timeline.set_frame_count(len(frames))
            self.timeline.set_current_frame(0)
            
            # Update UI
            self.project_path = filepath
            self.is_modified = False
            self._update_title()
            self.status_label.config(text=f"Opened project: {os.path.basename(filepath)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open project: {str(e)}")
    
    def save_project(self):
        """Save the current animation project."""
        if not self.project_path:
            return self.save_project_as()
        
        try:
            # Get frames data from canvas
            frames_data = self.canvas.get_all_frames()
            
            # Convert tuples to strings for JSON serialization
            frames_json = {}
            for frame_idx, pixel_data in frames_data.items():
                frames_json[str(frame_idx)] = {f"{x},{y}": color for (x, y), color in pixel_data.items()}
            
            # Create project data structure
            project_data = {
                "version": "1.0",
                "size": {
                    "width": self.canvas.grid_size,
                    "height": self.canvas.grid_size
                },
                "fps": self.canvas.fps,
                "frames": frames_json
            }
            
            # Save to file
            with open(self.project_path, 'w') as f:
                json.dump(project_data, f, indent=2)
                
            self.is_modified = False
            self._update_title()
            self.status_label.config(text=f"Project saved: {os.path.basename(self.project_path)}")
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save project: {str(e)}")
            return False
    
    def save_project_as(self):
        """Save the current animation project with a new name."""
        filepath = filedialog.asksaveasfilename(
            title="Save Animation Project",
            defaultextension=".ledanim",
            filetypes=[("LED Animation Files", "*.ledanim"), ("All Files", "*.*")]
        )
        
        if not filepath:
            return False
        
        self.project_path = filepath
        return self.save_project()
    
    def export_frames(self):
        """Export animation frames as PNG images."""
        messagebox.showinfo("Not Implemented", 
                          "Frame export will be implemented in a future version.")
    
    def export_gif(self):
        """Export animation as an animated GIF."""
        messagebox.showinfo("Not Implemented", 
                          "GIF export will be implemented in a future version.")
    
    def export_led_data(self):
        """Export animation data in LED controller format."""
        messagebox.showinfo("Not Implemented", 
                          "LED data export will be implemented in a future version.")
    
    def undo(self):
        """Undo the last action."""
        # This would be implemented with a proper undo/redo system
        messagebox.showinfo("Not Implemented", 
                          "Undo functionality will be implemented in a future version.")
    
    def redo(self):
        """Redo the last undone action."""
        # This would be implemented with a proper undo/redo system
        messagebox.showinfo("Not Implemented", 
                          "Redo functionality will be implemented in a future version.")
    
    def cut(self):
        """Cut the selected pixels to clipboard."""
        # This would use the canvas selection
        messagebox.showinfo("Not Implemented", 
                          "Cut functionality will be implemented in a future version.")
    
    def copy(self):
        """Copy the selected pixels to clipboard."""
        # This would use the canvas selection
        messagebox.showinfo("Not Implemented", 
                          "Copy functionality will be implemented in a future version.")
    
    def paste(self):
        """Paste pixels from clipboard."""
        # This would paste from clipboard
        messagebox.showinfo("Not Implemented", 
                          "Paste functionality will be implemented in a future version.")
    
    def select_all(self):
        """Select all pixels in the current frame."""
        # This would use the canvas selection
        messagebox.showinfo("Not Implemented", 
                          "Select All functionality will be implemented in a future version.")
    
    def deselect(self):
        """Clear the current selection."""
        # This would use the canvas selection
        messagebox.showinfo("Not Implemented", 
                          "Deselect functionality will be implemented in a future version.")
    
    def toggle_grid(self):
        """Toggle the grid visibility."""
        self.canvas.show_grid = self.show_grid_var.get()
        self.canvas.redraw()
    
    def zoom_in(self):
        """Increase the zoom level."""
        self.canvas.set_zoom(self.canvas.zoom_factor * 1.25)
        self.status_label.config(text=f"Zoom: {int(self.canvas.zoom_factor * 100)}%")
    
    def zoom_out(self):
        """Decrease the zoom level."""
        self.canvas.set_zoom(self.canvas.zoom_factor * 0.8)
        self.status_label.config(text=f"Zoom: {int(self.canvas.zoom_factor * 100)}%")
    
    def reset_zoom(self):
        """Reset zoom to 100%."""
        self.canvas.set_zoom(1.0)
        self.status_label.config(text="Zoom: 100%") 

    def _add_keyframe(self):
        """Add a keyframe at the current frame."""
        messagebox.showinfo("Not Implemented", "Keyframe functionality will be implemented in Phase 2.")
        
    def _remove_keyframe(self):
        """Remove a keyframe at the current frame."""
        messagebox.showinfo("Not Implemented", "Keyframe functionality will be implemented in Phase 2.") 
    
    def send_to_led_wall(self):
        """Send the animation to the LED wall."""
        try:
            # Create a configuration dialog
            config_dialog = tk.Toplevel(self.root)
            config_dialog.title("LED Wall Configuration")
            config_dialog.geometry("400x300")
            config_dialog.transient(self.root)
            config_dialog.grab_set()
            
            # Frame for grid settings
            grid_frame = ttk.LabelFrame(config_dialog, text="Grid Mapping")
            grid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Base Entity ID
            ttk.Label(grid_frame, text="Base Entity ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            base_id_var = tk.StringVar(value="100")
            ttk.Entry(grid_frame, textvariable=base_id_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
            ttk.Label(grid_frame, text="(First entity ID on the wall)").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
            
            # Grid width
            ttk.Label(grid_frame, text="LED Wall Width:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
            width_var = tk.StringVar(value="128")
            ttk.Entry(grid_frame, textvariable=width_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
            ttk.Label(grid_frame, text="(Number of LEDs across)").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
            
            # Grid mapping type
            ttk.Label(grid_frame, text="Mapping Type:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
            mapping_var = tk.StringVar(value="snake")
            ttk.Combobox(grid_frame, textvariable=mapping_var, values=["snake", "linear"], 
                          width=10, state="readonly").grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
            ttk.Label(grid_frame, text="(Snake=zigzag pattern, Linear=row by row)").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
            
            # Animation settings frame
            anim_frame = ttk.LabelFrame(config_dialog, text="Playback Settings")
            anim_frame.pack(fill=tk.X, padx=10, pady=10)
            
            # FPS
            ttk.Label(anim_frame, text="FPS:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            fps_var = tk.StringVar(value=self.fps_var.get())
            ttk.Spinbox(anim_frame, from_=1, to=30, textvariable=fps_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
            
            # Loop
            loop_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(anim_frame, text="Loop Animation", variable=loop_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
            
            # Buttons frame
            buttons_frame = ttk.Frame(config_dialog)
            buttons_frame.pack(fill=tk.X, pady=10)
            
            # Help info label
            ttk.Label(buttons_frame, text="Note: The animation will be mapped to the LED wall\nbased on the configuration above.", 
                     justify=tk.LEFT, foreground="#666666").pack(side=tk.LEFT, padx=10)
            
            # Cancel and Send buttons
            ttk.Button(buttons_frame, text="Cancel", command=config_dialog.destroy).pack(side=tk.RIGHT, padx=5)
            
            # Function to handle the send button
            def on_send():
                try:
                    # Get configuration values
                    base_id = int(base_id_var.get())
                    width = int(width_var.get())
                    mapping_type = mapping_var.get()
                    fps = int(fps_var.get())
                    loop = loop_var.get()
                    
                    # Get animation data
                    frames = self.canvas.get_all_frames()
                    
                    if not frames:
                        messagebox.showerror("Error", "No animation frames to send!")
                        return
                    
                    # Close the dialog
                    config_dialog.destroy()
                    
                    # Start the LED wall playback in a separate thread
                    threading.Thread(
                        target=self._play_animation_on_led_wall,
                        args=(frames, fps, base_id, width, mapping_type, loop),
                        daemon=True
                    ).start()
                    
                    # Show a status message
                    self.status_label.config(text="Sending animation to LED wall...")
                    
                except ValueError as e:
                    messagebox.showerror("Invalid Input", f"Please enter valid numbers for all fields: {str(e)}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to send animation to LED wall: {str(e)}")
            
            ttk.Button(buttons_frame, text="Send to LED Wall", command=on_send).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send animation to LED wall: {str(e)}")
    
    def _play_animation_on_led_wall(self, frames, fps, base_id=100, wall_width=128, mapping_type="snake", loop=True):
        """
        Play the animation on the LED wall.
        
        Args:
            frames: Dictionary of frame index to pixel data
            fps: Frames per second
            base_id: The first entity ID on the wall
            wall_width: Width of the LED wall in LEDs
            mapping_type: Type of mapping from grid to IDs ("snake" or "linear")
            loop: Whether to loop the animation
        """
        try:
            # Load configuration
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                      "config", "config.json")
            
            entity_table, universe_table, channel_mapping_table = load_config_tables(config_path)
            
            # Define a function to map grid coordinates to entity IDs based on the mapping type
            def map_to_entity_id(x, y):
                if mapping_type == "linear":
                    # Simple row-by-row mapping
                    return base_id + y * wall_width + x
                else:  # "snake" mapping (zigzag)
                    if y % 2 == 0:
                        # Even rows go left to right
                        return base_id + y * wall_width + x
                    else:
                        # Odd rows go right to left
                        return base_id + y * wall_width + (wall_width - 1 - x)
            
            # Convert animation frames to EntityState objects
            frame_indices = sorted(frames.keys())
            is_playing = True
            
            # Create a more detailed control window with status information
            control_window = tk.Toplevel(self.root)
            control_window.title("LED Wall Playback Control")
            control_window.geometry("500x350")
            control_window.transient(self.root)
            control_window.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable window close button
            
            # Add window icon if available
            try:
                icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "icon.ico")
                if os.path.exists(icon_path):
                    control_window.iconbitmap(icon_path)
            except:
                pass  # Ignore icon errors
            
            # Animation control frame
            control_frame = ttk.Frame(control_window)
            control_frame.pack(fill=tk.X, padx=20, pady=20)
            
            # Title
            title_label = ttk.Label(
                control_frame, 
                text="Animation Playback on LED Wall",
                font=("Arial", 14, "bold")
            )
            title_label.pack(pady=(0, 15))
            
            # Control buttons
            button_frame = ttk.Frame(control_frame)
            button_frame.pack(fill=tk.X, pady=5)
            
            # Stop button
            stop_button = ttk.Button(
                button_frame, 
                text="Stop Playback", 
                command=lambda: self._stop_playback_and_clear(is_playing, entity_table, universe_table, channel_mapping_table, control_window)
            )
            stop_button.pack(side=tk.LEFT, padx=5)
            
            # Clear wall button
            clear_button = ttk.Button(
                button_frame, 
                text="Clear LEDs", 
                command=lambda: self._clear_led_wall(entity_table, universe_table, channel_mapping_table)
            )
            clear_button.pack(side=tk.LEFT, padx=5)
            
            # Animation info frame
            info_frame = ttk.LabelFrame(control_window, text="Animation Information")
            info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
            
            # Info grid
            info_grid = ttk.Frame(info_frame)
            info_grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Create labels for status information
            ttk.Label(info_grid, text="Animation Status:", anchor=tk.W).grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
            status_var = tk.StringVar(value="Playing")
            ttk.Label(info_grid, textvariable=status_var, anchor=tk.W).grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)
            
            ttk.Label(info_grid, text="Current Frame:", anchor=tk.W).grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
            frame_var = tk.StringVar(value="0/0")
            ttk.Label(info_grid, textvariable=frame_var, anchor=tk.W).grid(row=1, column=1, sticky=tk.W, padx=5, pady=3)
            
            ttk.Label(info_grid, text="Playback Speed:", anchor=tk.W).grid(row=2, column=0, sticky=tk.W, padx=5, pady=3)
            ttk.Label(info_grid, text=f"{fps} FPS ({1000/fps:.2f}ms per frame)", anchor=tk.W).grid(row=2, column=1, sticky=tk.W, padx=5, pady=3)
            
            ttk.Label(info_grid, text="Looping:", anchor=tk.W).grid(row=3, column=0, sticky=tk.W, padx=5, pady=3)
            ttk.Label(info_grid, text="Enabled" if loop else "Disabled", anchor=tk.W).grid(row=3, column=1, sticky=tk.W, padx=5, pady=3)
            
            ttk.Separator(info_grid, orient=tk.HORIZONTAL).grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=8)
            
            ttk.Label(info_grid, text="Grid Mapping:", anchor=tk.W).grid(row=5, column=0, sticky=tk.W, padx=5, pady=3)
            ttk.Label(info_grid, text=f"Type: {mapping_type.capitalize()}, Wall Width: {wall_width}", anchor=tk.W).grid(row=5, column=1, sticky=tk.W, padx=5, pady=3)
            
            ttk.Label(info_grid, text="Base Entity ID:", anchor=tk.W).grid(row=6, column=0, sticky=tk.W, padx=5, pady=3)
            ttk.Label(info_grid, text=str(base_id), anchor=tk.W).grid(row=6, column=1, sticky=tk.W, padx=5, pady=3)
            
            # Wall connection info
            connection_frame = ttk.LabelFrame(control_window, text="Wall Connection")
            connection_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
            
            # Get universes being used
            universe_ips = []
            for universe_id, ip in universe_table.items():
                if universe_id in entity_table.values():
                    universe_ips.append((universe_id, ip))
            
            # Sort by universe ID
            universe_ips.sort()
            
            # Create connection info grid
            connection_grid = ttk.Frame(connection_frame)
            connection_grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Headers
            ttk.Label(connection_grid, text="Universe", font=("Arial", 9, "bold")).grid(row=0, column=0, padx=5, pady=3)
            ttk.Label(connection_grid, text="IP Address", font=("Arial", 9, "bold")).grid(row=0, column=1, padx=5, pady=3)
            ttk.Label(connection_grid, text="Status", font=("Arial", 9, "bold")).grid(row=0, column=2, padx=5, pady=3)
            
            # Status indicators
            status_vars = {}
            
            # Add universe rows (limit to 5 visible rows to avoid making window too large)
            visible_universes = min(len(universe_ips), 5)
            for i in range(visible_universes):
                universe_id, ip = universe_ips[i]
                ttk.Label(connection_grid, text=str(universe_id)).grid(row=i+1, column=0, padx=5, pady=2)
                ttk.Label(connection_grid, text=ip).grid(row=i+1, column=1, padx=5, pady=2)
                
                status_vars[universe_id] = tk.StringVar(value="Ready")
                ttk.Label(connection_grid, textvariable=status_vars[universe_id]).grid(row=i+1, column=2, padx=5, pady=2)
            
            # If there are more universes, show a message
            if len(universe_ips) > 5:
                ttk.Label(connection_grid, text=f"+ {len(universe_ips) - 5} more universes...").grid(row=6, column=0, columnspan=3, padx=5, pady=2)
            
            # Statistics frame
            stats_frame = ttk.Frame(control_window)
            stats_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
            
            # Pixel count
            pixel_count = sum(len(data) for data in frames.values())
            avg_pixel_count = pixel_count / len(frames) if frames else 0
            ttk.Label(stats_frame, text=f"Average Pixels/Frame: {avg_pixel_count:.1f}").pack(side=tk.LEFT)
            
            # Elapsed time and FPS indicator
            elapsed_var = tk.StringVar(value="Elapsed: 0.0s")
            ttk.Label(stats_frame, textvariable=elapsed_var).pack(side=tk.RIGHT)
            
            # Simple interface to stop playback
            def stop_playback():
                nonlocal is_playing
                is_playing = False
                self._clear_led_wall(entity_table, universe_table, channel_mapping_table)
                status_var.set("Stopped")
                
                # Enable window close button
                control_window.protocol("WM_DELETE_WINDOW", control_window.destroy)
            
            # Function to update UI from main thread
            def update_status(text):
                self.status_label.config(text=text)
            
            # Store the start time
            start_time = time.time()
            
            # Play the animation
            frame_idx = 0
            frame_delay = 1.0 / fps
            
            while is_playing and control_window.winfo_exists():
                # Get current frame index in a loop
                current_idx = frame_indices[frame_idx % len(frame_indices)]
                frame_data = frames[current_idx]
                
                # Update frame counter in UI
                frame_var.set(f"{current_idx + 1}/{max(frame_indices) + 1}")
                
                # Update elapsed time
                elapsed = time.time() - start_time
                elapsed_var.set(f"Elapsed: {elapsed:.1f}s")
                
                # Convert grid positions to entity IDs and create EntityState objects
                entities = []
                for (x, y), color in frame_data.items():
                    # Map grid coordinates to entity ID
                    entity_id = map_to_entity_id(x, y)
                    
                    # Only create entities that exist in the config
                    if entity_id in entity_table:
                        # Parse color from hex (e.g., "#FF0000" -> r=255, g=0, b=0)
                        r = int(color[1:3], 16)
                        g = int(color[3:5], 16)
                        b = int(color[5:7], 16)
                        
                        entities.append(EntityState(id=entity_id, r=r, g=g, b=b))
                
                # Group entities by universe
                universe_entities = {}
                for entity in entities:
                    if entity.id in entity_table:
                        universe_id = entity_table[entity.id]["universe"]
                        if universe_id not in universe_entities:
                            universe_entities[universe_id] = []
                        universe_entities[universe_id].append(entity)
                
                # Send data to each universe and update status
                for universe_id, universe_entities_list in universe_entities.items():
                    if universe_id in universe_table:
                        ip = universe_table[universe_id]
                        try:
                            create_and_send_dmx_packet(
                                universe_entities_list, 
                                ip, 
                                universe_id, 
                                channel_mapping_table
                            )
                            # Update status if this universe is in the UI
                            if universe_id in status_vars:
                                status_vars[universe_id].set(f"Sent {len(universe_entities_list)} LEDs")
                        except Exception as e:
                            if universe_id in status_vars:
                                status_vars[universe_id].set(f"Error: {str(e)}")
                
                # Update status
                self.root.after(0, update_status, f"Playing frame {current_idx + 1}/{max(frame_indices) + 1} to LED wall")
                
                # Wait for next frame
                time.sleep(frame_delay)
                
                # Move to next frame
                frame_idx += 1
                
                # Check if we should continue looping
                if not loop and frame_idx >= len(frame_indices):
                    break
            
            # Clear all LEDs after playback
            self._clear_led_wall(entity_table, universe_table, channel_mapping_table)
            self.root.after(0, update_status, "Animation playback completed")
            
            # Update status if window still exists
            if control_window.winfo_exists():
                status_var.set("Completed")
                # Enable window close button
                control_window.protocol("WM_DELETE_WINDOW", control_window.destroy)
                
        except Exception as e:
            # Update status on error
            self.root.after(0, lambda: messagebox.showerror("Playback Error", f"Error during playback: {str(e)}"))
            self.root.after(0, lambda: self.status_label.config(text=f"Playback error: {str(e)}"))
    
    def _stop_playback_and_clear(self, is_playing_ref, entity_table, universe_table, channel_mapping_table, control_window):
        """Stop playback, clear LEDs and close the window."""
        # Set is_playing to False (pass by reference doesn't work for booleans, this is just for UI updates)
        is_playing_ref = False
        
        # Clear the wall
        self._clear_led_wall(entity_table, universe_table, channel_mapping_table)
        
        # Update UI
        self.status_label.config(text="Playback stopped, LEDs cleared")
        
        # Close window
        control_window.destroy()
    
    def _clear_led_wall(self, entity_table, universe_table, channel_mapping_table):
        """
        Clear all LEDs on the wall by setting them to black.
        
        Args:
            entity_table: Dictionary mapping entity IDs to their properties
            universe_table: Dictionary mapping universe IDs to IP addresses
            channel_mapping_table: Dictionary mapping entity IDs to DMX start channels
        """
        try:
            # Group entities by universe
            universe_entities = {}
            
            for entity_id, properties in entity_table.items():
                universe_id = properties["universe"]
                
                if universe_id not in universe_entities:
                    universe_entities[universe_id] = []
                
                # Create entity with black color (all zeros)
                entity = EntityState(id=entity_id, r=0, g=0, b=0)
                universe_entities[universe_id].append(entity)
            
            # Send black to all universes
            for universe_id, entities in universe_entities.items():
                if universe_id in universe_table:
                    ip = universe_table[universe_id]
                    create_and_send_dmx_packet(
                        entities,
                        ip,
                        universe_id,
                        channel_mapping_table
                    )
            
            print("All LEDs cleared")
            
        except Exception as e:
            print(f"Error clearing LEDs: {str(e)}") 

    # Preset shape functions
    def _add_preset_shape(self, shape_pixels):
        """
        Add a preset shape to the current frame.
        
        Args:
            shape_pixels: Dictionary mapping (x, y) coordinates to color values
        """
        if not shape_pixels:
            return
            
        # Get center of canvas for positioning
        center_x = self.canvas.grid_size // 2
        center_y = self.canvas.grid_size // 2
        
        # Add pixels to the current frame
        for (x, y), color in shape_pixels.items():
            # Use current color if specified
            if color == "current":
                color = self.selected_color_var.get()
                
            # Draw the pixel
            self.canvas._draw_pixel(x, y, color)
        
        # Mark as modified
        self.is_modified = True
    
    def _add_rectangle_preset(self):
        """Add a rectangle preset to the current frame."""
        # Get current color
        color = self.selected_color_var.get()
        
        # Define rectangle
        rect_width, rect_height = 10, 6
        center_x = self.canvas.grid_size // 2
        center_y = self.canvas.grid_size // 2
        
        # Calculate corners
        start_x = center_x - rect_width // 2
        start_y = center_y - rect_height // 2
        end_x = start_x + rect_width - 1
        end_y = start_y + rect_height - 1
        
        # Create pixel map
        pixels = {}
        
        # Draw top and bottom edges
        for x in range(start_x, end_x + 1):
            pixels[(x, start_y)] = color
            pixels[(x, end_y)] = color
        
        # Draw left and right edges
        for y in range(start_y + 1, end_y):
            pixels[(start_x, y)] = color
            pixels[(end_x, y)] = color
        
        self._add_preset_shape(pixels)
    
    def _add_circle_preset(self):
        """Add a circle preset to the current frame."""
        # Get current color
        color = self.selected_color_var.get()
        
        # Define circle
        radius = 5
        center_x = self.canvas.grid_size // 2
        center_y = self.canvas.grid_size // 2
        
        # Create pixel map using Bresenham's circle algorithm
        pixels = {}
        
        # Draw the circle outline
        for theta in range(0, 360, 5):  # Iterate around the circle in 5 degree increments
            x = int(center_x + radius * math.cos(math.radians(theta)))
            y = int(center_y + radius * math.sin(math.radians(theta)))
            pixels[(x, y)] = color
        
        self._add_preset_shape(pixels)
    
    def _add_diamond_preset(self):
        """Add a diamond preset to the current frame."""
        # Get current color
        color = self.selected_color_var.get()
        
        # Define diamond
        size = 6
        center_x = self.canvas.grid_size // 2
        center_y = self.canvas.grid_size // 2
        
        # Create pixel map
        pixels = {}
        
        # Draw the diamond
        for i in range(size + 1):
            # Top half
            pixels[(center_x - i, center_y - (size - i))] = color
            pixels[(center_x + i, center_y - (size - i))] = color
            
            # Bottom half
            pixels[(center_x - i, center_y + (size - i))] = color
            pixels[(center_x + i, center_y + (size - i))] = color
        
        self._add_preset_shape(pixels)
    
    def _add_triangle_preset(self):
        """Add a triangle preset to the current frame."""
        # Get current color
        color = self.selected_color_var.get()
        
        # Define triangle
        size = 8
        center_x = self.canvas.grid_size // 2
        center_y = self.canvas.grid_size // 2
        
        # Define triangle vertices
        top_x, top_y = center_x, center_y - size
        left_x, left_y = center_x - size, center_y + size
        right_x, right_y = center_x + size, center_y + size
        
        # Create pixel map
        pixels = {}
        
        # Draw lines between the vertices using Bresenham's algorithm
        # Top to left
        self._draw_line_pixels(pixels, top_x, top_y, left_x, left_y, color)
        # Top to right
        self._draw_line_pixels(pixels, top_x, top_y, right_x, right_y, color)
        # Left to right
        self._draw_line_pixels(pixels, left_x, left_y, right_x, right_y, color)
        
        self._add_preset_shape(pixels)
    
    def _draw_line_pixels(self, pixels_dict, x1, y1, x2, y2, color):
        """
        Draw a line using Bresenham's algorithm and add to pixels dictionary.
        
        Args:
            pixels_dict: Dictionary to add pixels to
            x1, y1: Start coordinates
            x2, y2: End coordinates
            color: Color to use for the line
        """
        # Bresenham's line algorithm
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        while x1 != x2 or y1 != y2:
            pixels_dict[(x1, y1)] = color
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
                
        # Add the last point
        pixels_dict[(x1, y1)] = color
    
    def _add_cross_preset(self):
        """Add a cross preset to the current frame."""
        # Get current color
        color = self.selected_color_var.get()
        
        # Define cross
        size = 7
        center_x = self.canvas.grid_size // 2
        center_y = self.canvas.grid_size // 2
        
        # Create pixel map
        pixels = {}
        
        # Draw horizontal line
        for x in range(center_x - size, center_x + size + 1):
            pixels[(x, center_y)] = color
        
        # Draw vertical line
        for y in range(center_y - size, center_y + size + 1):
            pixels[(center_x, y)] = color
        
        self._add_preset_shape(pixels)
    
    def _add_x_preset(self):
        """Add an X preset to the current frame."""
        # Get current color
        color = self.selected_color_var.get()
        
        # Define X
        size = 6
        center_x = self.canvas.grid_size // 2
        center_y = self.canvas.grid_size // 2
        
        # Create pixel map
        pixels = {}
        
        # Draw diagonal lines
        for i in range(-size, size + 1):
            pixels[(center_x + i, center_y + i)] = color
            pixels[(center_x + i, center_y - i)] = color
        
        self._add_preset_shape(pixels)
    
    def _add_horizontal_line_preset(self):
        """Add a horizontal line preset to the current frame."""
        # Get current color
        color = self.selected_color_var.get()
        
        # Define line
        length = 20
        center_x = self.canvas.grid_size // 2
        center_y = self.canvas.grid_size // 2
        
        # Create pixel map
        pixels = {}
        
        # Draw horizontal line
        for x in range(center_x - length // 2, center_x + length // 2 + 1):
            pixels[(x, center_y)] = color
        
        self._add_preset_shape(pixels)
    
    def _add_vertical_line_preset(self):
        """Add a vertical line preset to the current frame."""
        # Get current color
        color = self.selected_color_var.get()
        
        # Define line
        length = 20
        center_x = self.canvas.grid_size // 2
        center_y = self.canvas.grid_size // 2
        
        # Create pixel map
        pixels = {}
        
        # Draw vertical line
        for y in range(center_y - length // 2, center_y + length // 2 + 1):
            pixels[(center_x, y)] = color
        
        self._add_preset_shape(pixels)
    
    def _add_horizontal_gradient_preset(self):
        """Add a horizontal gradient preset to the current frame."""
        # Get current color as base
        base_color = self.selected_color_var.get()
        
        # Parse RGB values
        r = int(base_color[1:3], 16)
        g = int(base_color[3:5], 16)
        b = int(base_color[5:7], 16)
        
        # Define gradient
        width = 20
        height = 8
        center_x = self.canvas.grid_size // 2
        center_y = self.canvas.grid_size // 2
        
        # Create pixel map
        pixels = {}
        
        # Draw gradient rectangle
        for x in range(width):
            # Calculate color for this column
            ratio = x / (width - 1)
            if ratio <= 0.5:
                # Start to middle: black to base color
                factor = ratio * 2  # 0 to 1
                col_r = int(r * factor)
                col_g = int(g * factor)
                col_b = int(b * factor)
            else:
                # Middle to end: base color to white
                factor = (ratio - 0.5) * 2  # 0 to 1
                col_r = int(r + (255 - r) * factor)
                col_g = int(g + (255 - g) * factor)
                col_b = int(b + (255 - b) * factor)
            
            # Format as hex color
            col_color = f"#{col_r:02x}{col_g:02x}{col_b:02x}"
            
            # Fill column
            for y in range(height):
                pixels[(center_x - width // 2 + x, center_y - height // 2 + y)] = col_color
        
        self._add_preset_shape(pixels)
    
    def _add_vertical_gradient_preset(self):
        """Add a vertical gradient preset to the current frame."""
        # Get current color as base
        base_color = self.selected_color_var.get()
        
        # Parse RGB values
        r = int(base_color[1:3], 16)
        g = int(base_color[3:5], 16)
        b = int(base_color[5:7], 16)
        
        # Define gradient
        width = 8
        height = 20
        center_x = self.canvas.grid_size // 2
        center_y = self.canvas.grid_size // 2
        
        # Create pixel map
        pixels = {}
        
        # Draw gradient rectangle
        for y in range(height):
            # Calculate color for this row
            ratio = y / (height - 1)
            if ratio <= 0.5:
                # Start to middle: black to base color
                factor = ratio * 2  # 0 to 1
                col_r = int(r * factor)
                col_g = int(g * factor)
                col_b = int(b * factor)
            else:
                # Middle to end: base color to white
                factor = (ratio - 0.5) * 2  # 0 to 1
                col_r = int(r + (255 - r) * factor)
                col_g = int(g + (255 - g) * factor)
                col_b = int(b + (255 - b) * factor)
            
            # Format as hex color
            col_color = f"#{col_r:02x}{col_g:02x}{col_b:02x}"
            
            # Fill row
            for x in range(width):
                pixels[(center_x - width // 2 + x, center_y - height // 2 + y)] = col_color
        
        self._add_preset_shape(pixels)
    
    def _add_checkerboard_preset(self):
        """Add a checkerboard preset to the current frame."""
        # Get current color
        color = self.selected_color_var.get()
        
        # Define checkerboard
        size = 8  # Total size of the board
        cell_size = 2  # Size of each cell
        center_x = self.canvas.grid_size // 2
        center_y = self.canvas.grid_size // 2
        
        # Create pixel map
        pixels = {}
        
        # Draw checkerboard
        for row in range(size):
            for col in range(size):
                # Only color alternating cells
                if (row + col) % 2 == 0:
                    # Fill this cell
                    for dx in range(cell_size):
                        for dy in range(cell_size):
                            x = center_x - (size * cell_size) // 2 + col * cell_size + dx
                            y = center_y - (size * cell_size) // 2 + row * cell_size + dy
                            pixels[(x, y)] = color
        
        self._add_preset_shape(pixels)
    
    def _add_random_dots_preset(self):
        """Add random dots preset to the current frame."""
        # Get current color
        color = self.selected_color_var.get()
        
        # Define random dots area
        width = 20
        height = 20
        center_x = self.canvas.grid_size // 2
        center_y = self.canvas.grid_size // 2
        
        # Create pixel map
        pixels = {}
        
        # Generate random dots (about 30% density)
        for _ in range(width * height // 3):
            x = center_x - width // 2 + random.randint(0, width - 1)
            y = center_y - height // 2 + random.randint(0, height - 1)
            pixels[(x, y)] = color
        
        self._add_preset_shape(pixels)
    
    def _add_star_preset(self):
        """Add a star preset to the current frame."""
        # Get current color
        color = self.selected_color_var.get()
        
        # Define star
        outer_radius = 7
        inner_radius = 3
        points = 5
        center_x = self.canvas.grid_size // 2
        center_y = self.canvas.grid_size // 2
        
        # Create pixel map
        pixels = {}
        
        # Calculate star points
        vertices = []
        for i in range(points * 2):
            # Alternate between outer and inner radius
            radius = outer_radius if i % 2 == 0 else inner_radius
            angle = math.pi * i / points
            x = center_x + int(radius * math.sin(angle))
            y = center_y + int(radius * math.cos(angle))
            vertices.append((x, y))
        
        # Connect the vertices to form the star
        for i in range(len(vertices)):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % len(vertices)]
            self._draw_line_pixels(pixels, x1, y1, x2, y2, color)
        
        self._add_preset_shape(pixels)
    
    def _add_heart_preset(self):
        """Add a heart preset to the current frame."""
        # Get current color
        color = self.selected_color_var.get()
        
        # Define heart
        size = 7
        center_x = self.canvas.grid_size // 2
        center_y = self.canvas.grid_size // 2
        
        # Create pixel map
        pixels = {}
        
        # Define heart shape points
        heart_points = []
        
        # Simple heart outline using a mathematical function
        for t in range(0, 628, 5):  # 0 to 2π in small increments
            t_rad = t / 100.0
            # Heart curve formula
            x = int(size * 16 * math.sin(t_rad) ** 3)
            y = int(size * (13 * math.cos(t_rad) - 5 * math.cos(2*t_rad) - 2 * math.cos(3*t_rad) - math.cos(4*t_rad)))
            
            # Scale and position
            x = center_x + x // 16
            y = center_y - y // 16  # Flip Y to match screen coordinates
            
            heart_points.append((x, y))
        
        # Connect the points to form the heart outline
        for i in range(len(heart_points) - 1):
            x1, y1 = heart_points[i]
            x2, y2 = heart_points[i + 1]
            self._draw_line_pixels(pixels, x1, y1, x2, y2, color)
        
        # Connect last to first
        x1, y1 = heart_points[-1]
        x2, y2 = heart_points[0]
        self._draw_line_pixels(pixels, x1, y1, x2, y2, color)
        
        self._add_preset_shape(pixels) 

    # Multi-frame animation preset functions
    def _add_animation_preset(self, frame_generator, num_frames=None):
        """
        Add a multi-frame animation preset.
        
        Args:
            frame_generator: Function that takes a frame index and returns pixels for that frame
            num_frames: Number of frames to generate, defaults to value in self.anim_frames_var
        """
        try:
            # Get number of frames
            if num_frames is None:
                num_frames = int(self.anim_frames_var.get())
            
            # Validate
            if num_frames < 2:
                messagebox.showwarning("Invalid Input", "Animation must have at least 2 frames.")
                return
            
            # Get animation mode (replace or append)
            anim_mode = self.anim_mode_var.get()
            
            if anim_mode == "replace":
                # Ask for confirmation if the user already has frames
                if len(self.canvas.frames) > 1:
                    if not messagebox.askyesno("Confirm", 
                                            "This will replace your existing animation with the preset.\n\n"
                                            "Do you want to continue?"):
                        return
                
                # Clear existing frames except the first one
                frames_to_remove = sorted([f for f in self.canvas.frames.keys() if f != 0], reverse=True)
                
                # Remove all frames except the first
                for frame in frames_to_remove:
                    self.canvas.set_frame(frame)
                    self.canvas.remove_frame()
                
                # Clear the first frame
                self.canvas.set_frame(0)
                self.canvas.clear_frame()
                
                # Start generating from frame 0
                start_frame_idx = 0
                
                # No transition needed
                add_transition = False
            else:  # append mode
                # Find the highest frame index
                start_frame_idx = max(self.canvas.frames.keys()) + 1 if self.canvas.frames else 0
                
                # Move to the last existing frame
                if self.canvas.frames:
                    last_frame_idx = max(self.canvas.frames.keys())
                    self.canvas.set_frame(last_frame_idx)
                    
                    # Check if we should add a transition
                    add_transition = self.transition_var.get() and last_frame_idx >= 0
                    if add_transition:
                        try:
                            # Get transition frames
                            transition_frames = int(self.transition_frames_var.get())
                            if transition_frames < 1:
                                transition_frames = 5  # Default
                        except ValueError:
                            transition_frames = 5  # Default
                    else:
                        transition_frames = 0
                else:
                    add_transition = False
                    transition_frames = 0
                    
                # If we have a previous animation and need to add a transition
                if add_transition:
                    # Get the last frame data
                    last_frame_data = self.canvas.get_frame_data()
                    
                    # Generate the first frame of the new animation to create transition
                    first_frame_data = frame_generator(0, num_frames)
                    
                    # Create transition frames
                    for t in range(transition_frames):
                        # Create a new frame
                        self.canvas.add_frame()
                        
                        # Calculate blend factor (0 to 1)
                        blend = (t + 1) / (transition_frames + 1)
                        
                        # Create transition frame by blending last frame and first frame
                        transition_frame = self._blend_frames(last_frame_data, first_frame_data, blend)
                        
                        # Add pixels to the frame
                        for (x, y), color in transition_frame.items():
                            self.canvas._draw_pixel(x, y, color)
                    
                    # Update start index to account for transition frames
                    start_frame_idx = max(self.canvas.frames.keys()) + 1
            
            # Generate main animation frames
            for i in range(num_frames):
                frame_idx = start_frame_idx + i
                
                # Add a new frame (except for first frame in replace mode)
                if i > 0 or anim_mode == "append":
                    self.canvas.add_frame()
                
                # Generate pixels for this frame
                pixels = frame_generator(i, num_frames)
                
                # Add pixels to the current frame
                for (x, y), color in pixels.items():
                    self.canvas._draw_pixel(x, y, color)
            
            # Return to the first frame of the sequence
            self.canvas.set_frame(start_frame_idx)
            
            # Update timeline
            self.timeline.set_frame_count(len(self.canvas.frames))
            self.timeline.set_current_frame(start_frame_idx)
            
            # Mark as modified
            self.is_modified = True
            self._update_title()
            
            # Show confirmation
            transition_msg = f" with {transition_frames} transition frames" if add_transition else ""
            if anim_mode == "replace":
                self.status_label.config(text=f"Generated {num_frames} animation frames")
            else:
                self.status_label.config(text=f"Appended {num_frames} animation frames{transition_msg}")
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please enter valid numbers: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate animation: {str(e)}")
    
    def _blend_frames(self, frame1: Dict[Tuple[int, int], str], 
                      frame2: Dict[Tuple[int, int], str], 
                      blend_factor: float) -> Dict[Tuple[int, int], str]:
        """
        Blend two frames to create a transition frame.
        
        Args:
            frame1: First frame pixel data
            frame2: Second frame pixel data
            blend_factor: Blend factor from 0 to 1 (0=first frame, 1=second frame)
            
        Returns:
            Blended frame pixel data
        """
        # Create a new empty frame
        blended_frame = {}
        
        # Get all unique pixel positions
        all_positions = set(list(frame1.keys()) + list(frame2.keys()))
        
        # Blend each pixel
        for pos in all_positions:
            # Get colors from each frame (defaulting to black if not present)
            color1 = frame1.get(pos, "#000000")
            color2 = frame2.get(pos, "#000000")
            
            # Parse colors
            r1 = int(color1[1:3], 16)
            g1 = int(color1[3:5], 16)
            b1 = int(color1[5:7], 16)
            
            r2 = int(color2[1:3], 16)
            g2 = int(color2[3:5], 16)
            b2 = int(color2[5:7], 16)
            
            # Blend colors
            r = int(r1 * (1 - blend_factor) + r2 * blend_factor)
            g = int(g1 * (1 - blend_factor) + g2 * blend_factor)
            b = int(b1 * (1 - blend_factor) + b2 * blend_factor)
            
            # Format as hex color
            blended_color = f"#{r:02x}{g:02x}{b:02x}"
            
            # Add to blended frame
            blended_frame[pos] = blended_color
        
        return blended_frame
    
    def _add_ripple_animation(self):
        """Add a ripple animation that expands outward."""
        color = self.selected_color_var.get()
        center_x = self.canvas.grid_size // 2
        center_y = self.canvas.grid_size // 2
        max_radius = 15
        
        def generate_ripple_frame(frame_idx, total_frames):
            # Calculate radius for this frame
            progress = frame_idx / (total_frames - 1)
            radius = int(max_radius * progress)
            
            # Create pixel map for this frame
            pixels = {}
            
            # Draw circle at the calculated radius
            for theta in range(0, 360, 5):  # 5 degree increments
                x = int(center_x + radius * math.cos(math.radians(theta)))
                y = int(center_y + radius * math.sin(math.radians(theta)))
                
                if 0 <= x < self.canvas.grid_size and 0 <= y < self.canvas.grid_size:
                    pixels[(x, y)] = color
            
            return pixels
        
        self._add_animation_preset(generate_ripple_frame)
    
    def _add_wipe_right_animation(self):
        """Add a wipe right animation."""
        color = self.selected_color_var.get()
        
        def generate_wipe_frame(frame_idx, total_frames):
            # Calculate how many columns to fill
            grid_size = self.canvas.grid_size
            cols_to_fill = int((frame_idx + 1) * grid_size / total_frames)
            
            # Create pixel map for this frame
            pixels = {}
            
            # Fill columns up to the calculated position
            for x in range(cols_to_fill):
                for y in range(grid_size):
                    pixels[(x, y)] = color
            
            return pixels
        
        self._add_animation_preset(generate_wipe_frame)
    
    def _add_wipe_left_animation(self):
        """Add a wipe left animation."""
        color = self.selected_color_var.get()
        
        def generate_wipe_frame(frame_idx, total_frames):
            # Calculate how many columns to fill
            grid_size = self.canvas.grid_size
            cols_to_fill = int((frame_idx + 1) * grid_size / total_frames)
            
            # Create pixel map for this frame
            pixels = {}
            
            # Fill columns from the right side
            for x in range(grid_size - cols_to_fill, grid_size):
                for y in range(grid_size):
                    pixels[(x, y)] = color
            
            return pixels
        
        self._add_animation_preset(generate_wipe_frame)
    
    def _add_wipe_down_animation(self):
        """Add a wipe down animation."""
        color = self.selected_color_var.get()
        
        def generate_wipe_frame(frame_idx, total_frames):
            # Calculate how many rows to fill
            grid_size = self.canvas.grid_size
            rows_to_fill = int((frame_idx + 1) * grid_size / total_frames)
            
            # Create pixel map for this frame
            pixels = {}
            
            # Fill rows up to the calculated position
            for y in range(rows_to_fill):
                for x in range(grid_size):
                    pixels[(x, y)] = color
            
            return pixels
        
        self._add_animation_preset(generate_wipe_frame)
    
    def _add_wipe_up_animation(self):
        """Add a wipe up animation."""
        color = self.selected_color_var.get()
        
        def generate_wipe_frame(frame_idx, total_frames):
            # Calculate how many rows to fill
            grid_size = self.canvas.grid_size
            rows_to_fill = int((frame_idx + 1) * grid_size / total_frames)
            
            # Create pixel map for this frame
            pixels = {}
            
            # Fill rows from the bottom
            for y in range(grid_size - rows_to_fill, grid_size):
                for x in range(grid_size):
                    pixels[(x, y)] = color
            
            return pixels
        
        self._add_animation_preset(generate_wipe_frame)
    
    def _add_pulse_animation(self):
        """Add a pulsing circle animation."""
        color = self.selected_color_var.get()
        center_x = self.canvas.grid_size // 2
        center_y = self.canvas.grid_size // 2
        min_radius = 2
        max_radius = 12
        
        def generate_pulse_frame(frame_idx, total_frames):
            # Calculate radius for this frame (ping-pong pattern)
            progress = frame_idx / (total_frames - 1)
            if progress > 0.5:
                progress = 1.0 - progress  # reverse after halfway point
            progress = progress * 2  # scale to 0-1 range
            radius = int(min_radius + (max_radius - min_radius) * progress)
            
            # Create pixel map for this frame
            pixels = {}
            
            # Draw filled circle
            for y in range(center_y - radius, center_y + radius + 1):
                for x in range(center_x - radius, center_x + radius + 1):
                    if (x - center_x)**2 + (y - center_y)**2 <= radius**2:
                        if 0 <= x < self.canvas.grid_size and 0 <= y < self.canvas.grid_size:
                            pixels[(x, y)] = color
            
            return pixels
        
        self._add_animation_preset(generate_pulse_frame)
    
    def _add_rainbow_animation(self):
        """Add a rainbow animation that cycles through colors."""
        
        def generate_rainbow_frame(frame_idx, total_frames):
            grid_size = self.canvas.grid_size
            pixels = {}
            
            # Calculate hue offset for this frame
            hue_offset = frame_idx / total_frames * 360
            
            # Fill grid with colors
            for y in range(grid_size):
                for x in range(grid_size):
                    # Calculate hue based on position
                    hue = (hue_offset + (x + y) / (grid_size * 2) * 360) % 360
                    
                    # Convert HSV to RGB (simplified)
                    h = hue / 60.0
                    i = int(h)
                    f = h - i
                    p = 0
                    q = int(255 * (1 - f))
                    t = int(255 * f)
                    v = 255
                    
                    if i == 0:
                        r, g, b = v, t, p
                    elif i == 1:
                        r, g, b = q, v, p
                    elif i == 2:
                        r, g, b = p, v, t
                    elif i == 3:
                        r, g, b = p, q, v
                    elif i == 4:
                        r, g, b = t, p, v
                    else:
                        r, g, b = v, p, q
                    
                    # Format as hex color
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    pixels[(x, y)] = color
            
            return pixels
        
        self._add_animation_preset(generate_rainbow_frame)
    
    def _add_sparkle_animation(self):
        """Add a sparkling animation with random dots."""
        color = self.selected_color_var.get()
        
        def generate_sparkle_frame(frame_idx, total_frames):
            grid_size = self.canvas.grid_size
            pixels = {}
            
            # Number of sparkles to add in this frame
            num_sparkles = max(5, grid_size // 4)
            
            # Add random sparkles
            for _ in range(num_sparkles):
                x = random.randint(0, grid_size - 1)
                y = random.randint(0, grid_size - 1)
                
                # 50% chance of using the current color, otherwise use a random bright color
                if random.random() > 0.5:
                    pixel_color = color
                else:
                    # Generate a bright random color
                    r = random.randint(192, 255)
                    g = random.randint(192, 255)
                    b = random.randint(192, 255)
                    pixel_color = f"#{r:02x}{g:02x}{b:02x}"
                
                pixels[(x, y)] = pixel_color
            
            return pixels
        
        self._add_animation_preset(generate_sparkle_frame)
    
    def _add_snake_animation(self):
        """Add a moving snake animation."""
        color = self.selected_color_var.get()
        snake_length = 8
        
        def generate_snake_frame(frame_idx, total_frames):
            grid_size = self.canvas.grid_size
            pixels = {}
            
            # The snake moves in a spiral pattern
            # Starting from the center, calculate the position for this frame
            center_x = grid_size // 2
            center_y = grid_size // 2
            
            # Calculate total path length for a spiral
            path_points = []
            
            # Generate spiral path
            step_size = 1
            x, y = center_x, center_y
            direction = 0  # 0: right, 1: down, 2: left, 3: up
            steps_taken = 0
            steps_to_take = 1
            
            # Generate enough points to fill most of the grid
            for _ in range(grid_size * grid_size // 2):
                path_points.append((x, y))
                
                # Move in the current direction
                if direction == 0:  # right
                    x += 1
                elif direction == 1:  # down
                    y += 1
                elif direction == 2:  # left
                    x -= 1
                else:  # up
                    y -= 1
                
                # Check if we need to change direction
                steps_taken += 1
                if steps_taken == steps_to_take:
                    direction = (direction + 1) % 4
                    steps_taken = 0
                    
                    # After completing a half turn (right+down or left+up), increase the steps
                    if direction == 0 or direction == 2:
                        steps_to_take += 1
            
            # Calculate the snake's starting position for this frame
            start_pos = (frame_idx * len(path_points) // total_frames) % len(path_points)
            
            # Draw the snake from the starting position
            for i in range(snake_length):
                pos = (start_pos + i) % len(path_points)
                x, y = path_points[pos]
                
                # Only draw if within grid bounds
                if 0 <= x < grid_size and 0 <= y < grid_size:
                    # Fade color based on position in snake
                    fade = 1.0 - i / snake_length
                    r = int(int(color[1:3], 16) * fade)
                    g = int(int(color[3:5], 16) * fade)
                    b = int(int(color[5:7], 16) * fade)
                    
                    pixel_color = f"#{r:02x}{g:02x}{b:02x}"
                    pixels[(x, y)] = pixel_color
            
            return pixels
        
        self._add_animation_preset(generate_snake_frame)
    
    def _add_spin_animation(self):
        """Add a spinning line animation."""
        color = self.selected_color_var.get()
        line_length = min(self.canvas.grid_size // 2, 12)
        
        def generate_spin_frame(frame_idx, total_frames):
            grid_size = self.canvas.grid_size
            center_x = grid_size // 2
            center_y = grid_size // 2
            pixels = {}
            
            # Calculate angle for this frame (full 360° rotation)
            angle = frame_idx / total_frames * 2 * math.pi
            
            # Calculate start and end points for the line
            x1 = center_x + int(math.cos(angle) * line_length)
            y1 = center_y + int(math.sin(angle) * line_length)
            x2 = center_x + int(math.cos(angle + math.pi) * line_length)
            y2 = center_y + int(math.sin(angle + math.pi) * line_length)
            
            # Draw the line
            self._draw_line_pixels(pixels, x1, y1, x2, y2, color)
            
            return pixels
        
        self._add_animation_preset(generate_spin_frame) 

    def save_animation_preset(self):
        """Save the current animation as a preset that can be reused."""
        # Check if we have any frames
        if not self.canvas.frames:
            messagebox.showinfo("No Animation", "There is no animation to save.")
            return
            
        # Get a name for the preset
        preset_name = tk.simpledialog.askstring(
            "Save Preset", 
            "Enter a name for this preset:",
            parent=self.root
        )
        
        if not preset_name:
            return  # User canceled
            
        # Sanitize the name for use as a filename
        safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in preset_name)
        
        # Create the preset directory if it doesn't exist
        if not os.path.exists(self.custom_presets_dir):
            os.makedirs(self.custom_presets_dir)
            
        # Save the animation data
        try:
            # Get all frame data
            frames_data = self.canvas.get_all_frames()
            
            # Create a metadata structure
            preset_data = {
                "name": preset_name,
                "frames": frames_data,
                "fps": self.canvas.fps,
                "created_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "frame_count": len(frames_data)
            }
            
            # Save to file
            preset_file = os.path.join(self.custom_presets_dir, f"{safe_name}.preset")
            with open(preset_file, "wb") as f:
                pickle.dump(preset_data, f)
                
            messagebox.showinfo("Preset Saved", f"Animation preset '{preset_name}' has been saved.")
            
            # Reload the custom presets
            self.load_custom_presets()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save preset: {str(e)}")
    
    def load_custom_presets(self):
        """Load and display custom animation presets."""
        # Clear existing presets
        for widget in self.custom_presets_container.winfo_children():
            widget.destroy()
            
        # Check if presets directory exists
        if not os.path.exists(self.custom_presets_dir):
            os.makedirs(self.custom_presets_dir)
            
        # Look for preset files
        preset_files = [f for f in os.listdir(self.custom_presets_dir) if f.endswith(".preset")]
        
        if not preset_files:
            # No presets found
            ttk.Label(
                self.custom_presets_container,
                text="No custom presets found.\nCreate animations and save them as presets.",
                justify=tk.CENTER
            ).pack(pady=20)
            return
            
        # Load and display each preset
        for i, preset_file in enumerate(preset_files):
            try:
                # Load the preset data
                file_path = os.path.join(self.custom_presets_dir, preset_file)
                with open(file_path, "rb") as f:
                    preset_data = pickle.load(f)
                    
                # Create a frame for this preset
                preset_frame = ttk.Frame(self.custom_presets_container)
                preset_frame.pack(fill=tk.X, padx=5, pady=5)
                
                # Add preset name and details
                name = preset_data.get("name", os.path.splitext(preset_file)[0])
                frame_count = preset_data.get("frame_count", "?")
                
                ttk.Label(
                    preset_frame,
                    text=f"{name}\n({frame_count} frames)",
                    justify=tk.LEFT
                ).pack(side=tk.LEFT, padx=5)
                
                # Add buttons
                button_frame = ttk.Frame(preset_frame)
                button_frame.pack(side=tk.RIGHT)
                
                # Load button
                ttk.Button(
                    button_frame,
                    text="Load",
                    command=lambda p=preset_data: self.load_animation_from_preset(p)
                ).pack(side=tk.LEFT, padx=2)
                
                # Append button
                ttk.Button(
                    button_frame,
                    text="Append",
                    command=lambda p=preset_data: self.load_animation_from_preset(p, append=True)
                ).pack(side=tk.LEFT, padx=2)
                
                # Delete button
                ttk.Button(
                    button_frame,
                    text="Delete",
                    command=lambda f=file_path, n=name: self.delete_animation_preset(f, n)
                ).pack(side=tk.LEFT, padx=2)
                
            except Exception as e:
                print(f"Error loading preset {preset_file}: {str(e)}")
    
    def load_animation_from_preset(self, preset_data, append=False):
        """
        Load an animation from a saved preset.
        
        Args:
            preset_data: The preset data dictionary
            append: Whether to append to current animation or replace it
        """
        try:
            # Get frames data
            frames_data = preset_data.get("frames", {})
            
            if not frames_data:
                messagebox.showinfo("Empty Preset", "This preset contains no frame data.")
                return
                
            # Check if we should confirm replacement
            if not append and len(self.canvas.frames) > 1:
                if not messagebox.askyesno("Replace Animation", 
                                         "This will replace your current animation.\n\nDo you want to continue?"):
                    return
            
            # Handle append vs. replace
            if append:
                # Find the highest frame index
                start_idx = max(self.canvas.frames.keys()) + 1 if self.canvas.frames else 0
                
                # Create a mapping from preset frame indices to new frame indices
                frame_map = {i: start_idx + idx for idx, i in enumerate(sorted(frames_data.keys()))}
                
                # Add frames one by one
                for old_idx, new_idx in frame_map.items():
                    # Set frame data
                    self.canvas.frames[new_idx] = frames_data[old_idx].copy()
                
                # Set current frame to first new frame
                self.canvas.set_frame(start_idx)
                
                # Update timeline
                self.timeline.set_frame_count(len(self.canvas.frames))
                self.timeline.set_current_frame(start_idx)
                
            else:
                # Replace all frames
                self.canvas.set_all_frames(frames_data)
                
                # Go to first frame
                self.canvas.set_frame(min(frames_data.keys()))
                
                # Update timeline
                self.timeline.set_frame_count(len(self.canvas.frames))
                self.timeline.set_current_frame(min(frames_data.keys()))
            
            # Set FPS if available
            if "fps" in preset_data:
                self.canvas.fps = preset_data["fps"]
                self.fps_var.set(str(preset_data["fps"]))
            
            # Mark as modified
            self.is_modified = True
            self._update_title()
            
            # Show confirmation
            preset_name = preset_data.get("name", "Custom preset")
            if append:
                self.status_label.config(text=f"Appended animation from preset '{preset_name}'")
            else:
                self.status_label.config(text=f"Loaded animation from preset '{preset_name}'")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load preset: {str(e)}")
    
    def delete_animation_preset(self, file_path, preset_name):
        """
        Delete an animation preset.
        
        Args:
            file_path: Path to the preset file
            preset_name: Name of the preset for display
        """
        try:
            # Confirm deletion
            if not messagebox.askyesno("Confirm Delete", 
                                     f"Are you sure you want to delete the preset '{preset_name}'?\n\n"
                                     "This cannot be undone."):
                return
                
            # Delete the file
            os.remove(file_path)
            
            # Reload presets
            self.load_custom_presets()
            
            # Show confirmation
            self.status_label.config(text=f"Deleted preset '{preset_name}'")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete preset: {str(e)}")