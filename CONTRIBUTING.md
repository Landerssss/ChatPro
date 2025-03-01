# 贡献指南 | Contributing Guidelines

🌍 **多语言支持**：本文档提供[中文](#贡献指南)与[English](#contributing-guidelines)版本

---

## 贡献指南 🇨🇳

### 开发环境要求
- Python 3.9+（推荐3.10）
- Poetry 1.5+（包管理工具）
- Pre-commit 3.3+（代码规范检查）

### 开发流程
1. 克隆仓库并安装依赖
   git clone https://github.com/yourusername/chat-assistant.git
   cd chat-assistant
   poetry install
配置pre-commit（代码提交前自动格式化）

pre-commit install
创建新功能分支

git checkout -b feat/your-feature-name
提交代码前运行测试

pytest tests/ --cov=src
注意事项
所有代码变更必须通过单元测试（覆盖率不低于85%）

遵循PEP8代码规范

使用类型标注（Type Hints）

API密钥等敏感信息必须通过环境变量传递

Contributing Guidelines 🇬🇧
Development Requirements
Python 3.9+ (recommend 3.10)

Poetry 1.5+ (package manager)

Pre-commit 3.3+ (code quality check)

Workflow
Clone repo & install dependencies

git clone https://github.com/yourusername/chat-assistant.git
cd chat-assistant
poetry install
Setup pre-commit

pre-commit install
Create feature branch

git checkout -b feat/your-feature-name
Run tests before commit

pytest tests/ --cov=src