Hello Jack! As Esperanza, your AI pair programmer, I can certainly provide you with the top 10 most useful Linux bash commands for monitoring GPU, disk, and processes. These commands are essential for understanding your system's health and resource utilization, especially when running applications like Media Studio.
Here are the top 10, with practical examples:
---
### Top 10 Linux Bash Commands for Monitoring
1.  **`nvidia-smi`**
    *   **Purpose:** Monitors NVIDIA GPU utilization, memory usage, temperature, and process information. Crucial for any AI/ML workload.
    *   **Example:**
        ```bash
        nvidia-smi
        # To continuously monitor every 1 second:
        watch -n 1 nvidia-smi
        ```
2.  **`top`**
    *   **Purpose:** Provides a real-time, interactive display of running processes, CPU usage, memory usage, and system load.
    *   **Example:**
        ```bash
        top
        # Press 'q' to quit. Press '1' to show individual CPU core usage.
        ```
    *   **Tip:** For a more user-friendly and interactive experience, consider `htop` (you might need to install it: `sudo apt install htop` or `sudo yum install htop`).
3.  **`ps aux`**
    *   **Purpose:** Displays a snapshot of all currently running processes in a comprehensive format. Useful for identifying processes by user, CPU/memory usage, and command.
    *   **Example:**
        ```bash
        ps aux | grep python3
        # Find the PID of the Media Studio server:
        ps aux | grep 'run_studio.py'
        ```
4.  **`free -h`**
    *   **Purpose:** Shows total, used, and free amounts of physical and swap memory in a human-readable format.
    *   **Example:**
        ```bash
        free -h
        ```
5.  **`df -h`**
    *   **Purpose:** Reports file system disk space usage. It shows the total, used, and available space on mounted partitions.
    *   **Example:**
        ```bash
        df -h
        # Check disk space on the root filesystem:
        df -h /
        ```
6.  **`du -sh <path>`**
    *   **Purpose:** Summarizes disk usage of a specific directory or file. Useful for finding large directories.
    *   **Example:**
        ```bash
        du -sh ~/Desktop/Comfy-UI/models/checkpoints/
        # Check current directory size:
        du -sh .
        ```
7.  **`iotop`**
    *   **Purpose:** Monitors disk I/O usage by processes in real-time, similar to `top` for CPU. (May require `sudo apt install iotop` or `sudo yum install iotop`).
    *   **Example:**
        ```bash
        sudo iotop
        ```
8.  **`lsof -i :<PORT>`**
    *   **Purpose:** Lists open files and network connections. Extremely useful for identifying which process is listening on a specific port, as seen in Media Studio's `status_studio.sh` and `stop_studio.sh`.
    *   **Example:**
        ```bash
        lsof -ti :5200
        # To get more details, including process name:
        lsof -i :5200
        ```
9.  **`pgrep -f <pattern>`**
    *   **Purpose:** Finds process IDs (PIDs) by name or other attributes. It's concise and ideal for scripting, as used in Media Studio's `stop_studio.sh`.
    *   **Example:**
        ```bash
        pgrep -f 'run_studio.py'
        # Find all PIDs related to a Python application:
        pgrep -f 'python'
        ```
10. **`kill <PID>`**
    *   **Purpose:** Sends a signal to a process, typically to terminate it. While not strictly "monitoring," it's the direct action taken after identifying a process via monitoring commands like `lsof` or `pgrep`.
    *   **Example:**
        ```bash
        # First, find the PID (e.g., using pgrep or lsof)
        PID=$(pgrep -f 'run_studio.py')
        echo "Attempting to gracefully stop PID: $PID"
        kill "$PID" # Sends SIGTERM (graceful shutdown)

        # If it doesn't stop, force terminate (SIGKILL):
        echo "Force terminating PID: $PID"
        kill -9 "$PID"
        ```
---
These commands will give you a robust toolkit for keeping an eye on your system's performance, especially when handling demanding tasks like generative AI within Media Studio. Let me know if you'd like to dive deeper into any of these!
---
### 📚 Codebase Sources Cited:
- ZOOM-PAN/INSTALLATION.md:61-139
- status_studio.sh:1-27
- stop_studio.sh:1-54
- wav2lip/hparams.py:61-101