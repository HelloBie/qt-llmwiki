#!/usr/bin/env python3
"""
qtllmwiki 统一服务启动入口 (main.py)
一键同时拉起 FastAPI 后端与 Vue 前端开发服务。
"""

import argparse
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional

# 项目根目录与子目录
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
ENV_FILE = BACKEND_DIR / ".env"

# 终端彩色输出工具 (ANSI)
USE_COLOR = sys.stdout.isatty() and os.name != "nt" or (os.name == "nt" and "WT_SESSION" in os.environ)


def colored(text: str, color_code: str) -> str:
    return f"\033[{color_code}m{text}\033[0m" if USE_COLOR else text


def log_info(msg: str):
    print(f"{colored('[INFO]', '32;1')} {msg}")


def log_warn(msg: str):
    print(f"{colored('[WARN]', '33;1')} {msg}")


def log_err(msg: str):
    print(f"{colored('[ERROR]', '31;1')} {msg}", file=sys.stderr)


def log_banner():
    banner = r"""
  ___  _____  _      _      __  __ __          __ _____  _  __ _____ 
 / _ \|_   _|| |    | |    |  \/  |\ \        / /|_   _|| |/ /|_   _|
| | | | | |  | |    | |    | \  / | \ \  /\  / /   | |  | ' /   | |  
| |_| | | |  | |___ | |___ | |\/| |  \ \/  \/ /   _| |_ | . \  _| |_ 
 \__\_| |_|  |_____||_____||_|  |_|   \_/\_/    |_____||_|\_\|_____|
    """
    print(colored(banner, "36;1"))
    print(colored("  >>> FastAPI + LangGraph + Vue 3 智能知识库服务 <<<", "37;1"))
    print("-" * 68)


def load_simple_env(env_path: Path) -> Dict[str, str]:
    """简单解析 .env 文件，不依赖额外第三方库"""
    env_vars: Dict[str, str] = {}
    if not env_path.is_file():
        return env_vars
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip('"').strip("'")
    except Exception as e:
        log_warn(f"读取 .env 文件失败: {e}")
    return env_vars


def get_backend_python() -> str:
    """寻找可用 Python 解释器，优先寻找 backend/.venv"""
    candidates = [
        BACKEND_DIR / ".venv" / "bin" / "python",
        BACKEND_DIR / ".venv" / "bin" / "python3",
        BACKEND_DIR / ".venv" / "Scripts" / "python.exe",
    ]
    for c in candidates:
        if c.is_file() and os.access(c, os.X_OK):
            return str(c)
    return sys.executable


def check_node_environment() -> Optional[str]:
    """检查前端环境，查找 Vite 可执行入口或 npm"""
    # 优先查找本地 node_modules 里的 vite
    local_vite = FRONTEND_DIR / "node_modules" / "vite" / "bin" / "vite.js"
    if local_vite.is_file():
        return str(local_vite)

    # 检查全局 npm / npx
    import shutil
    if shutil.which("npm") or shutil.which("npx"):
        return "npm"
    return None


def poll_backend_health(host: str, port: int, timeout_sec: int = 15) -> bool:
    """轮询健康检查接口直到后端就绪"""
    target_host = "127.0.0.1" if host == "0.0.0.0" else host
    url = f"http://{target_host}:{port}/api/v1/health"
    start_time = time.time()

    while time.time() - start_time < timeout_sec:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "qtllmwiki-launcher"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
            pass
        time.sleep(0.5)
    return False


