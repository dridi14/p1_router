#!/usr/bin/env python3

"""
Improved P1 Router Configuration Editor with Network Testing Tools
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
import subprocess
import os
import math
import random
import socket
import threading
import time
import platform
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Constants - will be updated at runtime with absolute path
CONFIG_PATH = "config/config.json"

# Get absolute path to config file
def get_config_path():
    """Get absolute path to config file, handling different launch directories"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up one level if in download-and-launch
    
    # Try multiple possible paths
    possible_paths = [
        os.path.join(script_dir, "config", "config.json"),            # /download-and-launch/config/config.json
        os.path.join(project_root, "config", "config.json"),          # /config/config.json
        os.path.join(project_root, "p1_router", "config", "config.json")  # /p1_router/config/config.json
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # If not found, create directory and return default path
    default_path = os.path.join(script_dir, "config", "config.json")
    os.makedirs(os.path.dirname(default_path), exist_ok=True)
    return default_path
COLORS = {
    "error": "#ffcccc",
    "warning": "#ffffcc",
    "valid": "#ccffcc",
    "header_bg": "#2c3e50",
    "header_fg": "#ecf0f1",
    "alternate_row": "#f2f2f2",
    "selected": "#3498db"
}

class BulkEditDialog(tk.Toplevel):
    """Dialog for bulk editing operations"""
    
    def __init__(self, parent, selected_indices, config_data, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.selected_indices = selected_indices
        self.config_data = config_data
        self.result = None
        
        self.title("Bulk Edit Operations")
        self.geometry("600x500")
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        
        # Center the dialog
        self.center_window()
    
    def center_window(self):
        """Center the dialog on the parent window"""
        self.update_idletasks()
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        x = parent_x + (parent_width - self.winfo_width()) // 2
        y = parent_y + (parent_height - self.winfo_height()) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Set up the bulk edit interface"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_label = ttk.Label(
            main_frame, 
            text=f"Bulk Edit - {len(self.selected_indices)} entries selected",
            font=("Arial", 14, "bold")
        )
        header_label.pack(pady=(0, 20))
        
        # Create notebook for different operation types
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Tab 1: Basic Properties
        self.setup_basic_tab(notebook)
        
        # Tab 2: Pattern Assignment
        self.setup_pattern_tab(notebook)
        
        # Tab 3: Advanced Operations
        self.setup_advanced_tab(notebook)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Apply", command=self.apply_changes).pack(side=tk.RIGHT)
    
    def setup_basic_tab(self, notebook):
        """Set up the basic properties tab"""
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="Basic Properties")
        
        # Scrollable frame
        canvas = tk.Canvas(basic_frame)
        scrollbar = ttk.Scrollbar(basic_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Universe modification
        universe_frame = ttk.LabelFrame(scrollable_frame, text="Universe Assignment")
        universe_frame.pack(fill=tk.X, pady=10)
        
        self.universe_mode = tk.StringVar(value="keep")
        ttk.Radiobutton(universe_frame, text="Keep current values", variable=self.universe_mode, value="keep").pack(anchor=tk.W)
        
        set_universe_frame = ttk.Frame(universe_frame)
        set_universe_frame.pack(fill=tk.X, pady=5)
        ttk.Radiobutton(set_universe_frame, text="Set all to:", variable=self.universe_mode, value="set").pack(side=tk.LEFT)
        self.universe_value = tk.IntVar(value=0)
        ttk.Spinbox(set_universe_frame, from_=0, to=255, width=10, textvariable=self.universe_value).pack(side=tk.LEFT, padx=(10, 0))
        
        increment_universe_frame = ttk.Frame(universe_frame)
        increment_universe_frame.pack(fill=tk.X, pady=5)
        ttk.Radiobutton(increment_universe_frame, text="Increment starting from:", variable=self.universe_mode, value="increment").pack(side=tk.LEFT)
        self.universe_start = tk.IntVar(value=0)
        ttk.Spinbox(increment_universe_frame, from_=0, to=255, width=10, textvariable=self.universe_start).pack(side=tk.LEFT, padx=(10, 0))
        
        # IP Address modification
        ip_frame = ttk.LabelFrame(scrollable_frame, text="IP Address Assignment")
        ip_frame.pack(fill=tk.X, pady=10)
        
        self.ip_mode = tk.StringVar(value="keep")
        ttk.Radiobutton(ip_frame, text="Keep current values", variable=self.ip_mode, value="keep").pack(anchor=tk.W)
        
        set_ip_frame = ttk.Frame(ip_frame)
        set_ip_frame.pack(fill=tk.X, pady=5)
        ttk.Radiobutton(set_ip_frame, text="Set all to:", variable=self.ip_mode, value="set").pack(side=tk.LEFT)
        self.ip_value = tk.StringVar(value="192.168.1.45")
        ttk.Entry(set_ip_frame, width=20, textvariable=self.ip_value).pack(side=tk.LEFT, padx=(10, 0))
        
        # Entity range modification
        range_frame = ttk.LabelFrame(scrollable_frame, text="Entity Range Adjustment")
        range_frame.pack(fill=tk.X, pady=10)
        
        self.range_mode = tk.StringVar(value="keep")
        ttk.Radiobutton(range_frame, text="Keep current ranges", variable=self.range_mode, value="keep").pack(anchor=tk.W)
        
        offset_frame = ttk.Frame(range_frame)
        offset_frame.pack(fill=tk.X, pady=5)
        ttk.Radiobutton(offset_frame, text="Add offset:", variable=self.range_mode, value="offset").pack(side=tk.LEFT)
        self.range_offset = tk.IntVar(value=0)
        ttk.Spinbox(offset_frame, from_=-9999, to=9999, width=10, textvariable=self.range_offset).pack(side=tk.LEFT, padx=(10, 0))
        
        # Pack scrollable components
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_pattern_tab(self, notebook):
        """Set up the pattern assignment tab"""
        pattern_frame = ttk.Frame(notebook)
        notebook.add(pattern_frame, text="Pattern Assignment")
        
        # Pattern type selection
        pattern_type_frame = ttk.LabelFrame(pattern_frame, text="Pattern Type")
        pattern_type_frame.pack(fill=tk.X, pady=10)
        
        self.pattern_type = tk.StringVar(value="sequential_universe")
        
        ttk.Radiobutton(
            pattern_type_frame, 
            text="Sequential Universe Assignment",
            variable=self.pattern_type, 
            value="sequential_universe"
        ).pack(anchor=tk.W)
        
        ttk.Radiobutton(
            pattern_type_frame, 
            text="Entity Range Distribution",
            variable=self.pattern_type, 
            value="range_distribution"
        ).pack(anchor=tk.W)
        
        ttk.Radiobutton(
            pattern_type_frame, 
            text="Controller Load Balancing",
            variable=self.pattern_type, 
            value="load_balance"
        ).pack(anchor=tk.W)
        
        # Pattern parameters
        params_frame = ttk.LabelFrame(pattern_frame, text="Pattern Parameters")
        params_frame.pack(fill=tk.X, pady=10)
        
        # Sequential universe parameters
        seq_frame = ttk.Frame(params_frame)
        seq_frame.pack(fill=tk.X, pady=5)
        ttk.Label(seq_frame, text="Starting Universe:").pack(side=tk.LEFT)
        self.seq_start_universe = tk.IntVar(value=0)
        ttk.Spinbox(seq_frame, from_=0, to=255, width=10, textvariable=self.seq_start_universe).pack(side=tk.LEFT, padx=(10, 0))
        
        # Entities per universe
        entities_frame = ttk.Frame(params_frame)
        entities_frame.pack(fill=tk.X, pady=5)
        ttk.Label(entities_frame, text="Entities per Universe:").pack(side=tk.LEFT)
        self.entities_per_universe = tk.IntVar(value=170)
        ttk.Spinbox(entities_frame, from_=1, to=512, width=10, textvariable=self.entities_per_universe).pack(side=tk.LEFT, padx=(10, 0))
        
        # Base IP for load balancing
        ip_base_frame = ttk.Frame(params_frame)
        ip_base_frame.pack(fill=tk.X, pady=5)
        ttk.Label(ip_base_frame, text="Base IP (for load balancing):").pack(side=tk.LEFT)
        self.base_ip = tk.StringVar(value="192.168.1.45")
        ttk.Entry(ip_base_frame, width=20, textvariable=self.base_ip).pack(side=tk.LEFT, padx=(10, 0))
        
        # Preview
        preview_frame = ttk.LabelFrame(pattern_frame, text="Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.preview_text = tk.Text(preview_frame, height=8, width=50)
        preview_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=preview_scroll.set)
        
        self.preview_text.pack(side="left", fill="both", expand=True)
        preview_scroll.pack(side="right", fill="y")
        
        ttk.Button(pattern_frame, text="Generate Preview", command=self.generate_preview).pack(pady=10)
    
    def setup_advanced_tab(self, notebook):
        """Set up the advanced operations tab"""
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="Advanced")
        
        # Delete operations
        delete_frame = ttk.LabelFrame(advanced_frame, text="Delete Operations")
        delete_frame.pack(fill=tk.X, pady=10)
        
        self.delete_selected = tk.BooleanVar()
        ttk.Checkbutton(
            delete_frame, 
            text="Delete selected entries", 
            variable=self.delete_selected
        ).pack(anchor=tk.W, pady=5)
        
        # Duplicate operations
        duplicate_frame = ttk.LabelFrame(advanced_frame, text="Duplicate Operations")
        duplicate_frame.pack(fill=tk.X, pady=10)
        
        self.duplicate_selected = tk.BooleanVar()
        ttk.Checkbutton(
            duplicate_frame, 
            text="Duplicate selected entries", 
            variable=self.duplicate_selected
        ).pack(anchor=tk.W, pady=5)
        
        dup_offset_frame = ttk.Frame(duplicate_frame)
        dup_offset_frame.pack(fill=tk.X, pady=5)
        ttk.Label(dup_offset_frame, text="Entity ID offset for duplicates:").pack(side=tk.LEFT)
        self.duplicate_offset = tk.IntVar(value=1000)
        ttk.Spinbox(dup_offset_frame, from_=1, to=9999, width=10, textvariable=self.duplicate_offset).pack(side=tk.LEFT, padx=(10, 0))
        
        # Validation fix
        validation_frame = ttk.LabelFrame(advanced_frame, text="Validation Fixes")
        validation_frame.pack(fill=tk.X, pady=10)
        
        self.fix_overlaps = tk.BooleanVar()
        ttk.Checkbutton(
            validation_frame, 
            text="Auto-fix entity overlaps", 
            variable=self.fix_overlaps
        ).pack(anchor=tk.W, pady=5)
        
        self.optimize_universes = tk.BooleanVar()
        ttk.Checkbutton(
            validation_frame, 
            text="Optimize universe capacity", 
            variable=self.optimize_universes
        ).pack(anchor=tk.W, pady=5)
    
    def generate_preview(self):
        """Generate preview of pattern assignment"""
        self.preview_text.delete(1.0, tk.END)
        
        pattern_type = self.pattern_type.get()
        
        if pattern_type == "sequential_universe":
            self.preview_sequential_universe()
        elif pattern_type == "range_distribution":
            self.preview_range_distribution()
        elif pattern_type == "load_balance":
            self.preview_load_balance()
    
    def preview_sequential_universe(self):
        """Preview sequential universe assignment"""
        start_universe = self.seq_start_universe.get()
        entities_per_universe = self.entities_per_universe.get()
        
        preview_text = "Sequential Universe Assignment Preview:\n\n"
        
        for i, idx in enumerate(self.selected_indices[:5]):  # Show first 5 as preview
            entry = self.config_data[idx]
            entity_count = entry["to"] - entry["from"] + 1
            universe = start_universe + (i * entity_count) // entities_per_universe
            
            preview_text += f"Entry {i+1}: Universe {universe}\n"
            preview_text += f"  Entities: {entry['from']}-{entry['to']} ({entity_count} entities)\n"
            preview_text += f"  IP: {entry['ip']}\n\n"
        
        if len(self.selected_indices) > 5:
            preview_text += f"... and {len(self.selected_indices) - 5} more entries"
        
        self.preview_text.insert(1.0, preview_text)
    
    def preview_range_distribution(self):
        """Preview entity range distribution"""
        entities_per_universe = self.entities_per_universe.get()
        
        preview_text = "Entity Range Distribution Preview:\n\n"
        
        total_entities = sum(
            self.config_data[idx]["to"] - self.config_data[idx]["from"] + 1 
            for idx in self.selected_indices
        )
        
        universes_needed = (total_entities + entities_per_universe - 1) // entities_per_universe
        
        preview_text += f"Total entities: {total_entities}\n"
        preview_text += f"Entities per universe: {entities_per_universe}\n"
        preview_text += f"Universes needed: {universes_needed}\n\n"
        
        preview_text += "Distribution:\n"
        for i in range(min(universes_needed, 5)):
            start_entity = i * entities_per_universe
            end_entity = min((i + 1) * entities_per_universe - 1, total_entities - 1)
            preview_text += f"Universe {i}: Entities {start_entity}-{end_entity}\n"
        
        if universes_needed > 5:
            preview_text += f"... and {universes_needed - 5} more universes"
        
        self.preview_text.insert(1.0, preview_text)
    
    def preview_load_balance(self):
        """Preview load balancing across controllers"""
        base_ip = self.base_ip.get()
        
        preview_text = "Controller Load Balancing Preview:\n\n"
        
        # Simple load balancing - distribute across IP addresses
        ip_parts = base_ip.split(".")
        if len(ip_parts) == 4:
            base_num = int(ip_parts[3])
            
            for i, idx in enumerate(self.selected_indices[:5]):
                entry = self.config_data[idx]
                controller_num = base_num + (i % 4)  # Distribute across 4 controllers
                new_ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{controller_num}"
                
                preview_text += f"Entry {i+1}: Controller {new_ip}\n"
                preview_text += f"  Entities: {entry['from']}-{entry['to']}\n"
                preview_text += f"  Universe: {entry['universe']}\n\n"
        
        if len(self.selected_indices) > 5:
            preview_text += f"... and {len(self.selected_indices) - 5} more entries"
        
        self.preview_text.insert(1.0, preview_text)
    
    def apply_changes(self):
        """Apply the bulk edit changes"""
        if self.delete_selected.get():
            # Mark for deletion (will be handled by parent)
            self.result = {"action": "delete", "indices": self.selected_indices}
        elif self.duplicate_selected.get():
            # Create duplicates
            self.result = {"action": "duplicate", "indices": self.selected_indices, "offset": self.duplicate_offset.get()}
        else:
            # Apply modifications
            changes = {}
            
            # Universe changes
            if self.universe_mode.get() == "set":
                changes["universe"] = {"mode": "set", "value": self.universe_value.get()}
            elif self.universe_mode.get() == "increment":
                changes["universe"] = {"mode": "increment", "start": self.universe_start.get()}
            
            # IP changes
            if self.ip_mode.get() == "set":
                changes["ip"] = {"mode": "set", "value": self.ip_value.get()}
            
            # Range changes
            if self.range_mode.get() == "offset":
                changes["range"] = {"mode": "offset", "value": self.range_offset.get()}
            
            # Pattern changes
            if self.pattern_type.get() != "sequential_universe":
                changes["pattern"] = {
                    "type": self.pattern_type.get(),
                    "entities_per_universe": self.entities_per_universe.get(),
                    "start_universe": self.seq_start_universe.get(),
                    "base_ip": self.base_ip.get()
                }
            
            self.result = {"action": "modify", "indices": self.selected_indices, "changes": changes}
        
        self.destroy()
    
    def cancel(self):
        """Cancel the bulk edit operation"""
        self.result = None
        self.destroy()


