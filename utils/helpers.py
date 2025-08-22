# utils/helpers.py
"""
General utility functions and helpers
"""

import time
from datetime import datetime, timedelta


def wait_between_calls(seconds=2):
    """Add delay between API calls"""
    print(f"   ⏳ 等待 {seconds} 秒后进行下次调用...")
    time.sleep(seconds)


def format_number(num):
    """Format numbers with commas for better readability"""
    if isinstance(num, (int, float)):
        return f"{num:,}"
    return str(num)


def calculate_percentage(part, total):
    """Calculate percentage with error handling"""
    if total == 0:
        return 0.0
    return (part / total) * 100


def truncate_text(text, max_length, suffix="..."):
    """Truncate text to specified length with suffix"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_price_change(change_rate):
    """Format price change with appropriate sign and percentage"""
    if change_rate > 0:
        return f"+{change_rate:.2%}"
    else:
        return f"{change_rate:.2%}"


def get_price_movement_description(abs_change):
    """Get descriptive text for price movement magnitude"""
    if abs_change > 0.1:
        return "剧烈波动"
    elif abs_change > 0.05:
        return "显著波动"
    elif abs_change > 0.02:
        return "轻微波动"
    else:
        return "基本稳定"


def estimate_openai_cost(total_tokens, model="gpt-4o-mini"):
    """Estimate OpenAI API cost based on token usage"""
    # Pricing as of 2024 (input + output combined estimate)
    if model == "gpt-4o-mini":
        cost_per_1m_tokens = 0.375  # USD per 1M tokens
    else:
        cost_per_1m_tokens = 0.375  # Default fallback
    
    return (total_tokens * cost_per_1m_tokens) / 1000000


def create_date_ranges(total_days):
    """Create date ranges for multi-timeframe API calls"""
    now = datetime.now()
    
    if total_days <= 3:
        # For 3 days or less, use single call
        return [(now - timedelta(days=total_days), None)]
    elif total_days <= 7:
        # For 4-7 days, split into 2 calls
        mid_point = total_days // 2
        return [
            (now - timedelta(days=mid_point), None),  # Recent half
            (now - timedelta(days=total_days), now - timedelta(days=mid_point))  # Older half
        ]
    else:
        # For more than 7 days, split into 3 calls
        third = total_days // 3
        return [
            (now - timedelta(days=third), None),  # Most recent third
            (now - timedelta(days=third*2), now - timedelta(days=third)),  # Middle third
            (now - timedelta(days=total_days), now - timedelta(days=third*2))  # Oldest third
        ]


def clean_topic_name(topic_name):
    """Clean and standardize topic names"""
    if topic_name.startswith('- '):
        topic_name = topic_name[2:].strip()
    if topic_name.startswith('-'):
        topic_name = topic_name[1:].strip()
    # Remove brackets if present
    if topic_name.startswith('[') and topic_name.endswith(']'):
        topic_name = topic_name[1:-1].strip()
    return topic_name


def deduplicate_tweets_by_id(tweets):
    """Remove duplicate tweets based on ID"""
    seen_ids = set()
    unique_tweets = []
    
    for tweet in tweets:
        try:
            # Extract tweet ID for duplicate detection
            tweet_id = (
                tweet.get('rest_id') or 
                tweet.get('legacy', {}).get('id_str') or
                tweet.get('id_str') or
                str(hash(str(tweet)))  # Fallback hash if no ID found
            )
            
            if tweet_id not in seen_ids:
                seen_ids.add(tweet_id)
                unique_tweets.append(tweet)
        except Exception:
            # If we can't extract ID, include the tweet anyway
            unique_tweets.append(tweet)
    
    return unique_tweets