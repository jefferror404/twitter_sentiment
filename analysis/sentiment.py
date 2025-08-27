# analysis/sentiment.py (Enhanced with Silent Mode)
"""
Enhanced sentiment analysis with silent mode for clean output
"""

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .filters import TweetFilter
from .influence import InfluenceCalculator
from .topics import TopicAnalyzer
from api.coinex_api import CoinExAPI
from utils.tweet_parser import TweetParser
from utils.formatters import ReportFormatter
from config import ANALYSIS_CONFIG


class CryptoSentimentAnalyzer:
    def __init__(self, openai_api_key=None, silent_mode=False):
        self.openai_client = OpenAI(api_key=openai_api_key) if openai_api_key and OPENAI_AVAILABLE else None
        self.total_tokens_used = 0
        self.price_context = None
        self.silent_mode = silent_mode
        
        # Initialize components
        self.tweet_filter = TweetFilter(openai_api_key, silent_mode=silent_mode)
        self.influence_calculator = InfluenceCalculator()
        self.topic_analyzer = TopicAnalyzer(openai_api_key)
        self.coinex_api = CoinExAPI()
        self.tweet_parser = TweetParser()
        self.report_formatter = ReportFormatter()
    
    def analyze_sentiment_and_topic_combined(self, text):
        """Combined sentiment and topic analysis with price context awareness"""
        if not self.openai_client:
            return None
        
        try:
            # Build price context string if available
            price_context_str = ""
            if self.price_context:
                price_change = self.price_context['change_rate']
                price_direction = "上涨" if price_change > 0 else "下跌" if price_change < 0 else "平稳"
                abs_change = abs(price_change)
                
                # Determine price movement significance
                if abs_change > 0.1:
                    movement_desc = "剧烈波动"
                elif abs_change > 0.05:
                    movement_desc = "显著波动"
                elif abs_change > 0.02:
                    movement_desc = "轻微波动"
                else:
                    movement_desc = "基本稳定"
                
                price_context_str = f"""
MARKET CONTEXT: 当前代币价格{movement_desc}，24小时{price_direction} {price_change:.2%}

IMPORTANT - 价格感知情感分析指引:
- 价格上涨时 ({price_change:.2%} > 0): 中性/模糊评论可能偏向积极，兴奋情绪可能被放大
- 价格下跌时 ({price_change:.2%} < 0): 中性/模糊评论可能偏向消极，担忧情绪可能被加剧
- 价格平稳时 (≈0%): 主要关注纯粹情感，减少价格偏见
- 强烈价格波动 (>5%): 显著影响推文的情感背景和解读
"""

            prompt = f"""
            Analyze this cryptocurrency tweet for BOTH sentiment and topic. Consider crypto slang, sarcasm, market context, and community dynamics.
            
            {price_context_str}
            
            Tweet: "{text}"
            
            SENTIMENT Guidelines:
            NEGATIVE: 
            Security issues (安全问题,黑客,资金被盗,漏洞,攻击,恶意软件), 
            Legal/Regulatory (破产,执法,监管,洗钱,风控,诈骗), 
            Market risks (下架,突发,风险提示,交易所ST,交易所充提), 
            Technical issues (代幣增發,代幣釋放,代幣解鎖,跨链桥,停試營運), 
            General negative (dump,crash,scam,fraud,rug pull)
            
            POSITIVE: 
            General positive (moon,pump,bullish,gem,上幣,上所,空投), 
            Product Development (产品开发,产品发布,合约升级)
            
            NEUTRAL: Factual reporting, 
            Technical updates (硬分叉,迁移,换币,代币经济学变更)
            
            TOPIC Categories - Choose the MOST SPECIFIC sub-topic:
            
            🆕 SPECIFIC TOPIC EXAMPLES:
            Technology: 智能合约漏洞, 跨链桥风险, 共识机制升级, DeFi协议风险, 钱包安全
            Market: 大户抛售, 机构买入, 交易所上架, 做市商操控, 流动性危机
            Community: CEO离职, 团队解散, 社区分歧, 开发停滞, 路线图延期
            Regulation: SEC调查, 监管政策, 合规问题, 法律诉讼, 政府禁令
            Price: 突破支撑位, 跌破阻力位, 技术指标看涨, 成交量萎缩, 价格操控
            Partnerships: 与大厂合作, 投资机构入股, 战略联盟, 生态扩展, 技术整合
            
            IMPORTANT: 
            - Be VERY SPECIFIC about what exactly the concern/excitement is about
            - Instead of "技术风险" use "智能合约漏洞" or "跨链桥风险"
            - Instead of "社区担忧" use "CEO离职" or "开发停滞"  
            - Instead of "社区乐观" use "与大厂合作" or "生态扩展"
            - Max 8 characters for topic name
            
            Respond EXACTLY in this format:
            SENTIMENT: [POSITIVE/NEGATIVE/NEUTRAL]
            CONFIDENCE: [0.0-1.0]
            TOPIC: [specific topic, max 8 chars]
            REASON: [One sentence explanation including price context influence if applicable]
            """
            
            response = self.openai_client.chat.completions.create(
                model=ANALYSIS_CONFIG['openai_model'],
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=120,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse the structured response
            lines = content.split('\n')
            sentiment = None
            confidence = 0.5
            topic = "未分类"
            reason = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith('SENTIMENT:'):
                    sentiment = line.split(':', 1)[1].strip()
                elif line.startswith('CONFIDENCE:'):
                    try:
                        confidence = float(line.split(':', 1)[1].strip())
                    except:
                        confidence = 0.5
                elif line.startswith('TOPIC:'):
                    topic = line.split(':', 1)[1].strip()
                    # Clean up topic
                    if topic.startswith('- '):
                        topic = topic[2:].strip()
                    if topic.startswith('-'):
                        topic = topic[1:].strip()
                elif line.startswith('REASON:'):
                    reason = line.split(':', 1)[1].strip()
            
            # Fallback parsing if structured format fails
            if not sentiment:
                content_upper = content.upper()
                if 'NEGATIVE' in content_upper:
                    sentiment = 'NEGATIVE'
                elif 'POSITIVE' in content_upper:
                    sentiment = 'POSITIVE'
                else:
                    sentiment = 'NEUTRAL'
            
            # Track token usage
            if hasattr(response, 'usage'):
                self.total_tokens_used += response.usage.total_tokens
            
            return {
                'sentiment': sentiment,
                'confidence': confidence,
                'topic': topic,
                'reasoning': reason,
                'raw_response': content,
                'price_aware': bool(self.price_context)
            }
            
        except Exception as e:
            return None
    
    def analyze_tweet_sentiment(self, text):
        """Price-aware sentiment analysis using combined function"""
        combined_result = self.analyze_sentiment_and_topic_combined(text)
        
        if not combined_result:
            # Fallback if OpenAI fails
            return {
                'sentiment': 'NEUTRAL',
                'sentiment_score': 0,
                'confidence': 0.5,
                'topic': '未分类',
                'openai_analysis': None,
                'analysis_method': 'fallback_neutral',
                'price_influenced': False
            }
        
        # Convert sentiment to sentiment_score for compatibility
        sentiment_score = 0
        if combined_result['sentiment'] == 'POSITIVE':
            sentiment_score = 1
        elif combined_result['sentiment'] == 'NEGATIVE':
            sentiment_score = -1
        
        return {
            'sentiment': combined_result['sentiment'],
            'sentiment_score': sentiment_score,
            'confidence': combined_result['confidence'],
            'topic': combined_result['topic'],
            'openai_analysis': combined_result,
            'analysis_method': 'price_aware_combined',
            'price_influenced': combined_result.get('price_aware', False)
        }
    
    def generate_openai_summary(self, tweets_sample, token_symbol):
        """Generate OpenAI summary of tweets in Simplified Chinese with price context"""
        if not self.openai_client:
            return "OpenAI不可用，无法生成智能摘要"
        
        try:
            max_tweets = ANALYSIS_CONFIG['max_tweets_for_summary']
            sample_tweets = tweets_sample[:max_tweets] if len(tweets_sample) > max_tweets else tweets_sample
            tweets_text = "\n".join([f"- {tweet['text'][:120]}..." if len(tweet['text']) > 120 else f"- {tweet['text']}" 
                                   for tweet in sample_tweets])
            
            # Add price context to summary if available
            price_context_str = ""
            if self.price_context:
                price_change = self.price_context['change_rate']
                price_usd = self.price_context['price_usd']
                price_context_str = f"""
当前市场状况: {token_symbol} 价格 ${price_usd:.6f} (24H: {price_change:+.2%})
请在分析中考虑价格波动对社区情绪的影响。
"""
            
            prompt = f"""
            请分析这{len(tweets_sample)}条关于{token_symbol}的推文，并提供综合摘要。请用简体中文回复。
            
            {price_context_str}
            
            推文样本:
            {tweets_text}
            
            请提供包含以下内容的摘要(以下面的point form形式显示):
            1. 整体情绪和社区氛围 包含讨论的主要话题和热点）
            2. 主要担忧或兴奋点（包含讨论的主要话题和热点）
            3. 提及的风险因素（包含技术、市场、监管等具体风险类型）
            
            请保持简洁但有深度的分析(最多3-4句话)。重点关注对投资者有用的见解。
            请务必用简体中文回复。
            """
            
            response = self.openai_client.chat.completions.create(
                model=ANALYSIS_CONFIG['openai_model'],
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=300,
                temperature=0.3
            )
            
            # Track token usage
            if hasattr(response, 'usage'):
                self.total_tokens_used += response.usage.total_tokens
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"OpenAI摘要生成失败: {e}"
    
    def comprehensive_analysis(self, tweets, token_symbol):
        """Perform comprehensive price-aware sentiment analysis with enhanced filtering"""
        print(f"\n{'='*80}")
        print(f"🚀 价格感知情感分析: {token_symbol}")
        print(f"{'='*80}")
        print(f"📊 原始推文数量: {len(tweets)}")
        
        # Step 1: Get price data from CoinEx API
        print(f"💰 获取 {token_symbol} 价格数据...")
        self.price_context = self.coinex_api.get_price_context(token_symbol)
        price_success = self.price_context is not None
        
        # Step 2: Enhanced filtering with team accounts
        filtered_tweets, exclusion_reasons = self.tweet_filter.filter_tweets(
            tweets, self.tweet_parser.parse_tweet_data, token_symbol
        )
        
        if not filtered_tweets:
            print("❌ 过滤后无可分析推文")
            return None
        
        if price_success:
            print(f"📈 开始价格感知分析 {len(filtered_tweets)} 条有效推文...")
        else:
            print(f"📈 开始标准分析 {len(filtered_tweets)} 条有效推文...")
        
        # First, do bulk topic analysis once with enhanced categorization
        tweets_for_topic_analysis = []
        for tweet in filtered_tweets:
            parsed = self.tweet_parser.parse_tweet_data(tweet)
            tweets_for_topic_analysis.append({'text': parsed['text']})
        
        self.topic_analyzer.generate_bulk_topic_analysis_with_sentiment(tweets_for_topic_analysis, token_symbol)
        
        tweet_analyses = []
        sentiment_summary = {'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0}
        total_weighted_impact = 0
        high_influence_tweets = []
        viral_tweets = []
        price_influenced_count = 0
        
        for i, tweet in enumerate(filtered_tweets):
            try:
                parsed_tweet = self.tweet_parser.parse_tweet_data(tweet)
                
                # Use price-aware sentiment analysis
                sentiment_result = self.analyze_tweet_sentiment(parsed_tweet['text'])
                influence_data = self.influence_calculator.calculate_influence_score(parsed_tweet['user'])
                viral_data = self.influence_calculator.calculate_viral_index(parsed_tweet['metrics'])
                
                impact_data = self.influence_calculator.calculate_weighted_sentiment_impact(
                    sentiment_result, 
                    influence_data['influence_score'], 
                    viral_data['viral_index']
                )
                
                sentiment_summary[sentiment_result['sentiment']] += 1
                total_weighted_impact += impact_data['weighted_impact']
                
                # Count price-influenced analyses
                if sentiment_result.get('price_influenced', False):
                    price_influenced_count += 1
                
                # Get topic with sentiment from the combined analysis
                tweet_topic = self.topic_analyzer.get_tweet_topic_with_sentiment(
                    parsed_tweet['text'], 
                    sentiment_result.get('openai_analysis')
                )
                
                tweet_analysis = {
                    'tweet_num': i + 1,
                    'tweet_id': parsed_tweet['tweet_id'],
                    'user': parsed_tweet['user']['username'],
                    'text_preview': parsed_tweet['text'][:150] + '...' if len(parsed_tweet['text']) > 150 else parsed_tweet['text'],
                    'sentiment': sentiment_result,
                    'topic': tweet_topic,
                    'influence': influence_data,
                    'viral': viral_data,
                    'weighted_impact': impact_data,
                    'engagement': parsed_tweet['metrics']
                }
                
                tweet_analyses.append(tweet_analysis)
                
                if influence_data['influence_score'] >= 1.0:
                    high_influence_tweets.append(tweet_analysis)
                
                if viral_data['viral_index'] >= 5.0:
                    viral_tweets.append(tweet_analysis)
                    
            except Exception as e:
                print(f"Error analyzing tweet {i+1}: {e}")
                continue
        
        # Analyze topic sentiment distribution
        topic_sentiment_analysis = self.topic_analyzer.analyze_topic_sentiment_distribution(tweet_analyses)
        
        # Consolidate token usage from all components
        self.total_tokens_used += self.tweet_filter.total_tokens_used
        self.total_tokens_used += self.topic_analyzer.total_tokens_used
        
        # Get team filter stats
        team_filter_stats = self.tweet_filter.get_team_filter_stats()
        
        # Create enhanced result with team filtering info
        result = {
            'tweet_analyses': tweet_analyses,
            'sentiment_summary': sentiment_summary,
            'total_weighted_impact': total_weighted_impact,
            'high_influence_tweets': high_influence_tweets,
            'viral_tweets': viral_tweets,
            'filtering_stats': self.tweet_filter.filtered_counts,
            'team_filter_stats': team_filter_stats,
            'price_aware_stats': {
                'price_data_available': price_success,
                'price_influenced_count': price_influenced_count,
                'price_influence_rate': price_influenced_count / len(tweet_analyses) if tweet_analyses else 0,
                'price_context': self.price_context
            },
            'exclusion_reasons': exclusion_reasons,
            'bulk_topics': self.topic_analyzer.bulk_topics,
            'topic_sentiment_analysis': topic_sentiment_analysis,
            'total_tokens_used': self.total_tokens_used
        }
        
        # Generate and print the enhanced report
        self.report_formatter.print_enhanced_report(
            token_symbol, len(filtered_tweets), sentiment_summary, total_weighted_impact,
            high_influence_tweets, viral_tweets, tweet_analyses, tweets, result,
            self.generate_openai_summary, tweets_for_topic_analysis
        )
        
        return result

    def comprehensive_analysis_silent(self, tweets, token_symbol, target_days):
        """🆕 Silent version of comprehensive analysis with clean output"""
        # Step 1: Get price data (silent)
        self.price_context = self.coinex_api.get_price_context_silent(token_symbol)
        price_success = self.price_context is not None
        
        # Step 2: Filter tweets (silent) - Use the existing silent TweetFilter
        filtered_tweets, exclusion_reasons = self.tweet_filter.filter_tweets_silent(
            tweets, self.tweet_parser.parse_tweet_data, token_symbol
        )
        
        if not filtered_tweets:
            # 🆕 Handle case where no tweets remain after filtering
            return None
        
        # Step 3: Topic analysis (silent)
        tweets_for_topic_analysis = []
        for tweet in filtered_tweets:
            parsed = self.tweet_parser.parse_tweet_data(tweet)
            tweets_for_topic_analysis.append({'text': parsed['text']})
        
        self.topic_analyzer.generate_bulk_topic_analysis_with_sentiment(tweets_for_topic_analysis, token_symbol)
        
        # Step 4: Analyze tweets (silent)
        tweet_analyses = []
        sentiment_summary = {'POSITIVE': 0, 'NEGATIVE': 0, 'NEUTRAL': 0}
        total_weighted_impact = 0
        high_influence_tweets = []
        viral_tweets = []
        price_influenced_count = 0
        
        for i, tweet in enumerate(filtered_tweets):
            try:
                parsed_tweet = self.tweet_parser.parse_tweet_data(tweet)
                
                sentiment_result = self.analyze_tweet_sentiment(parsed_tweet['text'])
                influence_data = self.influence_calculator.calculate_influence_score(parsed_tweet['user'])
                viral_data = self.influence_calculator.calculate_viral_index(parsed_tweet['metrics'])
                
                impact_data = self.influence_calculator.calculate_weighted_sentiment_impact(
                    sentiment_result, 
                    influence_data['influence_score'], 
                    viral_data['viral_index']
                )
                
                sentiment_summary[sentiment_result['sentiment']] += 1
                total_weighted_impact += impact_data['weighted_impact']
                
                if sentiment_result.get('price_influenced', False):
                    price_influenced_count += 1
                
                tweet_topic = self.topic_analyzer.get_tweet_topic_with_sentiment(
                    parsed_tweet['text'], 
                    sentiment_result.get('openai_analysis')
                )
                
                tweet_analysis = {
                    'tweet_num': i + 1,
                    'tweet_id': parsed_tweet['tweet_id'],
                    'user': parsed_tweet['user']['username'],
                    'text_preview': parsed_tweet['text'][:150] + '...' if len(parsed_tweet['text']) > 150 else parsed_tweet['text'],
                    'sentiment': sentiment_result,
                    'topic': tweet_topic,
                    'influence': influence_data,
                    'viral': viral_data,
                    'weighted_impact': impact_data,
                    'engagement': parsed_tweet['metrics']
                }
                
                tweet_analyses.append(tweet_analysis)
                
                if influence_data['influence_score'] >= 1.0:
                    high_influence_tweets.append(tweet_analysis)
                
                if viral_data['viral_index'] >= 5.0:
                    viral_tweets.append(tweet_analysis)
                    
            except Exception:
                continue
        
        # Consolidate stats
        topic_sentiment_analysis = self.topic_analyzer.analyze_topic_sentiment_distribution(tweet_analyses)
        self.total_tokens_used += self.tweet_filter.total_tokens_used
        self.total_tokens_used += self.topic_analyzer.total_tokens_used
        team_filter_stats = self.tweet_filter.get_team_filter_stats()
        
        # Create result
        result = {
            'tweet_analyses': tweet_analyses,
            'sentiment_summary': sentiment_summary,
            'total_weighted_impact': total_weighted_impact,
            'high_influence_tweets': high_influence_tweets,
            'viral_tweets': viral_tweets,
            'filtering_stats': self.tweet_filter.filtered_counts,
            'team_filter_stats': team_filter_stats,
            'price_aware_stats': {
                'price_data_available': price_success,
                'price_influenced_count': price_influenced_count,
                'price_influence_rate': price_influenced_count / len(tweet_analyses) if tweet_analyses else 0,
                'price_context': self.price_context
            },
            'exclusion_reasons': exclusion_reasons,
            'bulk_topics': self.topic_analyzer.bulk_topics,
            'topic_sentiment_analysis': topic_sentiment_analysis,
            'total_tokens_used': self.total_tokens_used
        }
        
        # 🆕 Generate clean, simplified report
        self.report_formatter.print_clean_report(
            token_symbol, len(tweets), len(filtered_tweets), sentiment_summary, 
            high_influence_tweets, viral_tweets, tweet_analyses, tweets, result,
            self.generate_openai_summary, tweets_for_topic_analysis, target_days
        )
        
        return result