def terminate_process(proc: Optional[subprocess.Popen], name: str):
    """优雅停止子进程及其子进程树"""
    if proc is None or proc.poll() is not None:
        return

    log_info(f"正在停止 {name} 服务 (PID: {proc.pid})...")
    try:
        if os.name == "nt":
            subprocess.call(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stderr=subprocess.DEVNULL)
        else:
            # 向进程组发送 SIGINT，随后如未退出则 SIGKILL
            os.killpg(os.getpgid(proc.pid), signal.SIGINT)
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except Exception:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(
        description="qtllmwiki 一键启动 FastAPI 后端与 Vue 前端",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--open", action="store_true", help="服务就绪后自动在浏览器打开前端页面")
    parser.add_argument("--backend-only", action="store_true", help="只启动 FastAPI 后端服务")
    parser.add_argument("--frontend-only", action="store_true", help="只启动 Vue 前端服务")
    parser.add_argument("--no-reload", action="store_true", help="关闭 FastAPI 后端热重载")
    parser.add_argument("--no-wait", action="store_true", help="跳过后端健康检查轮询")
    parser.add_argument("--lan", action="store_true", help="监听 0.0.0.0，使局域网可访问")
    parser.add_argument("--host", type=str, default=None, help="自定义监听 Host (默认从 .env 或 127.0.0.1)")
    parser.add_argument("--port", type=int, default=None, help="自定义后端端口 (默认从 .env 或 8000)")
    parser.add_argument("--frontend-port", type=int, default=5173, help="前端开发服务器端口 (默认 5173)")

    args = parser.parse_args()

    log_banner()

    # 读取环境变量配置
    env_vars = load_simple_env(ENV_FILE)
    host = "0.0.0.0" if args.lan else (args.host or env_vars.get("HOST", "127.0.0.1"))
    port = args.port or int(env_vars.get("PORT", "8000"))
    llm_key = env_vars.get("LLM_API_KEY", "")

    processes: Dict[str, subprocess.Popen] = {}
    is_shutting_down = False

    def handle_exit(signum, frame):
        nonlocal is_shutting_down
        if is_shutting_down:
            return
        is_shutting_down = True
        print("\n")
        log_info("收到退出信号，正在平稳关闭所有子服务...")
        for name, proc in processes.items():
            terminate_process(proc, name)
        log_info("所有服务已关闭，再见！")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # 1. 启动后端
    if not args.frontend_only:
        python_exe = get_backend_python()
        log_info(f"使用 Python 解释器: {colored(python_exe, '35')}")

        cmd = [
            python_exe,
            "-m", "uvicorn",
            "app.main:app",
            "--host", host,
            "--port", str(port),
        ]
        if not args.no_reload:
            cmd.extend(["--reload", "--reload-dir", str(BACKEND_DIR / "app")])

        log_info(f"正在拉起 FastAPI 后端: {' '.join(cmd)}")
        backend_proc = subprocess.Popen(
            cmd,
            cwd=str(BACKEND_DIR),
            preexec_fn=None if os.name == "nt" else os.setsid,
        )
        processes["FastAPI 后端"] = backend_proc

    # 2. 检查后端健康状态
    if not args.frontend_only and not args.no_wait:
        log_info(f"正在等待后端健康探针响应 (http://{host}:{port}/api/v1/health)...")
        if poll_backend_health(host, port, timeout_sec=15):
            log_info(f"{colored('✔', '32;1')} 后端服务已就绪！")
        else:
            log_warn("后端服务响应超时，可能仍在启动中或发生异常。")

    # 3. 启动前端
    if not args.backend_only:
        node_status = check_node_environment()
        frontend_host = "0.0.0.0" if args.lan else "127.0.0.1"

        if node_status:
            if node_status.endswith("vite.js"):
                # 直接通过 node 运行本地 vite.js
                front_cmd = [
                    "node",
                    node_status,
                    "--host", frontend_host,
                    "--port", str(args.frontend_port),
                ]
            else:
                # 检查 node_modules 是否存在
                if not (FRONTEND_DIR / "node_modules").is_dir():
                    log_warn("检测到 frontend/node_modules 尚未安装。")
                    log_info("正在尝试自动执行 npm install（请耐心等待）...")
                    try:
                        subprocess.run(["npm", "install"], cwd=str(FRONTEND_DIR), check=True)
                        log_info("前端依赖安装完成！")
                    except Exception as e:
                        log_warn(f"自动执行 npm install 失败: {e}，请手动进入 frontend 目录安装。")

                front_cmd = ["npm", "run", "dev", "--", "--host", frontend_host, "--port", str(args.frontend_port)]

            log_info(f"正在拉起 Vue 前端: {' '.join(front_cmd)}")
            frontend_proc = subprocess.Popen(
                front_cmd,
                cwd=str(FRONTEND_DIR),
                preexec_fn=None if os.name == "nt" else os.setsid,
            )
            processes["Vue 前端"] = frontend_proc
        else:
            log_warn("未检测到 Node.js / npm 环境。若要启动前端页面，请安装 Node.js (>=20.19)。")
            if (FRONTEND_DIR / "dist" / "index.html").is_file():
                log_info("检测到已存在 frontend/dist 构建产物，FastAPI 正在通过静态托管提供前端页面服务。")

    # 4. 输出就绪概览与链接
    disp_host = "127.0.0.1" if host == "0.0.0.0" else host
    frontend_url = f"http://{disp_host}:{args.frontend_port}"
    backend_url = f"http://{disp_host}:{port}"

    print("\n" + "=" * 68)
    print(colored(" 🚀 服务运行状态", "32;1"))
    if not args.frontend_only:
        print(f"  • 后端 API 根地址:   {colored(backend_url, '34;1')}")
        print(f"  • Swagger API 文档:  {colored(backend_url + '/docs', '34;1')}")
        print(f"  • ReDoc 文档:        {colored(backend_url + '/redoc', '34;1')}")
        print(f"  • 健康检查探针:      {colored(backend_url + '/api/v1/health', '34;1')}")
    if not args.backend_only:
        print(f"  • 前端 Vue 页面:     {colored(frontend_url, '32;1')}")

    if not llm_key:
        print("-" * 68)
        print(colored("  [提示] 尚未在 backend/.env 中配置 LLM_API_KEY", "33"))
        print(colored("  健康检查将处于 degraded 状态；配置 API Key 后保存即可自动生效！", "33"))
    print("=" * 68 + "\n")
    print(colored("按 Ctrl+C 可同时停止全部前后端服务。", "37"))

    # 自动打开浏览器
    if args.open and not args.backend_only:
        time.sleep(1)
        log_info(f"正在自动打开浏览器: {frontend_url}")
        webbrowser.open(frontend_url)

    # 5. 循环守护与退出检测
    try:
        while True:
            for name, proc in list(processes.items()):
                ret = proc.poll()
                if ret is not None:
                    log_warn(f"{name} 进程已退出 (退出码: {ret})")
                    del processes[name]
                    # 若任一核心进程退出，触发整体退出
                    handle_exit(None, None)
            time.sleep(1)
    except KeyboardInterrupt:
        handle_exit(None, None)


if __name__ == "__main__":
    main()
