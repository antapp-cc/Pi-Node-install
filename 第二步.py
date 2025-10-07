import sys
import os
import urllib.request
import ssl
import json
import subprocess
import time
import ctypes
from PyQt5.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import (QPixmap, QIcon, QColor, QLinearGradient, QPainter, QFont,
                        QPainterPath, QRegion, QBrush, QPalette, QPen)

class ModernInstaller(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("蚁巢anthive - PNAI-p02安装")
        self.setFixedSize(800, 600)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # 配置URL列表
        self.config_urls = [
            主服务端配置文件URL
            备用服务端配置文件URL
        ]
        
        # 临时文件路径
        self.temp_dir = os.environ.get('TEMP', '.')
        self.docker_path = os.path.join(self.temp_dir, "Docker.exe")
        self.openvpn_path = os.path.join(self.temp_dir, "OpenVPN.msi")
        self.wsl_update_path = os.path.join(self.temp_dir, "wsl.msi")
        
        # 初始化变量
        self.current_progress = 0
        self.downloads_complete = False
        self.install_process = None
        self.drag_position = None
        self.config_list = []  # 存储所有成功的配置

        # 设置窗口圆角
        self.setWindowRoundedCorners()
        
        # 创建主界面
        self.init_ui()
        
        # 开始安装流程
        QTimer.singleShot(500, self.start_installation)
    
    def setWindowRoundedCorners(self):
        # 创建圆角窗口
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 15, 15)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        
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
        title_layout.setSpacing(0)
        
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
        
        self.title_label = QLabel("蚁巢anthive - PNAI-p02安装")
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
        self.step2 = self.create_step("2", "下载组件", False)
        self.step_line2 = self.create_step_line()
        self.step3 = self.create_step("3", "安装程序", False)
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
    
    def fetch_config(self):
        """从网络获取配置文件，支持备用URL并收集所有可用配置"""
        self.config_list = []  # 清空之前的配置
        
        for config_url in self.config_urls:
            try:
                # 创建请求对象并设置User-Agent
                req = urllib.request.Request(config_url, headers={'User-Agent': self.user_agent})
                
                # 下载配置文件
                with urllib.request.urlopen(req, context=ssl_context) as response:
                    config_content = response.read().decode('utf-8')
                    config_data = json.loads(config_content)
                    self.config_list.append(config_data)
                    
                print(f"成功从 {config_url} 获取配置")
            except Exception as e:
                print(f"尝试从 {config_url} 获取配置失败: {str(e)}")
                continue
        
        # 检查是否获取到任何配置
        if not self.config_list:
            self.show_error("所有配置URL尝试失败，请检查网络连接")
            return False
        
        return True
    
    def start_installation(self):
        # 更新步骤指示器
        self.update_step(1)
        
        # 获取配置文件
        self.update_progress(5, "正在获取配置信息...", "连接服务器...")
        if not self.fetch_config():
            return
        
        # 第一阶段: 准备安装环境
        self.update_progress(10, "正在准备安装环境...", "初始化组件...")
        QTimer.singleShot(1000, self.download_components)
    
    def download_components(self):
        # 更新步骤指示器
        self.update_step(2)
        
        # 下载Docker
        if not self.download_file(
            "docker", 
            self.docker_path, 
            "Docker安装程序",
            start_progress=10,
            end_progress=30
        ):
            return
        
        # 下载OpenVPN
        if not self.download_file(
            "openvpn", 
            self.openvpn_path, 
            "OpenVPN安装程序",
            start_progress=30,
            end_progress=40
        ):
            return
        
        # 下载WSL更新
        if not self.download_file(
            "wsl", 
            self.wsl_update_path, 
            "WSL安装程序",
            start_progress=40,
            end_progress=60
        ):
            return
        
        # 所有下载完成后进入安装阶段
        self.downloads_complete = True
        self.update_progress(60, "所有组件下载完成", "准备安装...")
        QTimer.singleShot(1000, self.install_components)
    
    def download_file(self, file_type, path, name, start_progress, end_progress):
        """下载文件并支持备用地址"""
        last_exception = None
        
        # 遍历所有可用的配置
        for config_data in self.config_list:
            try:
                # 从当前配置获取下载地址
                if file_type == "docker":
                    url = config_data.get("docker_url", "")
                elif file_type == "openvpn":
                    url = config_data.get("openvpn_url", "")
                elif file_type == "wsl":
                    url = config_data.get("wsl_update_url", "")
                
                if not url:
                    continue  # 跳过无效URL
                    
                # 创建请求对象并设置User-Agent
                req = urllib.request.Request(url, headers={'User-Agent': self.user_agent}
                
                # 获取远程文件大小
                with urllib.request.urlopen(req, context=ssl_context) as response:
                    remote_size = int(response.headers['Content-Length'])
                
                # 检查本地文件是否存在且大小匹配
                if os.path.exists(path):
                    local_size = os.path.getsize(path)
                    if local_size == remote_size:
                        self.update_progress(end_progress, f"{name}已存在且大小匹配", "跳过下载...")
                        return True
                    else:
                        # 大小不匹配，删除旧文件
                        os.remove(path)
                        self.status_detail.setText(f"文件大小不匹配 ({local_size} ≠ {remote_size}字节)，重新下载...")
                
                # 下载文件
                self.update_progress(start_progress, f"下载{name}...", "正在连接到服务器...")
                
                # 重新创建请求对象（因为urlopen会消耗流）
                req = urllib.request.Request(url, headers={'User-Agent': self.user_agent})
                with urllib.request.urlopen(req, context=ssl_context) as response:
                    with open(path, 'wb') as out_file:
                        total_size = int(response.headers['Content-Length'])
                        downloaded = 0
                        while True:
                            buffer = response.read(8192)
                            if not buffer:
                                break
                            downloaded += len(buffer)
                            out_file.write(buffer)
                            
                            # 更新进度
                            if total_size > 0:
                                percent = min(100, int(downloaded * 100 / total_size))
                                download_mb = downloaded / 1024 / 1024
                                total_mb = total_size / 1024 / 1024
                                current_progress = start_progress + int(percent * (end_progress - start_progress) / 100)
                                
                                self.update_progress(
                                    current_progress,
                                    f"下载{name}...", 
                                    f"下载中: {min(100, percent)}% ({download_mb:.1f}MB/{total_mb:.1f}MB)"
                                )
                
                # 验证下载后的文件大小
                local_size = os.path.getsize(path)
                if local_size != remote_size:
                    raise Exception(f"文件大小不匹配: 本地({local_size}字节) ≠ 远程({remote_size}字节)")
                
                self.update_progress(end_progress, f"{name}下载完成", "文件验证通过")
                return True
                
            except Exception as e:
                last_exception = e
                # 删除可能损坏的文件
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except:
                        pass
                # 尝试下一个配置源
                self.status_detail.setText(f"下载失败，尝试备用地址...")
                continue
        
        # 所有配置源都尝试失败
        self.show_error(f"所有下载地址尝试失败: {str(last_exception)}")
        return False
    
    def install_components(self):
        # 更新步骤指示器
        self.update_step(3)
        
        if not self.downloads_complete:
            return
            
        # 安装OpenVPN
        self.update_progress(60, "安装OpenVPN...", "运行安装程序...")
        try:
            # 静默安装OpenVPN
        except Exception as e:
            self.show_error(f"OpenVPN安装失败: {str(e)}")
        
        # 安装WSL更新
        self.update_progress(70, "安装WSL更新...", "运行安装程序...")
        try:
            # 静默安装WSL更新
        except Exception as e:
            self.show_error(f"WSL更新安装失败: {str(e)}")
        
        # 配置WSL
        self.update_progress(80, "配置WSL...", "设置默认版本为2...")
        try:
            # 设置WSL默认版本为2
        except Exception as e:
            self.show_error(f"WSL配置失败: {str(e)}")
        
        # 安装Docker
        self.update_progress(90, "安装Docker...", "运行安装程序...")
        try:
            # 静默安装Docker
        except Exception as e:
            self.show_error(f"Docker安装失败: {str(e)}")
        
        # 所有安装完成
        self.update_progress(100, "所有组件安装完成", "清理临时文件...")
        QTimer.singleShot(1000, self.cleanup_and_complete)
    
    def cleanup_and_complete(self):
        # 清理临时文件
        try:
            for path in [self.docker_path, self.openvpn_path, self.wsl_update_path]:
                if os.path.exists(path):
                    os.remove(path)
        except Exception as e:
            print(f"删除临时文件失败: {str(e)}")
        
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
        message_label = QLabel("PNAI-p02已成功安装\n请重启电脑以使配置生效")
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
        
        # 开始倒计时
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown = 5  # 5秒倒计时
        self.update_countdown()  # 立即更新一次
        self.countdown_timer.start(1000)  # 每秒更新一次
    
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
