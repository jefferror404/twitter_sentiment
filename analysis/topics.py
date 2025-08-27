# analysis/topics.py (Complete Fixed Version)
"""
Enhanced topic analysis with GPT-5 support and silent mode
"""

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from config import ANALYSIS_CONFIG, TOPIC_KEYWORDS, SPECIFIC_TOPIC_KEYWORDS


class TopicAnalyzer:
    def __init__(self, openai_api_key, model_name=None):
        self.openai_client = OpenAI(api_key=openai_api_key) if openai_api_key and OPENAI_AVAILABLE else None
        self.model = model_name or ANALYSIS_CONFIG.get('openai_model', 'gpt-4o-mini')
        self.bulk_topics = {}
        self.total_tokens_used = 0
    
    def get_api_params(self, max_tokens=800):
        """Get correct API parameters for GPT-5 compatibility"""
        base_params = {'temperature': 0.3}
        
        if self.model.startswith('gpt-5'):
            base_params['max_completion_tokens'] = max_tokens
        else:
            base_params['max_tokens'] = max_tokens
        
        return base_params
    
    def generate_bulk_topic_analysis_with_sentiment(self, tweets, token_symbol):
        """Generate topic analysis with GPT-5 support"""
        if not self.openai_client:
            return
        
        try:
            tweets_text = "\n".join([f"{i+1}. {tweet['text'][:100]}..." 
                                   for i, tweet in enumerate(tweets[:20])])
            
            prompt = f"""分析这些关于{token_symbol}的推文话题分布。请用简体中文回复。

推文内容:
{tweets_text}

请按以下格式回复:
1. [话题名称] - [推文数量]
2. [话题名称] - [推文数量]
3. [话题名称] - [推文数量]

要求:
- 话题名称最多8个字符
- 按推文数量降序排列
- 最多列出8个话题"""

            api_params = self.get_api_params(400)
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **api_params
            )
            
            if hasattr(response, 'usage'):
                self.total_tokens_used += response.usage.total_tokens
            
            # Parse response and store in bulk_topics
            content = response.choices[0].message.content
            lines = content.strip().split('\n')
            
            for line in lines:
                if '. ' in line and ' - ' in line:
                    try:
                        topic_part = line.split('. ', 1)[1]
                        topic_name = topic_part.split(' - ')[0].strip()
                        count_str = topic_part.split(' - ')[1].strip()
                        count = int(''.join(filter(str.isdigit, count_str)))
                        self.bulk_topics[topic_name] = count
                    except:
                        continue
                        
        except Exception as e:
            print(f"OpenAI话题分析错误: {e}")
    
    def generate_bulk_topic_analysis_with_sentiment_silent(self, tweets, token_symbol):
        """Silent version of topic analysis"""
        if not self.openai_client:
            return
        
        try:
            tweets_text = "\n".join([f"{i+1}. {tweet['text'][:100]}..." 
                                   for i, tweet in enumerate(tweets[:20])])
            
            prompt = f"""分析这些关于{token_symbol}的推文话题分布。请用简体中文回复。

推文内容:
{tweets_text}

请按以下格式回复:
1. [话题名称] - [推文数量]
2. [话题名称] - [推文数量]
3. [话题名称] - [推文数量]

要求:
- 话题名称最多8个字符
- 按推文数量降序排列
- 最多列出8个话题"""

            api_params = self.get_api_params(400)
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **api_params
            )
            
            if hasattr(response, 'usage'):
                self.total_tokens_used += response.usage.total_tokens
            
            # Parse and store silently
            content = response.choices[0].message.content
            lines = content.strip().split('\n')
            
            for line in lines:
                if '. ' in line and ' - ' in line:
                    try:
                        topic_part = line.split('. ', 1)[1]
                        topic_name = topic_part.split(' - ')[0].strip()
                        count_str = topic_part.split(' - ')[1].strip()
                        count = int(''.join(filter(str.isdigit, count_str)))
                        self.bulk_topics[topic_name] = count
                    except:
                        continue
                        
        except Exception as e:
            # Silent failure for silent mode
            pass
    
    def get_tweet_topic_with_sentiment(self, tweet_text, openai_analysis=None):
        """Get topic for a tweet, using OpenAI analysis if available"""
        if openai_analysis and openai_analysis.get('topic'):
            return openai_analysis['topic']
        
        # Fallback to keyword-based topic detection
        return self.detect_topic_from_keywords(tweet_text)
    
    def detect_topic_from_keywords(self, text):
        """Detect topic using keyword matching as fallback"""
        text_lower = text.lower()
        
        # Check specific topic keywords first
        try:
            for topic, keywords in SPECIFIC_TOPIC_KEYWORDS.items():
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        return topic
        except:
            pass
        
        # Check general topic keywords
        try:
            for topic, keywords in TOPIC_KEYWORDS.items():
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        return topic
        except:
            pass
        
        # Simple fallback based on common crypto terms
        if any(word in text_lower for word in ['价格', 'price', '涨', '跌', '买', '卖']):
            return "价格讨论"
        elif any(word in text_lower for word in ['技术', 'tech', '开发', 'dev']):
            return "技术更新"
        elif any(word in text_lower for word in ['合作', 'partner', '联盟']):
            return "合作伙伴"
        elif any(word in text_lower for word in ['空投', 'airdrop', '免费']):
            return "空投活动"
        else:
            return "未分类"
    
    def analyze_topic_sentiment_distribution(self, tweet_analyses):
        """Analyze sentiment distribution across topics"""
        topic_sentiment = {}
        
        for analysis in tweet_analyses:
            topic = analysis.get('topic', '未分类')
            sentiment = analysis.get('sentiment', {}).get('sentiment', 'NEUTRAL')
            
            if topic not in topic_sentiment:
                topic_sentiment[topic] = {'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0, 'total': 0}
            
            topic_sentiment[topic][sentiment] += 1
            topic_sentiment[topic]['total'] += 1
        
        # Calculate percentages
        for topic, sentiments in topic_sentiment.items():
            total = sentiments['total']
            if total > 0:
                for sentiment in ['POSITIVE', 'NEGATIVE', 'NEUTRAL']:
                    sentiments[f'{sentiment}_pct'] = (sentiments[sentiment] / total) * 100
        
        return topic_sentiment
    
    def get_topic_summary(self):
        """Get a summary of detected topics"""
        if not self.bulk_topics:
            return "无话题数据"
        
        sorted_topics = sorted(self.bulk_topics.items(), key=lambda x: x[1], reverse=True)
        top_topics = sorted_topics[:5]
        
        summary_parts = []
        for topic, count in top_topics:
            summary_parts.append(f"{topic}({count}条)")
        
        return "; ".join(summary_parts)
    
    def reset_analysis(self):
        """Reset analysis data for new run"""
        self.bulk_topics = {}
        self.total_tokens_used = 0
    
    def analyze_single_tweet_topic(self, tweet_text, token_symbol):
        """Analyze topic for a single tweet using AI"""
        if not self.openai_client:
            return self.detect_topic_from_keywords(tweet_text)
        
        try:
            prompt = f"""分析这条关于{token_symbol}的推文属于什么话题。用简体中文回复话题名称，最多8个字符。

推文: "{tweet_text}"

请从以下类别中选择最具体的话题:
- 价格预测, 技术分析, 持仓分享, 交易策略
- 上币消息, 空投活动, 合作伙伴, 产品开发
- 安全漏洞, 监管政策, 社区动态, 市场风险

只回复话题名称，不要其他内容。"""

            api_params = self.get_api_params(50)
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **api_params
            )
            
            if hasattr(response, 'usage'):
                self.total_tokens_used += response.usage.total_tokens
            
            topic = response.choices[0].message.content.strip()
            return topic if len(topic) <= 8 else topic[:8]
            
        except Exception as e:
            return self.detect_topic_from_keywords(tweet_text)
    
    def get_topic_distribution(self):
        """Get topic distribution statistics"""
        if not self.bulk_topics:
            return {}
        
        total = sum(self.bulk_topics.values())
        distribution = {}
        
        for topic, count in self.bulk_topics.items():
            distribution[topic] = {
                'count': count,
                'percentage': (count / total) * 100 if total > 0 else 0
            }
        
        return distribution
    
    def get_top_topics(self, limit=5):
        """Get top N topics by count"""
        if not self.bulk_topics:
            return []
        
        sorted_topics = sorted(self.bulk_topics.items(), key=lambda x: x[1], reverse=True)
        return sorted_topics[:limit]
    
    def has_topic_data(self):
        """Check if topic analysis data is available"""
        return bool(self.bulk_topics)
    
    def get_token_usage(self):
        """Get total tokens used for topic analysis"""
        return self.total_tokens_used
