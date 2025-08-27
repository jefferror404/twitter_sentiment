# analysis/topics.py - Update TopicAnalyzer class
class TopicAnalyzer:
    def __init__(self, openai_api_key, model_name=None):
        self.openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None
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
            # Silent failure for silent mode
            pass

# analysis/filters.py - Update TweetFilter class
class TweetFilter:
    def __init__(self, openai_api_key, model_name=None, silent_mode=False):
        self.openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None
        self.model = model_name or ANALYSIS_CONFIG.get('openai_model', 'gpt-4o-mini')
        self.silent_mode = silent_mode
        self.total_tokens_used = 0
        self.filtered_counts = {}
    
    def get_api_params(self, max_tokens=300):
        """Get correct API parameters for GPT-5 compatibility"""
        base_params = {'temperature': 0.1}
        
        if self.model.startswith('gpt-5'):
            base_params['max_completion_tokens'] = max_tokens
        else:
            base_params['max_tokens'] = max_tokens
        
        return base_params
    
    def filter_tweets_silent(self, tweets, parse_function, token_symbol):
        """Silent version of tweet filtering"""
        filtered_tweets = []
        exclusion_reasons = {}
        
        for tweet in tweets:
            try:
                parsed_tweet = parse_function(tweet)
                
                # Apply your existing filtering logic here
                if self.is_valid_tweet(parsed_tweet, token_symbol):
                    filtered_tweets.append(tweet)
                else:
                    reason = self.get_exclusion_reason(parsed_tweet)
                    exclusion_reasons[parsed_tweet.get('tweet_id', 'unknown')] = reason
                    
            except Exception:
                continue
        
        return filtered_tweets, exclusion_reasons
    
    def is_valid_tweet(self, parsed_tweet, token_symbol):
        """Check if tweet passes filtering criteria"""
        text = parsed_tweet.get('text', '').lower()
        
        # Basic content filtering
        if len(text.strip()) < 10:
            return False
        
        # Check for spam patterns
        if self.contains_spam_patterns(text):
            return False
        
        # Check for news accounts
        username = parsed_tweet.get('user', {}).get('username', '').lower()
        if username in NEWS_ACCOUNTS:
            return False
        
        return True
    
    def contains_spam_patterns(self, text):
        """Check if text contains spam patterns"""
        import re
        
        # Check giveaway keywords
        for keyword in SPAM_PATTERNS['giveaway_keywords']:
            if keyword in text:
                return True
        
        # Check regex patterns
        for pattern in SPAM_PATTERNS['meaningless_patterns']:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        return False

