# Financial Analysis Chatbot | 金融分析聊天机器人

A ChatGPT-powered financial analysis chatbot supporting stock and cryptocurrency analysis.

一个基于 ChatGPT 的金融分析聊天机器人，支持股票和加密货币分析。

## Features | 功能特点

- 🤖 AI-driven financial analysis | AI 驱动的金融分析
- 📈 Real-time stock data analysis | 实时股票数据分析
- 🪙 Cryptocurrency market analysis | 加密货币市场分析
- 📰 Related news aggregation | 相关新闻聚合
- 🌐 Bilingual support (English/Chinese) | 中英文双语支持
- 📊 Technical indicator analysis | 技术指标分析

## Tech Stack | 技术栈

- Python 3.11
- Streamlit
- LangChain
- OpenAI API
- YFinance
- Plotly
- Docker

## Quick Start | 快速开始

### Local Development | 本地开发

1. Clone the repository | 克隆仓库

```bash
git clone https://github.com/你的用户名/financial-chatbot.git
cd financial-chatbot
```

2. Install dependencies | 安装依赖

```bash
pip install -r requirements.txt
```

3. Set environment variables | 设置环境变量

```bash
export OPENAI_API_KEY='your-api-key'
export ALPHAVANTAGE_API_KEY='your-api-key'
export GOLD_API_KEY='your-api-key'
```

4. Run the application | 运行应用

```bash
streamlit run Home.py
```

2. Run container | 运行容器

```bash
docker run -p 8501:8501 \
  -e OPENAI_API_KEY='your-api-key' \
  -e ALPHAVANTAGE_API_KEY='your-api-key' \
  -e GOLD_API_KEY='your-api-key' \
  financial-chatbot
```

## Usage Guide | 使用说明

### Stock Analysis | 股票分析
- Enter stock symbol | 输入股票代码
- Select analysis period | 选择分析周期
- View price trends | 查看价格走势
- Get AI analysis report | 获取 AI 分析报告
- Browse related news | 浏览相关新闻

### Cryptocurrency Analysis | 加密货币分析
- Select cryptocurrency | 选择加密货币
- Select analysis period | 选择分析周期
- View price trends | 查看价格走势
- Get AI analysis report | 获取 AI 分析报告
- Browse related news | 浏览相关新闻

## Project Structure | 项目结构

```
financial-chatbot/
├── Home.py                 # Main page | 主页
├── pages/                  # Pages directory | 页面目录
│   ├── stock_analysis.py   # Stock analysis page | 股票分析页面
│   └── crypto_analysis.py  # Cryptocurrency analysis page | 加密货币分析页面
├── components/            # Components directory | 组件目录
├── utils/                # Utility functions | 工具函数
├── requirements.txt      # Project dependencies | 项目依赖
└── Dockerfile           # Docker configuration | Docker 配置文件
```

## Requirements | 环境要求

- Python 3.11 or higher | Python 3.11 或更高版本
- Docker (optional | 可选)
- OpenAI API key | OpenAI API 密钥
- Alpha Vantage API key | Alpha Vantage API 密钥
- Gold API key | Gold API 密钥

## Getting API Keys | API 密钥获取

1. OpenAI API Key | OpenAI API 密钥
   - Visit | 访问 [OpenAI Platform](https://platform.openai.com/)
   - Register/Login | 注册/登录账号
   - Generate new key | 生成新密钥

2. Alpha Vantage API Key | Alpha Vantage API 密钥
   - Visit | 访问 [Alpha Vantage](https://www.alphavantage.co/)
   - Register free account | 注册免费账号
   - Get API key | 获取 API 密钥

3. Gold API Key | Gold API 密钥
   - Visit | 访问 [Gold API](https://www.goldapi.io/)
   - Register account | 注册账号
   - Get API key | 获取 API 密钥

## FAQ | 常见问题

1. How to switch language? | 如何切换语言？
   - Select language option in sidebar | 在侧边栏中选择语言选项

2. Which stock markets are supported? | 支持哪些股票市场？
   - Major global stock markets | 支持全球主要股票市场
   - Use standard stock symbols (e.g., AAPL, GOOGL) | 使用标准股票代码（如：AAPL, GOOGL）

3. Which cryptocurrencies are supported? | 支持哪些加密货币？
   - Major cryptocurrencies | 支持主流加密货币
   - Data from CoinGecko API | 数据来源于 CoinGecko API

## Contributing | 贡献指南

1. Fork the project | Fork 项目
2. Create feature branch | 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. Commit changes | 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch | 推送到分支 (`git push origin feature/AmazingFeature`)
5. Open Pull Request | 打开 Pull Request

## License | 许可证

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## Contact | 联系方式

Project Maintainer | 项目维护者 - [@liukai1919](https://github.com/liukai1919)

Project Link | 项目链接: [https://github.com/liukai1919/financial-chatbot](https://github.com/liukai1919/financial-chatbot)
