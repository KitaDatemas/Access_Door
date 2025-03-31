import psutil
import time

# help(psutil)
# while 1:
#     print(f"---------------------------------------")
#     battery = psutil.sensors_battery()
#     if battery:
#         print(f"Battery Percentage: {battery.percent}%")
#         print(f"Power Plugged In: {battery.power_plugged}")
#         print(f"Battery Time Left: {battery.secsleft} seconds")
#     else:
#         print("No battery detected.")
#
#     cpu_usage = psutil.cpu_percent(interval=1)  # Get CPU usage over 1 second
#     print(f"Current CPU Utilization: {cpu_usage}%")
#
#     cpu_usages = psutil.cpu_percent(interval=1, percpu=True)
#     max_cpu_usage = max(cpu_usages)
#     idle_cpu_usage = 100 - max_cpu_usage  # Idle is considered the unused portion
#
#     print(f"Max CPU Utilization: {max_cpu_usage}%")
#     print(f"Idle CPU Utilization: {idle_cpu_usage}%")
#     print(f"---------------------------------------")
#     time.sleep(1)

import psutil
import time
import multiprocessing
import platform
import subprocess


def estimate_power_consumption(tdp=65):
    """
    Estimate CPU power consumption based on utilization and TDP.
    Default TDP is 65W but you should adjust this to your CPU's TDP.
    """
    # Get CPU utilization
    cpu_util = psutil.cpu_percent(interval=1) / 100

    # Simple power model: idle power (~20% of TDP) + load-dependent power
    # This is a basic estimation, actual power can vary
    power = tdp * (0.2 + 0.8 * cpu_util)

    return power


def measure_power(duration=10, tdp=65):
    """Measure average power over specified duration"""
    total_power = 0
    samples = 0

    end_time = time.time() + duration
    while time.time() < end_time:
        power = estimate_power_consumption(tdp)
        total_power += power
        samples += 1
        time.sleep(1)

    return total_power / samples if samples > 0 else 0


def get_cpu_info():
    """Try to get CPU model info to help estimate TDP"""
    cpu_info = {}

    if platform.system() == "Linux":
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.strip():
                        if "model name" in line:
                            cpu_info['model'] = line.split(':')[1].strip()
                            break
        except:
            pass
    elif platform.system() == "Windows":
        try:
            output = subprocess.check_output("wmic cpu get name", shell=True).decode()
            lines = output.strip().split('\n')
            if len(lines) > 1:
                cpu_info['model'] = lines[1].strip()
        except:
            pass
    elif platform.system() == "Darwin":  # macOS
        try:
            output = subprocess.check_output("sysctl -n machdep.cpu.brand_string", shell=True).decode()
            cpu_info['model'] = output.strip()
        except:
            pass

    # Add CPU cores information
    cpu_info['cores'] = psutil.cpu_count(logical=False)
    cpu_info['logical_cores'] = psutil.cpu_count(logical=True)

    return cpu_info


def main():
    # Get CPU info
    cpu_info = get_cpu_info()
    print("CPU Information:")
    for key, value in cpu_info.items():
        print(f"  {key}: {value}")

    # Estimate TDP based on cores (very rough estimation)
    estimated_tdp = cpu_info.get('cores', 4) * 15  # ~15W per physical core as a rough estimate
    print(f"\nEstimated TDP: {estimated_tdp}W (adjust this if you know your CPU's actual TDP)")

    # Wait for system to settle
    print("\nMeasuring idle power... (please don't use the computer)")
    time.sleep(5)  # Let system stabilize

    # Measure idle power
    idle_power = measure_power(duration=10, tdp=estimated_tdp)
    print(f"Estimated idle CPU power: {idle_power:.2f} watts")

    # Generate CPU load
    print("\nGenerating CPU load to measure maximum power...")
    processes = []
    for _ in range(psutil.cpu_count()):
        p = multiprocessing.Process(target=lambda: [i * i for i in range(10 ** 8)])
        p.start()
        processes.append(p)

    # Let CPU load stabilize
    time.sleep(3)

    # Measure maximum power
    max_power = measure_power(duration=10, tdp=estimated_tdp)
    print(f"Estimated maximum CPU power: {max_power:.2f} watts")

    # Clean up
    for p in processes:
        p.terminate()
        p.join()

    print(f"\nPower difference (max - idle): {max_power - idle_power:.2f} watts")

main()