# utils/formatters.py - Update ReportFormatter class  
class ReportFormatter:
    def __init__(self):
        pass
    
    def print_clean_report(self, token_symbol, total_tweets, filtered_tweets_count, 
                          sentiment_summary, high_influence_tweets, viral_tweets, 
                          tweet_analyses, original_tweets, result, 
                          summary_generator, tweets_for_summary, target_days):
        """Generate clean report output for Streamlit"""
        
        # Header
        print(f'🔍 "{token_symbol}" 近{target_days}天推文情感分析')
        print(f"原获取推文数量: {total_tweets}; 过滤后有效推文: {filtered_tweets_count}")
        
        # Price data section
        price_context = result.get('price_aware_stats', {}).get('price_context')
        if price_context:
            print(f"💰 站内数据总览:")
            print(f"   💵 当前价格: ${price_context['price_usd']:.6f}")
            
            change_rate = price_context['change_rate']
            change_icon = "📈" if change_rate >= 0 else "📉"
            print(f"   {change_icon} 24H变化: {change_rate:+.2%}")
            
            volume = price_context.get('volume_24h', 'N/A')
            if volume != 'N/A':
                print(f"   💧 24H交易量: ${volume:,.0f}")
            else:
                print(f"   💧 24H交易量: 未获取")
        else:
            print(f"💰 站内数据总览:")
            print(f"💰 价格数据: 未获取到有效数据")
        
        # Sentiment distribution
        print(f"🎭 情绪分布:")
        total = sum(sentiment_summary.values())
        if total > 0:
            for sentiment, count in sentiment_summary.items():
                percentage = (count / total) * 100
                emoji = {"POSITIVE": "✅", "NEGATIVE": "❌", "NEUTRAL": "⚪"}[sentiment]
                sentiment_cn = {"POSITIVE": "正面", "NEGATIVE": "负面", "NEUTRAL": "中性"}[sentiment]
                print(f"   {emoji} {sentiment_cn}: {count} 条 ({percentage:.1f}%)")
        
        # AI Summary with error handling
        print(f"🤖 AI 智能分析摘要:")
        print("=" * 50)
        try:
            ai_summary = summary_generator(tweets_for_summary, token_symbol)
            if ai_summary and not ai_summary.startswith("OpenAI摘要生成失败"):
                print(ai_summary)
            else:
                print("摘要生成失败，请检查API配置")
        except Exception as e:
            print(f"摘要生成失败: {e}")
        print("=" * 50)
        
        # Topic analysis
        bulk_topics = result.get('bulk_topics', {})
        if bulk_topics:
            print(f"📈 热门话题榜:")
            print("AI智能话题分析:")
            for i, (topic, count) in enumerate(sorted(bulk_topics.items(), key=lambda x: x[1], reverse=True)[:8], 1):
                bar_length = min(8, max(1, count))
                bar = "█" * bar_length + "▁" * (8 - bar_length)
                print(f"{i}. {topic} {bar} ({count}条)")
        
        # Viral tweets table
        if viral_tweets:
            print(f"🔥 病毒式传播推文 (传播力≥5.0):")
            print("用户名 | 传播力 | 点赞 | 转推 | 回复 | 情绪 | 话题 | 推文链接")
            print("-" * 110)
            
            for tweet_data in viral_tweets[:10]:
                user = tweet_data['user']
                viral_index = tweet_data['viral']['viral_index']
                engagement = tweet_data['engagement']
                sentiment = tweet_data['sentiment']['sentiment']
                topic = tweet_data['topic']
                tweet_id = tweet_data['tweet_id']
                
                link = f"https://x.com/i/status/{tweet_id}"
                
                print(f"@{user} | {viral_index:.1f} | {engagement['likes']} | "
                      f"{engagement['retweets']} | {engagement['replies']} | "
                      f"{sentiment} | {topic} | {link}")
        
        # High influence users table
        if high_influence_tweets:
            print(f"👑 高影响力用户动态 (影响力≥1.0):")
            print("用户名 | 影响力 | 粉丝数 | 情绪 | 传播力 | 话题 | 推文链接")
            print("-" * 110)
            
            for tweet_data in high_influence_tweets[:10]:
                user = tweet_data['user']
                influence_score = tweet_data['influence']['influence_score']
                followers = tweet_data['influence']['user_data']['followers_count']
                sentiment = tweet_data['sentiment']['sentiment']
                viral_index = tweet_data['viral']['viral_index']
                topic = tweet_data['topic']
                tweet_id = tweet_data['tweet_id']
                
                link = f"https://x.com/i/status/{tweet_id}"
                
                print(f"@{user} | {influence_score:.1f} | {followers:,} | "
                      f"{sentiment} | {viral_index:.1f} | {topic} | {link}")

# config.py - Update your configuration
ANALYSIS_CONFIG = {
    'target_days': 7,
    'max_pages_per_call': 3,
    'max_tweets_for_summary': 15,
    'max_tweets_for_topic_analysis': 20,
    'openai_model': "gpt-5-nano"  # Use fastest GPT-5 model
}

# Streamlit app.py - Update capture_analysis_output function
def capture_analysis_output(token_symbol):
    """Capture the output from the analysis function with full GPT-5 support"""
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    
    try:
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            # Configuration
            target_days = ANALYSIS_CONFIG['target_days']
            max_pages_per_call = ANALYSIS_CONFIG['max_pages_per_call']
            model_name = ANALYSIS_CONFIG['openai_model']
            
            # Initialize components with model support
            twitter_api = TwitterAPI()
            analyzer = CryptoSentimentAnalyzer(
                openai_api_key=OPENAI_API_KEY,
                model_name=model_name,  # Pass model name
                silent_mode=True
            )
            
            # Create smart querystring
            base_querystring = twitter_api.create_smart_querystring_silent(
                token_symbol,
                additional_filters={}
            )
            
            # Get tweets
            all_tweets = twitter_api.get_tweets_multi_timeframe_silent(
                base_querystring, 
                total_days=target_days, 
                max_pages_per_call=max_pages_per_call
            )
            
            if all_tweets:
                # Run analysis with proper model support
                analysis_result = analyzer.comprehensive_analysis_silent(
                    all_tweets, token_symbol, target_days
                )
                
                if not analysis_result:
                    print(f'🔍 "{token_symbol}" 近{target_days}天推文情感分析')
                    print(f"原获取推文数量: {len(all_tweets)}; 过滤后有效推文: 0")
                    print("❌ 过滤后无可分析推文，請檢查其他社群資訊")
                    return None, stdout_buffer.getvalue()
                
                return analysis_result, stdout_buffer.getvalue()
            else:
                print(f'🔍 "{token_symbol}" 近{target_days}天推文情感分析')
                print(f"原获取推文数量: 0; 过滤后有效推文: 0")
                print("❌ 过滤后无可分析推文，請檢查其他社群資訊")
                return None, stdout_buffer.getvalue()
                
    except Exception as e:
        error_msg = f"💥 分析过程中出现错误: {str(e)}\n{traceback.format_exc()}"
        return None, error_msg
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
