import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
from openai import OpenAI
import threading
import json
import os
import base64
import requests
from datetime import datetime
from pptx import Presentation
from pptx.util import Inches, Pt
from docx import Document
import re

# ==========================================
# 配置与常量
# ==========================================
DEFAULT_CONFIG = {
    "api_key": "",
    "base_url": "https://api.siliconflow.cn/v1",  # 默认使用 SiliconFlow (DeepSeek)
    "model": "deepseek-ai/DeepSeek-V3",
    "history_dir": "chat_history"
}

THEME = {
    'bg': '#FFFFFF',
    'primary': '#1E88E5',
    'secondary': '#F5F5F5',
    'text': '#333333',
    'user_bg': '#E3F2FD', # 蓝色系气泡
    'ai_bg': '#F5F5F5',   # 灰色系气泡
    'success': '#4CAF50',
    'warning': '#FF9800'
}

# ==========================================
# 工具类：处理文件生成逻辑
# ==========================================
class ToolManager:
    @staticmethod
    def generate_ppt(content, filename="output.pptx"):
        """
        将Markdown格式的幻灯片内容转换为PPTX
        格式要求：
        # 标题
        - 要点1
        - 要点2
        """
        try:
            prs = Presentation()
            slides_content = content.split('---') # 假设AI用 --- 分割幻灯片
            
            for slide_text in slides_content:
                if not slide_text.strip(): continue
                
                lines = slide_text.strip().split('\n')
                title_text = lines[0].replace('#', '').strip()
                points = [line.strip().replace('-', '').replace('*', '').strip() for line in lines[1:] if line.strip()]
                
                # 添加幻灯片
                slide_layout = prs.slide_layouts[1] # 标题+内容布局
                slide = prs.slides.add_slide(slide_layout)
                
                # 设置标题
                title = slide.shapes.title
                title.text = title_text
                
                # 设置内容
                body_shape = slide.placeholders[1]
                tf = body_shape.text_frame
                
                for point in points:
                    p = tf.add_paragraph()
                    p.text = point
                    p.level = 0
            
            save_path = os.path.join(os.getcwd(), filename)
            prs.save(save_path)
            return save_path
        except Exception as e:
            raise Exception(f"PPT生成失败: {str(e)}")

    @staticmethod
    def generate_word(content, filename="output.docx"):
        try:
            doc = Document()
            doc.add_heading('ChatPro 生成文档', 0)
            doc.add_paragraph(content)
            save_path = os.path.join(os.getcwd(), filename)
            doc.save(save_path)
            return save_path
        except Exception as e:
            raise Exception(f"Word生成失败: {str(e)}")

    @staticmethod
    def generate_flowchart(mermaid_code, filename="flowchart.png"):
        """使用 Mermaid.ink 免费API将代码转换为PNG"""
        try:
            # 清理代码块标记
            mermaid_code = mermaid_code.replace("```mermaid", "").replace("```", "").strip()
            
            # Base64编码
            graphbytes = mermaid_code.encode("utf8")
            base64_bytes = base64.b64encode(graphbytes)
            base64_string = base64_bytes.decode("ascii")
            
            url = "https://mermaid.ink/img/" + base64_string
            
            response = requests.get(url)
            if response.status_code == 200:
                save_path = os.path.join(os.getcwd(), filename)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return save_path
            else:
                raise Exception("无法连接到Mermaid服务器")
        except Exception as e:
            raise Exception(f"流程图生成失败: {str(e)}")

