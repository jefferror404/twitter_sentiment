# analysis/filters.py (Enhanced with Silent Team Filtering)
"""
Enhanced tweet filtering with silent team filtering mode
"""

import re
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from config import NEWS_ACCOUNTS, SPAM_PATTERNS, TEAM_FILTER_CONFIG
from data.team_filter import TeamFilter


class TweetFilter:
    def __init__(self, openai_api_key=None, silent_mode=False):
        self.news_accounts = NEWS_ACCOUNTS
        self.spam_patterns = SPAM_PATTERNS
        self.openai_client = OpenAI(api_key=openai_api_key) if openai_api_key and OPENAI_AVAILABLE else None
        self.silent_mode = silent_mode
        
        # 🆕 Initialize team filter with silent mode
        self.team_filter = None
        if TEAM_FILTER_CONFIG['enable_team_filtering']:
            self.team_filter = TeamFilter(
                TEAM_FILTER_CONFIG['excel_file_path'], 
                silent_mode=silent_mode
            )
        
        self.total_tokens_used = 0
        self.filtered_counts = {
            'news_accounts': 0,
            'spam_basic': 0,
            'team_accounts': 0,
            'spam_ai': 0,
            'informative_ai': 0,
            'total_filtered': 0
        }
    
    def is_news_account(self, username):
        """Check if username belongs to news/informative accounts"""
        if not username or username == 'N/A':
            return False
        return username.lower().replace('@', '') in self.news_accounts
    
    def is_team_account(self, username, token_symbol):
        """Check if username belongs to the project team"""
        if not self.team_filter:
            return False
        return self.team_filter.is_team_account(username, token_symbol)
    
    def detect_basic_spam(self, text, user_data):
        """Basic spam detection using patterns and keywords"""
        if not text or len(text.strip()) < 5:
            return True, "Too short"
        
        text_lower = text.lower()
        
        # Check giveaway keywords
        giveaway_matches = sum(1 for keyword in self.spam_patterns['giveaway_keywords'] 
                              if keyword in text_lower)
        if giveaway_matches >= 2:
            return True, "Giveaway spam"
        
        # Check meaningless patterns
        for pattern in self.spam_patterns['meaningless_patterns']:
            if re.match(pattern, text.strip(), re.IGNORECASE):
                return True, "Meaningless content"
        
        # Check token spam (too many token symbols)
        if re.search(self.spam_patterns['token_spam_pattern'], text):
            return True, "Token list spam"
        
        # Check excessive emojis
        if re.search(self.spam_patterns['excessive_emojis'], text):
            return True, "Excessive emojis"
        
        # Check repeated characters
        if re.search(self.spam_patterns['repeated_chars'], text):
            return True, "Repeated characters"
        
        # Check very low effort tweets
        words = text.split()
        if len(words) <= 2 and not any(word.startswith('$') for word in words):
            return True, "Too few words"
        
        return False, "Clean"
    
    def ai_content_filter(self, text, username):
        """Use AI to detect spam and informative content with shorter reasons"""
        if not self.openai_client:
            return {'is_spam': False, 'is_informative': False, 'reason': 'OpenAI not available'}
        
        try:
            prompt = f"""
            Analyze this tweet to determine if it should be EXCLUDED from sentiment analysis.
            
            Tweet: "{text}"
            Username: @{username}
            
            EXCLUDE if the tweet is:
            
            1. SPAM/GIVEAWAY content:
            - Asks for retweets, likes, follows for rewards
            - Asks users to "drop wallet", "tag friends", etc.
            - Promotes giveaways, airdrops, presales
            - Very low quality with minimal meaning
            - Just lists many token symbols without context
            
            2. PURELY INFORMATIVE content (no sentiment):
            - News reports without opinion/emotion
            - Data/price updates without sentiment
            - Technical analysis without clear bullish/bearish stance
            - Factual announcements from official accounts
            - Pure market data or statistics
            
            INCLUDE if the tweet has:
            - Personal opinions, emotions, or reactions
            - Bullish/bearish sentiment about projects
            - Community discussion with sentiment
            - Investment advice or speculation
            - Excitement, fear, or other emotional responses
            
            Respond EXACTLY in this format:
            SPAM: [YES/NO]
            INFORMATIVE: [YES/NO]
            REASON: [Very brief explanation, max 20 chars]
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse response
            is_spam = False
            is_informative = False
            reason = "Unknown"
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('SPAM:'):
                    is_spam = 'YES' in line.upper()
                elif line.startswith('INFORMATIVE:'):
                    is_informative = 'YES' in line.upper()
                elif line.startswith('REASON:'):
                    reason = line.split(':', 1)[1].strip()
                    # Ensure reason is short
                    if len(reason) > 20:
                        reason = reason[:17] + "..."
            
            # Track token usage
            if hasattr(response, 'usage'):
                self.total_tokens_used += response.usage.total_tokens
            
            return {
                'is_spam': is_spam,
                'is_informative': is_informative,
                'reason': reason
            }
            
        except Exception as e:
            if not self.silent_mode:
                print(f"AI content filter error: {e}")
            return {'is_spam': False, 'is_informative': False, 'reason': f'AI error'}
    
    def should_exclude_tweet(self, parsed_tweet, token_symbol):
        """Enhanced comprehensive tweet filtering logic with team filtering"""
        text = parsed_tweet['text']
        username = parsed_tweet['user']['username']
        
        # 1. Filter news/informative accounts
        if self.is_news_account(username):
            self.filtered_counts['news_accounts'] += 1
            return True, f"News account: @{username}"
        
        # 2. Filter project team accounts
        if self.is_team_account(username, token_symbol):
            self.filtered_counts['team_accounts'] += 1
            return True, f"Team account: @{username}"
        
        # 3. Basic spam detection
        is_basic_spam, basic_reason = self.detect_basic_spam(text, parsed_tweet['user'])
        if is_basic_spam:
            self.filtered_counts['spam_basic'] += 1
            return True, f"Basic spam: {basic_reason}"
        
        # 4. AI-powered content filtering
        ai_filter = self.ai_content_filter(text, username)
        
        if ai_filter['is_spam']:
            self.filtered_counts['spam_ai'] += 1
            return True, f"AI spam: {ai_filter['reason']}"
        
        if ai_filter['is_informative']:
            self.filtered_counts['informative_ai'] += 1
            return True, f"AI informative: {ai_filter['reason']}"
        
        return False, "Include for analysis"
    
    def get_detailed_filter_reason(self, reason):
        """Extract and format detailed filtering reason"""
        if "AI spam:" in reason:
            return reason.split("AI spam:", 1)[1].strip()
        elif "AI informative:" in reason:
            return reason.split("AI informative:", 1)[1].strip()
        elif "Basic spam:" in reason:
            return reason.split("Basic spam:", 1)[1].strip()
        elif "News account:" in reason:
            return reason.split("News account:", 1)[1].strip()
        elif "Team account:" in reason:
            return reason.split("Team account:", 1)[1].strip()
        else:
            return reason
    
    def filter_tweets(self, tweets, parse_tweet_func, token_symbol):
        """Enhanced filter with team filtering and token symbol"""
        if not self.silent_mode:
            print(f"\n🔍 开始推文过滤 (总共 {len(tweets)} 条)...")
            
            # Show team filtering info
            if self.team_filter and TEAM_FILTER_CONFIG['show_team_accounts_debug']:
                self.team_filter.show_team_accounts_for_token(token_symbol)
            elif self.team_filter:
                self.team_filter.validate_token_coverage(token_symbol)
        
        filtered_tweets = []
        exclusion_reasons = []
        
        for i, tweet in enumerate(tweets):
            try:
                parsed_tweet = parse_tweet_func(tweet)
                should_exclude, reason = self.should_exclude_tweet(parsed_tweet, token_symbol)
                
                if should_exclude:
                    # Store more detailed information for the table
                    exclusion_reasons.append({
                        'tweet_num': i + 1,
                        'user': parsed_tweet['user']['username'],
                        'reason': reason,
                        'detailed_reason': self.get_detailed_filter_reason(reason),
                        'text_preview': parsed_tweet['text'][:100] + '...' if len(parsed_tweet['text']) > 100 else parsed_tweet['text'],
                        'full_text': parsed_tweet['text'],
                        'followers': parsed_tweet['user']['followers_count']
                    })
                    self.filtered_counts['total_filtered'] += 1
                else:
                    filtered_tweets.append(tweet)
                    
            except Exception as e:
                if not self.silent_mode:
                    print(f"Error filtering tweet {i+1}: {e}")
                # Include tweet if filtering fails
                filtered_tweets.append(tweet)
        
        # Print enhanced filtering summary (only if not silent)
        if not self.silent_mode:
            print(f"📊 过滤结果:")
            print(f"   🗞️  新闻账户过滤: {self.filtered_counts['news_accounts']} 条")
            if self.team_filter and self.team_filter.is_loaded:
                print(f"   👥 团队账户过滤: {self.filtered_counts['team_accounts']} 条")
            print(f"   🚫 基础垃圾过滤: {self.filtered_counts['spam_basic']} 条")
            print(f"   🤖 AI垃圾过滤: {self.filtered_counts['spam_ai']} 条")
            print(f"   📰 AI信息过滤: {self.filtered_counts['informative_ai']} 条")
            print(f"   📉 总过滤数量: {self.filtered_counts['total_filtered']} 条")
            print(f"   ✅ 保留分析: {len(filtered_tweets)} 条")
        
        return filtered_tweets, exclusion_reasons
    
    def get_team_filter_stats(self):
        """Get team filter statistics"""
        if not self.team_filter:
            return {'enabled': False}
        
        stats = self.team_filter.get_filtering_stats()
        stats['enabled'] = True
        stats['filtered_count'] = self.filtered_counts['team_accounts']
        
        return stats
    
    def filter_tweets_silent(self, tweets, parse_tweet_func, token_symbol):
        """Silent version of filter_tweets"""
        filtered_tweets = []
        exclusion_reasons = []
        
        # Silent team validation
        if self.team_filter:
            self.team_filter.validate_token_coverage_silent(token_symbol)
        
        for i, tweet in enumerate(tweets):
            try:
                parsed_tweet = parse_tweet_func(tweet)
                should_exclude, reason = self.should_exclude_tweet(parsed_tweet, token_symbol)
                
                if should_exclude:
                    exclusion_reasons.append({
                        'tweet_num': i + 1,
                        'user': parsed_tweet['user']['username'],
                        'reason': reason,
                        'detailed_reason': self.get_detailed_filter_reason(reason),
                        'text_preview': parsed_tweet['text'][:100] + '...' if len(parsed_tweet['text']) > 100 else parsed_tweet['text'],
                        'full_text': parsed_tweet['text'],
                        'followers': parsed_tweet['user']['followers_count']
                    })
                    self.filtered_counts['total_filtered'] += 1
                else:
                    filtered_tweets.append(tweet)
                    
            except Exception:
                filtered_tweets.append(tweet)
        
        return filtered_tweets, exclusion_reasons
    
    def validate_token_coverage_silent(self, token_symbol):
        """Silent version of validate_token_coverage"""
        token_symbol = token_symbol.upper().strip()
        return token_symbol in self.team_accounts_db