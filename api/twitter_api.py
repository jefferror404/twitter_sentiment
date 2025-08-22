# api/twitter_api.py (Enhanced with Silent Mode)
"""
Twitter API integration with silent mode for clean output
"""

import requests
import json
import time
import re
from datetime import datetime, timedelta
from config import TWITTER_API_CONFIG


class TwitterAPI:
    def __init__(self):
        self.url = TWITTER_API_CONFIG['url']
        self.headers = TWITTER_API_CONFIG['headers']
        self.api_key = TWITTER_API_CONFIG['api_key']
        self.search_cache = {}  # Cache successful search patterns
    
    def extract_tweets_from_response(self, response_data, verbose=False):
        """Extract tweet data from the complex nested response structure"""
        tweets = []

        try:
            data = response_data.get('data', {})
            if 'data' in data:
                inner_data = data['data']
                instructions = inner_data.get('search_by_raw_query', {}).get('search_timeline', {}).get('timeline', {}).get('instructions', [])

                for instruction in instructions:
                    if instruction.get('type') == 'TimelineAddEntries':
                        entries = instruction.get('entries', [])

                        for entry in entries:
                            content = entry.get('content', {})
                            entry_type = content.get('entryType')

                            if entry_type == 'TimelineTimelineItem':
                                item_content = content.get('itemContent', {})
                                item_type = item_content.get('itemType')

                                if item_type == 'TimelineTweet':
                                    tweet_results = item_content.get('tweet_results', {})
                                    tweet_result = tweet_results.get('result', {})
                                    typename = tweet_result.get('__typename')

                                    if tweet_result and typename == 'Tweet':
                                        tweets.append(tweet_result)

            if verbose:
                print(f"✅ 成功提取 {len(tweets)} 条推文")
            return tweets

        except Exception as e:
            if verbose:
                print(f"❌ 提取推文时出错: {e}")
            return []

    def extract_cursors_from_response(self, response_data):
        """Extract pagination cursors from the response"""
        try:
            data = response_data.get('data', {})
            if 'data' in data:
                inner_data = data['data']
                instructions = inner_data.get('search_by_raw_query', {}).get('search_timeline', {}).get('timeline', {}).get('instructions', [])

                cursors = {}
                for instruction in instructions:
                    if instruction.get('type') == 'TimelineAddEntries':
                        entries = instruction.get('entries', [])

                        for entry in entries:
                            content = entry.get('content', {})
                            if content.get('entryType') == 'TimelineTimelineCursor':
                                cursor_type = content.get('cursorType')
                                cursor_value = content.get('value')
                                if cursor_type and cursor_value:
                                    cursors[cursor_type.lower()] = cursor_value

                return cursors
            return {}

        except Exception as e:
            print(f"提取游标时出错: {e}")
            return {}

    def test_search_pattern(self, search_pattern, test_days=1):
        """Test a specific search pattern and return tweet count"""
        try:
            test_querystring = {
                "words": search_pattern,
                "apiKey": self.api_key,
                "resFormat": "json",
                "product": "Top",
                "since": (datetime.now() - timedelta(days=test_days)).strftime("%Y-%m-%d")
            }
            
            response = requests.get(self.url, headers=self.headers, params=test_querystring, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                tweets = self.extract_tweets_from_response(response_data, verbose=False)
                return len(tweets)
            else:
                return 0
                
        except Exception as e:
            return 0

    def determine_search_pattern(self, token_symbol):
        """Determine the best search pattern using simplified logic"""
        print(f"\n🔍 智能搜索模式检测: {token_symbol}")
        
        # Check cache first
        cache_key = token_symbol.upper()
        if cache_key in self.search_cache:
            cached_pattern = self.search_cache[cache_key]
            print(f"   💾 使用缓存的搜索模式: {cached_pattern}")
            return cached_pattern
        
        # Rule 1: Check if token contains numbers
        has_numbers = bool(re.search(r'\d', token_symbol))
        
        # Rule 2: Check length
        token_length = len(token_symbol)
        
        # Determine initial pattern based on rules
        if has_numbers:
            # If contains numbers (e.g., USD1, A8), use hashtag
            initial_pattern = f"#{token_symbol}"
            fallback_pattern = f"${token_symbol}"
            print(f"   📋 规则: 包含数字 → 优先使用 #{token_symbol}")
        elif token_length >= 7:
            # If >= 7 characters, use hashtag
            initial_pattern = f"#{token_symbol}"
            fallback_pattern = f"${token_symbol}"
            print(f"   📋 规则: 长度≥7字符 → 优先使用 #{token_symbol}")
        else:
            # If <= 6 characters and no numbers, use dollar sign
            initial_pattern = f"${token_symbol}"
            fallback_pattern = f"#{token_symbol}"
            print(f"   📋 规则: 长度≤6字符且无数字 → 优先使用 ${token_symbol}")
        
        # Test initial pattern
        print(f"   🧪 测试初始模式: '{initial_pattern}'...", end=" ")
        initial_count = self.test_search_pattern(initial_pattern)
        print(f"{initial_count} 条推文")
        
        if initial_count > 0:
            # Initial pattern works, use it
            print(f"   ✅ 初始模式有效，选择: '{initial_pattern}'")
            self.search_cache[cache_key] = initial_pattern
            return initial_pattern
        else:
            # Initial pattern failed, try fallback
            print(f"   ❌ 初始模式无推文，测试备用模式: '{fallback_pattern}'...", end=" ")
            fallback_count = self.test_search_pattern(fallback_pattern)
            print(f"{fallback_count} 条推文")
            
            if fallback_count > 0:
                print(f"   ✅ 备用模式有效，选择: '{fallback_pattern}'")
                self.search_cache[cache_key] = fallback_pattern
                return fallback_pattern
            else:
                # Both failed, use initial pattern as default
                print(f"   ⚠️ 两种模式均无推文，默认使用: '{initial_pattern}'")
                self.search_cache[cache_key] = initial_pattern
                return initial_pattern

    def determine_search_pattern_silent(self, token_symbol):
        """🆕 Silent version of search pattern detection"""
        # Check cache first
        cache_key = token_symbol.upper()
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]
        
        # Rule 1: Check if token contains numbers
        has_numbers = bool(re.search(r'\d', token_symbol))
        
        # Rule 2: Check length
        token_length = len(token_symbol)
        
        # Determine initial pattern based on rules
        if has_numbers:
            initial_pattern = f"#{token_symbol}"
            fallback_pattern = f"${token_symbol}"
        elif token_length >= 7:
            initial_pattern = f"#{token_symbol}"
            fallback_pattern = f"${token_symbol}"
        else:
            initial_pattern = f"${token_symbol}"
            fallback_pattern = f"#{token_symbol}"
        
        # Test initial pattern
        initial_count = self.test_search_pattern(initial_pattern)
        
        if initial_count > 0:
            self.search_cache[cache_key] = initial_pattern
            return initial_pattern
        else:
            # Test fallback
            fallback_count = self.test_search_pattern(fallback_pattern)
            
            if fallback_count > 0:
                self.search_cache[cache_key] = fallback_pattern
                return fallback_pattern
            else:
                # Both failed, use initial pattern as default
                self.search_cache[cache_key] = initial_pattern
                return initial_pattern

    def get_multiple_pages(self, base_querystring, max_pages=3):
        """Get multiple pages of results using pagination"""
        all_tweets = []
        current_querystring = base_querystring.copy()
        current_querystring['apiKey'] = self.api_key

        for page in range(max_pages):
            try:
                response = requests.get(self.url, headers=self.headers, params=current_querystring)

                if response.status_code != 200:
                    print(f"   ❌ API请求失败: {response.status_code}")
                    if response.status_code == 401:
                        print("   🔑 API认证失败 - 请检查API密钥")
                    elif response.status_code == 429:
                        print("   ⏰ API调用频率超限 - 请稍后再试")
                    break

                response_data = response.json()

                # Extract tweets from this page
                page_tweets = self.extract_tweets_from_response(response_data, verbose=False)
                if not page_tweets:
                    break

                all_tweets.extend(page_tweets)

                # Get cursors for next page
                cursors = self.extract_cursors_from_response(response_data)

                if 'bottom' in cursors:
                    current_querystring['cursor'] = cursors['bottom']
                else:
                    break

            except requests.exceptions.RequestException as e:
                print(f"   ❌ 网络请求错误: {e}")
                break
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON解析错误: {e}")
                break
            except Exception as e:
                print(f"   ❌ 获取推文时出错: {e}")
                break

        return all_tweets

    def get_multiple_pages_silent(self, base_querystring, max_pages=3):
        """🆕 Silent version of get_multiple_pages"""
        all_tweets = []
        current_querystring = base_querystring.copy()
        current_querystring['apiKey'] = self.api_key

        for page in range(max_pages):
            try:
                response = requests.get(self.url, headers=self.headers, params=current_querystring)

                if response.status_code != 200:
                    break

                response_data = response.json()
                page_tweets = self.extract_tweets_from_response(response_data, verbose=False)
                if not page_tweets:
                    break

                all_tweets.extend(page_tweets)

                # Get cursors for next page
                cursors = self.extract_cursors_from_response(response_data)

                if 'bottom' in cursors:
                    current_querystring['cursor'] = cursors['bottom']
                else:
                    break

            except:
                break

        return all_tweets

    def get_tweets_with_date_range(self, querystring_template, since_date, until_date=None, max_pages=3):
        """Get tweets for a specific date range"""
        querystring = querystring_template.copy()
        querystring["since"] = since_date
        if until_date:
            querystring["until"] = until_date
        
        print(f"📅 获取时间段: {since_date}" + (f" 到 {until_date}" if until_date else " 至今"))
        
        tweets = self.get_multiple_pages(querystring, max_pages)
        print(f"   ✅ 获取到 {len(tweets)} 条推文")
        return tweets

    def get_tweets_with_date_range_silent(self, querystring_template, since_date, until_date=None, max_pages=3):
        """🆕 Silent version of get_tweets_with_date_range"""
        querystring = querystring_template.copy()
        querystring["since"] = since_date
        if until_date:
            querystring["until"] = until_date
        
        tweets = self.get_multiple_pages_silent(querystring, max_pages)
        return tweets

    def get_tweets_multi_timeframe(self, querystring_template, total_days=7, max_pages_per_call=3):
        """Multi-timeframe tweet collection with smart search pattern"""
        print(f"🔄 使用多时间段策略获取 {total_days} 天的推文数据...")
        
        all_tweets = []
        tweet_ids_seen = set()  # To avoid duplicates
        
        # Calculate date ranges
        now = datetime.now()
        
        # Strategy: Split into multiple smaller time ranges
        if total_days <= 3:
            # For 3 days or less, use single call
            date_ranges = [
                (now - timedelta(days=total_days), None)
            ]
        elif total_days <= 7:
            # For 4-7 days, split into 2 calls
            mid_point = total_days // 2
            date_ranges = [
                (now - timedelta(days=mid_point), None),  # Recent half
                (now - timedelta(days=total_days), now - timedelta(days=mid_point))  # Older half
            ]
        else:
            # For more than 7 days, split into 3 calls
            third = total_days // 3
            date_ranges = [
                (now - timedelta(days=third), None),  # Most recent third
                (now - timedelta(days=third*2), now - timedelta(days=third)),  # Middle third
                (now - timedelta(days=total_days), now - timedelta(days=third*2))  # Oldest third
            ]
        
        print(f"📊 将分 {len(date_ranges)} 次API调用获取数据:")
        
        for i, (since_date, until_date) in enumerate(date_ranges, 1):
            print(f"\n🔍 第 {i}/{len(date_ranges)} 次API调用:")
            
            since_str = since_date.strftime("%Y-%m-%d")
            until_str = until_date.strftime("%Y-%m-%d") if until_date else None
            
            try:
                batch_tweets = self.get_tweets_with_date_range(
                    querystring_template, since_str, until_str, max_pages_per_call
                )
                
                # Remove duplicates by tweet ID
                new_tweets = []
                for tweet in batch_tweets:
                    try:
                        # Extract tweet ID for duplicate detection
                        tweet_id = (
                            tweet.get('rest_id') or 
                            tweet.get('legacy', {}).get('id_str') or
                            tweet.get('id_str') or
                            str(hash(str(tweet)))  # Fallback hash if no ID found
                        )
                        
                        if tweet_id not in tweet_ids_seen:
                            tweet_ids_seen.add(tweet_id)
                            new_tweets.append(tweet)
                    except Exception as e:
                        # If we can't extract ID, include the tweet anyway
                        new_tweets.append(tweet)
                
                all_tweets.extend(new_tweets)
                print(f"   📈 去重后新增: {len(new_tweets)} 条")
                
                # Add small delay between API calls to be respectful
                if i < len(date_ranges):
                    print("   ⏳ 等待 2 秒后进行下次调用...")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"   ❌ 第 {i} 次调用失败: {e}")
                continue
        
        print(f"\n🎯 多时间段获取完成:")
        print(f"   📊 总推文数: {len(all_tweets)} 条")
        print(f"   🔍 去重处理: 已去除重复推文")
        print(f"   📅 时间跨度: {total_days} 天")
        
        return all_tweets

    def get_tweets_multi_timeframe_silent(self, querystring_template, total_days=7, max_pages_per_call=3):
        """🆕 Silent version of multi-timeframe tweet collection"""
        all_tweets = []
        tweet_ids_seen = set()  # To avoid duplicates
        
        # Calculate date ranges
        now = datetime.now()
        
        if total_days <= 3:
            date_ranges = [(now - timedelta(days=total_days), None)]
        elif total_days <= 7:
            mid_point = total_days // 2
            date_ranges = [
                (now - timedelta(days=mid_point), None),
                (now - timedelta(days=total_days), now - timedelta(days=mid_point))
            ]
        else:
            third = total_days // 3
            date_ranges = [
                (now - timedelta(days=third), None),
                (now - timedelta(days=third*2), now - timedelta(days=third)),
                (now - timedelta(days=total_days), now - timedelta(days=third*2))
            ]
        
        for i, (since_date, until_date) in enumerate(date_ranges, 1):
            since_str = since_date.strftime("%Y-%m-%d")
            until_str = until_date.strftime("%Y-%m-%d") if until_date else None
            
            try:
                batch_tweets = self.get_tweets_with_date_range_silent(
                    querystring_template, since_str, until_str, max_pages_per_call
                )
                
                # Remove duplicates by tweet ID
                new_tweets = []
                for tweet in batch_tweets:
                    try:
                        tweet_id = (
                            tweet.get('rest_id') or 
                            tweet.get('legacy', {}).get('id_str') or
                            tweet.get('id_str') or
                            str(hash(str(tweet)))
                        )
                        
                        if tweet_id not in tweet_ids_seen:
                            tweet_ids_seen.add(tweet_id)
                            new_tweets.append(tweet)
                    except Exception:
                        new_tweets.append(tweet)
                
                all_tweets.extend(new_tweets)
                
                # Add small delay between API calls
                if i < len(date_ranges):
                    time.sleep(2)
                    
            except Exception:
                continue
        
        return all_tweets

    def create_smart_querystring(self, token_symbol, additional_filters=None):
        """Create querystring with simplified smart search pattern detection"""
        # Find the optimal search pattern
        optimal_search_term = self.determine_search_pattern(token_symbol)
        
        base_querystring = {
            "words": optimal_search_term,
            "resFormat": "json",
            "product": "Top",
        }
        
        if additional_filters:
            base_querystring.update(additional_filters)
        
        print(f"🎯 最终搜索词: '{optimal_search_term}'")
        return base_querystring

    def create_smart_querystring_silent(self, token_symbol, additional_filters=None):
        """🆕 Silent version of create_smart_querystring"""
        optimal_search_term = self.determine_search_pattern_silent(token_symbol)
        
        base_querystring = {
            "words": optimal_search_term,
            "resFormat": "json",
            "product": "Top",
        }
        
        if additional_filters:
            base_querystring.update(additional_filters)
        
        return base_querystring

    def create_base_querystring(self, token_symbol, additional_filters=None):
        """Enhanced base querystring creation with smart search"""
        return self.create_smart_querystring(token_symbol, additional_filters)
    
    def get_search_pattern_stats(self):
        """Get statistics about cached search patterns"""
        if not self.search_cache:
            return "无缓存的搜索模式"
        
        stats = {
            'dollar_patterns': 0,
            'hashtag_patterns': 0,
            'total': len(self.search_cache)
        }
        
        for pattern in self.search_cache.values():
            if pattern.startswith('$'):
                stats['dollar_patterns'] += 1
            elif pattern.startswith('#'):
                stats['hashtag_patterns'] += 1
        
        return f"搜索模式统计: ${stats['dollar_patterns']} 个, #{stats['hashtag_patterns']} 个 (共{stats['total']}个)"
    
    def show_search_rules_summary(self):
        """Show the search pattern rules"""
        print("\n📋 搜索模式规则:")
        print("   1️⃣ 包含数字 (如 USD1, A8) → 优先 #标签")
        print("   2️⃣ 长度≥7字符 (如 PUNDIAI) → 优先 #标签") 
        print("   3️⃣ 长度≤6字符且无数字 (如 BTC, ETH) → 优先 $符号")
        print("   4️⃣ 如初始模式无推文 → 自动尝试备用模式")
        print("   5️⃣ 成功模式会被缓存，避免重复测试")