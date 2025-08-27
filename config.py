# config.py
"""
Configuration settings with secure API key handling
"""

import os

# Try to import streamlit for secrets, but don't fail if not available
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

def get_secret(key, default=""):
    """Safely get secrets from environment or Streamlit secrets"""
    # First try environment variables
    env_value = os.getenv(key)
    if env_value:
        return env_value
    
    # Then try Streamlit secrets if available
    if STREAMLIT_AVAILABLE:
        try:
            return st.secrets.get(key, default)
        except:
            return default
    
    return default

# API Configuration - SAFE PLACEHOLDER KEYS FOR GITHUB
TWITTER_API_CONFIG = {
    'url': "https://twitter-api-v1-1-enterprise.p.rapidapi.com/base/apitools/search",
    'headers': {
        "x-rapidapi-key": get_secret("RAPIDAPI_KEY", "your_rapidapi_key_here"),
        "x-rapidapi-host": "twitter-api-v1-1-enterprise.p.rapidapi.com",
    },
    'api_key': get_secret("TWITTER_API_KEY", "your_twitter_api_key_here")
}

OPENAI_API_KEY = get_secret("OPENAI_API_KEY", "your_openai_api_key_here")

COINEX_API_URL = "https://www.coinex.com/res/vote2/project"

# Analysis Configuration
ANALYSIS_CONFIG = {
    'target_days': 7,
    'max_pages_per_call': 3,
    'max_tweets_for_summary': 15,
    'max_tweets_for_topic_analysis': 20,
    'openai_model': "gpt-4o-mini"
}

# Simplified Smart Search Configuration
SMART_SEARCH_CONFIG = {
    'enable_smart_search': True,
    'cache_patterns': True,
    'test_timeout': 10,
    'show_rules': True,
}

# Team Filtering Configuration
TEAM_FILTER_CONFIG = {
    'excel_file_path': 'data/project_twitter.xlsx',
    'enable_team_filtering': True,
    'case_sensitive': False,
    'show_filtered_teams': True,
    'show_team_accounts_debug': False
}

# User influence tier weights
INFLUENCE_TIERS = {
    'tier_1': {'min_followers': 100000, 'weight': 1.5},
    'tier_2': {'min_followers': 10000, 'weight': 1.0},
    'tier_3': {'min_followers': 1000, 'weight': 0.7},
    'tier_4': {'min_followers': 0, 'weight': 0.5}
}

# Verification bonus multipliers
VERIFICATION_BONUS = {
    'legacy_verified': 1.2,
    'blue_verified': 1.1
}

# News/Informative accounts to exclude (case-insensitive)
NEWS_ACCOUNTS = {
    'coindesk', 'cointelegraph', 'theblock__', 'watcherguru', 'blockworks_',
    'decryptmedia', 'foresight_news', 'blockbeatsasia', 'odailychina', 'panewscn',
    'jinsefinance', 'whale_alert', 'lookonchain', 'coinmarketcap', 'coingecko',
    'glassnode', 'defillama', 'peckshieldalert', 'wublockchain', 'thedefiant',
    'decrypt', 'bitcoinmagazine', 'cryptopotato', 'ambcrypto', 'cryptoslate',
    'newsbtc', 'beincrypto', 'cryptonews', 'bitcoinist', 'santimentfeed',
    'nansen_ai', 'delphi_digital', 'messaricrypto', 'chainalysis', 'elliptic',
    'cryptoquant_com', 'intotheblock', 'coinmetrics', 'cryptocompare'
}

# Spam detection patterns
SPAM_PATTERNS = {
    'giveaway_keywords': [
        'giveaway', 'airdrop', 'drop your wallet', 'drop wallet', 'tag friends',
        'retweet to win', 'rt to win', 'follow and rt', 'like and rt',
        'comment your wallet', 'drop address', 'whitelist', 'presale',
        'claim your', 'free tokens', 'free crypto', 'prize pool'
    ],
    'meaningless_patterns': [
        r'^[a-zA-Z]{1,3}$',
        r'^\$\w+\s*$',
        r'^(lol|lmao|wow|nice|cool|good|bad|yes|no|ok|wtf)\.?!?$'
    ],
    'token_spam_pattern': r'(\$\w+\s*){5,}',
    'excessive_emojis': r'([\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]){10,}',
    'repeated_chars': r'(.)\1{5,}',
}

# Topic keywords for fallback analysis
TOPIC_KEYWORDS = {
    '价格预测': ['预测', '目标价', 'target', 'prediction', '看涨', '看跌', '分析', '走势'],
    '持仓分享': ['持仓', '买入', '卖出', 'buy', 'sell', 'hold', '加仓', '建仓', '仓位'],
    '技术分析': ['技术分析', 'TA', '图表', 'chart', '支撑', '阻力', '突破', '形态'],
    '上币': ['上币', '新币', 'listing', 'list', '上线', '首发'],
    '空投': ['空投', 'airdrop', '免费', '赠送', '福利'],
    '交易策略': ['策略', '交易', '操作', 'strategy', '买卖', '入场', '出场'],
    '项目评价': ['评价', '分析', '观察', '看法', '评估', '点评'],
    '代币解锁': ['解锁', 'unlock', 'vest', '释放', '流通'],
    'rug pull': ['rug pull', 'rug', '跑路', '圈钱', '诈骗'],
    '产品开发': ['开发', '产品', 'development', 'product', '功能', '更新'],
    '合作伙伴': ['合作', '伙伴', 'partnership', 'collaborate', '联盟'],
    '社区活动': ['活动', '社区', '互动', '参与', '讨论']
}

# Specific keyword mapping for topic detection
SPECIFIC_TOPIC_KEYWORDS = {
    '上币': ['上币', '新币', 'listing', 'list'],
    '上所': ['上所', '交易所', 'exchange'],
    '空投': ['空投', 'airdrop', '免费'],
    '产品开发': ['开发', '产品', 'development', 'product'],
    '合作伙伴': ['合作', '伙伴', 'partnership', 'collaborate'],
    'rug pull': ['rug pull', 'rug', '跑路', '圈钱'],
    '交易所下架': ['下架', 'delist', '停止交易'],
    '充提暂停': ['充提', '暂停', 'suspend', 'withdrawal'],
    '代币增发': ['增发', 'mint', '新增'],
    '代币解锁': ['解锁', 'unlock', 'vest'],
    '黑客攻击': ['黑客', 'hack', '攻击', 'exploit'],
    '价格预测': ['预测', '目标价', 'target', 'prediction'],
    '技术分析': ['技术分析', 'TA', '图表', 'chart'],
    '持仓分享': ['持仓', '买入', '卖出', 'buy', 'sell', 'hold']
}

# Generic to specific topic mapping
TOPIC_MAPPING = {
    '价格分析': '价格预测',
    '社区讨论': '持仓分享', 
    '投资建议': '交易策略',
    '正面事件': '产品开发',
    '安全风险': '安全漏洞',
    '市场风险': 'rug pull',
    '技术变更': '代币解锁',
    '监管合规': '合规问题'
}

# Generic categories to avoid
GENERIC_CATEGORIES = [
    '正面事件', '市场风险', '价格讨论', '社区动态', '技术变更', 
    '安全风险', '监管合规', '价格分析', '社区讨论', '投资建议'
]
