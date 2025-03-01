# 智能对话助手 (Intelligent Chat Assistant)

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

## 项目描述
基于Python开发的对话软件，已深度集成OpenAI API，支持本地加密存储对话历史。当前版本（V0-V2）已完成核心对话框架搭建，未来将逐步添加自定义API接入、智能文档生成等企业级功能。项目遵循MIT开源协议。

## 核心特性
- 🤖 实时AI对话（支持GPT-3.5/4）
- 📁 本地AES加密存储对话记录
- 🎨 Markdown格式消息渲染
- ⚙️ 模块化架构设计

## 版本路线图
| 版本 | 状态   | 核心功能                          |
|------|--------|-----------------------------------|
| V0   | ✅ 完成 | 基础对话框架搭建                 |
| V1   | ✅ 完成 | 对话历史存储系统                 |
| V2   | ✅ 完成 | 多主题UI界面                     |
| V3   | 🚧 开发 | 自定义API接入端口                |
| V4   | ⏳ 计划 | 智能流程图/PPT生成               |
| V5   | ⏳ 计划 | 企业级部署方案                   |

## 快速开始
```bash
# 克隆仓库
git clone https://github.com/yourusername/chat-assistant.git

# 安装依赖
pip install -r requirements.txt

# 启动程序
python main.py --api_key your_openai_key