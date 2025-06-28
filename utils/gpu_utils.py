import pynvml
import time
from .helpers import connect_print
from ..config import config

def get_gpu_info():
    """Retrieves detailed information about installed NVIDIA GPUs"""
    try:
        # Initialize NVML
        pynvml.nvmlInit()
        
        # Number of GPUs
        device_count = pynvml.nvmlDeviceGetCount()
        gpu_infos = []
        
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            
            # GPU name
            name = pynvml.nvmlDeviceGetName(handle)
            
            # GPU utilization
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_util = utilization.gpu
            
            # Memory
            memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
            memory_total = memory.total / 1024**2  # In MB
            memory_used = memory.used / 1024**2  # In MB
            memory_percent = (memory.used / memory.total) * 100
            
            # Temperature
            temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            
            # Power
            try:
                power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / config.POWER_CONVERSION_FACTOR  # In watts
                power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / config.POWER_CONVERSION_FACTOR  # In watts
            except pynvml.NVMLError:
                power_usage = 0
                power_limit = 0
                
            # Fans
            try:
                fan_speed = pynvml.nvmlDeviceGetFanSpeed(handle)
            except pynvml.NVMLError:
                fan_speed = 0
                
            # Clock frequencies (GPU and memory)
            try:
                clock_info = {
                    "graphics_clock": pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS),
                    "memory_clock": pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM),
                    "sm_clock": pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM)
                }
            except pynvml.NVMLError:
                clock_info = {
                    "graphics_clock": 0,
                    "memory_clock": 0,
                    "sm_clock": 0
                }
                
            # PCIe utilization
            try:
                pcie_throughput_tx = pynvml.nvmlDeviceGetPcieThroughput(handle, pynvml.NVML_PCIE_UTIL_TX_BYTES)
                pcie_throughput_rx = pynvml.nvmlDeviceGetPcieThroughput(handle, pynvml.NVML_PCIE_UTIL_RX_BYTES)
                pcie_generation = pynvml.nvmlDeviceGetMaxPcieLinkGeneration(handle)
                pcie_width_max = pynvml.nvmlDeviceGetMaxPcieLinkWidth(handle)
                pcie_width_current = pynvml.nvmlDeviceGetCurrPcieLinkWidth(handle)
                pcie_info = {
                    "tx_bytes": pcie_throughput_tx,
                    "rx_bytes": pcie_throughput_rx,
                    "generation": pcie_generation,
                    "width_max": pcie_width_max,
                    "width_current": pcie_width_current
                }
            except pynvml.NVMLError:
                pcie_info = {
                    "tx_bytes": 0,
                    "rx_bytes": 0,
                    "generation": 0,
                    "width_max": 0,
                    "width_current": 0
                }
                
            # Error counters (ECC)
            try:
                if pynvml.nvmlDeviceGetEccMode(handle)[0]:  # Check if ECC is enabled
                    volatile_ecc = pynvml.nvmlDeviceGetMemoryErrorCounter(handle, pynvml.NVML_MEMORY_ERROR_TYPE_UNCORRECTED, pynvml.NVML_VOLATILE_ECC)
                    aggregate_ecc = pynvml.nvmlDeviceGetMemoryErrorCounter(handle, pynvml.NVML_MEMORY_ERROR_TYPE_UNCORRECTED, pynvml.NVML_AGGREGATE_ECC)
                    ecc_errors = {
                        "enabled": True,
                        "volatile": volatile_ecc,
                        "aggregate": aggregate_ecc
                    }
                else:
                    ecc_errors = {
                        "enabled": False,
                        "volatile": 0,
                        "aggregate": 0
                    }
            except pynvml.NVMLError:
                ecc_errors = {
                    "enabled": False,
                    "volatile": 0,
                    "aggregate": 0
                }
                
            gpu_info = {
                "index": i,
                "name": name,
                "utilization": {
                    "gpu": gpu_util,
                },
                "memory": {
                    "total": round(memory_total, 2),
                    "used": round(memory_used, 2),
                    "percent": round(memory_percent, 2)
                },
                "temperature": temperature,
                "power": {
                    "usage": round(power_usage, 2),
                    "limit": round(power_limit, 2)
                },
                "fan_speed": fan_speed,
                "clocks": clock_info,
                "pcie": pcie_info,
                "ecc": ecc_errors
            }
            
            gpu_infos.append(gpu_info)
            
        # Close NVML
        pynvml.nvmlShutdown()
        return {"gpus": gpu_infos, "timestamp": time.time()}
        
    except Exception as e:
        connect_print(f"Error retrieving GPU info: {str(e)}")
        return {"error": str(e), "timestamp": time.time()}

def log_gpu_info(gpu_info):
    """Displays the most important GPU information in a condensed format"""
    if "error" in gpu_info:
        connect_print(f"GPU Info: Error: {gpu_info['error']}")
    else:
        for gpu in gpu_info["gpus"]:
            # Condensed format: GPU_INDEX | NAME | UTIL% | MEM_USED/TOTAL (MEM%) | TEMP°C | POWER_USED/LIMIT W
            connect_print(f"GPU {gpu['index']} | {gpu['name']} | Util: {gpu['utilization']['gpu']}% | Mem: {int(gpu['memory']['used'])}/{int(gpu['memory']['total'])}MB ({gpu['memory']['percent']}%) | Temp: {gpu['temperature']}°C | Power: {gpu['power']['usage']}/{gpu['power']['limit']}W | Fan: {gpu['fan_speed']}%") 