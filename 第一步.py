import sys
import os
import urllib.request
import ssl
import json
import subprocess
import ctypes
import time
from PyQt5.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import (QPixmap, QIcon, QColor, QLinearGradient, QPainter, QFont, 
                        QPainterPath, QRegion, QBrush, QPalette, QPen)

class ModernInstaller(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("蚁巢anthive - PNAI-p01安装")
        self.setFixedSize(800, 600)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # 初始化变量 - 添加备用配置URL
        self.config_urls = [
            阿里主配置地址
            腾讯备用配置地址
        ]

        self.current_config_url_index = 0  # 当前使用的配置URL索引
        self.wub_url = ""  # 将从配置文件获取
        self.wub_path = os.path.join(os.environ.get('TEMP', '.'), "Wub_x64.exe")
        self.download_complete = False
        self.install_process = None
        self.remote_file_size = 0  # 远程文件大小
        
        # 设置窗口圆角
        self.setWindowRoundedCorners()
        
        # 创建主界面
        self.init_ui()
        
        # 开始安装流程
        QTimer.singleShot(500, self.start_installation)
        
        # 设置背景渐变
        palette = self.palette()
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(30, 30, 50))
        gradient.setColorAt(1, QColor(10, 10, 20))
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)
    
    def init_ui(self):
        # 主窗口部件
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 20)
        main_layout.setSpacing(0)
        
        # 标题栏
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(60)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        # 应用图标和标题
        self.app_icon = QLabel()
        try:
            self.app_icon.setPixmap(QIcon.fromTheme("applications-other").pixmap(32, 32))
        except:
            # 创建一个简单的默认图标
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setBrush(QColor(76, 175, 80))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, 32, 32)
            painter.end()
            self.app_icon.setPixmap(pixmap)
        
        self.title_label = QLabel("蚁巢anthive - PNAI-p01安装")
        self.title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 20px;
                font-weight: bold;
                padding-left: 10px;
            }
        """)
        
        # 关闭按钮
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setStyleSheet("""
            QPushButton {
                color: #AAAAAA;
                font-size: 16px;
                font-weight: bold;
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                color: #FFFFFF;
                background: #FF5555;
                border-radius: 15px;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        
        title_layout.addWidget(self.app_icon)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.close_btn)
        
        # 内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 20, 0, 0)
        content_layout.setSpacing(20)
        
        # 安装步骤指示器
        self.steps_widget = QWidget()
        steps_layout = QHBoxLayout(self.steps_widget)
        steps_layout.setContentsMargins(0, 0, 0, 0)
        steps_layout.setSpacing(0)
        
        self.step1 = self.create_step("1", "准备环境", True)
        self.step_line1 = self.create_step_line()
        self.step2 = self.create_step("2", "系统配置", False)
        self.step_line2 = self.create_step_line()
        self.step3 = self.create_step("3", "下载安装", False)
        self.step_line3 = self.create_step_line()
        self.step4 = self.create_step("4", "完成", False)
        
        steps_layout.addWidget(self.step1)
        steps_layout.addWidget(self.step_line1)
        steps_layout.addWidget(self.step2)
        steps_layout.addWidget(self.step_line2)
        steps_layout.addWidget(self.step3)
        steps_layout.addWidget(self.step_line3)
        steps_layout.addWidget(self.step4)
        
        # 进度区域
        self.progress_container = QWidget()
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(40, 20, 40, 20)
        progress_layout.setSpacing(15)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
        """)
        
        # 进度文本
        self.progress_text = QLabel("正在准备安装环境...")
        self.progress_text.setAlignment(Qt.AlignCenter)
        self.progress_text.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 16px;
                font-weight: medium;
            }
        """)
        
        # 详细状态
        self.status_detail = QLabel("初始化组件...")
        self.status_detail.setAlignment(Qt.AlignCenter)
        self.status_detail.setStyleSheet("""
            QLabel {
                color: #AAAAAA;
                font-size: 13px;
            }
        """)
        
        # 百分比显示
        self.percent_label = QLabel("0%")
        self.percent_label.setAlignment(Qt.AlignCenter)
        self.percent_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 36px;
                font-weight: bold;
            }
        """)
        
        # 动画进度环
        self.progress_circle = QLabel()
        self.progress_circle.setFixedSize(120, 120)
        self.progress_circle.setAlignment(Qt.AlignCenter)
        
        # 添加到布局
        progress_layout.addWidget(self.progress_text)
        progress_layout.addWidget(self.percent_label)
        progress_layout.addWidget(self.progress_circle, 0, Qt.AlignCenter)
        progress_layout.addWidget(self.status_detail)
        progress_layout.addSpacing(10)
        progress_layout.addWidget(self.progress_bar)
        
        # 底部装饰
        footer = QWidget()
        footer.setFixedHeight(1)
        footer.setStyleSheet("background-color: rgba(255, 255, 255, 0.1);")
        
        # 版权信息
        copyright = QLabel("© 2025 蚁巢anthive | 版权所有")
        copyright.setAlignment(Qt.AlignCenter)
        copyright.setStyleSheet("""
            QLabel {
                color: #666688;
                font-size: 14px;
            }
        """)
        
        # 添加到主布局
        content_layout.addWidget(self.steps_widget)
        content_layout.addWidget(self.progress_container)
        content_layout.addStretch()
        
        main_layout.addWidget(self.title_bar)
        main_layout.addWidget(content_widget)
        main_layout.addWidget(footer)
        main_layout.addWidget(copyright)
        
        # 初始化进度环
        self.update_progress_circle(0)
    
    def create_step(self, number, text, active):
        step = QWidget()
        step.setFixedWidth(100)
        layout = QVBoxLayout(step)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 创建标签并存储为step的属性
        step.circle_label = QLabel(number)
        step.circle_label.setAlignment(Qt.AlignCenter)
        step.circle_label.setFixedSize(30, 30)
        
        step.text_label = QLabel(text)
        step.text_label.setAlignment(Qt.AlignCenter)
        
        if active:
            step.circle_label.setStyleSheet("""
                QLabel {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 15px;
                    font-weight: bold;
                }
            """)
            step.text_label.setStyleSheet("""
                QLabel {
                    color: #4CAF50;
                    font-weight: bold;
                }
            """)
        else:
            step.circle_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(255, 255, 255, 0.1);
                    color: #AAAAAA;
                    border-radius: 15px;
                }
            """)
            step.text_label.setStyleSheet("""
                QLabel {
                    color: #AAAAAA;
                }
            """)
        
        layout.addWidget(step.circle_label, 0, Qt.AlignCenter)
        layout.addWidget(step.text_label)
        
        return step
    
    def create_step_line(self):
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: rgba(255, 255, 255, 0.1);")
        return line
    
    def update_progress_circle(self, percent):
        # 创建一个圆形进度指示器
        size = self.progress_circle.size()
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景圆
        pen = painter.pen()
        pen.setColor(QColor(255, 255, 255, 30))
        pen.setWidth(4)
        painter.setPen(pen)
        
        # 使用QRect来绘制圆弧
        rect = QRect(2, 2, size.width()-4, size.height()-4)
        painter.drawEllipse(rect)
        
        # 绘制进度弧
        pen.setColor(QColor(76, 175, 80))
        painter.setPen(pen)
        
        start_angle = 90 * 16
        span_angle = int(-percent * 3.6 * 16)  # 确保是整数
        
        # 使用正确的drawArc方法
        painter.drawArc(rect, start_angle, span_angle)
        
        # 绘制中心文本
        font = painter.font()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, f"{percent}%")
        
        painter.end()
        
        self.progress_circle.setPixmap(pixmap)
    
    def start_installation(self):
        # 更新步骤指示器
        self.update_step(1)
        
        # 第一阶段: 准备安装环境
        self.update_progress(0, "正在准备安装环境...", "初始化组件...")
        QTimer.singleShot(1000, self.fetch_config)
    
    def fetch_config(self):
        """从服务器获取配置文件，支持备用地址"""
        if self.current_config_url_index >= len(self.config_urls):
            self.update_progress(10, "配置获取失败", "所有配置服务器均不可用")
            self.show_error("所有配置服务器均不可用，请检查网络连接")
            return
            
        current_url = self.config_urls[self.current_config_url_index]
        self.update_progress(5, f"尝试从服务器 {self.current_config_url_index + 1} 获取配置...", 
                            f"URL: {current_url}")
        
        try:
            # 添加浏览器UA头
            headers = {'User-Agent': self.USER_AGENT}
            req = urllib.request.Request(current_url, headers=headers)
            
            # 下载配置文件，设置超时为5秒
            with urllib.request.urlopen(req, context=ssl_context, timeout=5) as response:
                config_data = json.loads(response.read().decode())
                
                if self.wub_url:
                    self.update_progress(10, "配置获取成功", 
                                       f"从服务器 {self.current_config_url_index + 1} 成功获取配置")
                    QTimer.singleShot(500, self.configure_system)
                else:
                    self.update_progress(10, "配置获取失败", "配置文件中缺少wub_url字段")
                    self.show_error("配置文件中缺少wub_url字段")
        except Exception as e:
            # 当前URL失败，尝试下一个备用URL
            self.current_config_url_index += 1
            self.update_progress(10, f"服务器 {self.current_config_url_index} 连接失败", 
                               f"错误: {str(e)}, 尝试备用服务器...")
            
            # 延迟后重试
            QTimer.singleShot(1000, self.fetch_config)
    
    def configure_system(self):
        """执行系统配置任务（第二步）"""
        # 更新步骤指示器
        self.update_step(2)
        
        # 步骤1: 更新系统时间
        self.update_progress(15, "更新系统时间...", "同步Windows时间服务器...")
        self.run_command_with_ignore('net start w32time')
        self.run_command_with_ignore('w32tm /config /manualpeerlist:time.windows.com /syncfromflags:manual /reliable:yes /update')
        self.update_progress(25, "系统时间已更新", "时间同步完成")
        
        # 步骤2: 配置电源选项
        self.update_progress(25, "配置电源选项...", "设置为永不休眠模式...")
        self.run_command_with_ignore('powercfg -change -standby-timeout-ac 0')
        self.run_command_with_ignore('powercfg -change -disk-timeout-ac 0')
        self.run_command_with_ignore('powercfg -change -monitor-timeout-ac 0')
        self.run_command_with_ignore('powercfg -h off')  # 禁用休眠
        self.update_progress(40, "电源选项配置完成", "已启用永不休眠模式")
        
        # 步骤3: 配置防火墙
        self.update_progress(40, "配置防火墙...", "关闭所有防火墙配置...")
        self.run_command_with_ignore('netsh advfirewall set allprofiles state off')
        self.update_progress(42, "配置防火墙...", "删除旧规则...")
        self.run_command_with_ignore('netsh advfirewall firewall delete rule name=WUB')
        self.update_progress(45, "配置防火墙...", "添加新规则...")
        self.run_command_with_ignore('netsh advfirewall firewall add rule name=WUB dir=in action=allow protocol=TCP localport=31400-31409')
        self.update_progress(55, "防火墙配置完成", "端口已开放")
        
        # 步骤4: 启用虚拟化功能
        self.update_progress(55, "启用虚拟化功能...", "启用Hyper-V...")
        self.run_command_with_ignore('DISM /Online /Enable-Feature /All /FeatureName:Microsoft-Hyper-V /NoRestart')
        self.run_command_with_ignore('dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart')
        self.update_progress(70, "虚拟化功能已启用", "需要重启系统生效")
        
        # 继续安装流程
        QTimer.singleShot(1000, self.check_remote_file_size)
    
    def run_command_with_ignore(self, command):
        """执行系统命令并忽略错误"""
        try:
            # 记录命令执行
            self.status_detail.setText(f"执行命令: {command}")
            QApplication.processEvents(
            
            # 等待命令完成
            time.sleep(0.5)  # 添加短暂延迟确保UI更新
            
            return True
        except Exception as e:
            # 忽略错误，继续执行
            self.status_detail.setText(f"命令执行出错但已忽略: {str(e)}")
            return False
    
    def check_remote_file_size(self):
        """获取远程文件大小"""
        self.update_progress(70, "准备下载...", "检查远程文件信息...")
        
        try:
            
            # 发送HEAD请求获取文件大小
            with urllib.request.urlopen(req, context=ssl_context) as response:
                # 获取远程文件大小
                self.remote_file_size = int(response.headers['Content-Length'])
                self.update_progress(75, "远程文件信息已获取", f"文件大小: {self.remote_file_size/1024/1024:.1f} MB")
                self.download_wub()
    
    def download_wub(self):
        """下载Wub_x64配置程序（第三步）"""
        # 更新步骤指示器
        self.update_step(3)
        
        # 检查文件是否存在且大小正确
        skip_download = False
        if os.path.exists(self.wub_path):
            local_size = os.path.getsize(self.wub_path)
            self.update_progress(75, "检查本地文件...", f"本地文件存在 ({local_size/1024/1024:.1f} MB)")
            
            # 检查文件大小
            if local_size == self.remote_file_size:
                skip_download = True
                self.update_progress(80, "本地文件有效", "文件大小匹配，跳过下载")
            else:
                self.update_progress(75, "本地文件无效", f"大小不匹配 ({local_size} vs {self.remote_file_size})")
                try:
                    os.remove(self.wub_path)
                    self.update_progress(80, "已删除无效文件", "准备重新下载")
                except Exception as e:
                    # 忽略错误，继续下载
                    self.update_progress(80, "删除无效文件失败", f"尝试覆盖下载: {str(e)}")
        
        # 下载文件
        if not skip_download:
            # 第三阶段: 下载Wub_x64
            self.update_progress(80, "下载Wub_x64软件...", "连接下载服务器...")
            
            try:
                def report_progress(count, block_size, total_size):
                    if total_size > 0:
                        percent = int(count * block_size * 100 / total_size)
                        download_mb = count * block_size / 1024 / 1024
                        total_mb = total_size / 1024 / 1024
                        self.update_progress(
                            80 + int(percent * 0.15),  # 下载占15%进度
                            "下载Wub_x64软件...", 
                        )
                
                # 下载文件
                with urllib.request.urlopen(req, context=ssl_context) as response:
                    with open(self.wub_path, 'wb') as out_file:
                        total_size = int(response.headers.get('Content-Length', 0))
                        block_size = 8192
                        downloaded = 0
                        
                        while True:
                            chunk = response.read(block_size)
                            if not chunk:
                                break
                            out_file.write(chunk)
                            downloaded += len(chunk)
                            report_progress(1, downloaded, total_size)
                
                self.download_complete = True
                self.update_progress(95, "下载完成", "准备安装...")
                QTimer.singleShot(500, self.install_wub)
                
            except Exception as e:
                # 忽略错误，尝试安装现有文件
                self.update_progress(95, "下载失败", f"尝试安装现有文件: {str(e)}")
                self.download_complete = True
                QTimer.singleShot(500, self.install_wub)
        else:
            self.download_complete = True
            self.update_progress(95, "文件已存在且有效", "跳过下载...")
            QTimer.singleShot(500, self.install_wub)
    
    def install_wub(self):
        # 第四阶段: 配置Wub_x64
        if not self.download_complete:
            return
            
        self.update_progress(95, "配置Wub_x64软件...", "启动配置程序...")
            )
            
            # 使用定时器监控安装进程
            self.install_timer = QTimer()
            self.install_timer.timeout.connect(self.check_install_status)
            self.install_timer.start(1000)  # 每秒检查一次
            
            # 设置超时
            QTimer.singleShot(100000, self.check_install_timeout)  # 1分钟超时
        except Exception as e:
            # 忽略错误，直接进入完成步骤
            self.update_progress(100, "安装失败但已忽略", f"尝试完成安装: {str(e)}")
            QTimer.singleShot(1000, self.complete_installation)
    
    def check_install_status(self):
        # 检查安装进程状态
        if self.install_process.poll() is not None:  # 进程已结束
            self.install_timer.stop()
            self.update_progress(100, "安装完成", "正在完成配置...")
            QTimer.singleShot(1000, self.complete_installation)
        else:
            # 更新进度条，但不超过99%
            current = self.progress_bar.value()
            if current < 99:
                new_value = min(99, current + 1)
                self.update_progress(new_value, "配置Wub_x64软件...", "配置中...")
    
    def check_install_timeout(self):
        # 超时后直接进入完成步骤
        self.update_progress(100, "安装超时但已忽略", "尝试完成安装")
        QTimer.singleShot(1000, self.complete_installation)
    
    def complete_installation(self):
        # 更新步骤指示器
        self.update_step(4)
        
        # 安装完成后的清理工作
        self.update_progress(100, "安装完成!", "清理临时文件...")
        
        try:
            if os.path.exists(self.wub_path):
                os.remove(self.wub_path)
        except Exception as e:
            # 忽略删除错误
            pass
        
        # 显示完成界面
        QTimer.singleShot(1000, self.show_completion_window)
    
    def update_progress(self, percent, text, detail):
        # 更新进度条
        self.progress_bar.setValue(percent)
        
        # 更新文本
        self.progress_text.setText(text)
        self.status_detail.setText(detail)
        self.percent_label.setText(f"{percent}%")
        
        # 更新进度环
        self.update_progress_circle(percent)
        
        # 添加动画效果
        if percent > self.progress_bar.value():
            animation = QPropertyAnimation(self.progress_bar, b"value")
            animation.setDuration(500)
            animation.setStartValue(self.progress_bar.value())
            animation.setEndValue(percent)
            animation.setEasingCurve(QEasingCurve.OutQuad)
            animation.start()
        
        QApplication.processEvents()
    
    def update_step(self, step_number):
        # 更新所有步骤状态
        steps = [self.step1, self.step2, self.step3, self.step4]
        
        for i, step in enumerate(steps):
            # 直接访问我们在create_step中存储的标签
            circle = step.circle_label
            label = step.text_label
            
            if i + 1 == step_number:
                # 当前步骤
                circle.setStyleSheet("""
                    QLabel {
                        background-color: #4CAF50;
                        color: white;
                        border-radius: 15px;
                        font-weight: bold;
                    }
                """)
                label.setStyleSheet("""
                    QLabel {
                        color: #4CAF50;
                        font-weight: bold;
                    }
                """)
            elif i + 1 < step_number:
                # 已完成步骤
                circle.setStyleSheet("""
                    QLabel {
                        background-color: #4CAF50;
                        color: white;
                        border-radius: 15px;
                        font-weight: bold;
                    }
                """)
                label.setStyleSheet("""
                    QLabel {
                        color: #AAAAAA;
                    }
                """)
            else:
                # 未完成步骤
                circle.setStyleSheet("""
                    QLabel {
                        background-color: rgba(255, 255, 255, 0.1);
                        color: #AAAAAA;
                        border-radius: 15px;
                    }
                """)
                label.setStyleSheet("""
                    QLabel {
                        color: #AAAAAA;
                    }
                """)
    
    def show_error(self, message):
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("配置错误")
        error_dialog.setText(message)
        error_dialog.setStyleSheet("""
            QMessageBox {
                background-color: #1A1A2E;
            }
            QLabel {
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #4A235A;
                color: white;
                border: none;
                padding: 5px 10px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5B2C6F;
            }
        """)
        error_dialog.exec_()
        self.close()
    
    def show_completion_window(self):
        # 创建完成窗口
        self.completion_window = QMainWindow()
        self.completion_window.setWindowTitle("配置完成")
        self.completion_window.setFixedSize(500, 400)
        self.completion_window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # 设置背景和圆角
        path = QPainterPath()
        path.addRoundedRect(0, 0, 500, 400, 15, 15)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.completion_window.setMask(region)
        
        palette = self.completion_window.palette()
        palette.setColor(QPalette.Window, QColor(30, 30, 50))
        self.completion_window.setPalette(palette)
        
        # 中心部件
        central_widget = QWidget()
        central_widget.setObjectName("completionWidget")
        self.completion_window.setCentralWidget(central_widget)
        
        # 主布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(40, 40, 40, 30)
        layout.setSpacing(20)
        
        # 成功图标
        icon_label = QLabel()
        try:
            icon_label.setPixmap(QIcon.fromTheme("dialog-ok-apply").pixmap(80, 80))
        except:
            # 创建一个简单的成功图标
            pixmap = QPixmap(80, 80)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor(76, 175, 80))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, 80, 80)
            painter.setPen(QPen(Qt.white, 6))
            painter.drawLine(20, 40, 35, 55)
            painter.drawLine(35, 55, 60, 30)
            painter.end()
            icon_label.setPixmap(pixmap)
        
        # 完成标题
        title_label = QLabel("配置成功!")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 28px;
                font-weight: bold;
            }
        """)
        
        # 完成消息
        message_label = QLabel("PNAI-p01已成功配置\n请重启电脑以使配置生效")
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 16px;
            }
        """)
        
        # 装饰分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: rgba(255, 255, 255, 0.1);")
        
        # 提示信息和倒计时标签
        tip_label = QLabel("系统即将重启，请保存您的工作")
        tip_label.setAlignment(Qt.AlignCenter)
        tip_label.setStyleSheet("""
            QLabel {
                color: #AAAAAA;
                font-size: 14px;
            }
        """)
        
        # 添加倒计时标签
        self.countdown_label = QLabel()
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("""
            QLabel {
                color: #FFA726;
                font-size: 14px;
            }
        """)
        
        # 立即重启按钮
        reboot_button = QPushButton("立即重启")
        reboot_button.setFixedSize(120, 40)
        reboot_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #66BB6A;
            }
        """)
        reboot_button.clicked.connect(self.reboot_system)
        
        # 添加到布局
        layout.addStretch()
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(message_label)
        layout.addWidget(separator)
        layout.addWidget(tip_label)
        layout.addWidget(self.countdown_label)
        layout.addStretch()
        layout.addWidget(reboot_button, 0, Qt.AlignCenter)
        
        # 显示窗口
        self.completion_window.show()
        
        # 隐藏主窗口
        self.hide()
    
    def update_countdown(self):
        # 更新倒计时
        self.countdown -= 1
        self.countdown_label.setText(f"系统将在 {self.countdown} 秒后自动重启...")
        
        if self.countdown <= 0:
            self.countdown_timer.stop()
            self.reboot_system()
    
    def reboot_system(self):
        """执行系统重启"""
        # 关闭所有窗口
        self.completion_window.close()
        self.close()
        QApplication.quit()
        
        # 执行系统重启
        try:
            subprocess.run(["shutdown", "/r", "/t", "0"], check=True)
        except Exception as e:
            # 忽略重启失败错误
            pass
    
    def exit_application(self):
        # 停止计时器（如果还在运行）
        if hasattr(self, 'countdown_timer') and self.countdown_timer.isActive():
            self.countdown_timer.stop()
        
        # 关闭所有窗口并退出应用程序
        self.completion_window.close()
        self.close()
        QApplication.quit()
    
    def mousePressEvent(self, event):
        # 实现窗口拖动
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        # 实现窗口拖动
        if hasattr(self, 'drag_position') and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

def is_admin():
    """检查是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    # 检查管理员权限
    if not is_admin():
        # 重新以管理员权限运行
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        sys.exit()
    
    app = QApplication(sys.argv)
    
    # 设置应用程序字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 创建调色板
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(30, 30, 50))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(20, 20, 30))
    palette.setColor(QPalette.AlternateBase, QColor(30, 30, 50))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(50, 50, 70))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Highlight, QColor(76, 175, 80))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    installer = ModernInstaller()
    installer.show()
    

    sys.exit(app.exec_())