# ==========================================
# 核心UI类
# ==========================================
class ChatProV3:
    def __init__(self, root):
        self.root = root
        self.root.title("ChatPro V3 - 全能AI工作台")
        self.root.geometry("1000x700")
        self.root.configure(bg=THEME['bg'])
        
        # 初始化状态
        self.config = DEFAULT_CONFIG
        self.messages = []
        self.is_generating = False
        
        # 尝试加载本地配置
        self.load_config()
        
        # 初始化UI
        self.setup_styles()
        self.create_layout()
        self.check_api_key()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TFrame', background=THEME['bg'])
        style.configure('TButton', font=('Microsoft YaHei', 9), padding=5)
        style.configure('Action.TButton', background=THEME['primary'], foreground='white')
        
        style.map('Action.TButton', 
                  background=[('active', '#1565C0')],
                  foreground=[('active', 'white')])

    def create_layout(self):
        # 1. 顶部工具栏 (设置 & 模型选择)
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(header_frame, text="ChatPro V3", font=("Arial", 14, "bold"), background=THEME['bg']).pack(side=tk.LEFT)
        
        ttk.Button(header_frame, text="⚙️ 设置API", command=self.show_settings).pack(side=tk.RIGHT)
        self.model_label = ttk.Label(header_frame, text=f"当前模型: {self.config['model']}", background=THEME['bg'], foreground='gray')
        self.model_label.pack(side=tk.RIGHT, padx=10)

        # 2. 主体区域 (左侧历史，右侧聊天)
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧：功能面板
        left_panel = ttk.Frame(main_paned, width=200)
        main_paned.add(left_panel, weight=1)
        
        # 快捷工具区
        tool_labelframe = ttk.LabelFrame(left_panel, text=" 🛠️ 生产力工具 ", padding=5)
        tool_labelframe.pack(fill=tk.X, pady=5)
        
        ttk.Button(tool_labelframe, text="📊 生成 PPT 大纲与文件", command=lambda: self.insert_instruction("ppt")).pack(fill=tk.X, pady=2)
        ttk.Button(tool_labelframe, text="🔀 生成流程图 (Mermaid)", command=lambda: self.insert_instruction("flow")).pack(fill=tk.X, pady=2)
        ttk.Button(tool_labelframe, text="📝 导出 Word 文档", command=lambda: self.insert_instruction("word")).pack(fill=tk.X, pady=2)
        
        # 历史记录区 (简化版)
        ttk.Label(left_panel, text="最近文件:", background=THEME['bg']).pack(anchor='w', pady=(10,0))
        self.file_list = tk.Listbox(left_panel, height=10, bd=0, bg=THEME['secondary'])
        self.file_list.pack(fill=tk.BOTH, expand=True, pady=5)
        self.file_list.bind('<Double-Button-1>', self.open_file_from_list)

        # 右侧：聊天区域
        right_panel = ttk.Frame(main_paned)
        main_paned.add(right_panel, weight=4)
        
        # 聊天记录
        self.chat_display = scrolledtext.ScrolledText(right_panel, font=("Microsoft YaHei", 10), 
                                                    wrap=tk.WORD, bd=0, padx=10, pady=10,
                                                    bg=THEME['secondary'])
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.tag_config('user', background=THEME['user_bg'], lmargin1=20, lmargin2=20, rmargin=20)
        self.chat_display.tag_config('ai', background=THEME['ai_bg'], lmargin1=20, lmargin2=20, rmargin=20)
        self.chat_display.tag_config('system', foreground='gray', justify='center')
        self.chat_display.configure(state='disabled')
        
        # 输入区域
        input_frame = ttk.Frame(right_panel)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.input_text = tk.Text(input_frame, height=4, font=("Microsoft YaHei", 10), bd=1, relief="solid")
        self.input_text.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_text.bind("<Return>", self.on_enter_press)
        
        send_btn = ttk.Button(input_frame, text="发送 / 执行", style='Action.TButton', command=self.send_message)
        send_btn.pack(side=tk.RIGHT, fill=tk.Y)

    # ==========================================
    # 逻辑处理方法
    # ==========================================
    def check_api_key(self):
        if not self.config.get("api_key"):
            self.append_system_message("欢迎使用 ChatPro V3！请点击右上角【设置API】配置你的密钥。")
        else:
            self.append_system_message("系统就绪。ChatPro V3 已连接。")

    def insert_instruction(self, tool_type):
        prompts = {
            "ppt": "请为我生成一份关于[主题]的PPT大纲。要求：使用Markdown格式，幻灯片之间用 '---' 分隔。第一行为标题。",
            "flow": "请生成一个关于[主题]的流程图。要求：直接输出 Mermaid 代码块 (```mermaid ... ```)。",
            "word": "请帮我写一份关于[主题]的文章/报告，用于导出Word文档。"
        }
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert(tk.END, prompts.get(tool_type, ""))
        self.input_text.focus()

    def send_message(self):
        if self.is_generating: return
        
        content = self.input_text.get("1.0", tk.END).strip()
        if not content: return
        
        if not self.config.get("api_key"):
            messagebox.showwarning("缺少API Key", "请先在设置中配置API Key")
            self.show_settings()
            return

        self.input_text.delete("1.0", tk.END)
        self.append_message("You", content)
        
        # 启动线程处理API请求
        self.is_generating = True
        threading.Thread(target=self.process_ai_response, args=(content,)).start()

    def process_ai_response(self, user_input):
        client = OpenAI(api_key=self.config["api_key"], base_url=self.config["base_url"])
        
        full_response = ""
        try:
            # 判断意图 (简单关键词判断，V4可升级为函数调用)
            is_ppt = "PPT" in user_input.upper()
            is_flow = "mermaid" in user_input.lower() or "流程图" in user_input
            
            response = client.chat.completions.create(
                model=self.config["model"],
                messages=[
                    {"role": "system", "content": "你是一个全能助手。如果是PPT请求，请严格用Markdown和---分隔。如果是流程图，请提供Mermaid代码。"},
                    {"role": "user", "content": user_input}
                ],
                stream=True
            )
            
            self.start_ai_message()
            for chunk in response:
                if chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    full_response += text
                    self.update_ai_message(text)
            
            self.end_ai_message()
            
            # 后处理：自动生成文件
            if is_ppt:
                self.handle_ppt_generation(full_response)
            elif is_flow:
                self.handle_flowchart_generation(full_response)
                
        except Exception as e:
            self.append_system_message(f"API请求错误: {str(e)}")
        finally:
            self.is_generating = False

    # ==========================================
    # 文件生成处理
    # ==========================================
    def handle_ppt_generation(self, content):
        if messagebox.askyesno("自动生成", "检测到PPT内容，是否生成 .pptx 文件？"):
            try:
                filename = f"PPT_{datetime.now().strftime('%H%M%S')}.pptx"
                path = ToolManager.generate_ppt(content, filename)
                self.append_system_message(f"✅ PPT已生成: {path}")
                self.file_list.insert(0, filename)
            except Exception as e:
                self.append_system_message(f"❌ PPT生成失败: {str(e)}")

    def handle_flowchart_generation(self, content):
        # 提取 mermaid 代码
        match = re.search(r"```mermaid(.*?)```", content, re.DOTALL)
        if match and messagebox.askyesno("自动生成", "检测到流程图代码，是否渲染为图片？"):
            try:
                code = match.group(1)
                filename = f"Flow_{datetime.now().strftime('%H%M%S')}.png"
                path = ToolManager.generate_flowchart(code, filename)
                self.append_system_message(f"✅ 流程图已保存: {path}")
                self.file_list.insert(0, filename)
                # 这里可以扩展代码在聊天框直接显示图片
            except Exception as e:
                self.append_system_message(f"❌ 流程图渲染失败: {str(e)}")

    # ==========================================
    # UI 辅助方法
    # ==========================================
    def append_message(self, role, text):
        self.chat_display.configure(state='normal')
        tag = 'user' if role == 'You' else 'ai'
        self.chat_display.insert(tk.END, f"\n{role}:\n", tag)
        self.chat_display.insert(tk.END, f"{text}\n")
        self.chat_display.configure(state='disabled')
        self.chat_display.see(tk.END)

    def start_ai_message(self):
        self.chat_display.configure(state='normal')
        self.chat_display.insert(tk.END, "\nAI:\n", 'ai')
        self.chat_display.configure(state='disabled')

    def update_ai_message(self, text):
        self.chat_display.configure(state='normal')
        self.chat_display.insert(tk.END, text, 'ai')
        self.chat_display.see(tk.END)
        self.chat_display.configure(state='disabled')
        
    def end_ai_message(self):
        self.chat_display.configure(state='normal')
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.configure(state='disabled')

    def append_system_message(self, text):
        self.chat_display.configure(state='normal')
        self.chat_display.insert(tk.END, f"\n[System] {text}\n", 'system')
        self.chat_display.see(tk.END)
        self.chat_display.configure(state='disabled')

    def on_enter_press(self, event):
        if not event.state & 0x1: # 如果没有按Shift
            self.send_message()
            return 'break'

    def open_file_from_list(self, event):
        selection = self.file_list.curselection()
        if selection:
            filename = self.file_list.get(selection[0])
            os.startfile(filename) # Windows专用，Mac/Linux需改用 subprocess

    # ==========================================
    # 设置面板
    # ==========================================
    def show_settings(self):
        win = tk.Toplevel(self.root)
        win.title("API 设置")
        win.geometry("400x250")
        
        tk.Label(win, text="API Key:").pack(pady=5)
        key_entry = ttk.Entry(win, width=50)
        key_entry.insert(0, self.config.get("api_key", ""))
        key_entry.pack(pady=5)
        
        tk.Label(win, text="Base URL (默认 SiliconFlow):").pack(pady=5)
        url_entry = ttk.Entry(win, width=50)
        url_entry.insert(0, self.config.get("base_url", ""))
        url_entry.pack(pady=5)

        tk.Label(win, text="Model Name:").pack(pady=5)
        model_entry = ttk.Entry(win, width=50)
        model_entry.insert(0, self.config.get("model", "deepseek-ai/DeepSeek-V3"))
        model_entry.pack(pady=5)
        
        def save():
            self.config["api_key"] = key_entry.get().strip()
            self.config["base_url"] = url_entry.get().strip()
            self.config["model"] = model_entry.get().strip()
            self.save_config()
            self.model_label.config(text=f"当前模型: {self.config['model']}")
            self.check_api_key()
            win.destroy()
            
        ttk.Button(win, text="保存", command=save).pack(pady=20)

    def load_config(self):
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    self.config.update(json.load(f))
            except: pass

    def save_config(self):
        with open("config.json", "w") as f:
            json.dump(self.config, f)

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatProV3(root)
    root.mainloop()