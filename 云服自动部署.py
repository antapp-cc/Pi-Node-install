import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import paramiko
import threading
import json
import sys
import ctypes
        
    @staticmethod
    def apply(style: ttk.Style):
        style.theme_use("clam")
        # 全局
        style.configure(
            ".",
            background=DarkTheme.BG,
            foreground=DarkTheme.TEXT,
            fieldbackground=DarkTheme.CARD,
            borderwidth=0,
            relief=tk.FLAT,
            font=("Segoe UI", 10)
        )

        # 分组框
        style.configure("Group.TLabelframe",
                        background=DarkTheme.CARD, foreground=DarkTheme.MUTED,
                        borderwidth=1, relief=tk.SOLID)
        style.configure("Group.TLabelframe.Label",
                        font=("Segoe UI Semibold", 10),
                        foreground=DarkTheme.MUTED,
                        background=DarkTheme.CARD)

        # 输入
        style.configure("Clean.TEntry",
                        padding=6, bordercolor=DarkTheme.BORDER,
                        foreground=DarkTheme.TEXT,
                        fieldbackground=DarkTheme.CARD,
                        relief=tk.SOLID)
        style.map("Clean.TEntry",
                  bordercolor=[("focus", DarkTheme.ACCENT)])

        style.configure("TCombobox", padding=6,
                        foreground=DarkTheme.TEXT,
                        fieldbackground=DarkTheme.CARD)

        # 按钮
        style.configure("Primary.TButton",
                        background=DarkTheme.ACCENT, foreground="#ffffff",
                        padding=(12, 8), relief=tk.FLAT)
        style.map("Primary.TButton",
                  background=[("active", "#2563eb"), ("disabled", "#9db7fb")])

        # 次按钮
        style.configure("Ghost.TButton",
                        background=DarkTheme.CARD, foreground=DarkTheme.TEXT,
                        padding=(10, 7), bordercolor=DarkTheme.BORDER, relief=tk.SOLID)
        style.map("Ghost.TButton",
                  background=[("active", "#3d3d3d")])

        # 进度条
        style.configure("Clean.Horizontal.TProgressbar",
                        troughcolor="#333333", background=DarkTheme.ACCENT)

        # 分隔线
        style.configure("Clean.TSeparator", background=DarkTheme.BORDER)

        # 底部版权字体样式
        style.configure("Footer.TLabel", font=("Segoe UI", 10, "bold"),
                        foreground=DarkTheme.MUTED, background=DarkTheme.BG)

