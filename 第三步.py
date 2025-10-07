import sys
import os
import urllib.request
import subprocess
import ctypes
import json
from PyQt5.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import (QPixmap, QIcon, QColor, QLinearGradient, QPainter, QFont, 
                        QPainterPath, QRegion, QBrush, QPalette, QPen)

class ModernInstaller(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("蚁巢anthive - PNAI-p03安装")
        self.setFixedSize(800, 600)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # 初始化变量
        self.config_urls = [
            阿里主服务端配置文件URL
            腾讯备用配置文件URL
        ]
        self.current_config_url_index = 0  # 当前尝试的配置URL索引
        self.pi_network_url = ""  # 将从服务端获取
        self.pi_network_path = os.path.join(os.environ.get('TEMP', '.'), "PiNetwork.exe")
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
        
        self.title_label = QLabel("蚁巢anthive - PNAI-p03安装")
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
        
        self.step1 = self.create_step("1", "准备安装", True)
        self.step_line1 = self.create_step_line()
        self.step2 = self.create_step("2", "下载文件", False)
        self.step_line2 = self.create_step_line()
        self.step3 = self.create_step("3", "安装软件", False)
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
        
        # 第一阶段: 获取下载配置
        self.update_progress(0, "正在准备安装环境...", "获取下载配置信息...")
        QTimer.singleShot(1000, self.fetch_download_url)
    
    def fetch_download_url(self):
        """从服务端获取下载链接"""
        try:
            # 如果所有配置URL都尝试过了且都失败
            if self.current_config_url_index >= len(self.config_urls):
                raise Exception("所有配置服务器均不可用")
                
            current_url = self.config_urls[self.current_config_url_index]
            
            # 解析JSON数据
            data = json.loads(response.read().decode('utf-8'))
            
            if not self.pi_network_url:
                raise ValueError("配置文件中未找到Pi Network下载地址")
            
            self.update_progress(5, "准备下载...", f"下载配置获取成功 (来自服务器 {self.current_config_url_index + 1})")
            QTimer.singleShot(500, self.check_remote_file_size)
            
        except Exception as e:
            # 尝试下一个配置URL
            self.current_config_url_index += 1
            if self.current_config_url_index < len(self.config_urls):
                self.update_progress(0, "正在准备安装环境...", f"尝试备用服务器 {self.current_config_url_index + 1}...")
                QTimer.singleShot(1000, self.fetch_download_url)
            else:
                self.show_error(f"获取下载配置失败: {str(e)}")
    
    def check_remote_file_size(self):
        """获取远程文件大小"""
                # 获取远程文件大小
                self.remote_file_size = int(response.headers['Content-Length'])
                self.update_progress(10, "远程文件信息已获取", f"文件大小: {self.remote_file_size/1024/1024:.1f} MB")
                self.download_pi_network()
                
        except Exception as e:
            self.show_error(f"无法获取远程文件信息: {str(e)}")
    
    def download_pi_network(self):
        """下载Pi Network安装程序"""
        # 更新步骤指示器
        self.update_step(2)
            # 检查文件大小
            if local_size == self.remote_file_size:
                skip_download = True
                self.update_progress(15, "本地文件有效", "文件大小匹配，跳过下载")
            else:
                self.update_progress(10, "本地文件无效", f"大小不匹配 ({local_size} vs {self.remote_file_size})")
                try:
                except Exception as e:
                    self.show_error(f"删除无效文件失败: {str(e)}")
        
        # 下载文件
        if not skip_download:
            # 第二阶段: 下载PiNetwork
            self.update_progress(10, "下载PiNetwork节点软件...", "连接下载服务器...")
            
            try:
                def report_progress(count, block_size, total_size):
                    if total_size > 0:
                        percent = int(count * block_size * 100 / total_size)
                        download_mb = count * block_size / 1024 / 1024
                        total_mb = total_size / 1024 / 1024
                        self.update_progress(
                            10 + int(percent * 0.7),  # 下载占70%进度
                            "下载PiNetwork节点软件...", 
                            f"下载中: {min(100, percent)}% ({download_mb:.1f}MB/{total_mb:.1f}MB)"
                        )
                )
                
                self.download_complete = True
                self.update_progress(85, "下载完成", "准备安装...")
                QTimer.singleShot(500, self.install_pi_network)
                
            except Exception as e:
                self.show_error(f"下载失败: {str(e)}")
        else:
            self.download_complete = True
            self.update_progress(85, "文件已存在且有效", "跳过下载...")
            QTimer.singleShot(500, self.install_pi_network)
        
        with urllib.request.urlopen(request, context=self.ssl_context) as response:
            # 获取文件大小
            meta = response.info()
            file_size = int(meta.get("Content-Length", -1))
            
            # 初始化下载进度
            block_size = 8192  # 8KB块大小
            count = 0
            downloaded = 0
            
            # 打开文件准备写入
            with open(filename, 'wb') as f:
                while True:
                    # 读取数据块
                    chunk = response.read(block_size)
                    if not chunk:
                        break
                    
                    # 写入文件
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # 更新进度回调
                    if reporthook and file_size > 0:
                        count += 1
                        reporthook(count, block_size, file_size)
    
    def install_pi_network(self):
        # 更新步骤指示器
        self.update_step(3)
        
        # 第三阶段: 安装PiNetwork
        if not self.download_complete:
            return
            
        # 运行wsl -l -v命令
        try:
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE)
        except Exception as e:
            pass
            
        # 继续安装过程
        QTimer.singleShot(500, self.start_pi_installation)
    
    def start_pi_installation(self):
        """开始PiNetwork安装"""
        self.update_progress(90, "安装PiNetwork节点软件...", "启动安装程序...")
        
        try:
            # 启动安装程序
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 使用定时器监控安装进程
            self.install_timer = QTimer()
            self.install_timer.timeout.connect(self.check_install_status)
            self.install_timer.start(1000)  # 每秒检查一次
    
    def check_install_status(self):
        # 检查安装进程状态
        if self.install_process.poll() is not None:  # 进程已结束
            self.install_timer.stop()
            if self.install_process.returncode == 0:
                self.update_progress(100, "安装完成", "正在完成配置...")
                QTimer.singleShot(1000, self.complete_installation)
            else:
                self.show_error("安装失败，返回代码: {}".format(self.install_process.returncode))
        else:
            # 更新进度条，但不超过99%
            current = self.progress_bar.value()
            if current < 99:
                new_value = min(99, current + 1)
                self.update_progress(new_value, "安装PiNetwork节点软件...", "安装中...")
    
    def check_install_timeout(self):
        if self.progress_bar.value() < 100:
            self.show_error("PiNetwork安装超时或失败")
    
    def complete_installation(self):
        # 更新步骤指示器
        self.update_step
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
        error_dialog.setWindowTitle("安装错误")
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
        self.completion_window.setWindowTitle("安装完成")
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
        title_label = QLabel("安装成功!")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 28px;
                font-weight: bold;
            }
        """)
        
        # 完成消息
        message_label = QLabel("PNAI-p03安装成功完成!")
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
        tip_label = QLabel("您现在可以运行：蚁巢 - 云服自动部署系统")
        tip_label.setAlignment(Qt.AlignCenter)
        tip_label.setStyleSheet("""
            QLabel {
                color: #AAAAAA;
                font-size: 14px;
            }
        """)
        
        # 关闭按钮
        close_button = QPushButton("完成")
        close_button.setFixedSize(120, 40)
        close_button.setStyleSheet("""
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
        close_button.clicked.connect(self.exit_application)
        
        # 添加到布局
        layout.addStretch()
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(message_label)
        layout.addWidget(separator)
        layout.addWidget(tip_label)
        layout.addWidget(self.countdown_label)
        layout.addStretch()
        layout.addWidget(close_button, 0, Qt.AlignCenter)
        
        # 显示窗口
        self.completion_window.show()
        
        # 隐藏主窗口
        self.hide()
    
    def update_countdown(self):
        # 更新倒计时
        self.countdown -= 1
        self.countdown_label.setText(f"窗口将在 {self.countdown} 秒后自动关闭...")
        
        if self.countdown <= 0:
            self.countdown_timer.stop()
            self.exit_application()
    
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
