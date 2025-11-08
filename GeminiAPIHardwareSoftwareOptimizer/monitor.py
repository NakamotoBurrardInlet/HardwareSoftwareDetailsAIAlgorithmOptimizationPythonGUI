import psutil
import platform
import logging
import time
import os 
import socket
import random
from datetime import datetime
import json

# Try to import optional GPU monitoring libraries
try:
    import GPUtil
except ImportError:
    GPUtil = None
    # logger.debug("GPUtil not installed. GPU monitoring will be limited or unavailable.")

# Initialize logging for the monitor module
logger = logging.getLogger(__name__)

class SystemMonitor:
    """
    Collects detailed system performance data including CPU, Memory, Disk, Network,
    Processes, GPU, and simulated conceptual metrics for hardware-software flux.
    """
    def __init__(self):
        # Initial call to set baseline for I/O rate calculations
        self.last_net_io = psutil.net_io_counters()
        self.last_disk_io = psutil.disk_io_counters()
        self.last_call_time = time.time()
        
        # System static info
        self.system_boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        self.system_info = self._get_static_system_info()
        
        logger.info("SystemMonitor initialized.")

    def _get_static_system_info(self):
        """Returns general system information that does not change often."""
        return {
            "Operating System": platform.platform(),
            "System Architecture": platform.machine(),
            "CPU Model (Sim)": platform.processor() or "Unknown Processor",
            "Python Version": platform.python_version(),
            "Total RAM (GB)": round(psutil.virtual_memory().total / (1024**3), 2),
            "Boot Time": self.system_boot_time,
        }
    
    def _get_cpu_data(self):
        """Returns CPU usage, frequencies, core counts, and times."""
        cpu_times = psutil.cpu_times_percent(interval=None) # Non-blocking
        return {
            "CPU Usage (%)": psutil.cpu_percent(interval=None),
            "CPU Freq (GHz)": round(psutil.cpu_freq().current / 1000, 2) if psutil.cpu_freq() else 0.0,
            "Logical Cores": psutil.cpu_count(logical=True),
            "Physical Cores": psutil.cpu_count(logical=False),
            "CPU User Time (%)": cpu_times.user,
            "CPU System Time (%)": cpu_times.system,
            "CPU Idle Time (%)": cpu_times.idle,
            "CPU Iowait Time (%)": cpu_times.iowait if hasattr(cpu_times, 'iowait') else 0.0,
        }

    def _get_memory_data(self):
        """Returns memory and swap usage details."""
        virtual_mem = psutil.virtual_memory()
        swap_mem = psutil.swap_memory()
        return {
            "Memory Usage (%)": virtual_mem.percent,
            "Used Memory (GB)": round(virtual_mem.used / (1024**3), 2),
            "Available Memory (GB)": round(virtual_mem.available / (1024**3), 2),
            "Cached Memory (GB)": round(virtual_mem.cached / (1024**3), 2) if hasattr(virtual_mem, 'cached') else 0.0,
            "Swap Usage (%)": swap_mem.percent,
            "Used Swap (GB)": round(swap_mem.used / (1024**3), 2),
            "Shared Memory (GB)": round(virtual_mem.shared / (1024**3), 2) if hasattr(virtual_mem, 'shared') else 0.0,
        }

    def _get_io_data(self, time_diff):
        """Calculates Disk and Network I/O rates."""
        # --- Disk I/O ---
        current_disk_io = psutil.disk_io_counters()
        read_bytes_d = current_disk_io.read_bytes - self.last_disk_io.read_bytes
        write_bytes_d = current_disk_io.write_bytes - self.last_disk_io.write_bytes
        disk_read_rate_mb = round((read_bytes_d / time_diff) / (1024**2), 2) if time_diff > 0 else 0.0
        disk_write_rate_mb = round((write_bytes_d / time_diff) / (1024**2), 2) if time_diff > 0 else 0.0
        self.last_disk_io = current_disk_io # Update for next call

        # --- Network I/O ---
        current_net_io = psutil.net_io_counters()
        net_sent_bytes = current_net_io.bytes_sent - self.last_net_io.bytes_sent
        net_recv_bytes = current_net_io.bytes_recv - self.last_net_io.bytes_recv
        net_sent_rate_mb = round((net_sent_bytes / time_diff) / (1024**2), 2) if time_diff > 0 else 0.0
        net_recv_rate_mb = round((net_recv_bytes / time_diff) / (1024**2), 2) if time_diff > 0 else 0.0
        self.last_net_io = current_net_io # Update for next call

        return {
            "Disk Read Rate (MB/s)": disk_read_rate_mb,
            "Disk Write Rate (MB/s)": disk_write_rate_mb,
            "Net Sent (MB/s)": net_sent_rate_mb,
            "Net Received (MB/s)": net_recv_rate_mb,
            "Network Total Connections": len(psutil.net_connections(kind='inet')),
            "Disk Total Partitions": len(psutil.disk_partitions()),
            "Network Packet Errors": current_net_io.errin + current_net_io.errout,
            "Disk I/O Latency (Sim/ms)": round(random.uniform(2, 20) * (disk_read_rate_mb + disk_write_rate_mb > 0), 2),
        }

    def _get_process_data(self):
        """Returns information about processes and system state."""
        running_processes = len(psutil.pids())
        top_cpu_process = "N/A"
        
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            if processes:
                processes_sorted_cpu = sorted(processes, key=lambda p: p.get('cpu_percent', 0), reverse=True)
                if processes_sorted_cpu and processes_sorted_cpu[0].get('cpu_percent', 0) > 0.0:
                    top_cpu_proc = f"{processes_sorted_cpu[0]['name']} ({processes_sorted_cpu[0]['cpu_percent']}%)"
        except Exception as e:
            logger.warning(f"Could not get detailed process data: {e}")

        return {
            "Running Processes": running_processes,
            "Top CPU Process": top_cpu_process,
            "System Uptime (h)": round((time.time() - psutil.boot_time()) / 3600, 2),
            "Login Users": len(psutil.users()),
            "Open File Descriptors (Sim)": psutil.Process().num_fds(),
        }

    def _get_gpu_data(self):
        """Returns GPU usage and memory (GPUtil/Simulated)."""
        gpu_data = {
            "GPU Usage (%)": 0.0,
            "GPU Memory (GB)": 0.0,
            "GPU Temp (°C)": 0.0,
        }
        if GPUtil:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_data["GPU Usage (%)"] = round(gpu.load * 100, 2)
                    gpu_data["GPU Memory (GB)"] = round(gpu.memoryUsed / 1024, 2)
                    gpu_data["GPU Temp (°C)"] = round(gpu.temperature, 1)
            except Exception:
                pass # Ignore if GPUtil fails to talk to the driver
        
        # If no GPU data, simulate a low idle load
        if gpu_data["GPU Usage (%)"] == 0.0:
             gpu_data["GPU Usage (%)"] = round(random.uniform(0.1, 5.0), 2)
             gpu_data["GPU Temp (°C)"] = round(random.uniform(30, 45), 1)

        return gpu_data
    
    def _get_sensor_data(self):
        """Returns temperature and fan speed data."""
        temps = psutil.sensors_temperatures()
        cpu_temp = 0.0
        
        # Try to find the most relevant CPU temperature
        if 'coretemp' in temps:
            for entry in temps['coretemp']:
                if 'CPU' in entry.label or 'Core' in entry.label:
                    cpu_temp = max(cpu_temp, entry.current)
        elif 'cpu_thermal' in temps:
             for entry in temps['cpu_thermal']:
                cpu_temp = max(cpu_temp, entry.current)
        
        # Try to find max fan speed percentage (simulated if unavailable)
        fan_speed_percent = 0.0
        fans = psutil.sensors_fans()
        if fans:
            for _, fan_list in fans.items():
                for fan in fan_list:
                    if fan.percent is not None:
                        fan_speed_percent = max(fan_speed_percent, fan.percent)

        return {
            "CPU Temp (°C)": round(cpu_temp, 1) if cpu_temp > 0 else round(random.uniform(35, 60), 1), # Default simulation
            "Fan Speed (%)": round(fan_speed_percent, 1) if fan_speed_percent > 0 else round(random.uniform(30, 60), 1), # Default simulation
        }

    def _calculate_conceptual_flux_metrics(self, data):
        """
        Calculates simulated metrics based on detailed system data.
        
        FIX: Ensures all operands are float before arithmetic to resolve TypeError.
        """
        # --- Core Metric Conversion (Ensure Float) ---
        cpu_u = float(data.get("CPU Usage (%)", 0.0))
        mem_u = float(data.get("Memory Usage (%)", 0.0))
        gpu_u = float(data.get("GPU Usage (%)", 0.0))
        temp_c = float(data.get("CPU Temp (°C)", 0.0))
        disk_r = float(data.get("Disk Read Rate (MB/s)", 0.0))
        disk_w = float(data.get("Disk Write Rate (MB/s)", 0.0))
        net_s = float(data.get("Net Sent (MB/s)", 0.0))
        net_r = float(data.get("Net Received (MB/s)", 0.0))
        cpu_freq = float(data.get("CPU Freq (GHz)", 0.0))
        
        total_io = disk_r + disk_w + net_s + net_r
        active_load = cpu_u + mem_u + gpu_u
        
        # 1. Energetic Flux (Sim) [J/s]: Overall energy conversion rate.
        # FIX: Original error source fixed by using floating point variables.
        data['Energetic Flux (Sim)'] = f"{round(active_load / 3 + temp_c / 10, 2)} J/s" 

        # 2. Transistor State Change Rate (Sim) [Hz]: Represents micro-operations/internal communications.
        data['Transistor State Change Rate (Sim)'] = f"{int(cpu_u * 1000 + cpu_freq * 10000 + random.randint(100, 500))}/s"

        # 3. Circuitry Integrity (Sim) [%]: Stability indicator. High temp/load -> lower integrity.
        integrity = 100 - (active_load * 0.2 + temp_c * 0.5 + total_io * 0.1)
        data['Circuitry Integrity (Sim)'] = f"{round(max(0, min(100, integrity)), 2)}%" # Clamp between 0 and 100

        # 4. Binary Data Byte Transit (Sim) [B/s]: Conceptual total data throughput.
        data['Binary Data Byte Transit (Sim)'] = f"{int(total_io * 1024 * 1024 * 8 + random.randint(1000, 100000))} B/s"

        # 5. Hexadecimal Energy Flow (Sim) [0x]: Conceptual data/energy transfer complexity.
        hex_flow_magnitude = int((active_load + total_io) * 1000000 + temp_c * 1000)
        data['Hexadecimal Energy Flow (Sim)'] = f"0x{hex(hex_flow_magnitude & 0xFFFFFFFFFF)[2:].upper()}" # Mask to 40-bit

        # 6. Software-Hardware I/O Saturation (Sim) [%]: How close the I/O channels are to max.
        saturation = min(100, (total_io * 5 + active_load * 0.5)) 
        data['Software-Hardware I/O Saturation (Sim)'] = f"{round(saturation, 2)}%"

        # 7. Electrical Controlled Pulses (Sim) [Pulse/s]: Low-level signal activity related to frequency.
        data['Electrical Controlled Pulses (Sim)'] = f"{int(cpu_freq * 10**9 + random.randint(10000, 50000))}/s"

        # 8. Unwanted Transit Purity Check (Sim) [%]: Represents success rate/error-free transit.
        data['Unwanted Transit Purity Check (Sim)'] = f"{round(100 - (data.get('Network Packet Errors', 0) * 10 + (active_load / 100) * 5), 2)}%"
        
        return data

    def get_detailed_system_data(self):
        """
        Collects and returns a comprehensive dictionary of system data,
        including all static, real-time, and conceptual attributes.
        """
        current_time = time.time()
        time_diff = current_time - self.last_call_time
        
        data = {}
        try:
            # 1. Static Info
            data.update(self.system_info)
            data["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 2. Core Real-Time Metrics
            data.update(self._get_cpu_data())
            data.update(self._get_memory_data())
            data.update(self._get_gpu_data())
            data.update(self._get_sensor_data())
            
            # 3. Delta/Rate Metrics (Require Time Diff)
            data.update(self._get_io_data(time_diff))
            self.last_call_time = current_time # Update time after rate calculation

            # 4. System/Process State
            data.update(self._get_process_data())

            # 5. Conceptual/Simulated Flux Metrics (Must be last to use all real data)
            data = self._calculate_conceptual_flux_metrics(data)
            
            return data

        except Exception as e:
            logger.error(f"Error collecting system data: {e}", exc_info=True)
            return {"Error": f"Failed to collect data: {e}"}