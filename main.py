# main.py
"""
奶牛体况评分应用
支持中文字体显示和跨平台兼容
支持记录覆盖功能
支持牛号输入和站位快速选择
牛号绑定到特定站位
"""

import os
from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.core.text import LabelBase

# 注册中文字体
font_path = os.path.join(os.path.dirname(__file__), 'noto_sans_sc_regular.ttf')
if os.path.exists(font_path):
    LabelBase.register(name='Chinese', fn_regular=font_path)
else:
    # 如果没有字体文件，尝试使用系统默认字体
    try:
        if os.name == 'nt':  # Windows
            system_font = 'C:/Windows/Fonts/msyh.ttc'
            if os.path.exists(system_font):
                LabelBase.register(name='Chinese', fn_regular=system_font)
    except:
        pass  # 使用默认字体

# 设置横屏
Window.orientation = 'landscape'

class CowScore:
    def __init__(self, total_count, station_number, score, cow_number=""):
        self.total_count = total_count
        self.station_number = station_number
        self.score = score
        self.cow_number = cow_number  # 牛号字段
    
    def to_list(self):
        return [self.total_count, self.station_number, self.score, self.cow_number]

class CowScoreScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_position = 1
        self.max_station = 100
        self.cow_scores = []  # 所有记录
        self.position_scores = {}  # 记录每个位置的最新评分 {position: {'score': score, 'cow_number': cow_number}}
        self.station_cow_numbers = {}  # 每个站位绑定的牛号 {position: cow_number}
        self.setup_ui()
    
    def setup_ui(self):
        # 主布局
        main_layout = BoxLayout(orientation='horizontal', padding=10, spacing=10)
        
        # 左侧功能区
        left_panel = BoxLayout(orientation='vertical', size_hint_x=0.3, spacing=15)
        
        # 牛号输入
        cow_number_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        cow_number_label = Label(text='牛号:', font_size='16sp', font_name='Chinese', size_hint_x=0.3)
        self.cow_number_input = TextInput(multiline=False, font_size='16sp', font_name='Chinese', size_hint_x=0.7)
        cow_number_layout.add_widget(cow_number_label)
        cow_number_layout.add_widget(self.cow_number_input)
        left_panel.add_widget(cow_number_layout)
        
        # 当前位置显示
        current_pos_label = Label(text='当前位置', font_size='18sp', size_hint_y=None, height=40, font_name='Chinese')
        self.current_pos_display = Label(text='1', font_size='48sp', color=(1, 0.3, 0.2, 1), bold=True, font_name='Chinese')
        left_panel.add_widget(current_pos_label)
        left_panel.add_widget(self.current_pos_display)
        
        # 站位号显示和输入
        station_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        station_label = Label(text='站位:', font_size='16sp', font_name='Chinese')
        self.station_input = TextInput(text='1', multiline=False, font_size='16sp', font_name='Chinese', size_hint_x=0.6)
        self.station_input.bind(on_text_validate=self.on_station_input_enter)
        go_btn = Button(text='Go', font_size='14sp', font_name='Chinese', size_hint_x=0.4)
        go_btn.bind(on_press=self.go_to_station)
        station_layout.add_widget(station_label)
        station_layout.add_widget(self.station_input)
        station_layout.add_widget(go_btn)
        left_panel.add_widget(station_layout)
        
        # 站位号大显示
        station_display_label = Label(text='站位号', font_size='18sp', size_hint_y=None, height=40, font_name='Chinese')
        self.station_display = Label(text='1', font_size='72sp', color=(0.1, 0.6, 1, 1), bold=True, font_name='Chinese')
        left_panel.add_widget(station_display_label)
        left_panel.add_widget(self.station_display)
        
        # 控制按钮
        nav_buttons = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, spacing=10)
        prev_btn = Button(text='上一位', font_size='18sp', font_name='Chinese')
        next_btn = Button(text='下一位', font_size='18sp', font_name='Chinese')
        prev_btn.bind(on_press=self.move_previous)
        next_btn.bind(on_press=self.move_next)
        nav_buttons.add_widget(prev_btn)
        nav_buttons.add_widget(next_btn)
        left_panel.add_widget(nav_buttons)
        
        # 快速站位按钮
        quick_station_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=5)
        quick_stations = [1, 25, 50, 75, 100]
        for station in quick_stations:
            btn = Button(text=str(station), font_size='14sp', font_name='Chinese')
            btn.bind(on_press=lambda instance, s=station: self.go_to_station_number(s))
            quick_station_layout.add_widget(btn)
        left_panel.add_widget(Label(text='快速跳转:', font_size='14sp', font_name='Chinese', size_hint_y=None, height=25))
        left_panel.add_widget(quick_station_layout)
        
        # 导出按钮
        export_btn = Button(text='导出Excel', font_size='18sp', size_hint_y=None, height=60, background_color=(0.3, 0.7, 0.3, 1), font_name='Chinese')
        export_btn.bind(on_press=self.export_to_excel)
        left_panel.add_widget(export_btn)
        
        # 统计信息
        self.total_count_label = Label(text='总记录: 0个站位', font_size='16sp', font_name='Chinese')
        left_panel.add_widget(self.total_count_label)
        
        # 记录状态显示
        self.record_status_label = Label(text='', font_size='14sp', color=(0, 0.8, 0, 1), font_name='Chinese')
        left_panel.add_widget(self.record_status_label)
        
        # 中间显示区
        center_panel = BoxLayout(orientation='vertical', size_hint_x=0.3, spacing=20)
        
        # 当前评分显示
        current_score_label = Label(text='当前评分', font_size='18sp', size_hint_y=None, height=40, font_name='Chinese')
        self.current_score_display = Label(text='--', font_size='36sp', color=(0.6, 0.1, 0.7, 1), bold=True, font_name='Chinese')
        center_panel.add_widget(current_score_label)
        center_panel.add_widget(self.current_score_display)
        
        # 当前牛号显示
        current_cow_label = Label(text='当前牛号', font_size='16sp', size_hint_y=None, height=30, font_name='Chinese')
        self.current_cow_display = Label(text='--', font_size='18sp', color=(0.1, 0.6, 1, 1), font_name='Chinese')
        center_panel.add_widget(current_cow_label)
        center_panel.add_widget(self.current_cow_display)
        
        # 右侧评分按钮区
        right_panel = BoxLayout(orientation='vertical', size_hint_x=0.4)
        score_label = Label(text='体况评分', font_size='18sp', size_hint_y=None, height=40, font_name='Chinese')
        right_panel.add_widget(score_label)
        
        # 评分按钮滚动区域
        scroll = ScrollView()
        score_grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        score_grid.bind(minimum_height=score_grid.setter('height'))
        
        # 评分按钮颜色配置
        score_colors = [
            (0.9, 0.3, 0.2, 1),    # 2.5 - 红色
            (1.0, 0.6, 0.0, 1),    # 2.75 - 橙色
            (1.0, 0.9, 0.2, 1),    # 3.0 - 黄色
            (0.8, 0.9, 0.2, 1),    # 3.25 - 黄绿
            (0.5, 0.8, 0.3, 1),    # 3.5 - 绿色
            (0.3, 0.7, 0.3, 1),    # 3.75 - 深绿
            (0.0, 0.6, 0.5, 1),    # 4.0 - 青色
            (0.2, 0.3, 0.7, 1),    # 4.25 - 蓝色
            (0.6, 0.1, 0.7, 1)     # 4.5 - 紫色
        ]
        
        scores = [2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 4.0, 4.25, 4.5]
        
        # 创建评分按钮
        for i, score in enumerate(scores):
            score_btn = Button(
                text=str(score),
                font_size='24sp',
                size_hint_y=None,
                height=60,
                background_color=score_colors[i],
                font_name='Chinese'
            )
            # 使用偏函数来避免Lambda问题
            def make_callback(s):
                return lambda instance: self.record_score(s)
            score_btn.bind(on_press=make_callback(score))
            score_grid.add_widget(score_btn)
        
        scroll.add_widget(score_grid)
        right_panel.add_widget(scroll)
        
        # 组装所有面板
        main_layout.add_widget(left_panel)
        main_layout.add_widget(center_panel)
        main_layout.add_widget(right_panel)
        
        self.add_widget(main_layout)
        self.update_current_score_display()  # 初始化当前评分显示
        self.update_cow_number_input()  # 初始化牛号输入框
    
    def on_station_input_enter(self, instance):
        """站位输入框回车事件"""
        self.go_to_station(None)
    
    def go_to_station(self, instance):
        """跳转到指定站位"""
        try:
            station_num = int(self.station_input.text)
            if 1 <= station_num <= self.max_station:
                self.current_position = station_num
                self.update_display()
                self.update_current_score_display()
                self.update_cow_number_input()  # 更新牛号输入框
            else:
                self.record_status_label.text = f'站位号应在1-{self.max_station}之间'
        except ValueError:
            self.record_status_label.text = '请输入有效的站位号'
    
    def go_to_station_number(self, station_number):
        """快速跳转到指定站位"""
        self.current_position = station_number
        self.station_input.text = str(station_number)
        self.update_display()
        self.update_current_score_display()
        self.update_cow_number_input()  # 更新牛号输入框
    
    def move_previous(self, instance):
        self.current_position -= 1
        if self.current_position < 1:
            self.current_position = self.max_station
        self.update_display()
        self.update_current_score_display()
        self.update_cow_number_input()  # 清空并更新牛号输入框
    
    def move_next(self, instance):
        self.current_position += 1
        if self.current_position > self.max_station:
            self.current_position = 1
        self.update_display()
        self.update_current_score_display()
        self.update_cow_number_input()  # 清空并更新牛号输入框
    
    def update_display(self):
        self.current_pos_display.text = str(self.current_position)
        self.station_display.text = str(self.current_position)
        self.station_input.text = str(self.current_position)
    
    def update_cow_number_input(self):
        """更新牛号输入框 - 显示当前站位绑定的牛号"""
        if self.current_position in self.station_cow_numbers:
            cow_number = self.station_cow_numbers[self.current_position]
            self.cow_number_input.text = cow_number
        else:
            self.cow_number_input.text = ''  # 清空输入框
    
    def update_current_score_display(self):
        """更新当前评分和牛号显示"""
        if self.current_position in self.position_scores:
            data = self.position_scores[self.current_position]
            score = data['score']
            cow_number = data['cow_number']
            self.current_score_display.text = str(score)
            self.current_score_display.color = (0, 0.8, 0, 1)  # 绿色表示已记录
            self.current_cow_display.text = cow_number if cow_number else '--'
            self.current_cow_display.color = (0.1, 0.6, 1, 1)
        else:
            self.current_score_display.text = '--'
            self.current_score_display.color = (0.6, 0.1, 0.7, 1)  # 紫色表示未记录
            self.current_cow_display.text = '--'
            self.current_cow_display.color = (0.6, 0.6, 0.6, 1)
    
    def record_score(self, score):
        # 获取当前输入的牛号
        cow_number = self.cow_number_input.text.strip()
        
        # 将牛号绑定到当前站位
        self.station_cow_numbers[self.current_position] = cow_number
        
        # 检查当前位置是否已有记录
        old_data = self.position_scores.get(self.current_position, None)
        
        # 更新当前位置的评分和牛号（覆盖旧记录）
        self.position_scores[self.current_position] = {
            'score': score,
            'cow_number': cow_number
        }
        
        # 更新显示
        self.update_current_score_display()
        self.total_count_label.text = f'总记录: {len(self.position_scores)}个站位'
        
        # 显示记录状态
        if old_data is not None:
            old_score = old_data['score']
            cow_info = f"(牛号:{cow_number})" if cow_number else ""
            self.record_status_label.text = f'站位{self.current_position}: {old_score} → {score} {cow_info}'
        else:
            cow_info = f"(牛号:{cow_number})" if cow_number else ""
            self.record_status_label.text = f'站位{self.current_position}记录: {score} {cow_info}'
        
        # 自动跳转到下一位
        self.move_next(None)
    
    def export_to_excel(self, instance):
        if not self.position_scores:
            self.record_status_label.text = '没有数据可导出'
            return
        
        try:
            from datetime import datetime
            from openpyxl import Workbook
            
            # 准备导出数据（按站位号排序）
            export_data = []
            for position in sorted(self.position_scores.keys()):
                data = self.position_scores[position]
                score = data['score']
                cow_number = data['cow_number']
                # 为每个记录创建CowScore对象
                cow_score = CowScore(len(export_data) + 1, position, score, cow_number)
                export_data.append(cow_score)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"奶牛体况评分_{timestamp}.xlsx"
            
            # 跨平台文件保存路径
            if 'ANDROID_ARGUMENT' in os.environ:
                # 安卓平台
                try:
                    from jnius import autoclass
                    Environment = autoclass('android.os.Environment')
                    documents_dir = Environment.getExternalStoragePublicDirectory(
                        Environment.DIRECTORY_DOCUMENTS
                    ).getAbsolutePath()
                    filepath = os.path.join(documents_dir, filename)
                except:
                    # 如果jnius不可用，使用应用私有目录
                    filepath = os.path.join(os.getcwd(), filename)
                    documents_dir = os.getcwd()
            else:
                # 桌面平台
                documents_dir = os.path.expanduser('~/Documents')
                if not os.path.exists(documents_dir):
                    documents_dir = os.getcwd()
                filepath = os.path.join(documents_dir, filename)
            
            # 创建工作簿
            wb = Workbook()
            ws = wb.active
            ws.title = "奶牛体况评分"
            
            # 写入表头
            headers = ['总计牛数', '站位号', '体况评分', '牛号']
            ws.append(headers)
            
            # 写入数据
            for score_obj in export_data:
                ws.append(score_obj.to_list())
            
            # 确保目录存在
            os.makedirs(documents_dir, exist_ok=True)
            
            # 保存文件
            wb.save(filepath)
            
            # 显示导出成功状态
            if 'ANDROID_ARGUMENT' in os.environ:
                self.record_status_label.text = f'导出成功至Documents文件夹'
            else:
                self.record_status_label.text = f'导出成功: {filename}'
            
        except Exception as e:
            # 显示导出失败状态
            self.record_status_label.text = f'导出失败: {str(e)}'

class CowScoreApp(App):
    def build(self):
        return CowScoreScreen()

if __name__ == '__main__':
    CowScoreApp().run()