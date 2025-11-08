import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import time
import json
import logging
from datetime import datetime
import os 
import sys
from colorama import init, Fore, Style # Import Colorama

# Initialize Colorama for cross-platform colored terminal output
init(autoreset=True)

# Local imports
from monitor import SystemMonitor
from ai_integration import GeminiAIIntegration
from gui_elements import ScrollingTextHandler, create_tooltip
from utils import save_data_to_csv, save_data_to_excel

# Configure logging for the application
# We use a custom handler for the GUI, but the root logger still goes to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerformanceEnhancerApp:
    """
    Main application class for the Advanced System Performance Enhancer (ASPE) - AI Driven.
    Provides a GUI for monitoring system performance with a robust, functional main looping 
    composition for data refresh and multi-threaded AI analysis.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("ASPE: AI-Driven Hardware-Software Optimizer (v2.0)")
        self.root.geometry("1600x1000") # Increased size for more detail
        self.root.minsize(1200, 700) 
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing) 

        self.api_key = tk.StringVar(value="") 
        self.monitoring_active = False
        self._stop_monitoring_event = threading.Event() 
        self.data_history = [] 
        
        self.system_monitor = SystemMonitor()
        self.ai_integration = GeminiAIIntegration()

        # Thread references
        self.monitoring_thread = None
        
        # Default update interval: 10 seconds
        self.update_interval_ms = 10000 

        self._create_widgets()
        
        # Redirect application logging to the AI results display
        self.log_handler = ScrollingTextHandler(self.ai_results_display)
        logger.addHandler(self.log_handler)
        self.log_handler.setLevel(logging.INFO) 
        
        self._load_api_key_from_file() 
        self._update_button_states() 

        logger.info(f"{Fore.CYAN}--- ASPE Application Initialized ---{Style.RESET_ALL}")
        print(f"{Fore.CYAN}--- ASPE Application Initialized ---{Style.RESET_ALL}")

    def _create_widgets(self):
        """Initializes and lays out all GUI widgets."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)

        # Tab Frames
        monitor_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitor_frame, text="System Monitoring & Flux Display")

        ai_control_frame = ttk.Frame(self.notebook)
        self.notebook.add(ai_control_frame, text="AI Analysis & Enhancement")
        
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")

        # Create Tab Contents
        self._create_monitor_tab(monitor_frame)
        self._create_ai_control_tab(ai_control_frame)
        self._create_settings_tab(settings_frame)

    def _create_monitor_tab(self, parent_frame):
        """Creates widgets for the System Monitoring tab."""
        
        # --- Control Frame ---
        control_frame = ttk.Frame(parent_frame, padding=(10, 5))
        control_frame.pack(pady=5, padx=10, fill="x")
        
        self.start_btn = ttk.Button(control_frame, text="Start Monitoring (F5)", command=self.start_monitoring)
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = ttk.Button(control_frame, text="Stop Monitoring (F6)", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_btn.pack(side="left", padx=5)

        self.enhance_btn = ttk.Button(control_frame, text=f"{Fore.GREEN}TRIGGER AI ENHANCEMENT ALGORITHM{Style.RESET_ALL}", 
                                       command=self.run_ai_enhancement, state=tk.DISABLED)
        self.enhance_btn.pack(side="left", padx=25)
        create_tooltip(self.enhance_btn, "Sends current, detailed system flux data to Gemini AI for deep optimization analysis.")
        
        ttk.Button(control_frame, text="Clear Display & Logs", command=self.clear_display).pack(side="right", padx=5)
        ttk.Button(control_frame, text="Save Data Snapshot (CSV)", command=self.save_current_data_csv, state=tk.DISABLED).pack(side="right", padx=5)


        # --- Display Frames (Split) ---
        display_paned = ttk.Panedwindow(parent_frame, orient=tk.VERTICAL)
        display_paned.pack(pady=5, padx=10, fill="both", expand=True)

        # 1. Performance Data Display
        perf_frame = ttk.Frame(display_paned)
        display_paned.add(perf_frame, weight=3) # Takes 3/4 of the space
        
        self.performance_display_label = ttk.Label(perf_frame, text=f"** High-Complexity System Flux & Data Transit (40+ Attributes) **", 
                                                 font=("Arial", 10, "bold"))
        self.performance_display_label.pack(pady=(5, 2), padx=5, anchor="w")
        
        # Use a listbox for a structured, two-column display of data attributes
        self.perf_tree = ttk.Treeview(perf_frame, columns=("Attribute", "Value"), show="headings", selectmode="browse")
        self.perf_tree.heading("Attribute", text="Hardware/Software Attribute")
        self.perf_tree.heading("Value", text="Current Value & Unit")
        self.perf_tree.column("Attribute", width=400, anchor=tk.W)
        self.perf_tree.column("Value", width=200, anchor=tk.W)
        self.perf_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self._initialize_perf_tree()
        

        # 2. AI Results Display (Logs)
        ai_log_frame = ttk.Frame(display_paned)
        display_paned.add(ai_log_frame, weight=1) # Takes 1/4 of the space
        
        self.ai_results_label = ttk.Label(ai_log_frame, text="AI Analysis and Optimization Log (Terminal Output Mirror):", font=("Arial", 10, "bold"))
        self.ai_results_label.pack(pady=(5, 2), padx=5, anchor="w")
        self.ai_results_display = scrolledtext.ScrolledText(ai_log_frame, wrap=tk.WORD, height=8, font=("Consolas", 9), relief="sunken", borderwidth=2)
        self.ai_results_display.pack(pady=5, padx=5, fill="both", expand=True)

        # Bind F-keys
        self.root.bind('<F5>', lambda event: self.start_monitoring())
        self.root.bind('<F6>', lambda event: self.stop_monitoring())


    def _initialize_perf_tree(self):
        """Initializes the Treeview with static attribute headers and groupings."""
        self.tree_rows = {}
        # Define the 40+ attributes in logical groups
        groups = {
            "CORE_USAGE": ["CPU Usage (%)", "CPU Freq (GHz)", "Logical Cores", "CPU User Time (%)", "CPU System Time (%)", "CPU Idle Time (%)", "CPU Interrupt Time (%)"],
            "MEMORY_STATE": ["Memory Usage (%)", "Used Memory (GB)", "Available Memory (GB)", "Cached Memory (GB)", "Swap Usage (%)", "Shared Memory (GB)"],
            "GPU_STATE": ["GPU Usage (%)", "GPU Memory (GB)", "GPU Temp (°C)"],
            "I/O_TRANSIT_RATES": ["Disk Read Rate (MB/s)", "Disk Write Rate (MB/s)", "Net Sent (MB/s)", "Net Received (MB/s)", "Disk I/O Latency (Sim/ms)", "Network Packet Errors"],
            "SYSTEM_STATE": ["Running Processes", "Top CPU Process", "System Uptime (h)", "Open File Descriptors (Sim)", "Network Total Connections", "CPU Temp (°C)", "Fan Speed (%)"],
            "STATIC_INFO": ["Operating System", "System Architecture", "CPU Model (Sim)", "Total RAM (GB)", "Boot Time", "Python Version"],
            "FLUX_CONCEPTUAL": ["Energetic Flux (Sim) [J/s]", "Transistor State Change Rate (Sim) [Hz]", "Circuitry Integrity (Sim) [%]", "Binary Data Byte Transit (Sim) [B/s]", "Hexadecimal Energy Flow (Sim) [0x]", "Software-Hardware I/O Saturation (Sim) [%]", "Electrical Controlled Pulses (Sim) [Pulse/s]", "Unwanted Transit Purity Check (Sim) [%]"]
        }
        
        # Configure tag colors for better visibility
        self.perf_tree.tag_configure('GroupHeader', font=('Consolas', 10, 'bold'), background='#E0E0E0', foreground='#333333')
        self.perf_tree.tag_configure('FluxMetric', foreground='blue')
        self.perf_tree.tag_configure('HighUsage', foreground='red')
        self.perf_tree.tag_configure('Normal', foreground='black')

        for group_name, attributes in groups.items():
            iid_group = self.perf_tree.insert("", "end", text=group_name, values=(group_name.replace('_', ' ').title(), ""), tags=('GroupHeader',))
            for attr in attributes:
                iid = self.perf_tree.insert(iid_group, "end", text=attr, values=(attr, "Fetching..."), tags=('Normal',))
                self.tree_rows[attr] = iid
        
        self.perf_tree.bind("<Button-1>", self.on_tree_click) # Prevent collapse/expand

    def on_tree_click(self, event):
        """Prevents the headers from being selected/toggled."""
        region = self.perf_tree.identify("region", event.x, event.y)
        if region == "heading":
            return "break"
    
    def _update_perf_tree(self, data):
        """Updates the Treeview with the latest data snapshot."""
        if "Error" in data:
            self.perf_tree.delete(*self.perf_tree.get_children())
            self.perf_tree.insert("", "end", values=("ERROR", data["Error"]), tags=('HighUsage',))
            return

        for attr, iid in self.tree_rows.items():
            value = data.get(attr, "N/A")
            tag = 'Normal'
            
            # Apply dynamic tags/colors
            if "Flux" in attr or "Transit" in attr or "Circuitry" in attr or "Pulses" in attr or "Hexadecimal" in attr:
                tag = 'FluxMetric'
            elif attr in ["CPU Usage (%)", "Memory Usage (%)", "GPU Usage (%)"] and isinstance(value, (int, float)) and value > 80:
                tag = 'HighUsage'
            elif attr == "CPU Temp (°C)" and isinstance(value, (int, float)) and value > 85:
                 tag = 'HighUsage'
            
            # Update the value in the treeview
            self.perf_tree.item(iid, values=(attr, str(value)), tags=(tag,))
            
        # Ensure all groups are expanded
        for iid in self.perf_tree.get_children():
             self.perf_tree.item(iid, open=True)


    def _create_ai_control_tab(self, parent_frame):
        """Creates widgets for the AI Analysis & Enhancement tab."""
        ai_action_frame = ttk.LabelFrame(parent_frame, text="AI Analysis and Enhancement Reports", padding=(15, 10))
        ai_action_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Use a large, formatted text display for the full AI report
        ttk.Label(ai_action_frame, text="Full AI Enhancement Report:", font=("Arial", 10, "bold")).pack(pady=(0, 5), anchor="w")
        self.ai_report_display = scrolledtext.ScrolledText(ai_action_frame, wrap=tk.WORD, height=20, font=("Consolas", 10), relief="sunken", borderwidth=2)
        self.ai_report_display.pack(pady=5, fill="both", expand=True)
        self.ai_report_display.insert(tk.END, "The comprehensive AI analysis and enhancement report will appear here.\n")
        
        # Tag configuration for the report display
        self.ai_report_display.tag_config("Header", font=("Consolas", 12, "bold"), foreground="#007ACC")
        self.ai_report_display.tag_config("Critical", foreground="red", font=("Consolas", 10, "bold"))
        self.ai_report_display.tag_config("Suggestion", foreground="green")
        self.ai_report_display.tag_config("Conceptual", foreground="blue")
        self.ai_report_display.tag_config("Command", foreground="purple")


    def _create_settings_tab(self, parent_frame):
        """Creates widgets for the Settings tab."""
        # --- API Key Configuration ---
        api_config_frame = ttk.LabelFrame(parent_frame, text="Gemini API Key Configuration", padding=(15, 10))
        api_config_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(api_config_frame, text="Enter Gemini API Key:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        api_entry = ttk.Entry(api_config_frame, textvariable=self.api_key, show="*", width=60)
        api_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(api_config_frame, text="Set & Save API Key", command=self._set_api_key).grid(row=0, column=2, padx=5, pady=5)

        # --- Monitoring Settings ---
        monitor_config_frame = ttk.LabelFrame(parent_frame, text="Monitoring and Main Loop Settings", padding=(15, 10))
        monitor_config_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(monitor_config_frame, text="Update Interval (seconds):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.interval_entry = ttk.Entry(monitor_config_frame, width=10)
        # FIX: The original error was related to this line's structure in Python 2 or misuse of str(). Fixed here.
        self.interval_entry.insert(0, str(self.update_interval_ms // 1000)) 
        self.interval_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(monitor_config_frame, text="Apply Interval", command=self._apply_interval).grid(row=0, column=2, padx=5, pady=5)

        # --- Data Management ---
        data_management_frame = ttk.LabelFrame(parent_frame, text="Historical Data Management", padding=(15, 10))
        data_management_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(data_management_frame, text=f"Data Snapshots in History: {len(self.data_history)}", anchor="w").pack(pady=5, padx=5, fill="x")
        ttk.Button(data_management_frame, text="Export All History to CSV", command=self.save_all_history_csv).pack(pady=5, padx=5, fill="x")
        ttk.Button(data_management_frame, text=f"{Fore.RED}Clear All Stored Historical Data{Style.RESET_ALL}", command=self.clear_all_history).pack(pady=10, padx=5, fill="x")
        
    def _load_api_key_from_file(self):
        """Loads the API key from a local file if it exists."""
        key_file = "gemini_api_key.txt"
        if os.path.exists(key_file):
            try:
                with open(key_file, "r") as f:
                    key = f.read().strip()
                    if key:
                        self.api_key.set(key)
                        self.ai_integration.set_api_key(key)
                        logger.info(f"{Fore.GREEN}Gemini API Key loaded from file and initialized.{Style.RESET_ALL}")
            except Exception as e:
                logger.error(f"{Fore.RED}Failed to load API key from file: {e}{Style.RESET_ALL}")
        else:
            logger.warning(f"{Fore.YELLOW}No Gemini API key file found. AI analysis is simulated.{Style.RESET_ALL}")

    def _save_api_key_to_file(self, key):
        """Saves the API key to a local file."""
        key_file = "gemini_api_key.txt"
        try:
            with open(key_file, "w") as f:
                f.write(key)
            logger.info(f"{Fore.GREEN}Gemini API Key saved to file.{Style.RESET_ALL}")
        except Exception as e:
            logger.error(f"{Fore.RED}Failed to save API key to file: {e}{Style.RESET_ALL}")

    def _set_api_key(self):
        """Sets the Gemini API key, updates AI integration, and saves to file."""
        key = self.api_key.get()
        if key:
            try:
                self.ai_integration.set_api_key(key)
                self._save_api_key_to_file(key) 
                self._update_button_states()
                messagebox.showinfo("API Key Set", "Gemini API Key successfully configured and saved.")
            except ValueError as e:
                messagebox.showerror("API Key Error", f"Failed to set API Key: {e}")
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        else:
            messagebox.showwarning("API Key Missing", "Please enter your Gemini API Key.")

    def _apply_interval(self):
        """Applies the user-defined monitoring interval."""
        try:
            interval_sec = int(self.interval_entry.get())
            if 5 <= interval_sec <= 600: 
                self.update_interval_ms = interval_sec * 1000
                logger.info(f"{Fore.MAGENTA}Monitoring interval set to {interval_sec} seconds.{Style.RESET_ALL}")
                # If monitoring is active, stop and restart to apply new interval
                if self.monitoring_active:
                    self.stop_monitoring()
                    self.start_monitoring()
            else:
                messagebox.showwarning("Invalid Interval", "Interval must be between 5 and 600 seconds.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid integer for the interval.")

    def _update_button_states(self):
        """Manages the state of control buttons based on application status."""
        is_ai_ready = self.ai_integration.ai_enabled or self.api_key.get() # Allow running enhance in simulation mode
        
        self.start_btn.config(state=tk.DISABLED if self.monitoring_active else tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL if self.monitoring_active else tk.DISABLED)
        self.enhance_btn.config(state=tk.NORMAL if self.monitoring_active and is_ai_ready else tk.DISABLED)
        
        # Data saving is always disabled if no data has been collected
        has_data = len(self.data_history) > 0
        save_state = tk.NORMAL if has_data else tk.DISABLED
        
        # Only enable save buttons after first successful data collection
        self.root.nametowidget(self.start_btn.winfo_parent()).winfo_children()[-1].config(state=save_state) # Save CSV
        self.root.nametowidget(self.start_btn.winfo_parent()).winfo_children()[-2].config(state=save_state) # Save Excel (using indices might break layout)
        
        # The AI log display should reflect the AI status
        self.ai_report_display.insert(tk.END, f"\n{'-'*50}\n", "Header")
        if self.ai_integration.ai_enabled:
            self.ai_report_display.insert(tk.END, f"AI Status: Gemini API Key ACTIVE. Full analysis enabled.\n", "Suggestion")
        else:
            self.ai_report_display.insert(tk.END, f"AI Status: Simulated. Using local algorithm for conceptual responses.\n", "Warning")
        self.ai_report_display.see(tk.END)


    # --- Monitoring and Main Loop Functions ---

    def start_monitoring(self):
        """Starts the background monitoring thread."""
        if not self.monitoring_active:
            self.monitoring_active = True
            self._stop_monitoring_event.clear()
            self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitoring_thread.start()
            self._update_button_states()
            logger.info(f"{Fore.GREEN}System monitoring started by user. Main looping function active.{Style.RESET_ALL}")
            print(f"{Fore.GREEN}System monitoring started by user. Main looping function active.{Style.RESET_ALL}")

    def stop_monitoring(self):
        """Stops the background monitoring thread."""
        if self.monitoring_active:
            self.monitoring_active = False
            self._stop_monitoring_event.set() # Signal thread to stop
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                 # Optional: wait for thread to finish cleanly
                 # self.monitoring_thread.join(timeout=2) 
                 pass
            self._update_button_states()
            logger.info(f"{Fore.RED}System monitoring stopped by user.{Style.RESET_ALL}")
            print(f"{Fore.RED}System monitoring stopped by user.{Style.RESET_ALL}")

    def _monitor_loop(self):
        """
        The functional main looping composition. Runs in a separate thread 
        to continuously collect data without blocking the GUI.
        """
        while not self._stop_monitoring_event.is_set():
            start_time = time.time()
            data_snapshot = self.system_monitor.get_detailed_system_data()
            
            if "Error" not in data_snapshot:
                self.data_history.append(data_snapshot)
                # Use the thread-safe way to update the GUI
                self.root.after(0, lambda d=data_snapshot: self._update_gui_displays(d)) 
            else:
                 logger.error(f"{Fore.RED}Monitoring Error: {data_snapshot['Error']}{Style.RESET_ALL}")
            
            # Calculate sleep time to maintain a precise interval
            elapsed_time = time.time() - start_time
            sleep_time = max(0, (self.update_interval_ms / 1000) - elapsed_time)
            
            self._stop_monitoring_event.wait(sleep_time) # Wait using the event

    def _update_gui_displays(self, data):
        """Updates the GUI elements with the latest data snapshot (called from main thread)."""
        self._update_perf_tree(data)
        self._update_button_states() # Check if save buttons should be enabled
        
        # Log a summary of the flux metrics to the GUI log panel
        flux_summary = f"[{data['Timestamp']}] FLUX SNAPSHOT | CPU:{data['CPU Usage (%)']}% | MEM:{data['Memory Usage (%)']}% | TEMP:{data['CPU Temp (°C)']}°C | Integrity:{data['Circuitry Integrity (Sim)']} | Hex Flow:{data['Hexadecimal Energy Flow (Sim)']}"
        logger.info(flux_summary)
        print(f"{Fore.BLUE}{flux_summary}{Style.RESET_ALL}") # Console mirror

    # --- AI Integration Functions ---

    def run_ai_enhancement(self):
        """Starts the AI analysis in a background thread."""
        if not self.monitoring_active:
            messagebox.showwarning("Monitoring Required", "Please start monitoring before running an AI enhancement.")
            return

        if self.data_history:
            latest_data = self.data_history[-1]
            self.ai_analysis_thread = threading.Thread(target=self._ai_analysis_worker, args=(latest_data,), daemon=True)
            self.ai_analysis_thread.start()
            logger.info(f"{Fore.YELLOW}Triggering AI enhancement with latest data snapshot: {latest_data.get('Timestamp')}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Triggering AI enhancement with latest data snapshot: {latest_data.get('Timestamp')}{Style.RESET_ALL}")

    def _ai_analysis_worker(self, data_snapshot):
        """Worker function for calling the Gemini AI API."""
        try:
            # Call the AI integration function
            ai_response = self.ai_integration.call_gemini_api(data_snapshot)
            
            # Use the thread-safe way to update the GUI
            self.root.after(0, lambda r=ai_response: self._display_ai_report(r, data_snapshot['Timestamp']))
            
        except Exception as e:
            logger.error(f"{Fore.RED}AI Analysis failed in worker thread: {e}{Style.RESET_ALL}", exc_info=True)
            self.root.after(0, lambda: messagebox.showerror("AI Error", "AI Analysis failed. See logs for details."))

    def _display_ai_report(self, ai_response, timestamp):
        """Formats and displays the detailed AI report."""
        self.ai_report_display.delete(1.0, tk.END)
        self.ai_report_display.insert(tk.END, f"*** AI Enhancement Report: {timestamp} ***\n\n", "Header")

        self.ai_report_display.insert(tk.END, "1. System Analysis:\n", "Header")
        self.ai_report_display.insert(tk.END, f"  {ai_response.get('analysis', 'N/A')}\n\n", ("Critical" if "CRITICAL" in ai_response.get('analysis', '').upper() else "Normal"))

        self.ai_report_display.insert(tk.END, "2. Identified Root Cause(s):\n", "Header")
        self.ai_report_display.insert(tk.END, f"  {ai_response.get('root_cause', 'N/A')}\n\n")

        self.ai_report_display.insert(tk.END, "3. Software Optimization Suggestions:\n", "Header")
        for sug in ai_response.get('optimization_suggestions', []):
            self.ai_report_display.insert(tk.END, f"  - {sug}\n", "Suggestion")
        self.ai_report_display.insert(tk.END, "\n")

        self.ai_report_display.insert(tk.END, "4. Recommended Correction Commands (USE WITH EXTREME CAUTION!):\n", "Header")
        for cmd in ai_response.get('correction_commands', []):
            self.ai_report_display.insert(tk.END, f"  > {cmd}\n", "Command")
        self.ai_report_display.insert(tk.END, "\n")
        
        self.ai_report_display.insert(tk.END, "5. Hardware Enhancement Recommendations (Physical):\n", "Header")
        for hwe in ai_response.get('hardware_enhancements', []):
            self.ai_report_display.insert(tk.END, f"  * {hwe}\n")
        self.ai_report_display.insert(tk.END, "\n")

        self.ai_report_display.insert(tk.END, "6. Conceptual Transistor/Static Flux Enhancements (AI-Driven):\n", "Header")
        for conc in ai_response.get('conceptual_enhancements', []):
            self.ai_report_display.insert(tk.END, f"  * {conc}\n", "Conceptual")
        self.ai_report_display.insert(tk.END, f"\nGenerated By: {ai_response.get('generated_by', 'Unknown')}\n", "Header")

        self.ai_report_display.see(tk.END)
        logger.info(f"{Fore.CYAN}AI Report generated and displayed for snapshot {timestamp}.{Style.RESET_ALL}")
        print(f"{Fore.CYAN}AI Report generated and displayed for snapshot {timestamp}.{Style.RESET_ALL}")

    # --- Utility Functions ---

    def clear_display(self):
        """Clears all text displays."""
        self.perf_tree.delete(*self.perf_tree.get_children())
        self._initialize_perf_tree()
        self.ai_results_display.delete(1.0, tk.END)
        self.ai_report_display.delete(1.0, tk.END)
        logger.info(f"{Fore.YELLOW}Display panels cleared.{Style.RESET_ALL}")

    def clear_all_history(self):
        """Clears all stored historical data."""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear ALL collected historical data? This cannot be undone."):
            self.data_history.clear()
            self._update_button_states()
            logger.info(f"{Fore.RED}ALL historical data cleared from memory.{Style.RESET_ALL}")

    def save_current_data_csv(self):
        """Saves the last collected data snapshot to a CSV file."""
        if not self.data_history:
            messagebox.showwarning("No Data", "No data has been collected to save.")
            return
        
        # Save only the latest snapshot
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], initialfile=f"ASPE_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        if filepath:
            try:
                save_data_to_csv([self.data_history[-1]], filepath)
                messagebox.showinfo("Save Successful", f"Latest data snapshot saved to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save data: {e}")

    def save_all_history_csv(self):
        """Saves the entire historical data to a CSV file."""
        if not self.data_history:
            messagebox.showwarning("No Data", "No historical data has been collected to save.")
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], initialfile=f"ASPE_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        if filepath:
            try:
                save_data_to_csv(self.data_history, filepath)
                messagebox.showinfo("Save Successful", f"Historical data saved to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save data: {e}")

    def save_all_history_excel(self):
        """Saves the entire historical data to an Excel file."""
        if not self.data_history:
            messagebox.showwarning("No Data", "No historical data has been collected to save.")
            return
        
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")], initialfile=f"ASPE_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        if filepath:
            try:
                save_data_to_excel(self.data_history, filepath)
                messagebox.showinfo("Save Successful", f"Historical data saved to:\n{filepath}")
            except ImportError:
                messagebox.showerror("Save Error", "Required libraries (pandas/openpyxl) are missing. See console for instructions.")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save data: {e}")

    def on_closing(self):
        """Handles the application exit."""
        self.stop_monitoring()
        logger.info(f"{Fore.CYAN}Application closing. Goodbye.{Style.RESET_ALL}")
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    # Ensure all required packages are installed (for the user)
    try:
        import psutil
        import pandas # Checked here for a better error message, even if only used in utils.py
        import GPUtil
    except ImportError as e:
        print(f"\n{Fore.RED}*** CRITICAL DEPENDENCY MISSING ***{Style.RESET_ALL}")
        print(f"Please install required libraries: {Fore.YELLOW}pip install psutil pandas openpyxl gputil colorama{Style.RESET_ALL}\n")
        sys.exit(1)
        
    root = tk.Tk()
    app = PerformanceEnhancerApp(root)
    # The Tkinter mainloop is the primary functional main loop of the GUI application
    root.mainloop()