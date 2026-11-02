"""
RoboboSim Headless Cluster & Parallel Pool Manager
Allows spinning up multiple parallel headless simulation instances from a single call,
with configurable simulation speed, worlds, random seeds, and isolated ports.

Usage via CLI:
    python -m robobosim.RoboboPool start -e "Build/Robobo Sim.exe" -n 10 --speed 10 --world CuatroParedes
    python -m robobosim.RoboboPool test -e "Build/Robobo Sim.exe" -n 10 --speed 10 --world CuatroParedes

Usage via Python API:
    from robobosim.RoboboPool import RoboboPool

    with RoboboPool("Build/Robobo Sim.exe", num_instances=10, speed=10, world="CuatroParedes") as pool:
        for idx in range(pool.num_instances):
            rob = pool.get_robot(idx)
            sim = pool.get_sim(idx)
            # Train or evaluate...
"""

import os
import time
import socket
import argparse
import subprocess
import threading
import websocket
from typing import List, Dict, Optional, Any

from robobosim.RoboboSim import RoboboSim

try:
    from robobopy.Robobo import Robobo
    import robobopy.remotelib as robobo_remotelib
    ROBOBOPY_AVAILABLE = True
except ImportError:
    Robobo = Any
    ROBOBOPY_AVAILABLE = False


def wait_for_port(port: int, host: str = "127.0.0.1", timeout: float = 30.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.3):
                return True
        except (socket.error, ConnectionRefusedError, OSError):
            time.sleep(0.15)
    return False


