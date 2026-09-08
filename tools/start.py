#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeuroGolf · ARC 可视化工具  本地启动脚本
────────────────────────────────────────────────────────────
作用:在 Golf2026 根目录起一个静态 HTTP 服务,然后用浏览器打开
      http://localhost:8011/tools/arc_viewer.html
这样工具就能自动读取  ../data/taskNNN.json  和  ../task_overview_v32.tsv
(用 file:// 直接双击 html 会被浏览器 CORS 挡住读本地文件,所以推荐用这个)

用法:
    双击  start.bat            (Windows,最省事)
  或命令行:
    python start.py           (本脚本会自动找到 Golf2026 根目录)
    python start.py 8080      (自定义端口)

放置:本脚本应位于  Golf2026/tools/  下(和 arc_viewer.html 同目录)。
"""
import os, sys, socket, threading, webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

DEFAULT_PORT = 8011
HTML_REL = "tools/arc_viewer.html"   # 相对服务根(Golf2026)的路径


def find_root():
    """服务根 = 本脚本所在目录(tools)的上一级,即 Golf2026。
    若结构异常(找不到 tools 同级的 data),回退到脚本所在目录。"""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)            # tools 的上一级
    # 校验:根目录下应能找到 arc_viewer.html(tools/) 或 data/
    if os.path.isfile(os.path.join(root, HTML_REL)) or os.path.isdir(os.path.join(root, "data")):
        return root
    # 回退:也许 html 和 data 就在脚本同级
    return here


def pick_port(start):
    """端口被占用就顺延,最多试 20 个。"""
    for p in range(start, start + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:   # 连不上 = 空闲
                return p
    return start


class QuietHandler(SimpleHTTPRequestHandler):
    # 禁用缓存,确保改了 html / 数据后刷新即生效
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()
    def log_message(self, fmt, *args):
        sys.stderr.write("  %s - %s\n" % (self.address_string(), fmt % args))


def main():
    root = find_root()
    os.chdir(root)
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        try: port = int(sys.argv[1])
        except ValueError: pass
    port = pick_port(port)

    # 找到实际的 html 路径(优先 tools/,否则同级)
    html_url_path = HTML_REL
    if not os.path.isfile(os.path.join(root, HTML_REL)) and os.path.isfile(os.path.join(root, "arc_viewer.html")):
        html_url_path = "arc_viewer.html"
    url = f"http://localhost:{port}/{html_url_path}"

    handler = partial(QuietHandler, directory=root)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)

    print("=" * 60)
    print("  NeuroGolf · ARC 可视化工具  本地服务已启动")
    print("=" * 60)
    print(f"  服务根目录 : {root}")
    print(f"  打开地址   : {url}")
    print(f"  data 目录  : {'OK ' + os.path.join(root,'data') if os.path.isdir(os.path.join(root,'data')) else '未找到 data/ (可在工具内手动选)'}")
    tsv = os.path.join(root, "task_overview.tsv")
    print(f"  主表 tsv   : {'OK ' + tsv if os.path.isfile(tsv) else '未找到(工具内会显示“主表未加载”,不影响看题)'}")
    print("-" * 60)
    print("  关闭:在本窗口按 Ctrl+C")
    print("=" * 60)

    # 1 秒后自动开浏览器
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
        httpd.server_close()


if __name__ == "__main__":
    main()
