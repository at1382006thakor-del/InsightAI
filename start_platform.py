import subprocess
import socket
import os
import time
import webbrowser

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to a public DNS server to retrieve local IP associated with the active network interface
        s.connect(('8.8.8.8', 80))
        IP = s.getsockname()[0]
    except Exception:
        try:
            # Fallback for offline environments
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def main():
    ip = get_local_ip()
    print("===================================================")
    print("   InsightAI BI Platform Launcher (Network Mode)   ")
    print("===================================================")
    print(f"Detected Local IP: {ip}")
    print()

    # 1. Update frontend/.env with the detected network IP for Next.js to communicate with the REST API
    env_path = os.path.join("frontend", ".env")
    env_content = f"NEXT_PUBLIC_API_URL=http://{ip}:8000/api\n"
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_content)
        print(f"[OK] Updated 'frontend/.env' with API URL: http://{ip}:8000/api")
    except Exception as e:
        print(f"[ERROR] Failed to write 'frontend/.env': {e}")
        return

    # 2. Launch FastAPI Backend on 0.0.0.0 (so it is bound to all local interfaces)
    print("Launching Uvicorn Backend API in a separate window...")
    # On Windows, CREATE_NEW_CONSOLE (0x00000010) launches the command in a new terminal window
    subprocess.Popen(
        ['cmd', '/k', 'title InsightAI Backend API && .\\venv\\Scripts\\python.exe backend/run.py'],
        creationflags=0x00000010
    )

    # 3. Launch Next.js Frontend bound to all local interfaces (0.0.0.0)
    print("Launching Next.js Frontend in a separate window...")
    subprocess.Popen(
        ['cmd', '/k', 'title InsightAI Next.js Frontend && cd frontend && npm.cmd run dev -- -H 0.0.0.0'],
        creationflags=0x00000010
    )

    # 4. Wait for the servers to initialize
    print("Waiting 4 seconds for servers to initialize...")
    time.sleep(4)

    # 5. Open local browser pointing to the network IP
    url = f"http://{ip}:3000"
    print(f"Launching default web browser to {url}...")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[WARNING] Could not open browser automatically: {e}")

    print()
    print("===================================================")
    print("   System running. Close the spawned windows to exit.")
    print("===================================================")

if __name__ == "__main__":
    main()
