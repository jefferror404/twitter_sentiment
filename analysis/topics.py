# analysis/topics.py (Enhanced)
"""
Enhanced topic analysis with sentiment integration and better categorization
"""

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from config import ANALYSIS_CONFIG
from collections import defaultdict


class TopicAnalyzer:
    def __init__(self, openai_api_key=None):
        self.openai_client = OpenAI(api_key=openai_api_key) if openai_api_key and OPENAI_AVAILABLE else None
        self.bulk_topics = []
        self.topic_cache = {}
        self.total_tokens_used = 0
        self.topic_sentiment_map = {}  # Store topic-sentiment mapping
    
    def generate_bulk_topic_analysis_with_sentiment(self, tweets_sample, token_symbol):
        """Generate bulk topic analysis with sentiment - enhanced categorization"""
        if self.bulk_topics:  # Skip if already done
            return self.bulk_topics
        
        if not self.openai_client:
            print("   💡 OpenAI不可用，使用关键词匹配获取具体话题...")
            self.bulk_topics = self._extract_fallback_topics_with_sentiment(tweets_sample)
            return self.bulk_topics
        
        try:
            # Limit to avoid token limits
            max_tweets = ANALYSIS_CONFIG['max_tweets_for_topic_analysis']
            sample_tweets = tweets_sample[:max_tweets] if len(tweets_sample) > max_tweets else tweets_sample
            tweets_text = "\n".join([f"{i+1}. {tweet['text'][:150]}..." if len(tweet['text']) > 150 else f"{i+1}. {tweet['text']}" 
                                   for i, tweet in enumerate(sample_tweets)])
            
            prompt = f"""
            请分析这{len(sample_tweets)}条关于{token_symbol}的推文，识别主要讨论话题并归类其情感倾向。请用简体中文回复。
            
            推文内容:
            {tweets_text}
            
            重要说明：
            1. 合并相似的价格/交易相关话题，避免过度细分
            2. 为每个话题添加明确的情感方向
            3. 优先识别具有明确情感的重要话题
            
            话题分类指引（带情感）：
            
            价格交易类（合并处理）:
            - 价格看涨 (价格预测/技术分析/突破信号等看涨内容)
            - 价格看跌 (价格预测/技术分析/突破信号等看跌内容)
            - 交易分享 (持仓分享/交易策略/买卖操作等，标注看涨/看跌)
            
            项目发展类:
            - 利好消息 (上币/合作/产品发布等积极消息)
            - 利空消息 (下架/监管/技术问题等消极消息)
            
            社区情绪类:
            - 社区乐观 (积极讨论/看好未来)
            - 社区担忧 (风险警告/负面情绪)
            
            技术风险类:
            - 安全风险 (黑客/漏洞等)
            - 合规风险 (监管/法律问题)
            
            请按以下格式输出（最多6个主要话题）：
            
            话题1: [话题名称+情感] - [推文编号,推文编号,...]
            话题2: [话题名称+情感] - [推文编号,推文编号,...]
            
            要求：
            1. 话题名称要具体且包含情感方向，如"价格看涨"、"交易分享-看涨"、"利好消息"
            2. 避免过度细分相似话题
            3. 每个话题至少包含2条推文
            4. 按讨论热度排序
            5. 话题名称不超过8个字
            
            示例格式:
            话题1: 价格看涨 - 1,3,5,7
            话题2: 交易分享-看涨 - 2,4,6
            话题3: 利好消息 - 8,9
            """
            
            response = self.openai_client.chat.completions.create(
                model=ANALYSIS_CONFIG['openai_model'],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.2
            )
            
            # Track token usage
            if hasattr(response, 'usage'):
                self.total_tokens_used += response.usage.total_tokens
            
            # Parse the response
            content = response.choices[0].message.content.strip()
            topics = []
            
            for line in content.split('\n'):
                line = line.strip()
                if line and '话题' in line and ':' in line and '-' in line:
                    try:
                        # Extract topic name and tweet numbers
                        parts = line.split(':', 1)[1].strip().split(' - ')
                        if len(parts) == 2:
                            topic_name = parts[0].strip()
                            tweet_numbers_str = parts[1].strip()
                            
                            # Clean up topic name
                            if topic_name.startswith('- '):
                                topic_name = topic_name[2:].strip()
                            if topic_name.startswith('-'):
                                topic_name = topic_name[1:].strip()
                            if topic_name.startswith('[') and topic_name.endswith(']'):
                                topic_name = topic_name[1:-1].strip()
                            
                            # Only include if reasonably specific and has sentiment
                            if len(topic_name) <= 12:  # Slightly longer to accommodate sentiment
                                # Count tweets for this topic
                                tweet_count = len([x.strip() for x in tweet_numbers_str.split(',') if x.strip()])
                                
                                if tweet_count >= 1:  # At least 1 tweet
                                    topics.append({
                                        'name': topic_name,
                                        'count': tweet_count,
                                        'tweet_numbers': tweet_numbers_str
                                    })
                    except:
                        continue
            
            # If we still don't have enough topics, add fallback
            if len(topics) < 3:
                print("   💡 AI返回话题不足，使用关键词匹配补充...")
                fallback_topics = self._extract_fallback_topics_with_sentiment(tweets_sample)
                existing_names = {t['name'] for t in topics}
                for fallback_topic in fallback_topics:
                    if fallback_topic['name'] not in existing_names and len(topics) < 6:
                        topics.append(fallback_topic)
            
            # Sort by count and return top topics
            self.bulk_topics = sorted(topics, key=lambda x: x['count'], reverse=True)[:6]
            return self.bulk_topics
            
        except Exception as e:
            print(f"OpenAI话题分析错误: {e}")
            self.bulk_topics = self._extract_fallback_topics_with_sentiment(tweets_sample)
            return self.bulk_topics
    
    def _extract_fallback_topics_with_sentiment(self, tweets_sample):
        """Extract topics with sentiment using keyword matching as fallback"""
        topic_keywords = {
            '价格看涨': ['moon', 'pump', 'bullish', '看涨', '上涨', '突破', '牛市', '目标价', 'target'],
            '价格看跌': ['dump', 'bearish', '看跌', '下跌', '崩盘', '熊市', '抛售', 'crash'],
            '交易分享-看涨': ['买入', 'buy', 'long', '加仓', '建仓', '持有', 'hold'],
            '交易分享-看跌': ['卖出', 'sell', 'short', '减仓', '止损', '出货'],
            '利好消息': ['上币', '上所', '合作', '更新', '发布', 'listing', 'partnership'],
            '利空消息': ['下架', '暂停', 'delist', '风险', '警告', 'risk'],
            '社区乐观': ['看好', '潜力', '机会', '推荐', 'gem', 'alpha'],
            '社区担忧': ['担心', '风险', '小心', '谨慎', 'risky', 'caution'],
            '技术分析': ['技术', '图表', '分析', 'TA', 'chart', '支撑', '阻力'],
            '空投福利': ['空投', 'airdrop', '免费', '福利', '赠送']
        }
        
        fallback_topics = []
        
        for topic, keywords in topic_keywords.items():
            count = 0
            tweet_numbers = []
            
            for i, tweet in enumerate(tweets_sample[:15]):
                tweet_text = tweet.get('text', '').lower()
                if any(keyword.lower() in tweet_text for keyword in keywords):
                    count += 1
                    tweet_numbers.append(str(i + 1))
            
            if count > 0:
                fallback_topics.append({
                    'name': topic,
                    'count': count,
                    'tweet_numbers': ','.join(tweet_numbers[:min(count, 10)])
                })
        
        return fallback_topics
    
    def get_tweet_topic_with_sentiment(self, tweet_text, combined_result=None):
        """Get specific topic with sentiment from combined analysis"""
        # First try to use combined analysis result
        if combined_result and combined_result.get('topic'):
            topic = combined_result['topic']
            if topic.startswith('- '):
                topic = topic[2:].strip()
            if topic.startswith('-'):
                topic = topic[1:].strip()
            
            # Check if it already has sentiment or try to add sentiment
            if topic and topic != "未分类" and len(topic) <= 12:
                # If topic doesn't have sentiment, try to determine it
                if not any(sentiment_word in topic for sentiment_word in ['看涨', '看跌', '乐观', '担忧', '利好', '利空']):
                    return self._add_sentiment_to_topic(topic, tweet_text, combined_result)
                return topic
        
        # Fallback to bulk topic matching
        if self.bulk_topics:
            tweet_lower = tweet_text.lower()
            
            # Try to match with existing bulk topics (which should have sentiment)
            for topic in self.bulk_topics:
                topic_name = topic['name'].lower()
                # Extract keywords from topic name for matching
                topic_keywords = topic_name.replace('-', ' ').split()
                if any(keyword in tweet_lower for keyword in topic_keywords if len(keyword) > 2):
                    return topic['name']
        
        return "未分类"
    
    def _add_sentiment_to_topic(self, base_topic, tweet_text, combined_result):
        """Add sentiment direction to a base topic"""
        # Determine sentiment from combined result or tweet text
        sentiment = 'NEUTRAL'
        if combined_result:
            sentiment = combined_result.get('sentiment', 'NEUTRAL')
        
        # Map base topics to sentiment-aware versions
        if base_topic in ['价格预测', '技术分析', '突破信号']:
            if sentiment == 'POSITIVE':
                return '价格看涨'
            elif sentiment == 'NEGATIVE':
                return '价格看跌'
            else:
                return '技术分析'
        elif base_topic in ['持仓分享', '交易策略']:
            if sentiment == 'POSITIVE':
                return '交易分享-看涨'
            elif sentiment == 'NEGATIVE':
                return '交易分享-看跌'
            else:
                return '交易分享'
        elif base_topic in ['上币', '合作伙伴', '产品开发']:
            return '利好消息'
        elif base_topic in ['rug pull', '下架', '风险提示']:
            return '利空消息'
        else:
            return base_topic
    
    def analyze_topic_sentiment_distribution(self, tweet_analyses):
        """Analyze sentiment distribution for each topic"""
        topic_sentiment_counts = defaultdict(lambda: {'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0, 'total': 0})
        
        for tweet in tweet_analyses:
            topic = tweet.get('topic', '未分类')
            sentiment = tweet['sentiment']['sentiment']
            
            topic_sentiment_counts[topic][sentiment] += 1
            topic_sentiment_counts[topic]['total'] += 1
        
        return dict(topic_sentiment_counts)