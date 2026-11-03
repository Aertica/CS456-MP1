import socket, subprocess, sys, threading, time
import config

d_hb = block_s = False


def p_proxy(): 
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 1026))
    while True:
        data, _ = s.recvfrom(4096)
        if not d_hb:
            s.sendto(data, ("127.0.0.1", config.MONITOR_PORT))


def s_proxy(): 
    srv = socket.create_server(("127.0.0.1", 9201))
    while True:
        conn, _ = srv.accept()
        data = conn.recv(4096)
        conn.close()
        if not block_s:
            socket.create_connection(("127.0.0.1", config.SYNC_PORT)).sendall(data)


def run(args, hb_port=config.MONITOR_PORT):  
    code = (f"import sys, config; config.CRASH_PROBABILITY = config.REQUEST_CRASH_PROB = 0; "
            f"config.FAULT_MIN_S = config.FAULT_MAX_S = 9999; config.MONITOR_PORT = {hb_port}; "
            f"sys.argv = {args!r}; import runpy; runpy.run_path(sys.argv[0], run_name='__main__')")
    return subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.DEVNULL)


def send(host, ip, payload="hi"):  
    try:
        with socket.create_connection((host, config.PORT), timeout=2) as s:
            s.sendall(f"{ip}|10.0.0.1|{payload}\n".encode())
            return s.recv(1024).decode().split("|")[0].strip()
    except OSError:
        return "DOWN"


def cluster(primary_host):
    procs = [run(["monitor.py"])]
    time.sleep(0.5)
    procs.append(run(["service.py", "--role", "secondary"]))
    time.sleep(1.5)
    procs.append(run(["service.py", "--host", primary_host, "--sync-port", "9201"], hb_port=1026))
    time.sleep(1.5)
    return procs


threading.Thread(target=p_proxy, daemon=True).start()
threading.Thread(target=s_proxy, daemon=True).start()

print("Scenario 1: Dropping the heartbeats of a primary that is still running (on 127.0.0.2, acting as a second machine)")
procs = cluster("127.0.0.2")
d_hb = True
time.sleep(4)
d_hb = False
time.sleep(2)
print("  old primary:", send("127.0.0.2", "0.1.0.1"), "| new primary:", send("127.0.0.1", "0.1.0.1"))
send("127.0.0.1", "1.0.1.0", "+blacklist")
time.sleep(0.5)
print("  1.0.1.0 blocked on new primary -> old primary says:", send("127.0.0.2", "1.0.1.0"))
for p in procs: p.kill()
time.sleep(1)

print("Scenario 2: Blocking the sync while the primary blacklists 1.1.1.1, then crashing the primary")
procs = cluster("127.0.0.1")
block_s = True
send("127.0.0.1", "1.1.1.1", "+blacklist")
time.sleep(0.5)
block_s = False
print("  before crash, 1.1.1.1:", send("127.0.0.1", "1.1.1.1"))
procs[2].kill()
time.sleep(8)
print("  after failover, 1.1.1.1:", send("127.0.0.1", "1.1.1.1"))
for p in procs: p.kill()