class NetworkTestingTools(tk.Toplevel):
    """Network Testing Tools Window"""
    
    def __init__(self, parent, config_data, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.config_data = config_data
        self.test_results = {}
        self.is_testing = False
        
        self.title("Network Testing Tools")
        self.geometry("900x700")
        self.transient(parent)
        
        self.setup_ui()
        self.center_window()
    
    def center_window(self):
        """Center the window on the parent"""
        self.update_idletasks()
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        x = parent_x + (parent_width - self.winfo_width()) // 2
        y = parent_y + (parent_height - self.winfo_height()) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Set up the network testing interface"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="Network Testing Tools", 
                               font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Status indicator
        self.status_label = ttk.Label(header_frame, text="Ready", 
                                     foreground="green", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.RIGHT)
        
        # Create notebook for different test types
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Tab 1: Connectivity Tests
        self.setup_connectivity_tab(notebook)
        
        # Tab 2: Performance Tests
        self.setup_performance_tab(notebook)
        
        # Tab 3: Diagnostic Tools
        self.setup_diagnostic_tab(notebook)
        
        # Tab 4: Network Discovery
        self.setup_discovery_tab(notebook)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X)
        
        ttk.Button(control_frame, text="Run All Tests", 
                  command=self.run_all_tests).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Stop Tests", 
                  command=self.stop_tests).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Export Results", 
                  command=self.export_results).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Close", 
                  command=self.destroy).pack(side=tk.RIGHT)
    
    def setup_connectivity_tab(self, notebook):
        """Set up the connectivity testing tab"""
        conn_frame = ttk.Frame(notebook)
        notebook.add(conn_frame, text="Connectivity")
        
        # Scrollable frame
        canvas = tk.Canvas(conn_frame)
        scrollbar = ttk.Scrollbar(conn_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Test options
        options_frame = ttk.LabelFrame(scrollable_frame, text="Test Options", padding=10)
        options_frame.pack(fill="x", pady=(0, 10))
        
        self.ping_enabled = tk.BooleanVar(value=True)
        self.port_scan_enabled = tk.BooleanVar(value=True)
        self.timeout_var = tk.IntVar(value=5)
        
        ttk.Checkbutton(options_frame, text="Ping Test", 
                       variable=self.ping_enabled).pack(anchor="w")
        ttk.Checkbutton(options_frame, text="Port Scan (Art-Net: 6454)", 
                       variable=self.port_scan_enabled).pack(anchor="w")
        
        timeout_frame = ttk.Frame(options_frame)
        timeout_frame.pack(fill="x", pady=(10, 0))
        ttk.Label(timeout_frame, text="Timeout (seconds):").pack(side="left")
        ttk.Spinbox(timeout_frame, from_=1, to=30, width=10, 
                   textvariable=self.timeout_var).pack(side="left", padx=(10, 0))
        
        # Results display
        results_frame = ttk.LabelFrame(scrollable_frame, text="Connectivity Results", padding=10)
        results_frame.pack(fill="both", expand=True)
        
        # Create results treeview
        self.conn_tree = ttk.Treeview(results_frame, 
                                     columns=("ip", "ping", "port", "latency", "status"),
                                     show="headings", height=15)
        
        self.conn_tree.heading("ip", text="IP Address")
        self.conn_tree.heading("ping", text="Ping")
        self.conn_tree.heading("port", text="Art-Net Port")
        self.conn_tree.heading("latency", text="Latency (ms)")
        self.conn_tree.heading("status", text="Status")
        
        self.conn_tree.column("ip", width=120)
        self.conn_tree.column("ping", width=80)
        self.conn_tree.column("port", width=100)
        self.conn_tree.column("latency", width=100)
        self.conn_tree.column("status", width=200)
        
        conn_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", 
                                      command=self.conn_tree.yview)
        self.conn_tree.configure(yscrollcommand=conn_scrollbar.set)
        
        conn_scrollbar.pack(side="right", fill="y")
        self.conn_tree.pack(side="left", fill="both", expand=True)
        
        # Control buttons for connectivity
        conn_control_frame = ttk.Frame(scrollable_frame)
        conn_control_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(conn_control_frame, text="Test Connectivity", 
                  command=self.test_connectivity).pack(side="left", padx=(0, 10))
        ttk.Button(conn_control_frame, text="Clear Results", 
                  command=self.clear_connectivity_results).pack(side="left")
        
        # Update scroll region
        def configure_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scrollable_frame.bind("<Configure>", configure_scroll)
    
    def setup_performance_tab(self, notebook):
        """Set up the performance testing tab (placeholder)"""
        perf_frame = ttk.Frame(notebook)
        notebook.add(perf_frame, text="Performance")
        
        placeholder_label = ttk.Label(perf_frame, 
                                     text="Performance testing features\nwill be implemented in the next update.",
                                     font=("Arial", 12),
                                     justify=tk.CENTER)
        placeholder_label.pack(expand=True)
    
    def setup_diagnostic_tab(self, notebook):
        """Set up the diagnostic tools tab"""
        diag_frame = ttk.Frame(notebook)
        notebook.add(diag_frame, text="Diagnostics")
        
        # Diagnostic options
        options_frame = ttk.LabelFrame(diag_frame, text="Diagnostic Tools", padding=10)
        options_frame.pack(fill="x", pady=(0, 10))
        
        # Route trace
        trace_frame = ttk.Frame(options_frame)
        trace_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(trace_frame, text="Traceroute to:").pack(side="left")
        self.trace_target = tk.StringVar()
        ttk.Entry(trace_frame, textvariable=self.trace_target, width=20).pack(side="left", padx=(10, 10))
        ttk.Button(trace_frame, text="Trace Route", 
                  command=self.run_traceroute).pack(side="left")
        
        # Network info
        info_frame = ttk.Frame(options_frame)
        info_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(info_frame, text="Get Network Info", 
                  command=self.get_network_info).pack(side="left", padx=(0, 10))
        ttk.Button(info_frame, text="Check ARP Table", 
                  command=self.check_arp_table).pack(side="left", padx=(0, 10))
        ttk.Button(info_frame, text="Network Statistics", 
                  command=self.get_network_stats).pack(side="left")
        
        # Results display
        results_frame = ttk.LabelFrame(diag_frame, text="Diagnostic Results", padding=10)
        results_frame.pack(fill="both", expand=True)
        
        self.diag_text = tk.Text(results_frame, wrap=tk.WORD, height=20)
        diag_text_scroll = ttk.Scrollbar(results_frame, orient="vertical", 
                                        command=self.diag_text.yview)
        self.diag_text.configure(yscrollcommand=diag_text_scroll.set)
        
        diag_text_scroll.pack(side="right", fill="y")
        self.diag_text.pack(side="left", fill="both", expand=True)
        
        # Diagnostic control buttons
        diag_control_frame = ttk.Frame(diag_frame)
        diag_control_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(diag_control_frame, text="Clear Output", 
                  command=self.clear_diagnostic_output).pack(side="left", padx=(0, 10))
        ttk.Button(diag_control_frame, text="Save Output", 
                  command=self.save_diagnostic_output).pack(side="left")
    
    def setup_discovery_tab(self, notebook):
        """Set up the network discovery tab (placeholder)"""
        disc_frame = ttk.Frame(notebook)
        notebook.add(disc_frame, text="Discovery")
        
        placeholder_label = ttk.Label(disc_frame, 
                                     text="Network discovery features\nwill be implemented in the next update.",
                                     font=("Arial", 12),
                                     justify=tk.CENTER)
        placeholder_label.pack(expand=True)
    
    # Network testing implementation methods
    def test_connectivity(self):
        """Test connectivity to all configured controllers"""
        if self.is_testing:
            return
        
        self.is_testing = True
        self.status_label.config(text="Testing connectivity...", foreground="orange")
        
        # Clear previous results
        self.clear_connectivity_results()
        
        # Get unique IPs from configuration
        unique_ips = set(entry["ip"] for entry in self.config_data)
        
        def run_tests():
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_ip = {executor.submit(self.test_single_host, ip): ip 
                               for ip in unique_ips}
                
                for future in as_completed(future_to_ip):
                    ip = future_to_ip[future]
                    try:
                        result = future.result()
                        self.after(0, self.update_connectivity_result, ip, result)
                    except Exception as e:
                        self.after(0, self.update_connectivity_result, ip, 
                                 {"ping": "Error", "port": "Error", "latency": "N/A", 
                                  "status": f"Exception: {str(e)}"})
            
            self.after(0, self.finish_connectivity_test)
        
        threading.Thread(target=run_tests, daemon=True).start()
    
    def test_single_host(self, ip):
        """Test a single host for ping and port connectivity"""
        result = {"ping": "Failed", "port": "Closed", "latency": "N/A", "status": ""}
        
        # Ping test
        if self.ping_enabled.get():
            ping_result = self.ping_host(ip)
            result["ping"] = "Success" if ping_result["success"] else "Failed"
            result["latency"] = f"{ping_result['latency']:.1f}" if ping_result["latency"] else "N/A"
        
        # Port test (Art-Net port 6454)
        if self.port_scan_enabled.get():
            port_result = self.test_port(ip, 6454)
            result["port"] = "Open" if port_result else "Closed"
        
        # Determine overall status
        if result["ping"] == "Success" and result["port"] == "Open":
            result["status"] = "Fully accessible"
        elif result["ping"] == "Success":
            result["status"] = "Pingable, Art-Net port closed"
        elif result["port"] == "Open":
            result["status"] = "Art-Net port open, ping failed"
        else:
            result["status"] = "Not accessible"
        
        return result
    
    def ping_host(self, host):
        """Ping a host and return latency"""
        system = platform.system().lower()
        
        if system == "windows":
            cmd = ["ping", "-n", "1", "-w", str(self.timeout_var.get() * 1000), host]
        else:
            cmd = ["ping", "-c", "1", "-W", str(self.timeout_var.get()), host]
        
        try:
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout_var.get() + 2)
            end_time = time.time()
            
            if result.returncode == 0:
                latency = (end_time - start_time) * 1000  # Convert to milliseconds
                return {"success": True, "latency": latency}
            else:
                return {"success": False, "latency": None}
        except subprocess.TimeoutExpired:
            return {"success": False, "latency": None}
        except Exception:
            return {"success": False, "latency": None}
    
    def test_port(self, host, port):
        """Test if a specific port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout_var.get())
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def update_connectivity_result(self, ip, result):
        """Update the connectivity results display"""
        self.conn_tree.insert("", "end", values=(
            ip, result["ping"], result["port"], result["latency"], result["status"]
        ))
    
    def finish_connectivity_test(self):
        """Finish the connectivity test"""
        self.is_testing = False
        self.status_label.config(text="Connectivity test complete", foreground="green")
    
    def clear_connectivity_results(self):
        """Clear connectivity test results"""
        for item in self.conn_tree.get_children():
            self.conn_tree.delete(item)
    
    def run_traceroute(self):
        """Run traceroute to specified target"""
        target = self.trace_target.get().strip()
        if not target:
            messagebox.showwarning("Warning", "Please enter a target IP or hostname.")
            return
        
        self.diag_text.insert(tk.END, f"\n--- Traceroute to {target} ---\n")
        
        def run_trace():
            system = platform.system().lower()
            if system == "windows":
                cmd = ["tracert", target]
            else:
                cmd = ["traceroute", target]
            
            try:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                         stderr=subprocess.STDOUT, text=True)
                
                for line in process.stdout:
                    self.after(0, self.append_diagnostic_output, line)
                
                process.wait()
                self.after(0, self.append_diagnostic_output, f"\nTraceroute to {target} completed.\n")
            except Exception as e:
                self.after(0, self.append_diagnostic_output, f"Error running traceroute: {str(e)}\n")
        
        threading.Thread(target=run_trace, daemon=True).start()
    
    def get_network_info(self):
        """Get local network information"""
        self.diag_text.insert(tk.END, "\n--- Network Interface Information ---\n")
        
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            self.diag_text.insert(tk.END, f"Hostname: {hostname}\n")
            self.diag_text.insert(tk.END, f"Local IP: {local_ip}\n")
            
        except Exception as e:
            self.diag_text.insert(tk.END, f"Error getting network info: {str(e)}\n")
    
    def check_arp_table(self):
        """Check the ARP table"""
        self.diag_text.insert(tk.END, "\n--- ARP Table ---\n")
        
        def run_arp():
            try:
                system = platform.system().lower()
                if system == "windows":
                    cmd = ["arp", "-a"]
                else:
                    cmd = ["arp", "-a"]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                self.after(0, self.append_diagnostic_output, result.stdout)
                
            except Exception as e:
                self.after(0, self.append_diagnostic_output, f"Error checking ARP table: {str(e)}\n")
        
        threading.Thread(target=run_arp, daemon=True).start()
    
    def get_network_stats(self):
        """Get network statistics"""
        self.diag_text.insert(tk.END, "\n--- Network Statistics ---\n")
        
        try:
            # Basic network info without external dependencies
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            self.diag_text.insert(tk.END, f"Hostname: {hostname}\n")
            self.diag_text.insert(tk.END, f"Local IP: {local_ip}\n")
            self.diag_text.insert(tk.END, "For detailed network statistics, install psutil package.\n")
        except Exception as e:
            self.diag_text.insert(tk.END, f"Error getting network statistics: {str(e)}\n")
    
    def append_diagnostic_output(self, text):
        """Append text to diagnostic output"""
        self.diag_text.insert(tk.END, text)
        self.diag_text.see(tk.END)
    
    def clear_diagnostic_output(self):
        """Clear diagnostic output"""
        self.diag_text.delete(1.0, tk.END)
    
    def save_diagnostic_output(self):
        """Save diagnostic output to file"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Diagnostic Output"
        )
        if filepath:
            try:
                with open(filepath, 'w') as f:
                    f.write(self.diag_text.get(1.0, tk.END))
                messagebox.showinfo("Success", "Diagnostic output saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save diagnostic output: {str(e)}")
    
    def run_all_tests(self):
        """Run all available tests"""
        if self.is_testing:
            return
        
        self.test_connectivity()
    
    def stop_tests(self):
        """Stop all running tests"""
        self.is_testing = False
        self.status_label.config(text="Tests stopped", foreground="red")
    
    def export_results(self):
        """Export all test results"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Test Results"
        )
        if filepath:
            try:
                # Collect connectivity results
                results = {"connectivity": [], "diagnostics": self.diag_text.get(1.0, tk.END)}
                
                for item in self.conn_tree.get_children():
                    values = self.conn_tree.item(item)["values"]
                    results["connectivity"].append({
                        "ip": values[0],
                        "ping": values[1],
                        "port": values[2],
                        "latency": values[3],
                        "status": values[4]
                    })
                
                with open(filepath, 'w') as f:
                    json.dump(results, f, indent=2)
                
                messagebox.showinfo("Success", "Test results exported successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export results: {str(e)}")


class ValidationResult:
    """Represents the validation state of configuration entries"""
    def __init__(self):
        self.overlaps: Dict[int, List[int]] = {}  # universe -> list of overlapping entity IDs
        self.capacity_warnings: Dict[int, int] = {}  # universe -> count
        self.max_channels_per_universe = 170 * 3  # 170 RGB entities per universe (3 channels each)
        self.is_valid = True
    
    def validate_config(self, config_data: List[Dict[str, Any]]) -> None:
        """Validate the configuration for overlaps and capacity issues"""
        self.overlaps.clear()
        self.capacity_warnings.clear()
        self.is_valid = True
        
        # Track entities per universe
        universe_entities: Dict[int, Dict[int, bool]] = {}
        universe_counts: Dict[int, int] = {}
        
        for entry in config_data:
            universe = entry["universe"]
            from_id = entry["from"]
            to_id = entry["to"]
            
            # Initialize tracking for this universe if needed
            if universe not in universe_entities:
                universe_entities[universe] = {}
                universe_counts[universe] = 0
            
            # Check for overlaps and count entities
            for entity_id in range(from_id, to_id + 1):
                if entity_id in universe_entities[universe]:
                    # Overlap found
                    if universe not in self.overlaps:
                        self.overlaps[universe] = []
                    self.overlaps[universe].append(entity_id)
                    self.is_valid = False
                else:
                    universe_entities[universe][entity_id] = True
                    universe_counts[universe] += 1
        
        # Check universe capacity
        for universe, count in universe_counts.items():
            channels = count * 3  # Assuming RGB (3 channels per entity)
            if channels > self.max_channels_per_universe:
                self.capacity_warnings[universe] = count
                self.is_valid = False
    
    def get_status_summary(self) -> Tuple[str, str]:
        """Return a summary status message and color"""
        if not self.is_valid:
            if self.overlaps:
                return "Error: Entity overlaps detected", "error"
            elif self.capacity_warnings:
                return "Warning: Universe capacity exceeded", "warning"
        return "Configuration valid", "valid"


class LEDWallVisualization(tk.Toplevel):
    """Visualization window for the LED wall"""
    
    def __init__(self, parent, config_data, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.config_data = config_data
        self.title("LED Wall Visualization (128x128)")
        self.geometry("800x800")
        
        # Entity ID to position mapping
        self.entity_positions = {}  # Will be populated when creating the grid
        self.selected_entity = None
        
        # Entity to universe mapping for color coding
        self.entity_universe_map = {}
        self.universe_colors = {}
        
        self.setup_ui()
        self.update_entity_universe_map()
        self.draw_led_wall()
    
    def setup_ui(self):
        """Set up the user interface components"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Controls frame (top)
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Zoom control
        ttk.Label(controls_frame, text="Zoom:").pack(side=tk.LEFT, padx=(0, 5))
        self.zoom_var = tk.DoubleVar(value=1.0)
        zoom_slider = ttk.Scale(controls_frame, from_=0.5, to=3.0, orient=tk.HORIZONTAL, 
                               variable=self.zoom_var, command=self.on_zoom_change, length=200)
        zoom_slider.pack(side=tk.LEFT, padx=(0, 10))
        
        # Display options
        ttk.Label(controls_frame, text="Display:").pack(side=tk.LEFT, padx=(10, 5))
        self.display_var = tk.StringVar(value="universe")
        ttk.Radiobutton(controls_frame, text="Universe Colors", variable=self.display_var, 
                       value="universe", command=self.draw_led_wall).pack(side=tk.LEFT)
        ttk.Radiobutton(controls_frame, text="Entity IDs", variable=self.display_var, 
                       value="entity", command=self.draw_led_wall).pack(side=tk.LEFT, padx=(10, 0))
        
        # Canvas frame (center)
        self.canvas_frame = ttk.Frame(main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas with scrollbars
        self.canvas_container = ttk.Frame(self.canvas_frame)
        self.canvas_container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        h_scrollbar = ttk.Scrollbar(self.canvas_container, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        v_scrollbar = ttk.Scrollbar(self.canvas_container)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas for drawing the LED wall
        self.canvas = tk.Canvas(
            self.canvas_container, 
            width=800, 
            height=800,
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set,
            background="black"
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbars
        h_scrollbar.config(command=self.canvas.xview)
        v_scrollbar.config(command=self.canvas.yview)
        
        # Bind mouse events for interaction
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<Motion>", self.on_canvas_hover)
        
        # Info panel (bottom)
        self.info_frame = ttk.LabelFrame(main_frame, text="Entity Information")
        self.info_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.info_label = ttk.Label(self.info_frame, text="Hover over an LED to see entity details")
        self.info_label.pack(pady=10)
        
        # Close button
        ttk.Button(main_frame, text="Close", command=self.destroy).pack(pady=(10, 0), side=tk.RIGHT)
        
        # Assign universe colors
        self.assign_universe_colors()
    
    def assign_universe_colors(self):
        """Assign unique colors to each universe for visualization"""
        # Get unique universe IDs
        universes = set(entry["universe"] for entry in self.config_data)
        
        # Color palette - use HSV to get distinct colors with consistent brightness
        self.universe_colors = {}
        
        for i, universe in enumerate(sorted(universes)):
            # Generate HSV color and convert to RGB
            hue = i / len(universes)
            # Create a bright, saturated color
            r, g, b = self.hsv_to_rgb(hue, 0.8, 0.9)
            color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
            self.universe_colors[universe] = color
    
    def hsv_to_rgb(self, h, s, v):
        """Convert HSV color to RGB (values from 0-1)"""
        if s == 0.0:
            return v, v, v
        
        i = int(h * 6)
        f = (h * 6) - i
        p = v * (1 - s)
        q = v * (1 - s * f)
        t = v * (1 - s * (1 - f))
        
        i = i % 6
        if i == 0:
            return v, t, p
        elif i == 1:
            return q, v, p
        elif i == 2:
            return p, v, t
        elif i == 3:
            return p, q, v
        elif i == 4:
            return t, p, v
        else:
            return v, p, q
    
    def update_entity_universe_map(self):
        """Create a mapping of entity IDs to universes for color coding"""
        self.entity_universe_map = {}
        
        for entry in self.config_data:
            universe = entry["universe"]
            from_id = entry["from"]
            to_id = entry["to"]
            
            for entity_id in range(from_id, to_id + 1):
                self.entity_universe_map[entity_id] = universe
    
    def draw_led_wall(self, *args):
        """Draw the LED wall visualization on the canvas"""
        self.canvas.delete("all")  # Clear canvas
        
        # Get current zoom level
        zoom = self.zoom_var.get()
        
        # LED wall dimensions
        wall_width = 128
        wall_height = 128
        
        # LED size based on zoom
        led_size = 5 * zoom
        spacing = 1 * zoom  # Space between LEDs
        
        # Total canvas size needed
        canvas_width = wall_width * (led_size + spacing)
        canvas_height = wall_height * (led_size + spacing)
        
        # Configure canvas scrolling
        self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))
        
        # Get display mode
        display_mode = self.display_var.get()
        
        # Track entity positions for interaction
        self.entity_positions = {}
        
        # Draw the grid
        entity_id = 100  # Starting entity ID based on the sample config
        
        for y in range(wall_height):
            for x in range(wall_width):
                # Calculate position
                x1 = x * (led_size + spacing)
                y1 = y * (led_size + spacing)
                x2 = x1 + led_size
                y2 = y1 + led_size
                
                # Determine color based on display mode
                if display_mode == "universe" and entity_id in self.entity_universe_map:
                    universe = self.entity_universe_map.get(entity_id)
                    color = self.universe_colors.get(universe, "gray")
                else:
                    # Default gray for entities without mapping
                    color = "gray"
                
                # Draw the LED
                led_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, width=0, tags=f"led_{entity_id}")
                
                # Store position for interaction
                self.entity_positions[entity_id] = (x, y, led_id)
                
                # If in entity mode, add entity ID as text
                if display_mode == "entity" and (x % 8 == 0 and y % 8 == 0):  # Only show some IDs to avoid clutter
                    self.canvas.create_text(
                        x1 + led_size/2,
                        y1 + led_size/2,
                        text=str(entity_id),
                        fill="white",
                        font=("Arial", max(int(7 * zoom), 1))
                    )
                
                entity_id += 1
    
    def on_zoom_change(self, *args):
        """Handle zoom level changes"""
        self.draw_led_wall()
    
    def on_canvas_click(self, event):
        """Handle click on the canvas"""
        # Convert canvas coordinates to LED grid coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Get current zoom level
        zoom = self.zoom_var.get()
        led_size = 5 * zoom
        spacing = 1 * zoom
        
        # Calculate grid position
        grid_x = int(canvas_x / (led_size + spacing))
        grid_y = int(canvas_y / (led_size + spacing))
        
        # Find entity at this position
        entity_id = 100 + grid_y * 128 + grid_x
        
        if entity_id in self.entity_positions:
            # Update selected entity
            if self.selected_entity:
                # Reset previous selection
                _, _, prev_led_id = self.entity_positions.get(self.selected_entity, (0, 0, None))
                if prev_led_id:
                    universe = self.entity_universe_map.get(self.selected_entity)
                    self.canvas.itemconfig(
                        prev_led_id, 
                        outline="",
                        width=0
                    )
            
            # Highlight new selection
            self.selected_entity = entity_id
            _, _, led_id = self.entity_positions.get(entity_id, (0, 0, None))
            if led_id:
                self.canvas.itemconfig(
                    led_id, 
                    outline="white",
                    width=2
                )
            
            # Update info panel
            universe = self.entity_universe_map.get(entity_id, "Not mapped")
            info_text = f"Entity ID: {entity_id} | Universe: {universe}"
            
            # Find controller IP for this entity
            controller_ip = "Unknown"
            for entry in self.config_data:
                if entry["from"] <= entity_id <= entry["to"]:
                    controller_ip = entry["ip"]
                    break
            
            info_text += f" | Controller IP: {controller_ip} | Position: ({grid_x}, {grid_y})"
            self.info_label.config(text=info_text)
            
            # If there's a parent reference, update it to show the selected entity
            if hasattr(self.parent, 'highlight_entity'):
                self.parent.highlight_entity(entity_id)
    
    def on_canvas_hover(self, event):
        """Handle mouse hover on the canvas"""
        # Convert canvas coordinates to LED grid coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Get current zoom level
        zoom = self.zoom_var.get()
        led_size = 5 * zoom
        spacing = 1 * zoom
        
        # Calculate grid position
        grid_x = int(canvas_x / (led_size + spacing))
        grid_y = int(canvas_y / (led_size + spacing))
        
        # Find entity at this position
        entity_id = 100 + grid_y * 128 + grid_x
        
        if entity_id in self.entity_positions:
            # Update info panel
            universe = self.entity_universe_map.get(entity_id, "Not mapped")
            info_text = f"Entity ID: {entity_id} | Universe: {universe} | Position: ({grid_x}, {grid_y})"
            self.info_label.config(text=info_text)