class StatusPill(ttk.Frame):
    def __init__(self, parent, title, value, color, *args, **kwargs):
        super().__init__(parent, style="Card.TFrame", *args, **kwargs)
        ttk.Label(self, text=title, style="Muted.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        self.dot = tk.Canvas(self, width=10, height=10, bg=DarkTheme.CARD, highlightthickness=0)
        self.dot.grid(row=1, column=0, sticky="w", padx=(0, 6))
        self._draw_dot(color)
        self.text = ttk.Label(self, text=value, style="Muted.TLabel")
        self.text.grid(row=1, column=1, sticky="w")
        self.grid_columnconfigure(1, weight=1)

    def _draw_dot(self, color):
        self.dot.delete("all")
        self.dot.create_oval(1, 1, 9, 9, fill=color, outline=color)

    def update(self, value, color):
        self.text.config(text=value)
        self._draw_dot(color)

class OpenVPNInstaller:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("蚁巢 - Node")
        self.root.geometry("640x600")
        self.root.minsize(640, 520)
        
        # 窗口居中
        self.center_window()
        
        # 设置深色主题
        self.style = ttk.Style()
        DarkTheme.apply(self.style)
        self.root.configure(bg=DarkTheme.BG)
        
        # 设置深色主题的滚动文本框
        scr_bg = DarkTheme.CARD
        scr_fg = DarkTheme.TEXT

        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=16, pady=(12, 4))
        ttk.Label(header, text="蚁巢 - Node云服自动部署系统", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="实现云服自动安装：OpenVPN 安装 / 端口转发 /本地配置/让你的安装更加简单！目前支持：Debian 11系统。",
                  style="Sub.TLabel").pack(anchor="w")

        # 主容器
        container = ttk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        # 顶部：表单 + 动作
        top = ttk.Frame(container)
        top.pack(fill=tk.X)

        form = ttk.Labelframe(top, text="服务器连接配置", style="Group.TLabelframe")
        form.pack(side=tk.LEFT, fill=tk.X, expand=True)

        frm = ttk.Frame(form, style="Card.TFrame")
        frm.pack(fill=tk.X, padx=10, pady=10)

        # 左列
        lf = ttk.Frame(frm, style="Card.TFrame")
        lf.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ttk.Label(lf, text="服务器 IP：", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self.server_ip = ttk.Entry(lf, width=24, style="Clean.TEntry")
        self.server_ip.grid(row=1, column=0, sticky="ew", pady=(4, 8))

        ttk.Label(lf, text="密码：", style="Muted.TLabel").grid(row=2, column=0, sticky="w")
        self.password = ttk.Entry(lf, width=24, style="Clean.TEntry")
        self.password.grid(row=3, column=0, sticky="ew", pady=(4, 0))

        # 右列
        rf = ttk.Frame(frm, style="Card.TFrame")
        rf.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ttk.Label(rf, text="用户名：", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self.username = ttk.Entry(rf, width=24, style="Clean.TEntry")
        self.username.grid(row=1, column=0, sticky="ew", pady=(4, 8))
        self.username.insert(0, "root")

        ttk.Label(rf, text="SSH 端口：", style="Muted.TLabel").grid(row=2, column=0, sticky="w")
        self.ssh_port = ttk.Entry(rf, width=24, style="Clean.TEntry")
        self.ssh_port.grid(row=3, column=0, sticky="ew", pady=(4, 0))
        self.ssh_port.insert(0, "22")

        frm.grid_columnconfigure(0, weight=1)
        frm.grid_columnconfigure(1, weight=1)

        # 动作卡片
        actions = ttk.Frame(top)
        actions.pack(side=tk.RIGHT, padx=(10, 0))
        self.install_button = ttk.Button(actions, text="⚡ 开始自动配置 ⚡ ", style="Primary.TButton",
                                         command=self.start_installation)
        self.install_button.grid(row=0, column=0, sticky="ew", padx=0, pady=(2, 6))
        self.progress = ttk.Progressbar(actions, mode="indeterminate", length=180,
                                        style="Clean.Horizontal.TProgressbar")
        self.progress.grid(row=1, column=0, sticky="ew")
        
        # 添加四个状态指示器
        self.pill_conn = StatusPill(status_container, "连接状态", "未连接", DarkTheme.MUTED)
        self.pill_vpn = StatusPill(status_container, "OpenVPN", "未安装", DarkTheme.MUTED)
        self.pill_pf = StatusPill(status_container, "端口转发", "未启用", DarkTheme.MUTED)
        self.pill_dl = StatusPill(status_container, "本地配置", "未导入", DarkTheme.MUTED)
        
        # 使用grid布局确保正确排列
        self.pill_conn.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="w")
        self.pill_vpn.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.pill_pf.grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.pill_dl.grid(row=0, column=3, padx=(10, 0), pady=5, sticky="w")
        
        status_container.grid_columnconfigure(0, weight=0)
        status_container.grid_columnconfigure(1, weight=0)
        status_container.grid_columnconfigure(2, weight=0)
        status_container.grid_columnconfigure(3, weight=0)

        ttk.Separator(container, orient=tk.HORIZONTAL, style="Clean.TSeparator").pack(fill=tk.X, pady=(8, 8))

        log_card = ttk.Labelframe(container, text="安装日志", style="Group.TLabelframe")
        log_card.pack(fill=tk.BOTH, expand=True)
        self.log_area = scrolledtext.ScrolledText(
            log_card, wrap=tk.WORD, font=("Consolas", 10),
            bg=scr_bg, fg=scr_fg, insertbackground=DarkTheme.ACCENT,
            relief=tk.SOLID, borderwidth=1, padx=8, pady=6, height=12
        )
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_area.configure(state=tk.DISABLED)
        self._init_log_tags()

        footer = ttk.Frame(self.root)
        footer.pack(fill=tk.X, padx=16, pady=(0, 10))
        # 版权居中显示
        ttk.Label(footer, text="Pi - Node云服自动部署系统v3.0 © 2025 蚁巢", style="Footer.TLabel").pack(expand=True)
        
        self.ssh_client = None
        self.installation_running = False
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("OpenVPNInstaller")

        # 存储原始输入法状态
        self.original_input_method = None

    def center_window(self):
        """将窗口居中显示在屏幕上"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _init_log_tags(self):
        self.log_area.tag_config("success", foreground=DarkTheme.OK)
        self.log_area.tag_config("error", foreground=DarkTheme.ERR)
        self.log_area.tag_config("warning", foreground=DarkTheme.WARN)
        self.log_area.tag_config("info", foreground=DarkTheme.ACCENT)
        self.log_area.tag_config("debug", foreground=DarkTheme.MUTED)
        self.log_area.tag_config("credential", foreground="#c792ea")
        self.log_area.tag_config("service", foreground="#7fdbca")

    def log_message(self, message, tag="info"):
        self.log_area.configure(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_area.yview(tk.END)
        self.log_area.configure(state=tk.DISABLED)
        self.logger.info(message)
        
    def switch_to_english_input(self, event):
        """切换输入法为英文模式"""
        try:
            # 加载user32动态链接库
            user32 = ctypes.WinDLL('user32')
            imm32 = ctypes.WinDLL('imm32')
            
            # 模拟按下并释放Shift键
            user32.keybd_event(0x10, 0, 0, 0)  # 按下Shift键
            user32.keybd_event(0x10, 0, 2, 0)  # 释放Shift键

    def restore_input_method(self, event):
        """恢复原始输入法状态"""
        try:
            if self.original_input_method:
                user32 = ctypes.WinDLL('user32')
                imm32 = ctypes.WinDLL('imm32')
                
                foreground_hwnd = user32.GetForegroundWindow()
                thread_id = user32.GetWindowThreadProcessId(foreground_hwnd, None)
                imm32.ImmSetOpenStatus(self.original_input_method, 1)
                
                self.log_message("输入法已恢复", "info")
        except:
            pass
    
    def start_installation(self):
        if self.installation_running:
            self.log_message("安装已在运行中", "warning")
            return
            
        server_ip = self.server_ip.get()
        username = self.username.get()
        password = self.password.get()
        ssh_port = self.ssh_port.get()
        
        vpn_port = "1194"
        client_name = "client"
        dns_server = "Cloudflare"
        compression = "y"
        
        if not server_ip or not username or not password:
            messagebox.showerror("输入错误", "请填写所有必填字段")
            return
        
        try:
            ssh_port = int(ssh_port)
            vpn_port = int(vpn_port)
        except ValueError:
            messagebox.showerror("输入错误", "端口号必须是整数")
            return
        
        # 仅在安装开始时清空日志区域
        self.log_area.configure(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.configure(state='disabled')
        
        self.installation_running = True
        self.install_button.config(state=tk.DISABLED)
        
        # 重置所有状态指示器
        self.pill_conn.update("未连接", DarkTheme.MUTED)
        self.pill_vpn.update("未安装", DarkTheme.MUTED)
        self.pill_pf.update("未启用", DarkTheme.MUTED)
        self.pill_dl.update("未导入", DarkTheme.MUTED)
        
        # 启动进度条动画
        self.progress.start(10)  # 10毫秒刷新间隔，数字越小越快
        
        thread = threading.Thread(
            target=self.install_openvpn,
            args=(server_ip, username, password, ssh_port, vpn_port, client_name, 
                  dns_server, compression)
        )
        thread.daemon = True
        thread.start()
    
    def install_openvpn(self, server_ip, username, password, ssh_port, vpn_port, 
                        client_name, dns_server, compression):
        try:
            self.log_message("正在连接到服务器...", "info")
            self.pill_conn.update("连接中...", DarkTheme.WARN)  # 更新连接状态
            
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(server_ip, port=ssh_port, username=username, password=password)
            
            self.log_message("✓ 连接成功", "success")
            self.pill_conn.update("已连接", DarkTheme.OK)  # 更新连接状态
            
            self.log_message("下载OpenVPN安装脚本...", "info")
            self.pill_vpn.update("安装中...", DarkTheme.WARN)  # 更新VPN状态
            
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                error = stderr.read().decode()
                self.log_message(f"下载失败: {error}", "error")
                self.pill_vpn.update("安装失败", DarkTheme.ERR)  # 更新VPN状态
                return
            
            self.log_message("✓ 脚本下载完成", "success")
            self.log_message("设置执行权限...", "info")
                error = stderr.read().decode()
                self.log_message(f"权限设置失败: {error}", "error")
                self.pill_vpn.update("安装失败", DarkTheme.ERR)  # 更新VPN状态
                return
            
            self.log_message("✓ 权限设置完成", "success")
            
            self.log_message(f"开始安装OpenVPN (端口: {vpn_port})...", "info")
            
            responses_json = json.dumps(responses)
            self.log_message(f"使用配置响应: {responses}", "debug")
            
            auto_cmd = f"""echo '{responses_json}' | ./openvpn-install.sh --auto"""
            
            self.log_message("安装进行中，请耐心等待...", "info")
            
            transport = self.ssh_client.get_transport()
            channel = transport.open_session()
            channel.get_pty(width=200)
            channel.exec_command(auto_cmd)
            
            client_password = None
            config_path = None
            while not channel.exit_status_ready():
                if channel.recv_ready():
                    output = channel.recv(1024).decode('utf-8', errors='ignore').strip()
                    if output:
                        output = re.sub(r'\x1b\[[0-9;]*m', '', output)
                        self.log_message(output, "debug")
                        
                        if "Password is:" in output:
                            client_password = output.split("Password is:")[1].split()[0].strip()
                            self.log_message(f"✓ 客户端密码: {client_password}", "credential")
                        elif "available at" in output:
                            match = re.search(r"available at (.+\.ovpn)", output)
                            if match:
                                config_path = match.group(1)
                                self.log_message(f"✓ 配置文件路径: {config_path}", "success")
                        elif "IPv4" in output and "network:" in output:
                            ip_match = re.search(r'IPv4 address: (\d+\.\d+\.\d+\.\d+)', output)
                            if ip_match:
                                server_ip = ip_match.group(1)
                                self.log_message(f"检测到服务器公网IP: {server_ip}", "info")
                
                time.sleep(0.1)
            
            exit_status = channel.recv_exit_status()
            if exit_status != 0:
                error = ""
                if channel.recv_stderr_ready():
                    error = channel.recv_stderr(1024).decode('utf-8', errors='ignore')
                if not error:
                    error = "安装失败，未知错误"
                self.log_message(f"OpenVPN安装失败: {error}", "error")
                self.pill_vpn.update("安装失败", DarkTheme.ERR)  # 更新VPN状态
                return
            
            self.log_message("✓ OpenVPN 安装完成", "success")
            self.pill_vpn.update("已安装", DarkTheme.OK)  # 更新VPN状态
            
            # 安装端口转发
            self.log_message("开始安装端口转发工具...", "service")
"""
            conf_cmd = f"""echo '{port_rules}' > /etc/rinetd.conf"""
            stdin, stdout, stderr = self.ssh_client.exec_command(conf_cmd)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                error = stderr.read().decode()
                self.log_message(f"配置文件创建失败: {error}", "error")
                self.pill_pf.update("配置失败", DarkTheme.ERR)  # 更新端口转发状态
                return
            
            self.log_message("✓ 端口转发配置完成", "service")
            
            self.log_message("✓ 端口转发服务已启动", "service")
            self.log_message("端口转发规则已生效:", "service")
            self.log_message(port_rules, "service")
            self.pill_pf.update("已启用", DarkTheme.OK)  # 更新端口转发状态
            
            # 文件下载部分
            self.log_message("下载客户端配置文件...", "info")
            self.pill_dl.update("导入中...", DarkTheme.WARN)  # 更新导入状态
            
            try:
                sftp = self.ssh_client.open_sftp()
                sftp.get(config_path, local_path)
                self.log_message(f"✓ 配置文件已保存到: {local_path}", "success")
                self.log_message("您可以使用此文件连接到VPN服务器", "info")
                self.pill_dl.update("已导入", DarkTheme.OK)  # 更新导入状态
                
                self.log_message("\n========== VPN 连接信息 ==========", "success")
                self.log_message(f"服务器地址: {server_ip}", "info")
                self.log_message(f"端口: {vpn_port}", "info")
                self.log_message(f"客户端名称: {client_name}", "info")
                self.log_message(f"配置文件: {local_path}", "info")
                
                if client_password:
                    self.log_message(f"客户端密码: {client_password}", "credential")
                
            except Exception as e:
                self.log_message(f"⚠ 无法下载配置文件: {str(e)}", "warning")
                self.pill_dl.update("导入失败", DarkTheme.ERR)  # 更新导入状态
                self.log_message("请手动从服务器下载配置文件:", "warning")
                self.log_message(f"    scp {username}@{server_ip}:{config_path} \"{local_path}\"", "warning")
            
            self.log_message("安装完成，可以直接连接云服，无需手动导入！", "success")

            # 更新所有状态为错误
            self.pill_conn.update("连接失败", DarkTheme.ERR)
            self.pill_vpn.update("安装失败", DarkTheme.ERR)
            self.pill_pf.update("配置失败", DarkTheme.ERR)
            self.pill_dl.update("导入失败", DarkTheme.ERR)
        
        finally:
            # 确保停止进度条动画
            self.root.after(0, self.progress.stop)
            
            try:
                if self.ssh_client:
                    self.ssh_client.close()
            except:
                pass
            
            self.installation_running = False
            self.install_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = OpenVPNInstaller(root)

    root.mainloop()