class SimpleWSClient:
    """
    Lightweight, deterministic WebSocket client for communicating with Robobo and RoboboSim.
    Handles authentication handshakes, command dispatching, and synchronous status waiting.
    """
    def __init__(self, port: int, host: str = "127.0.0.1"):
        self.url = f"ws://{host}:{port}/"
        self.ws = None
        self.msg_id = 0
        self.responses = []
        self.statuses = []

    def connect(self, password: str = None, retries: int = 5):
        for attempt in range(retries):
            try:
                self.ws = websocket.create_connection(self.url, timeout=10.0)
                if password:
                    self.ws.send(f"PASSWORD: {password}")
                    time.sleep(0.15)
                return
            except (ConnectionResetError, websocket.WebSocketException, OSError):
                if attempt == retries - 1:
                    raise
                time.sleep(0.4)

    def close(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass

    def send_command(self, name: str, params: Dict[str, Any] = None) -> int:
        import json
        self.msg_id += 1
        cmd = {
            "name": name,
            "id": self.msg_id,
            "parameters": {k: str(v) for k, v in (params or {}).items()}
        }
        self.ws.send(json.dumps(cmd))
        return self.msg_id

    def wait_for_status(self, status_name: str, timeout: float = 10.0) -> Dict[str, Any]:
        import json
        start = time.time()
        while time.time() - start < timeout:
            try:
                raw = self.ws.recv()
                msg = json.loads(raw)
                if msg.get("name") == status_name:
                    return msg.get("value", {})
                self.statuses.append(msg)
            except websocket.WebSocketTimeoutException:
                pass
        raise TimeoutError(f"Timed out waiting for status '{status_name}'")


class InstanceInfo:
    def __init__(self, instance_id: int, robot_port: int, sim_port: int, seed: int, log_path: str, proc: subprocess.Popen):
        self.instance_id = instance_id
        self.robot_port = robot_port
        self.sim_port = sim_port
        self.seed = seed
        self.log_path = log_path
        self.proc = proc
        self.robot_client: Optional[Robobo] = None
        self.sim_client: Optional[RoboboSim] = None


class RoboboPool:
    def __init__(
        self,
        executable_path: str,
        num_instances: int = 5,
        speed: float = 1.0,
        world: str = "CuatroParedes",
        custom_world: Optional[str] = None,
        base_instance_id: int = 1,
        robot_base_port: int = 20000,
        sim_base_port: int = 30000,
        port_step: int = 4,
        seed_base: int = 42,
        seed_per_instance: bool = True,
        random_mode: Optional[bool] = False,
        simpler_physics: bool = True,
        no_noise: bool = True,
        fixed_delta_time: float = 0.02,
        quit_after: float = -1.0,
        scene_config: Optional[str] = None,
        lockstep: bool = True,
        logs_dir: str = "logs",
        verbose: bool = True
    ):
        if not executable_path:
            raise ValueError("executable_path must be provided to RoboboPool.")
        self.executable_path = os.path.abspath(executable_path)
        self.num_instances = num_instances
        self.speed = speed
        self.world = world
        self.custom_world = custom_world
        self.base_instance_id = base_instance_id
        self.robot_base_port = robot_base_port
        self.sim_base_port = sim_base_port
        self.port_step = port_step
        self.seed_base = seed_base
        self.seed_per_instance = seed_per_instance
        self.random_mode = random_mode
        self.simpler_physics = simpler_physics
        self.no_noise = no_noise
        self.fixed_delta_time = fixed_delta_time
        self.quit_after = quit_after
        self.scene_config = scene_config
        self.lockstep = lockstep
        self.logs_dir = os.path.abspath(logs_dir)
        self.verbose = verbose
        self.instances: List[InstanceInfo] = []

    def start(self, timeout: float = 45.0):
        if not os.path.exists(self.executable_path):
            raise FileNotFoundError(f"Simulator executable not found at: {self.executable_path}")

        os.makedirs(self.logs_dir, exist_ok=True)

        if self.verbose:
            print("=" * 80)
            print(f"LAUNCHING ROBOBO SIMULATOR POOL ({self.num_instances} INSTANCES)")
            print(f"Speed: {self.speed}x | World: {self.world or self.custom_world} | Physics: {'Simplified' if self.simpler_physics else 'Realistic'}")
            print(f"Executable: {self.executable_path}")
            print("=" * 80)

        for i in range(self.num_instances):
            inst_id = self.base_instance_id + i
            robot_port = self.robot_base_port + i * self.port_step
            sim_port = self.sim_base_port + i * self.port_step
            seed = (self.seed_base + i) if self.seed_per_instance else self.seed_base
            log_path = os.path.join(self.logs_dir, f"sim_instance_{inst_id}.log")

            cmd = [
                self.executable_path,
                "-batchmode",
                "-nographics",
                "--speed", str(self.speed),
                "--seed", str(seed),
                "--instance", str(inst_id),
                "--port", str(robot_port),
                "--simPort", str(sim_port),
                "-logFile", log_path
            ]

            if self.custom_world:
                cmd.extend(["--customWorld", self.custom_world])
            elif self.world:
                cmd.extend(["--world", self.world])

            if self.random_mode is True:
                cmd.append("--randomMode")
            elif self.random_mode is False:
                cmd.append("--noRandomMode")

            if self.simpler_physics:
                cmd.append("--simplerPhysics")
            else:
                cmd.append("--realisticPhysics")

            if self.no_noise:
                cmd.append("--noNoise")
            else:
                cmd.append("--enableNoise")

            if self.lockstep:
                cmd.append("--lockstep")
            else:
                cmd.append("--freeRun")

            if self.fixed_delta_time != 0.02:
                cmd.extend(["--fixedDeltaTime", str(self.fixed_delta_time)])

            if self.quit_after > 0:
                cmd.extend(["--quitAfter", str(self.quit_after)])

            if self.scene_config:
                cmd.extend(["--sceneConfig", self.scene_config])

            if self.verbose:
                print(f"  [Instance {inst_id:>2}] Spawning PID -> RobotPort: {robot_port}, SimPort: {sim_port}, Seed: {seed}")

            proc = subprocess.Popen(cmd)
            self.instances.append(InstanceInfo(inst_id, robot_port, sim_port, seed, log_path, proc))

        if self.verbose:
            print("\nWaiting for all instances to bind and listen on sockets...")

        start_wait = time.time()
        for inst in self.instances:
            rem_timeout = max(1.0, timeout - (time.time() - start_wait))
            if not wait_for_port(inst.robot_port, timeout=rem_timeout):
                self.stop()
                raise TimeoutError(f"Instance {inst.instance_id} failed to open Robot port {inst.robot_port} within {timeout}s.")
            if not wait_for_port(inst.sim_port, timeout=rem_timeout):
                self.stop()
                raise TimeoutError(f"Instance {inst.instance_id} failed to open Sim port {inst.sim_port} within {timeout}s.")

        elapsed = time.time() - start_wait
        if self.verbose:
            print(f">>> All {self.num_instances} instances are READY! (Bootstrapped in {elapsed:.1f}s)")
            print("=" * 80 + "\n")

    def get_robot(self, index: int) -> Robobo:
        if not ROBOBOPY_AVAILABLE:
            raise ImportError("robobopy is not installed.")
        inst = self.instances[index]
        if inst.robot_client is None:
            rob = Robobo("127.0.0.1")
            port = inst.robot_port

            def custom_wsStartup():
                def on_open(ws):
                    ws.send("PASSWORD: " + rob.rem.password)
                    rob.rem.connectionState = robobo_remotelib.ConnectionState.CONNECTED

                def on_message(ws, message):
                    rob.rem.processMessage(message)

                def on_error(ws, error):
                    rob.rem.connectionState = robobo_remotelib.ConnectionState.ERROR

                def on_close(ws, status_code, msg):
                    rob.rem.connectionState = robobo_remotelib.ConnectionState.DISCONNECTED

                rob.rem.ws = websocket.WebSocketApp(
                    f"ws://127.0.0.1:{port}",
                    on_open=on_open,
                    on_message=on_message,
                    on_error=on_error,
                    on_close=on_close
                )
                t = threading.Thread(target=rob.rem.ws.run_forever, daemon=True)
                t.start()
                rob.rem.connectionState = robobo_remotelib.ConnectionState.CONNECTING
                while rob.rem.connectionState == robobo_remotelib.ConnectionState.CONNECTING:
                    time.sleep(0.05)

            rob.rem.wsStartup = custom_wsStartup
            rob.connect()
            inst.robot_client = rob
        return inst.robot_client

    def get_sim(self, index: int) -> RoboboSim:
        inst = self.instances[index]
        if inst.sim_client is None:
            sim = RoboboSim("127.0.0.1", port=inst.sim_port)
            sim.connect()
            inst.sim_client = sim
        return inst.sim_client

    def stop(self):
        if self.verbose:
            print(f"\nStopping {len(self.instances)} simulation instances...")

        for inst in self.instances:
            if inst.robot_client:
                try:
                    inst.robot_client.disconnect()
                except Exception:
                    pass
            if inst.sim_client:
                try:
                    inst.sim_client.disconnect()
                except Exception:
                    pass

        for inst in self.instances:
            try:
                inst.proc.terminate()
            except Exception:
                pass

        time.sleep(0.5)
        for inst in self.instances:
            try:
                inst.proc.kill()
            except Exception:
                pass

        if self.verbose:
            print("All instances stopped and resources cleaned up.")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def run_test(executable_path: str, num_instances: int = 10, speed: float = 10.0, world: str = "CuatroParedes"):
    print(f"Running automated test on {num_instances} instances at {speed}x speed...")
    with RoboboPool(executable_path=executable_path, num_instances=num_instances, speed=speed, world=world, lockstep=False) as pool:
        print("\nConnecting all clients and testing simultaneous actions...")
        robots = [pool.get_robot(i) for i in range(pool.num_instances)]
        sims = [pool.get_sim(i) for i in range(pool.num_instances)]

        time.sleep(1.0)
        init_locs = [sim.getRobotLocation(0) for sim in sims]

        print("\nIssuing simultaneous movements across all instances:")
        threads = []
        for i, rob in enumerate(robots):
            rs = -10 if i % 2 == 0 else 10
            ls = 10 if i % 2 == 0 else -10
            t = threading.Thread(target=rob.moveWheelsByTime, args=(rs, ls, 1.0, True))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        time.sleep(0.5)
        final_locs = [sim.getRobotLocation(0) for sim in sims]

        print("\n" + "=" * 80)
        print("TEST RESULTS:")
        print("=" * 80)
        for i in range(pool.num_instances):
            pos = final_locs[i]["position"]
            rot = final_locs[i]["rotation"]
            print(f"Instance {i+1:>2} (RobotPort {pool.instances[i].robot_port}): Pos=({pos['x']:>8.2f}, {pos['y']:>5.2f}, {pos['z']:>8.2f}) | Heading={rot['y']:>6.2f}°")
        print("=" * 80)
        print(">>> SUCCESS: All parallel instances executed and reported telemetry successfully! <<<")


def main():
    parser = argparse.ArgumentParser(description="RoboboSim Headless Cluster & Pool Manager")
    subparsers = parser.add_subparsers(dest="action", required=True)

    p_start = subparsers.add_parser("start", help="Spin up N simulator instances and keep running")
    p_start.add_argument("-e", "--exe", "--executable", dest="executable_path", type=str, required=True, help="Path to the RoboboSim executable")
    p_start.add_argument("-n", "--num-instances", type=int, default=5, help="Number of instances to spin up (default: 5)")
    p_start.add_argument("-s", "--speed", type=float, default=1.0, help="Simulation speed multiplier (e.g. 1, 5, 10, 20)")
    p_start.add_argument("-w", "--world", type=str, default="CuatroParedes", help="Target scene name")
    p_start.add_argument("--customWorld", type=str, default=None, help="Path to custom world JSON")
    p_start.add_argument("--seed", type=int, default=42, help="Base random seed")
    p_start.add_argument("--realisticPhysics", action="store_true", help="Use realistic NWH physics instead of simplified")
    p_start.add_argument("--lockstep", action="store_true", default=True, help="Enable lockstep tick-stepping mode (default in headless mode)")
    p_start.add_argument("--freeRun", "--noLockstep", dest="free_run", action="store_true", help="Disable lockstep and run real-time/accelerated free-running simulation")

    p_test = subparsers.add_parser("test", help="Spin up N instances, run simultaneous actions, and verify")
    p_test.add_argument("-e", "--exe", "--executable", dest="executable_path", type=str, required=True, help="Path to the RoboboSim executable")
    p_test.add_argument("-n", "--num-instances", type=int, default=5, help="Number of instances (default: 5)")
    p_test.add_argument("-s", "--speed", type=float, default=10.0, help="Simulation speed multiplier (default: 10.0)")
    p_test.add_argument("-w", "--world", type=str, default="CuatroParedes", help="Target scene name")

    args = parser.parse_args()

    if args.action == "test":
        run_test(executable_path=args.executable_path, num_instances=args.num_instances, speed=args.speed, world=args.world)
    elif args.action == "start":
        pool = RoboboPool(
            executable_path=args.executable_path,
            num_instances=args.num_instances,
            speed=args.speed,
            world=args.world,
            custom_world=args.customWorld,
            seed_base=args.seed,
            simpler_physics=not args.realisticPhysics,
            lockstep=not args.free_run
        )
        pool.start()
        print("Press Ctrl+C to stop all instances.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down pool...")
        finally:
            pool.stop()


if __name__ == "__main__":
    main()