class ImprovedConfigEditor(tk.Tk):
    """Improved version of the P1 Router Configuration Editor"""
    
    def __init__(self):
        super().__init__()
        self.title("P1 Router Configuration Editor")
        self.geometry("1200x800")
        self.config_data = []
        self.validation = ValidationResult()
        self.selected_row = None
        self.vis_window = None  # Reference to visualization window
        self.network_testing_window = None  # Reference to network testing window
        self.multi_select_mode = False
        self.selected_indices = set()  # Track multiple selections
        
        # Update CONFIG_PATH with absolute path
        global CONFIG_PATH
        CONFIG_PATH = get_config_path()
        print(f"Using config path: {CONFIG_PATH}")
        
        self.load_config()
        self.setup_ui()
        
        # Initialize filtering system after UI is set up
        self.filtered_indices = set(range(len(self.config_data))) if self.config_data else set()
        
        self.update_validation()
        self.populate_grid()
    
    def setup_ui(self):
        """Set up the user interface"""
        self.setup_styles()
        
        # Main container frame
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 1. Header with status
        self.header_frame = ttk.Frame(main_container, style="Header.TFrame")
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = ttk.Label(
            self.header_frame, 
            text="Validating configuration...", 
            style="Header.TLabel",
            padding=(10, 5)
        )
        self.status_label.pack(side=tk.LEFT)
        
        self.stats_label = ttk.Label(
            self.header_frame,
            text="",
            style="Header.TLabel",
            padding=(10, 5)
        )
        self.stats_label.pack(side=tk.RIGHT)
        
        # Selection info
        self.selection_label = ttk.Label(
            self.header_frame,
            text="",
            style="Header.TLabel",
            padding=(10, 5)
        )
        self.selection_label.pack(side=tk.RIGHT, padx=(20, 0))
        
        # 2. Toolbar with common actions
        toolbar = ttk.Frame(main_container)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # Main action buttons
        ttk.Button(toolbar, text="Add Entry", command=self.add_entry).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Delete Selected", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Save", command=self.save_config).pack(side=tk.LEFT, padx=5)
        
        # Bulk edit buttons
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(toolbar, text="Bulk Edit", command=self.open_bulk_edit).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Clear Selection", command=self.clear_selection).pack(side=tk.LEFT, padx=5)
        
        # Secondary actions
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(toolbar, text="Import CSV", command=self.import_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Export CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Run Main Router", command=self.run_main).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Run Tester", command=self.run_tester).pack(side=tk.LEFT, padx=5)
        
        # Add LED wall visualization button
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(
            toolbar, 
            text="LED Wall Visualization", 
            command=self.show_led_visualization
        ).pack(side=tk.LEFT, padx=5)
        
        # Add network testing tools button
        ttk.Button(
            toolbar, 
            text="Network Testing Tools", 
            command=self.show_network_testing
        ).pack(side=tk.LEFT, padx=5)
        
        # Add animation tool button
        ttk.Button(
            toolbar, 
            text="Animation Tool", 
            command=self.show_animation_tool
        ).pack(side=tk.LEFT, padx=5)
        
        # 3. Split view container
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel: Navigator (will be implemented in phase 2)
        self.nav_frame = ttk.LabelFrame(content_frame, text="Navigator")
        self.nav_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), expand=False)
        
        # Placeholder for navigator
        nav_placeholder = ttk.Label(self.nav_frame, text="Coming in next update", padding=20)
        nav_placeholder.pack(pady=50)
        
        self.setup_navigator()
        
        # Right panel: Main config grid
        grid_frame = ttk.Frame(content_frame)
        grid_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configuration grid with scrollbars
        grid_with_scroll = ttk.Frame(grid_frame)
        grid_with_scroll.pack(fill=tk.BOTH, expand=True)
        
        # Create the configuration grid (TreeView) with multi-select enabled
        self.grid = ttk.Treeview(
            grid_with_scroll,
            columns=("universe", "from", "to", "ip", "status", "original_idx"),
            show="headings",
            selectmode="extended"  # Enable multi-select
        )
        
        # Configure columns
        self.grid.heading("universe", text="Universe")
        self.grid.heading("from", text="From ID")
        self.grid.heading("to", text="To ID")
        self.grid.heading("ip", text="Controller IP")
        self.grid.heading("status", text="Status")
        
        self.grid.column("universe", width=100, anchor=tk.CENTER)
        self.grid.column("from", width=100, anchor=tk.CENTER)
        self.grid.column("to", width=100, anchor=tk.CENTER)
        self.grid.column("ip", width=150, anchor=tk.CENTER)
        self.grid.column("status", width=200, anchor=tk.W)
        
        # Hide the original_idx column (used for internal tracking)
        self.grid.column("original_idx", width=0, minwidth=0)
        self.grid.heading("original_idx", text="")
        
        # Add scrollbars
        y_scroll = ttk.Scrollbar(grid_with_scroll, orient=tk.VERTICAL, command=self.grid.yview)
        x_scroll = ttk.Scrollbar(grid_with_scroll, orient=tk.HORIZONTAL, command=self.grid.xview)
        self.grid.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
        # Pack the grid and scrollbars
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.grid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind events
        self.grid.bind("<ButtonRelease-1>", self.on_grid_click)
        self.grid.bind("<Return>", self.edit_selected)
        self.grid.bind("<Double-1>", self.edit_selected)
        self.grid.bind("<<TreeviewSelect>>", self.on_selection_change)
        
        # Bind keyboard shortcuts
        self.bind("<Control-a>", lambda e: self.select_all())
        self.bind("<Delete>", lambda e: self.delete_selected())
        self.bind("<Control-b>", lambda e: self.open_bulk_edit())
        
        # 4. Properties panel for detailed editing
        self.properties_frame = ttk.LabelFrame(main_container, text="Properties")
        self.properties_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Create a form layout for properties
        props_form = ttk.Frame(self.properties_frame)
        props_form.pack(fill=tk.X, padx=10, pady=10)
        
        # Form fields
        # Universe
        universe_frame = ttk.Frame(props_form)
        universe_frame.pack(fill=tk.X, pady=5)
        ttk.Label(universe_frame, text="Universe:").pack(side=tk.LEFT, padx=(0, 10))
        self.universe_var = tk.IntVar()
        universe_spin = ttk.Spinbox(universe_frame, from_=0, to=255, width=10, textvariable=self.universe_var)
        universe_spin.pack(side=tk.LEFT)
        
        # From - To ID
        range_frame = ttk.Frame(props_form)
        range_frame.pack(fill=tk.X, pady=5)
        ttk.Label(range_frame, text="Entity ID Range:").pack(side=tk.LEFT, padx=(0, 10))
        self.from_var = tk.IntVar()
        self.to_var = tk.IntVar()
        from_spin = ttk.Spinbox(range_frame, from_=0, to=9999, width=10, textvariable=self.from_var)
        to_spin = ttk.Spinbox(range_frame, from_=0, to=9999, width=10, textvariable=self.to_var)
        from_spin.pack(side=tk.LEFT)
        ttk.Label(range_frame, text=" to ").pack(side=tk.LEFT)
        to_spin.pack(side=tk.LEFT)
        
        # IP Address
        ip_frame = ttk.Frame(props_form)
        ip_frame.pack(fill=tk.X, pady=5)
        ttk.Label(ip_frame, text="Controller IP:").pack(side=tk.LEFT, padx=(0, 10))
        self.ip_var = tk.StringVar()
        ip_entry = ttk.Entry(ip_frame, width=20, textvariable=self.ip_var)
        ip_entry.pack(side=tk.LEFT)
        
        # Apply button
        button_frame = ttk.Frame(props_form)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Apply Changes", command=self.apply_property_changes).pack(side=tk.RIGHT)
        
        # 5. Footer with help
        footer = ttk.Frame(main_container)
        footer.pack(fill=tk.X, pady=(10, 0))
        
        help_text = "Select rows to edit. Use Ctrl+Click for multi-select, Shift+Click for range select. Press Ctrl+B for bulk edit."
        footer_label = ttk.Label(footer, text=help_text, foreground="#555555")
        footer_label.pack(side=tk.LEFT)
        
        # Disable properties until row is selected
        self.disable_properties()
    
    def on_selection_change(self, event=None):
        """Handle selection changes in the grid"""
        selected_items = self.grid.selection()
        self.selected_indices = set()
        
        for item in selected_items:
            # Try to get the original index from the hidden column
            try:
                original_index = self.grid.set(item, "original_idx")
                if original_index and str(original_index).isdigit():
                    self.selected_indices.add(int(original_index))
                else:
                    # Fallback to grid index for backward compatibility
                    index = self.grid.index(item)
                    self.selected_indices.add(index)
            except:
                # Fallback to grid index for backward compatibility
                index = self.grid.index(item)
                self.selected_indices.add(index)
        
        # Update selection display
        count = len(self.selected_indices)
        if count == 0:
            self.selection_label.config(text="")
            self.disable_properties()
        elif count == 1:
            self.selection_label.config(text="1 item selected")
            self.selected_row = list(self.selected_indices)[0]
            self.update_properties()
        else:
            self.selection_label.config(text=f"{count} items selected")
            self.disable_properties()
    
    def select_all(self):
        """Select all items in the grid"""
        self.grid.selection_set(self.grid.get_children())
        self.on_selection_change()
    
    def clear_selection(self):
        """Clear all selections"""
        self.grid.selection_remove(self.grid.selection())
        self.on_selection_change()
    
    def open_bulk_edit(self):
        """Open the bulk edit dialog"""
        if not self.selected_indices:
            messagebox.showwarning("No Selection", "Please select one or more rows to edit.")
            return
        
        # Open bulk edit dialog
        dialog = BulkEditDialog(self, list(self.selected_indices), self.config_data)
        self.wait_window(dialog)
        
        # Process the result
        if dialog.result:
            self.apply_bulk_changes(dialog.result)
    
    def apply_bulk_changes(self, bulk_result):
        """Apply bulk edit changes to the configuration"""
        action = bulk_result["action"]
        indices = bulk_result["indices"]
        
        if action == "delete":
            # Delete selected entries (in reverse order to maintain indices)
            for idx in sorted(indices, reverse=True):
                if 0 <= idx < len(self.config_data):
                    self.config_data.pop(idx)
        
        elif action == "duplicate":
            # Duplicate selected entries with offset
            offset = bulk_result["offset"]
            new_entries = []
            
            for idx in indices:
                if 0 <= idx < len(self.config_data):
                    entry = self.config_data[idx].copy()
                    entry["from"] += offset
                    entry["to"] += offset
                    new_entries.append(entry)
            
            self.config_data.extend(new_entries)
        
        elif action == "modify":
            # Apply modifications to selected entries
            changes = bulk_result["changes"]
            
            for i, idx in enumerate(indices):
                if 0 <= idx < len(self.config_data):
                    entry = self.config_data[idx]
                    
                    # Apply universe changes
                    if "universe" in changes:
                        universe_change = changes["universe"]
                        if universe_change["mode"] == "set":
                            entry["universe"] = universe_change["value"]
                        elif universe_change["mode"] == "increment":
                            entry["universe"] = universe_change["start"] + i
                    
                    # Apply IP changes
                    if "ip" in changes:
                        ip_change = changes["ip"]
                        if ip_change["mode"] == "set":
                            entry["ip"] = ip_change["value"]
                    
                    # Apply range changes
                    if "range" in changes:
                        range_change = changes["range"]
                        if range_change["mode"] == "offset":
                            offset = range_change["value"]
                            entry["from"] += offset
                            entry["to"] += offset
                    
                    # Apply pattern changes
                    if "pattern" in changes:
                        pattern = changes["pattern"]
                        if pattern["type"] == "sequential_universe":
                            entities_per_universe = pattern["entities_per_universe"]
                            entity_count = entry["to"] - entry["from"] + 1
                            entry["universe"] = pattern["start_universe"] + (i * entity_count) // entities_per_universe
        
        # Update the interface
        self.update_validation()
        self.populate_grid()
        self.clear_selection()
        
        # Update visualization if open
        if self.vis_window and hasattr(self.vis_window, 'winfo_exists') and self.vis_window.winfo_exists():
            self.vis_window.config_data = self.config_data
            self.vis_window.update_entity_universe_map()
            self.vis_window.assign_universe_colors()
            self.vis_window.draw_led_wall()
    
    def setup_styles(self):
        """Set up ttk styles for the application"""
        style = ttk.Style()
        style.configure("Header.TFrame", background=COLORS["header_bg"])
        style.configure("Header.TLabel", 
                         background=COLORS["header_bg"],
                         foreground=COLORS["header_fg"],
                         font=("Arial", 12, "bold"))
        
        # Configure Treeview for alternating row colors
        style.map('Treeview', background=[('selected', COLORS["selected"])])
        style.configure("Treeview", rowheight=25)
    
    def setup_navigator(self):
        """Set up the navigation panel with smart search and filter capabilities"""
        # Clear the placeholder
        for widget in self.nav_frame.winfo_children():
            widget.destroy()
        
        # Configure the navigator frame
        self.nav_frame.configure(text="Search & Filter", padding=10)
        self.nav_frame.configure(width=300)
        
        # Create scrollable content
        nav_canvas = tk.Canvas(self.nav_frame, highlightthickness=0)
        nav_scrollbar = ttk.Scrollbar(self.nav_frame, orient="vertical", command=nav_canvas.yview)
        self.nav_content = ttk.Frame(nav_canvas)
        
        nav_canvas.configure(yscrollcommand=nav_scrollbar.set)
        nav_canvas.create_window((0, 0), window=self.nav_content, anchor="nw")
        
        # Pack scrolling components
        nav_scrollbar.pack(side="right", fill="y")
        nav_canvas.pack(side="left", fill="both", expand=True)
        
        # Update scroll region when content changes
        def configure_scroll_region(event):
            nav_canvas.configure(scrollregion=nav_canvas.bbox("all"))
        self.nav_content.bind("<Configure>", configure_scroll_region)
        
        # === SMART SEARCH SECTION ===
        search_section = ttk.LabelFrame(self.nav_content, text="Smart Search", padding=10)
        search_section.pack(fill="x", pady=(0, 10))
        
        # Main search box
        search_frame = ttk.Frame(search_section)
        search_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(search_frame, text="Search:").pack(anchor="w")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(fill="x", pady=(2, 0))
        self.search_var.trace("w", self.on_search_change)
        
        # Search mode selection
        mode_frame = ttk.Frame(search_section)
        mode_frame.pack(fill="x", pady=(5, 0))
        
        ttk.Label(mode_frame, text="Search Mode:").pack(anchor="w")
        self.search_mode = tk.StringVar(value="smart")
        
        search_modes = [
            ("Smart (Auto-detect)", "smart"),
            ("Entity ID Range", "entity_range"),
            ("Universe Number", "universe"),
            ("IP Address", "ip"),
            ("Text Match", "text")
        ]
        
        for text, value in search_modes:
            ttk.Radiobutton(mode_frame, text=text, variable=self.search_mode, 
                           value=value, command=self.apply_filters).pack(anchor="w")
        
        # Quick search buttons
        quick_frame = ttk.Frame(search_section)
        quick_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Label(quick_frame, text="Quick Searches:").pack(anchor="w")
        quick_buttons_frame = ttk.Frame(quick_frame)
        quick_buttons_frame.pack(fill="x", pady=(2, 0))
        
        ttk.Button(quick_buttons_frame, text="Errors", 
                  command=lambda: self.quick_search("errors")).pack(side="left", padx=(0, 5))
        ttk.Button(quick_buttons_frame, text="Warnings", 
                  command=lambda: self.quick_search("warnings")).pack(side="left", padx=(0, 5))
        ttk.Button(quick_buttons_frame, text="Large Ranges", 
                  command=lambda: self.quick_search("large_ranges")).pack(side="left")
        
        # === FILTER SECTION ===
        filter_section = ttk.LabelFrame(self.nav_content, text="Advanced Filters", padding=10)
        filter_section.pack(fill="x", pady=(0, 10))
        
        # Universe filter
        universe_frame = ttk.Frame(filter_section)
        universe_frame.pack(fill="x", pady=(0, 5))
        
        self.filter_universe_enabled = tk.BooleanVar()
        ttk.Checkbutton(universe_frame, text="Filter by Universe:", 
                       variable=self.filter_universe_enabled,
                       command=self.apply_filters).pack(anchor="w")
        
        universe_range_frame = ttk.Frame(universe_frame)
        universe_range_frame.pack(fill="x", padx=(20, 0))
        
        ttk.Label(universe_range_frame, text="From:").grid(row=0, column=0, sticky="w")
        self.universe_from = tk.IntVar(value=0)
        ttk.Spinbox(universe_range_frame, from_=0, to=255, width=8, 
                   textvariable=self.universe_from, command=self.apply_filters).grid(row=0, column=1, padx=(5, 10))
        
        ttk.Label(universe_range_frame, text="To:").grid(row=0, column=2, sticky="w")
        self.universe_to = tk.IntVar(value=255)
        ttk.Spinbox(universe_range_frame, from_=0, to=255, width=8, 
                   textvariable=self.universe_to, command=self.apply_filters).grid(row=0, column=3, padx=(5, 0))
        
        # Entity ID filter
        entity_frame = ttk.Frame(filter_section)
        entity_frame.pack(fill="x", pady=(5, 5))
        
        self.filter_entity_enabled = tk.BooleanVar()
        ttk.Checkbutton(entity_frame, text="Filter by Entity ID Range:", 
                       variable=self.filter_entity_enabled,
                       command=self.apply_filters).pack(anchor="w")
        
        entity_range_frame = ttk.Frame(entity_frame)
        entity_range_frame.pack(fill="x", padx=(20, 0))
        
        ttk.Label(entity_range_frame, text="From:").grid(row=0, column=0, sticky="w")
        self.entity_from = tk.IntVar(value=0)
        ttk.Spinbox(entity_range_frame, from_=0, to=9999, width=8, 
                   textvariable=self.entity_from, command=self.apply_filters).grid(row=0, column=1, padx=(5, 10))
        
        ttk.Label(entity_range_frame, text="To:").grid(row=0, column=2, sticky="w")
        self.entity_to = tk.IntVar(value=9999)
        ttk.Spinbox(entity_range_frame, from_=0, to=9999, width=8, 
                   textvariable=self.entity_to, command=self.apply_filters).grid(row=0, column=3, padx=(5, 0))
        
        # IP Address filter
        ip_frame = ttk.Frame(filter_section)
        ip_frame.pack(fill="x", pady=(5, 5))
        
        self.filter_ip_enabled = tk.BooleanVar()
        ttk.Checkbutton(ip_frame, text="Filter by IP Subnet:", 
                       variable=self.filter_ip_enabled,
                       command=self.apply_filters).pack(anchor="w")
        
        ip_input_frame = ttk.Frame(ip_frame)
        ip_input_frame.pack(fill="x", padx=(20, 0))
        
        ttk.Label(ip_input_frame, text="Subnet:").pack(side="left")
        self.ip_filter_var = tk.StringVar(value="192.168.1.")
        ttk.Entry(ip_input_frame, textvariable=self.ip_filter_var, width=15).pack(side="left", padx=(5, 0))
        self.ip_filter_var.trace("w", lambda *args: self.apply_filters() if self.filter_ip_enabled.get() else None)
        
        # Status filter
        status_frame = ttk.Frame(filter_section)
        status_frame.pack(fill="x", pady=(5, 0))
        
        ttk.Label(status_frame, text="Filter by Status:").pack(anchor="w")
        status_check_frame = ttk.Frame(status_frame)
        status_check_frame.pack(fill="x", padx=(20, 0))
        
        self.show_valid = tk.BooleanVar(value=True)
        self.show_warnings = tk.BooleanVar(value=True)
        self.show_errors = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(status_check_frame, text="Valid", variable=self.show_valid, 
                       command=self.apply_filters).pack(anchor="w")
        ttk.Checkbutton(status_check_frame, text="Warnings", variable=self.show_warnings, 
                       command=self.apply_filters).pack(anchor="w")
        ttk.Checkbutton(status_check_frame, text="Errors", variable=self.show_errors, 
                       command=self.apply_filters).pack(anchor="w")
        
        # === STATISTICS SECTION ===
        stats_section = ttk.LabelFrame(self.nav_content, text="Filter Results", padding=10)
        stats_section.pack(fill="x", pady=(0, 10))
        
        self.filter_stats_label = ttk.Label(stats_section, text="No filters applied", 
                                           font=("Arial", 9), foreground="#666")
        self.filter_stats_label.pack(anchor="w")
        
        # === ACTIONS SECTION ===
        actions_section = ttk.LabelFrame(self.nav_content, text="Filter Actions", padding=10)
        actions_section.pack(fill="x")
        
        action_buttons_frame = ttk.Frame(actions_section)
        action_buttons_frame.pack(fill="x")
        
        ttk.Button(action_buttons_frame, text="Clear All Filters", 
                  command=self.clear_all_filters).pack(fill="x", pady=(0, 5))
        ttk.Button(action_buttons_frame, text="Select Filtered", 
                  command=self.select_filtered_items).pack(fill="x", pady=(0, 5))
        ttk.Button(action_buttons_frame, text="Export Filtered", 
                  command=self.export_filtered_items).pack(fill="x")
        
        # Initialize filter state
        self.filtered_indices = set(range(len(self.config_data))) if self.config_data else set()
        self.update_filter_stats()
    
    def on_search_change(self, *args):
        """Handle search text changes with debouncing"""
        # Cancel previous delayed call if exists
        if hasattr(self, '_search_after_id'):
            self.after_cancel(self._search_after_id)
        
        # Schedule new search after 300ms delay
        self._search_after_id = self.after(300, self.apply_filters)
    
    def apply_filters(self):
        """Apply all active filters to the configuration data"""
        if not hasattr(self, 'config_data') or not self.config_data:
            return
        
        self.filtered_indices = set()
        search_text = self.search_var.get().strip()
        search_mode = self.search_mode.get()
        
        for i, entry in enumerate(self.config_data):
            # Start with item included
            include_item = True
            
            # Apply search filter
            if search_text:
                include_item = self.matches_search(entry, search_text, search_mode)
            
            # Apply universe filter
            if include_item and self.filter_universe_enabled.get():
                universe = entry["universe"]
                if not (self.universe_from.get() <= universe <= self.universe_to.get()):
                    include_item = False
            
            # Apply entity ID filter
            if include_item and self.filter_entity_enabled.get():
                entity_from = entry["from"]
                entity_to = entry["to"]
                filter_from = self.entity_from.get()
                filter_to = self.entity_to.get()
                
                # Check if ranges overlap
                if not (entity_from <= filter_to and entity_to >= filter_from):
                    include_item = False
            
            # Apply IP filter
            if include_item and self.filter_ip_enabled.get():
                ip_filter = self.ip_filter_var.get().strip()
                if ip_filter and not entry["ip"].startswith(ip_filter):
                    include_item = False
            
            # Apply status filter
            if include_item:
                universe = entry["universe"]
                from_id = entry["from"]
                to_id = entry["to"]
                
                has_error = False
                has_warning = False
                
                # Check for errors (overlaps)
                if universe in self.validation.overlaps:
                    overlap_range = range(from_id, to_id + 1)
                    if any(entity_id in overlap_range for entity_id in self.validation.overlaps[universe]):
                        has_error = True
                
                # Check for warnings (capacity)
                if universe in self.validation.capacity_warnings and not has_error:
                    has_warning = True
                
                # Apply status filter
                if has_error and not self.show_errors.get():
                    include_item = False
                elif has_warning and not has_error and not self.show_warnings.get():
                    include_item = False
                elif not has_error and not has_warning and not self.show_valid.get():
                    include_item = False
            
            if include_item:
                self.filtered_indices.add(i)
        
        # Update the grid display
        self.update_grid_visibility()
        self.update_filter_stats()
    
    def matches_search(self, entry, search_text, search_mode):
        """Check if an entry matches the search criteria"""
        search_lower = search_text.lower()
        
        # Handle special search filters
        if search_text == "large_range_filter":
            # Return entries with more than 100 entities
            range_size = entry["to"] - entry["from"] + 1
            return range_size > 100
        
        if search_mode == "smart":
            # Auto-detect search type and apply intelligent matching
            
            # Check if it's a number range (e.g., "100-200", "100:200", "100..200")
            if any(sep in search_text for sep in ['-', ':', '..']):
                return self.matches_range_search(entry, search_text)
            
            # Check if it's a pure number (entity ID or universe)
            if search_text.isdigit():
                number = int(search_text)
                return (entry["universe"] == number or 
                       entry["from"] <= number <= entry["to"])
            
            # Check if it looks like an IP address
            if '.' in search_text and any(char.isdigit() for char in search_text):
                return entry["ip"].lower().find(search_lower) != -1
            
            # Default to text search across all fields
            return (str(entry["universe"]).find(search_text) != -1 or
                   str(entry["from"]).find(search_text) != -1 or
                   str(entry["to"]).find(search_text) != -1 or
                   entry["ip"].lower().find(search_lower) != -1)
        
        elif search_mode == "entity_range":
            return self.matches_range_search(entry, search_text)
        
        elif search_mode == "universe":
            if search_text.isdigit():
                return entry["universe"] == int(search_text)
            return str(entry["universe"]).find(search_text) != -1
        
        elif search_mode == "ip":
            return entry["ip"].lower().find(search_lower) != -1
        
        elif search_mode == "text":
            # Search all fields as text
            return (str(entry["universe"]).find(search_text) != -1 or
                   str(entry["from"]).find(search_text) != -1 or
                   str(entry["to"]).find(search_text) != -1 or
                   entry["ip"].lower().find(search_lower) != -1)
        
        return True
    
    def matches_range_search(self, entry, search_text):
        """Handle range-based searches like '100-200' or '100:200'"""
        try:
            # Handle different range separators
            if '-' in search_text and not search_text.startswith('-'):
                parts = search_text.split('-', 1)
            elif ':' in search_text:
                parts = search_text.split(':', 1)
            elif '..' in search_text:
                parts = search_text.split('..', 1)
            else:
                # Single number
                if search_text.isdigit():
                    number = int(search_text)
                    return entry["from"] <= number <= entry["to"]
                return False
            
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                search_from = int(parts[0])
                search_to = int(parts[1])
                
                # Check if ranges overlap
                return (entry["from"] <= search_to and entry["to"] >= search_from)
            
        except ValueError:
            pass
        
        return False
    
    def quick_search(self, search_type):
        """Perform quick searches for common patterns"""
        # Clear existing search
        self.search_var.set("")
        
        # Reset all filters first
        self.filter_universe_enabled.set(False)
        self.filter_entity_enabled.set(False)
        self.filter_ip_enabled.set(False)
        
        if search_type == "errors":
            self.show_valid.set(False)
            self.show_warnings.set(False)
            self.show_errors.set(True)
        
        elif search_type == "warnings":
            self.show_valid.set(False)
            self.show_warnings.set(True)
            self.show_errors.set(False)
        
        elif search_type == "large_ranges":
            # Find entries with more than 100 entities
            self.show_valid.set(True)
            self.show_warnings.set(True)
            self.show_errors.set(True)
            # Set a special search to identify large ranges
            self.search_var.set("large_range_filter")
        
        self.apply_filters()
    
    def update_grid_visibility(self):
        """Update grid to show only filtered items"""
        # Store current selection
        selected_items = self.grid.selection()
        selected_indices = set()
        for item in selected_items:
            idx = self.grid.index(item)
            selected_indices.add(idx)
        
        # Clear and repopulate grid
        for item in self.grid.get_children():
            self.grid.delete(item)
        
        # Add only filtered items
        for original_idx in sorted(self.filtered_indices):
            if original_idx >= len(self.config_data):
                continue
                
            entry = self.config_data[original_idx]
            universe = entry["universe"]
            from_id = entry["from"]
            to_id = entry["to"]
            ip = entry["ip"]
            
            # Determine status
            status = "OK"
            tags = ()
            
            # Check for overlaps
            if universe in self.validation.overlaps:
                overlap_range = range(from_id, to_id + 1)
                if any(entity_id in overlap_range for entity_id in self.validation.overlaps[universe]):
                    status = "Error: Overlapping entities"
                    tags = ("error",)
            
            # Check for capacity warnings
            if universe in self.validation.capacity_warnings:
                if "error" not in tags:
                    status = f"Warning: Universe capacity exceeded ({self.validation.capacity_warnings[universe]} entities)"
                    tags = ("warning",)
            
            # Insert into grid with original index stored in hidden column
            item_id = self.grid.insert("", tk.END, values=(universe, from_id, to_id, ip, status, original_idx), tags=tags)
            
            # Apply row coloring
            if "error" in tags:
                self.grid.item(item_id, tags=("error",))
            elif "warning" in tags:
                self.grid.item(item_id, tags=("warning",))
        
        # Configure tag colors
        self.grid.tag_configure("error", background=COLORS["error"])
        self.grid.tag_configure("warning", background=COLORS["warning"])
        self.grid.tag_configure("alternate", background=COLORS["alternate_row"])
        
        # Try to restore selection if items are still visible
        new_selection = []
        for item in self.grid.get_children():
            try:
                original_idx = self.grid.set(item, "original_idx")
                if original_idx and str(original_idx).isdigit():
                    original_idx = int(original_idx)
                    if original_idx in selected_indices:
                        new_selection.append(item)
            except:
                pass
        
        if new_selection:
            self.grid.selection_set(new_selection)
    
    def update_filter_stats(self):
        """Update the filter statistics display"""
        total_items = len(self.config_data) if self.config_data else 0
        filtered_items = len(self.filtered_indices)
        
        if filtered_items == total_items:
            stats_text = f"Showing all {total_items} entries"
        else:
            stats_text = f"Showing {filtered_items} of {total_items} entries"
            
            # Add breakdown by status if filters are active
            if filtered_items < total_items:
                valid_count = 0
                warning_count = 0
                error_count = 0
                
                for idx in self.filtered_indices:
                    if idx >= len(self.config_data):
                        continue
                    
                    entry = self.config_data[idx]
                    universe = entry["universe"]
                    from_id = entry["from"]
                    to_id = entry["to"]
                    
                    has_error = False
                    has_warning = False
                    
                    if universe in self.validation.overlaps:
                        overlap_range = range(from_id, to_id + 1)
                        if any(entity_id in overlap_range for entity_id in self.validation.overlaps[universe]):
                            has_error = True
                    
                    if universe in self.validation.capacity_warnings and not has_error:
                        has_warning = True
                    
                    if has_error:
                        error_count += 1
                    elif has_warning:
                        warning_count += 1
                    else:
                        valid_count += 1
                
                if error_count > 0 or warning_count > 0:
                    stats_text += f"\n✓ {valid_count} valid"
                    if warning_count > 0:
                        stats_text += f", ⚠ {warning_count} warnings"
                    if error_count > 0:
                        stats_text += f", ✗ {error_count} errors"
        
        self.filter_stats_label.config(text=stats_text)
    
    def clear_all_filters(self):
        """Clear all search and filter criteria"""
        # Clear search
        self.search_var.set("")
        
        # Clear filters
        self.filter_universe_enabled.set(False)
        self.filter_entity_enabled.set(False)
        self.filter_ip_enabled.set(False)
        
        # Reset status filters
        self.show_valid.set(True)
        self.show_warnings.set(True)
        self.show_errors.set(True)
        
        # Reset search mode
        self.search_mode.set("smart")
        
        self.apply_filters()
    
    def select_filtered_items(self):
        """Select all currently filtered items in the grid"""
        all_items = self.grid.get_children()
        if all_items:
            self.grid.selection_set(all_items)
            self.on_selection_change()
    
    def export_filtered_items(self):
        """Export only the filtered items to CSV"""
        if not self.filtered_indices:
            messagebox.showwarning("No Data", "No items match the current filters.")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv", 
            filetypes=[("CSV files", "*.csv")],
            title="Export Filtered Data"
        )
        if not filepath:
            return
        
        try:
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["universe", "from", "to", "ip"])
                writer.writeheader()
                
                for idx in sorted(self.filtered_indices):
                    if idx < len(self.config_data):
                        writer.writerow(self.config_data[idx])
            
            messagebox.showinfo("Export", f"Exported {len(self.filtered_indices)} filtered entries to CSV.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export filtered CSV: {e}")
    
    def load_config(self):
        """Load the configuration file"""
        try:
            # Ensure config directory exists
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r") as f:
                    self.config_data = json.load(f)
            else:
                # Create default config if not exists
                self.config_data = [{
                    "universe": 0,
                    "from": 100,
                    "to": 269,
                    "ip": "192.168.1.45"
                }]
                self.save_config()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")
            self.destroy()
    
    def save_config(self):
        """Save the configuration file"""
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(self.config_data, f, indent=2)
            messagebox.showinfo("Success", "Configuration saved successfully.")
            self.update_validation()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")
    
    def update_validation(self):
        """Validate the current configuration and update status"""
        self.validation.validate_config(self.config_data)
        
        # Update status message
        status_msg, status_type = self.validation.get_status_summary()
        self.status_label.configure(text=status_msg)
        
        # Set background color based on status
        style = ttk.Style()
        style.configure("Header.TFrame", background=COLORS[status_type])
        style.configure("Header.TLabel", 
                         background=COLORS[status_type],
                         foreground="#000000" if status_type != "error" else "#ffffff")
        
        # Update stats
        universe_count = len(set(entry["universe"] for entry in self.config_data))
        ip_count = len(set(entry["ip"] for entry in self.config_data))
        entity_count = sum(entry["to"] - entry["from"] + 1 for entry in self.config_data)
        stats = f"Universes: {universe_count} | IPs: {ip_count} | Entities: {entity_count}"
        self.stats_label.configure(text=stats)
    
    def populate_grid(self):
        """Populate the grid with configuration data"""
        # Update validation first
        self.update_validation()
        
        # If we have search/filter capabilities, use the filtered view
        if hasattr(self, 'apply_filters') and hasattr(self, 'filtered_indices'):
            self.apply_filters()
        else:
            # Fallback to original behavior if search/filter not initialized yet
            self._populate_grid_original()
    
    def _populate_grid_original(self):
        """Original grid population method (fallback)"""
        # Clear existing items
        for item in self.grid.get_children():
            self.grid.delete(item)
        
        # Add data
        for idx, entry in enumerate(self.config_data):
            universe = entry["universe"]
            from_id = entry["from"]
            to_id = entry["to"]
            ip = entry["ip"]
            
            # Determine status and tags for row
            status = "OK"
            tags = ()
            
            # Check for overlaps
            if universe in self.validation.overlaps:
                overlap_range = range(from_id, to_id + 1)
                if any(entity_id in overlap_range for entity_id in self.validation.overlaps[universe]):
                    status = "Error: Overlapping entities"
                    tags = ("error",)
            
            # Check for capacity warnings
            if universe in self.validation.capacity_warnings:
                if "error" not in tags:
                    status = f"Warning: Universe capacity exceeded ({self.validation.capacity_warnings[universe]} entities)"
                    tags = ("warning",)
            
            # Insert into grid with original index stored in hidden column
            item_id = self.grid.insert("", tk.END, values=(universe, from_id, to_id, ip, status, idx), tags=tags)
            
            # Apply row coloring
            if "error" in tags:
                self.grid.item(item_id, tags=("error",))
            elif "warning" in tags:
                self.grid.item(item_id, tags=("warning",))
        
        # Configure tag colors
        self.grid.tag_configure("error", background=COLORS["error"])
        self.grid.tag_configure("warning", background=COLORS["warning"])
        self.grid.tag_configure("alternate", background=COLORS["alternate_row"])
    
    def on_grid_click(self, event):
        """Handle grid click event to select a row"""
        region = self.grid.identify_region(event.x, event.y)
        if region == "cell":
            # Get the selected item
            item_id = self.grid.identify_row(event.y)
            if item_id:
                # Let the selection change handler deal with updates
                pass
    
    def edit_selected(self, event=None):
        """Start editing the selected cell"""
        if not self.grid.selection():
            return
        
        # For now, just load the properties panel
        selected_items = self.grid.selection()
        if len(selected_items) == 1:
            self.selected_row = self.grid.index(selected_items[0])
            self.update_properties()
    
    def update_properties(self):
        """Update the properties panel with selected row data"""
        if self.selected_row is not None and self.selected_row < len(self.config_data):
            entry = self.config_data[self.selected_row]
            
            # Update properties form
            self.universe_var.set(entry["universe"])
            self.from_var.set(entry["from"])
            self.to_var.set(entry["to"])
            self.ip_var.set(entry["ip"])
            
            # Enable the properties panel
            self.enable_properties()
    
    def enable_properties(self):
        """Enable the properties panel fields"""
        for child in self.properties_frame.winfo_children():
            for widget in child.winfo_children():
                if isinstance(widget, (ttk.Entry, ttk.Spinbox, ttk.Button)):
                    widget.configure(state="normal")
    
    def disable_properties(self):
        """Disable the properties panel fields"""
        for child in self.properties_frame.winfo_children():
            for widget in child.winfo_children():
                if isinstance(widget, (ttk.Entry, ttk.Spinbox, ttk.Button)):
                    widget.configure(state="disabled")
    
    def apply_property_changes(self):
        """Apply changes from the properties panel to the selected row"""
        if self.selected_row is None or self.selected_row >= len(self.config_data):
            return
        
        # Update the configuration data
        self.config_data[self.selected_row] = {
            "universe": self.universe_var.get(),
            "from": self.from_var.get(),
            "to": self.to_var.get(),
            "ip": self.ip_var.get()
        }
        
        # Update the grid
        self.update_validation()
        self.populate_grid()
        
        # Select the updated row
        if self.selected_row < len(self.grid.get_children()):
            item_id = self.grid.get_children()[self.selected_row]
            self.grid.selection_set(item_id)
            self.grid.see(item_id)
    
    def add_entry(self):
        """Add a new entry to the configuration"""
        new_entry = {
            "universe": 0,
            "from": 0,
            "to": 0,
            "ip": "192.168.1.45"
        }
        self.config_data.append(new_entry)
        self.update_validation()
        self.populate_grid()
        
        # Select the new entry
        self.selected_row = len(self.config_data) - 1
        item_id = self.grid.get_children()[-1]
        self.grid.selection_set(item_id)
        self.grid.see(item_id)
        self.update_properties()
    
    def delete_selected(self):
        """Delete the selected entries"""
        if not self.selected_indices:
            messagebox.showwarning("No Selection", "Please select one or more rows to delete.")
            return
        
        count = len(self.selected_indices)
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {count} entr{'ies' if count > 1 else 'y'}?"):
            # Delete in reverse order to maintain indices
            for idx in sorted(self.selected_indices, reverse=True):
                if 0 <= idx < len(self.config_data):
                    self.config_data.pop(idx)
            
            self.update_validation()
            self.populate_grid()
            self.clear_selection()
    
    def import_csv(self):
        """Import configuration from CSV file"""
        filepath = filedialog.askopenfilename(title="Select CSV file", filetypes=[("CSV files", "*.csv")])
        if not filepath:
            return
        
        try:
            with open(filepath, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                self.config_data = []
                for row in reader:
                    self.config_data.append({
                        "universe": int(row["universe"]),
                        "from": int(row["from"]),
                        "to": int(row["to"]),
                        "ip": row["ip"]
                    })
            self.update_validation()
            self.populate_grid()
            messagebox.showinfo("Import", "CSV imported successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import CSV: {e}")
    
    def export_csv(self):
        """Export configuration to CSV file"""
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not filepath:
            return
        
        try:
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["universe", "from", "to", "ip"])
                writer.writeheader()
                for entry in self.config_data:
                    writer.writerow(entry)
            messagebox.showinfo("Export", "CSV exported successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV: {e}")
    
    def run_main(self):
        """Run the main router application"""
        self.save_config()
        try:
            # Get script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)  # Go up one level if in download-and-launch
            
            # Try multiple possible paths for main.py
            possible_paths = [
                os.path.join(project_root, "main.py"),                   # /main.py
                os.path.join(project_root, "p1_router", "main.py"),      # /p1_router/main.py
                os.path.join(project_root, "..", "p1_router", "main.py") # /../p1_router/main.py
            ]
            
            main_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    main_path = path
                    break
            
            if main_path:
                print(f"Running main router from: {main_path}")
                subprocess.Popen(["python", main_path])
            else:
                # Last resort - try running from current directory
                messagebox.showinfo("Path Info", f"Trying to run main.py from current directory: {os.getcwd()}")
                subprocess.Popen(["python", "main.py"])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start main router: {e}")
    
    def run_tester(self):
        """Run the tester application"""
        self.save_config()
        try:
            # Get script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)  # Go up one level if in download-and-launch
            
            # Try multiple possible paths for tester.py
            possible_paths = [
                os.path.join(project_root, "tester.py"),                   # /tester.py
                os.path.join(project_root, "p1_router", "tester.py"),      # /p1_router/tester.py
                os.path.join(project_root, "..", "p1_router", "tester.py") # /../p1_router/tester.py
            ]
            
            tester_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    tester_path = path
                    break
            
            if tester_path:
                print(f"Running tester from: {tester_path}")
                subprocess.Popen(["python", tester_path])
            else:
                # Last resort - try running from current directory
                messagebox.showinfo("Path Info", f"Trying to run tester.py from current directory: {os.getcwd()}")
                subprocess.Popen(["python", "tester.py"])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start tester: {e}")
    
    def show_led_visualization(self):
        """Show the LED wall visualization window"""
        # Close existing window if open
        if self.vis_window and self.vis_window.winfo_exists():
            self.vis_window.destroy()
        
        # Create new visualization window
        self.vis_window = LEDWallVisualization(self, self.config_data)
        
        # Set as transient to main window
        self.vis_window.transient(self)
        
        # Focus the new window
        self.vis_window.focus_set()
    
    def show_network_testing(self):
        """Open the network testing tools window"""
        try:
            testing_window = NetworkTestingTools(self, self.config_data)
            testing_window.transient(self)
            testing_window.grab_set()
            self.wait_window(testing_window)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open network testing tools: {e}")
    
    def show_animation_tool(self):
        """Launch the animation tool in a separate window"""
        try:
            # Import the animation_tool_launcher module
            import sys
            import os
            import subprocess
            
            # Get the path to the animation_tool_launcher.py file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            launcher_path = os.path.join(script_dir, "animation_tool_launcher.py")
            
            # Check if the launcher exists, if not use the one in download-and-launch
            if not os.path.exists(launcher_path):
                launcher_path = os.path.join(os.path.dirname(script_dir), "download-and-launch", "animation_tool_launcher.py")
            
            if not os.path.exists(launcher_path):
                messagebox.showerror("Error", "Could not find animation_tool_launcher.py")
                return
                
            # Get the project root directory to set as the working directory
            project_root = os.path.dirname(script_dir)
            
            # Launch the animation tool in a separate process
            subprocess.Popen([sys.executable, launcher_path], cwd=project_root)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not launch Animation Tool: {e}")
            import traceback
            traceback.print_exc()
    
    def highlight_entity(self, entity_id):
        """Highlight an entity in the grid when selected in the visualization"""
        # Find which row contains this entity
        for i, entry in enumerate(self.config_data):
            if entry["from"] <= entity_id <= entry["to"]:
                # Select this row
                item_id = self.grid.get_children()[i]
                self.grid.selection_set(item_id)
                self.grid.see(item_id)
                
                # Update properties panel
                self.selected_row = i
                self.update_properties()
                break


if __name__ == "__main__":
    app = ImprovedConfigEditor()
    app.mainloop() 