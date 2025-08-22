# 🚀 Crypto Sentiment Analyzer

A web-based tool for analyzing cryptocurrency sentiment from Twitter data using AI-powered analysis.

## Features

- 📊 **Sentiment Distribution**: Analyze positive, negative, and neutral sentiment
- 💰 **Price Context**: Real-time price data integration
- 🤖 **AI Analysis**: Intelligent summarization of community sentiment
- 🔥 **Viral Tweets**: Identify high-engagement content
- 👑 **Influencer Tracking**: Monitor high-influence user activities
- 📈 **Topic Analysis**: Categorize discussion themes

## Live Demo

🌐 **[Try the live app here](your-streamlit-url-here)**

## Local Setup

### Prerequisites

- Python 3.8+
- API Keys:
  - OpenAI API Key
  - RapidAPI Key (for Twitter data)
  - Twitter API Key

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd crypto-sentiment-analyzer
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up configuration:
```bash
cp config_template.py config.py
```
Edit `config.py` and add your API keys.

5. Run the Streamlit app:
```bash
streamlit run streamlit_app.py
```

## Deployment on Streamlit Cloud

### Quick Deploy Steps:

1. **Push to GitHub** (without API keys)
2. **Go to [share.streamlit.io](https://share.streamlit.io)**
3. **Connect your GitHub repo**
4. **Add secrets in Streamlit dashboard**
5. **Deploy!**

### Environment Variables Needed:

- `OPENAI_API_KEY`: Your OpenAI API key
- `RAPIDAPI_KEY`: Your RapidAPI key for Twitter data
- `TWITTER_API_KEY`: Your Twitter API access key

## Usage

1. Enter a cryptocurrency symbol (e.g., BTC, ETH, DOGE)
2. Click "开始分析" to start analysis
3. View comprehensive sentiment analysis results

## Project Structure

```
crypto-sentiment-analyzer/
├── streamlit_app.py          # Main Streamlit application
├── config_template.py        # Configuration template
├── requirements.txt          # Python dependencies
├── analysis/                 # Analysis modules
│   ├── sentiment.py
│   ├── filters.py
│   └── influence.py
├── api/                      # API integrations
│   ├── twitter_api.py
│   └── coinex_api.py
├── utils/                    # Utility functions
│   ├── formatters.py
│   └── tweet_parser.py
└── data/                     # Data files
    └── project_twitter.xlsx
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.

## Disclaimer

This tool is for educational and research purposes only. Not financial advice.