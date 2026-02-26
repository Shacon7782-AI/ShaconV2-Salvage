import os
import psutil
import platform

class HardwareOptimizer:
    """
    Optimizes performance for i5-12500H (12 Cores: 4P + 8E).
    Focuses on pinning heavy LLM tasks to P-Cores (Threads 0-7).
    """
    def __init__(self):
        self.p_core_threads = list(range(8)) # Indices of P-core threads on 12500H
        self.system = platform.system()
    
    def apply_p_core_affinity(self, pid: int = None):
        """
        Pins the specified process (default current) to P-Cores.
        """
        if self.system != "Windows":
            print(f"[HARDWARE] CPU Affinity not yet implemented for {self.system}")
            return

        try:
            p = psutil.Process(pid or os.getpid())
            p.cpu_affinity(self.p_core_threads)
            print(f"[HARDWARE] Applied P-Core Affinity (Threads 0-7) to PID {p.pid}")
            
            # Audit the hardware optimization
            from app.core.immudb_sidecar import immudb
            immudb.log_operation(
                "HARDWARE_AFFINITY", 
                {"pid": p.pid, "threads": self.p_core_threads}
            )
        except Exception as e:
            print(f"[HARDWARE ERROR] Failed to set CPU affinity: {e}")

    def get_thermal_status(self) -> dict:
        """
        Retrieves CPU temperature if available (may require admin/drivers on Windows).
        """
        status = {"status": "unknown", "temps": {}}
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    status["temps"] = temps
                    status["status"] = "nominal"
        except Exception as e:
            status["error"] = str(e)
        return status

# Global Singleton
optimizer = HardwareOptimizer()
