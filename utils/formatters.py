# utils/formatters.py (Enhanced with Clean Output)
"""
Enhanced output formatting with clean simplified output
"""

from .tweet_parser import TweetParser


class ReportFormatter:
    def __init__(self):
        self.tweet_parser = TweetParser()
    
    def print_table_header(self, columns, widths):
        """Helper function to print table headers"""
        header = "   "
        separator = "   "
        for i, (col, width) in enumerate(zip(columns, widths)):
            header += f"{col:<{width}}"
            separator += "-" * width
            if i < len(columns) - 1:
                header += " | "
                separator += "-|-"
        print(header)
        print(separator)

    def print_table_row(self, values, widths):
        """Helper function to print table rows"""
        row = "   "
        for i, (val, width) in enumerate(zip(values, widths)):
            val_str = str(val)
            if len(val_str) > width:
                val_str = val_str[:width-3] + "..."
            row += f"{val_str:<{width}}"
            if i < len(values) - 1:
                row += " | "
        print(row)

    def print_clean_report(self, token, total_tweets, effective_tweets, sentiment_summary, 
                          high_influence_tweets, viral_tweets, tweet_analyses, original_tweets, result,
                          generate_summary_func, tweets_for_summary, target_days):
        """🆕 Clean, simplified report format"""
        
        # 🆕 Updated header format
        print(f'🔍 "{token}" 近{target_days}天推文情感分析')
        print(f"原获取推文数量: {total_tweets}; 过滤后有效推文: {effective_tweets}")
        
        # Price data overview
        price_stats = result.get('price_aware_stats', {})
        if price_stats.get('price_data_available') and price_stats.get('price_context'):
            price_data = price_stats['price_context']
            print(f"💰 站内数据总览:")  # 🆕 Updated label
            print(f"   💵 当前价格: ${price_data['price_usd']:.6f}")
            print(f"   📈 24H变化: {price_data['change_rate']:+.2%}")
            print(f"   💧 24H交易量: ${price_data['volume_usd']:,.0f}")
        else:
            print("💰 站内数据总览:")  # 🆕 Updated label
            print("   💰 价格数据: 未获取到有效数据")
        
        print()
        
        # Sentiment distribution (keep entirely)
        total = sum(sentiment_summary.values())
        pos_pct = (sentiment_summary['POSITIVE'] / total * 100) if total > 0 else 0
        neg_pct = (sentiment_summary['NEGATIVE'] / total * 100) if total > 0 else 0
        neu_pct = (sentiment_summary['NEUTRAL'] / total * 100) if total > 0 else 0
        
        print(f"🎭 情绪分布:")
        print(f"   ✅ 正面: {sentiment_summary['POSITIVE']} 条 ({pos_pct:.1f}%)")
        print(f"   ❌ 负面: {sentiment_summary['NEGATIVE']} 条 ({neg_pct:.1f}%)")
        print(f"   ⚪ 中性: {sentiment_summary['NEUTRAL']} 条 ({neu_pct:.1f}%)")
        
        # 🆕 Remove AI analysis success rate lines
        # No longer showing:
        # - AI分析成功
        # - 价格感知分析
        
        # AI summary (keep entirely)
        print(f"\n🤖 AI 智能分析摘要:")
        print("   " + "="*50)
        try:
            ai_summary = generate_summary_func(tweets_for_summary, token)
            summary_lines = ai_summary.split('\n')
            for line in summary_lines:
                if line.strip():
                    print(f"   {line}")
            print("   " + "="*50)
        except Exception as e:
            print(f"   AI摘要生成失败: {e}")
        
        # 🆕 Simplified Topic analysis (remove sentiment breakdown)
        print(f"\n📈 热门话题榜:")
        bulk_topics = result.get('bulk_topics', [])
        
        if bulk_topics:
            print("   AI智能话题分析:")
            for i, topic in enumerate(bulk_topics[:6]):
                bar = '█' * min(int(topic['count']/2), 8) + '▁' * max(0, 8 - int(topic['count']/2))
                # 🆕 Remove the [主要:积极 20/6] part
                print(f"   {i+1:2d}. {topic['name']:<15} {bar} ({topic['count']}条)")
        else:
            print("   暂无话题分析结果")
        
        # High influence tweets and viral tweets (keep entirely)
        print(f"\n🔥 病毒式传播推文 (传播力≥5.0):")
        if viral_tweets:
            sorted_viral = sorted(viral_tweets, key=lambda x: x['viral']['viral_index'], reverse=True)[:6]
            
            # 🆕 Increased width for topic column
            columns = ["用户名", "传播力", "点赞", "转推", "回复", "情绪", "话题", "推文链接"]
            widths = [12, 8, 8, 8, 8, 8, 25, 45]  # Increased topic width from 18 to 25
            
            self.print_table_header(columns, widths)
            
            for tweet in sorted_viral:
                engagement = tweet['engagement']
                tweet_topic = tweet.get('topic', '未分类')
                
                original_tweet = None
                for orig_tweet in original_tweets:
                    parsed_orig = self.tweet_parser.parse_tweet_data(orig_tweet)
                    if parsed_orig['tweet_id'] == tweet['tweet_id']:
                        original_tweet = orig_tweet
                        break
                
                full_tweet_id = self.tweet_parser.extract_tweet_id_for_link(original_tweet) if original_tweet else tweet['tweet_id']
                tweet_link = self.tweet_parser.create_tweet_link(full_tweet_id)
                
                values = [
                    f"@{tweet['user']}",
                    f"{tweet['viral']['viral_index']:.1f}",
                    f"{engagement['likes']:,}",
                    f"{engagement['retweets']:,}",
                    f"{engagement['replies']:,}",
                    tweet['sentiment']['sentiment'],
                    tweet_topic,  # 🆕 Full topic name without truncation
                    tweet_link
                ]
                self.print_table_row(values, widths)
        else:
            print("   暂无符合条件的病毒式传播推文")
        
        # High influence tweets
        print(f"\n👑 高影响力用户动态 (影响力≥1.0):")
        if high_influence_tweets:
            sorted_influence = sorted(high_influence_tweets, key=lambda x: x['influence']['influence_score'], reverse=True)[:8]
            
            # 🆕 Increased width for topic column
            columns = ["用户名", "影响力", "粉丝数", "情绪", "传播力", "话题", "推文链接"]
            widths = [12, 8, 10, 8, 8, 25, 45]  # Increased topic width from 18 to 25
            
            self.print_table_header(columns, widths)
            
            for tweet in sorted_influence:
                followers = tweet['influence']['followers_tier'].split(': ')[1] if ': ' in tweet['influence']['followers_tier'] else str(tweet['user'])
                tweet_topic = tweet.get('topic', '未分类')
                
                original_tweet = None
                for orig_tweet in original_tweets:
                    parsed_orig = self.tweet_parser.parse_tweet_data(orig_tweet)
                    if parsed_orig['tweet_id'] == tweet['tweet_id']:
                        original_tweet = orig_tweet
                        break
                
                full_tweet_id = self.tweet_parser.extract_tweet_id_for_link(original_tweet) if original_tweet else tweet['tweet_id']
                tweet_link = self.tweet_parser.create_tweet_link(full_tweet_id)
                
                values = [
                    f"@{tweet['user']}",
                    f"{tweet['influence']['influence_score']:.1f}",
                    followers,
                    tweet['sentiment']['sentiment'],
                    f"{tweet['viral']['viral_index']:.1f}",
                    tweet_topic,  # 🆕 Full topic name without truncation
                    tweet_link
                ]
                self.print_table_row(values, widths)
        else:
            print("   暂无符合条件的高影响力用户推文")

    def print_filtered_tweets_table(self, exclusion_reasons, original_tweets):
        """Print detailed table of filtered tweets with wider AI columns (keep logic but don't show)"""
        # Keep all the logic for internal processing but don't print anything
        # This maintains the functionality for debugging purposes if needed
        
        if not exclusion_reasons:
            return
        
        # Enhanced grouping with team accounts (logic preserved)
        filter_groups = {
            '新闻账户': [],
            '团队账户': [],
            '基础垃圾': [],
            'AI垃圾': [],
            'AI信息': []
        }
        
        for reason in exclusion_reasons:
            if "News account" in reason['reason']:
                filter_groups['新闻账户'].append(reason)
            elif "Team account" in reason['reason']:
                filter_groups['团队账户'].append(reason)
            elif "Basic spam" in reason['reason']:
                filter_groups['基础垃圾'].append(reason)
            elif "AI spam" in reason['reason']:
                filter_groups['AI垃圾'].append(reason)
            elif "AI informative" in reason['reason']:
                filter_groups['AI信息'].append(reason)
        
        # Logic is preserved but output is suppressed
        # This can be re-enabled for debugging by uncommenting the print statements below
        
        """
        print(f"\n🔍 已过滤推文详情表 (共 {len(exclusion_reasons)} 条):")
        print("=" * 140)
        
        # Print each group
        for filter_type, filtered_tweets in filter_groups.items():
            if not filtered_tweets:
                continue
                
            print(f"\n📋 {filter_type} 过滤 ({len(filtered_tweets)} 条):")
            
            if filter_type in ['新闻账户', '团队账户', '基础垃圾']:
                columns = ["#", "用户名", "粉丝数", "推文预览", "推文链接"]
                widths = [3, 15, 8, 35, 45]
            else:
                columns = ["#", "用户名", "AI判断", "推文预览", "推文链接"]
                widths = [3, 15, 20, 30, 45]
            
            self.print_table_header(columns, widths)
            
            for reason in filtered_tweets:
                # Find the original tweet to get the full ID
                original_tweet = None
                for orig_tweet in original_tweets:
                    try:
                        parsed_orig = self.tweet_parser.parse_tweet_data(orig_tweet)
                        if (parsed_orig['user']['username'] == reason['user'] and 
                            reason['full_text'][:50] in parsed_orig['text']):
                            original_tweet = orig_tweet
                            break
                    except:
                        continue
                
                full_tweet_id = self.tweet_parser.extract_tweet_id_for_link(original_tweet) if original_tweet else "N/A"
                tweet_link = self.tweet_parser.create_tweet_link(full_tweet_id)
                
                text_preview = reason['text_preview']
                max_preview_len = 35 if filter_type in ['新闻账户', '团队账户', '基础垃圾'] else 30
                if len(text_preview) > max_preview_len:
                    text_preview = text_preview[:max_preview_len-3] + "..."
                
                if filter_type in ['新闻账户', '团队账户', '基础垃圾']:
                    values = [
                        str(reason['tweet_num']),
                        f"@{reason['user']}",
                        f"{reason['followers']:,}",
                        text_preview,
                        tweet_link
                    ]
                else:
                    ai_reason = reason['detailed_reason']
                    if len(ai_reason) > 20:
                        ai_reason = ai_reason[:17] + "..."
                    
                    values = [
                        str(reason['tweet_num']),
                        f"@{reason['user']}",
                        ai_reason,
                        text_preview,
                        tweet_link
                    ]
                
                self.print_table_row(values, widths)
        
        print(f"\n💡 验证提示: 点击推文链接可查看完整内容，验证过滤准确性")
        print("=" * 140)
        """

    def print_enhanced_report(self, token, tweet_count, sentiment_summary, total_weighted_impact,
                             high_influence_tweets, viral_tweets, tweet_analyses, original_tweets, result,
                             generate_summary_func, tweets_for_summary):
        """Enhanced report with team filtering statistics (original verbose version for debugging)"""
        
        print(f"\n📋 {token} 价格感知情绪分析报告")
        print("=" * 80)
        
        # Price awareness summary
        price_stats = result.get('price_aware_stats', {})
        if price_stats.get('price_data_available') and price_stats.get('price_context'):
            price_data = price_stats['price_context']
            print(f"💰 价格数据总览:")
            print(f"   💵 当前价格: ${price_data['price_usd']:.6f}")
            print(f"   📈 24H变化: {price_data['change_rate']:+.2%}")
            print(f"   💧 24H交易量: ${price_data['volume_usd']:,.0f}")
            print(f"   🎯 价格影响分析: {price_stats['price_influenced_count']}/{len(tweet_analyses)} 条 ({price_stats['price_influence_rate']*100:.1f}%)")
            
            # Price impact description
            abs_change = abs(price_data['change_rate'])
            if abs_change > 0.1:
                print(f"   ⚡ 价格剧烈波动对情感分析产生显著影响")
            elif abs_change > 0.05:
                print(f"   📊 价格明显波动适度影响情感解读")
            else:
                print(f"   😐 价格相对稳定，主要基于原始情感")
        else:
            print(f"💰 价格数据: 未获取到有效数据，使用标准情感分析")
        
        print()
        
        # Enhanced filtering summary with team filtering
        filtering_stats = result.get('filtering_stats', {})
        team_filter_stats = result.get('team_filter_stats', {})
        
        print(f"🔍 数据质量统计:")
        print(f"   📥 原始推文: {tweet_count + filtering_stats.get('total_filtered', 0)} 条")
        print(f"   🗞️  新闻过滤: {filtering_stats.get('news_accounts', 0)} 条")
        
        # Show team filtering if enabled
        if team_filter_stats.get('enabled', False):
            team_filtered = filtering_stats.get('team_accounts', 0)
            print(f"   👥 团队过滤: {team_filtered} 条")
            if team_filter_stats.get('is_loaded', False):
                print(f"      📊 团队数据库: {team_filter_stats.get('total_projects', 0)} 个项目")
        
        print(f"   🚫 垃圾过滤: {filtering_stats.get('spam_basic', 0) + filtering_stats.get('spam_ai', 0)} 条")
        print(f"   📰 信息过滤: {filtering_stats.get('informative_ai', 0)} 条")
        print(f"   ✅ 有效分析: {tweet_count} 条 ({tweet_count/(tweet_count + filtering_stats.get('total_filtered', 0))*100:.1f}%)")
        print()
        
        total = sum(sentiment_summary.values())
        pos_pct = (sentiment_summary['POSITIVE'] / total * 100) if total > 0 else 0
        neg_pct = (sentiment_summary['NEGATIVE'] / total * 100) if total > 0 else 0
        neu_pct = (sentiment_summary['NEUTRAL'] / total * 100) if total > 0 else 0
        
        print(f"🎭 情绪分布:")
        print(f"   ✅ 正面: {sentiment_summary['POSITIVE']} 条 ({pos_pct:.1f}%)")
        print(f"   ❌ 负面: {sentiment_summary['NEGATIVE']} 条 ({neg_pct:.1f}%)")
        print(f"   ⚪ 中性: {sentiment_summary['NEUTRAL']} 条 ({neu_pct:.1f}%)")
        
        # Add analysis success rate
        openai_success = 0
        price_aware_success = 0
        for tweet in tweet_analyses:
            if tweet['sentiment']['openai_analysis']:
                openai_success += 1
            if tweet['sentiment'].get('price_influenced', False):
                price_aware_success += 1
        
        print(f"   📊 AI分析成功: {openai_success}/{len(tweet_analyses)} 条 ({openai_success/len(tweet_analyses)*100:.1f}%)")
        if price_stats.get('price_data_available'):
            print(f"   💰 价格感知分析: {price_aware_success}/{len(tweet_analyses)} 条 ({price_aware_success/len(tweet_analyses)*100:.1f}%)")
        
        # Add neutral tweets table with sentiment-aware topics
        neutral_tweets = [t for t in tweet_analyses if t['sentiment']['sentiment'] == 'NEUTRAL']
        if neutral_tweets and len(neutral_tweets) > 0:
            print(f"\n⚪ 中性情绪推文详情:")
            
            columns = ["用户名", "话题", "价格影响", "推文链接"]
            widths = [15, 20, 10, 45]
            
            self.print_table_header(columns, widths)
            
            for tweet in neutral_tweets[:8]:
                tweet_topic = tweet.get('topic', '未分类')
                price_influenced = "是" if tweet['sentiment'].get('price_influenced', False) else "否"
                
                original_tweet = None
                for orig_tweet in original_tweets:
                    parsed_orig = self.tweet_parser.parse_tweet_data(orig_tweet)
                    if parsed_orig['tweet_id'] == tweet['tweet_id']:
                        original_tweet = orig_tweet
                        break
                
                full_tweet_id = self.tweet_parser.extract_tweet_id_for_link(original_tweet) if original_tweet else tweet['tweet_id']
                tweet_link = self.tweet_parser.create_tweet_link(full_tweet_id)
                
                values = [
                    f"@{tweet['user']}",
                    tweet_topic,
                    price_influenced,
                    tweet_link
                ]
                self.print_table_row(values, widths)
        
        print(f"\n🤖 AI 智能分析摘要:")
        print("   " + "="*50)
        try:
            ai_summary = generate_summary_func(tweets_for_summary, token)
            summary_lines = ai_summary.split('\n')
            for line in summary_lines:
                if line.strip():
                    print(f"   {line}")
            print("   " + "="*50)
        except Exception as e:
            print(f"   AI摘要生成失败: {e}")
        
        # Enhanced Topic analysis with sentiment
        print(f"\n📈 热门话题榜 (含情感方向):")
        bulk_topics = result.get('bulk_topics', [])
        topic_sentiment_analysis = result.get('topic_sentiment_analysis', {})
        
        if bulk_topics:
            print("   AI智能话题分析:")
            for i, topic in enumerate(bulk_topics[:6]):
                bar = '█' * min(int(topic['count']/2), 8) + '▁' * max(0, 8 - int(topic['count']/2))
                
                # Get sentiment distribution for this topic if available
                sentiment_info = ""
                if topic['name'] in topic_sentiment_analysis:
                    topic_stats = topic_sentiment_analysis[topic['name']]
                    pos_count = topic_stats.get('POSITIVE', 0)
                    neg_count = topic_stats.get('NEGATIVE', 0)
                    neu_count = topic_stats.get('NEUTRAL', 0)
                    
                    # Show dominant sentiment
                    if pos_count > neg_count and pos_count > neu_count:
                        sentiment_info = f" [主要:积极 {pos_count}/{topic['count']}]"
                    elif neg_count > pos_count and neg_count > neu_count:
                        sentiment_info = f" [主要:消极 {neg_count}/{topic['count']}]"
                    elif neu_count > 0:
                        sentiment_info = f" [主要:中性 {neu_count}/{topic['count']}]"
                
                print(f"   {i+1:2d}. {topic['name']:<15} {bar} ({topic['count']}条){sentiment_info}")
        else:
            print("   暂无话题分析结果")
        
        # Enhanced Viral tweets with sentiment-aware topics
        print(f"\n🔥 病毒式传播推文 (传播力≥5.0):")
        if viral_tweets:
            sorted_viral = sorted(viral_tweets, key=lambda x: x['viral']['viral_index'], reverse=True)[:6]
            
            columns = ["用户名", "传播力", "点赞", "转推", "回复", "情绪", "话题", "推文链接"]
            widths = [12, 8, 8, 8, 8, 8, 18, 45]
            
            self.print_table_header(columns, widths)
            
            for tweet in sorted_viral:
                engagement = tweet['engagement']
                tweet_topic = tweet.get('topic', '未分类')
                
                original_tweet = None
                for orig_tweet in original_tweets:
                    parsed_orig = self.tweet_parser.parse_tweet_data(orig_tweet)
                    if parsed_orig['tweet_id'] == tweet['tweet_id']:
                        original_tweet = orig_tweet
                        break
                
                full_tweet_id = self.tweet_parser.extract_tweet_id_for_link(original_tweet) if original_tweet else tweet['tweet_id']
                tweet_link = self.tweet_parser.create_tweet_link(full_tweet_id)
                
                values = [
                    f"@{tweet['user']}",
                    f"{tweet['viral']['viral_index']:.1f}",
                    f"{engagement['likes']:,}",
                    f"{engagement['retweets']:,}",
                    f"{engagement['replies']:,}",
                    tweet['sentiment']['sentiment'],
                    tweet_topic,
                    tweet_link
                ]
                self.print_table_row(values, widths)
        else:
            print("   暂无符合条件的病毒式传播推文")
        
        # Enhanced High influence tweets with sentiment-aware topics
        print(f"\n👑 高影响力用户动态 (影响力≥1.0):")
        if high_influence_tweets:
            sorted_influence = sorted(high_influence_tweets, key=lambda x: x['influence']['influence_score'], reverse=True)[:8]
            
            columns = ["用户名", "影响力", "粉丝数", "情绪", "传播力", "话题", "推文链接"]
            widths = [12, 8, 10, 8, 8, 18, 45]
            
            self.print_table_header(columns, widths)
            
            for tweet in sorted_influence:
                followers = tweet['influence']['followers_tier'].split(': ')[1] if ': ' in tweet['influence']['followers_tier'] else str(tweet['user'])
                tweet_topic = tweet.get('topic', '未分类')
                
                original_tweet = None
                for orig_tweet in original_tweets:
                    parsed_orig = self.tweet_parser.parse_tweet_data(orig_tweet)
                    if parsed_orig['tweet_id'] == tweet['tweet_id']:
                        original_tweet = orig_tweet
                        break
                
                full_tweet_id = self.tweet_parser.extract_tweet_id_for_link(original_tweet) if original_tweet else tweet['tweet_id']
                tweet_link = self.tweet_parser.create_tweet_link(full_tweet_id)
                
                values = [
                    f"@{tweet['user']}",
                    f"{tweet['influence']['influence_score']:.1f}",
                    followers,
                    tweet['sentiment']['sentiment'],
                    f"{tweet['viral']['viral_index']:.1f}",
                    tweet_topic,
                    tweet_link
                ]
                self.print_table_row(values, widths)
        else:
            print("   暂无符合条件的高影响力用户推文")
        
        # Show detailed filtered tweets table if available (keep logic but suppress output)
        exclusion_reasons = result.get('exclusion_reasons', [])
        if exclusion_reasons:
            self.print_filtered_tweets_table(exclusion_reasons, original_tweets)
        
        print(f"\n{'='*80}")
        
        # OpenAI token usage summary (commented out for clean output)
        """
        total_tokens_used = result.get('total_tokens_used', 0)
        if total_tokens_used > 0:
            estimated_cost = (total_tokens_used * 0.375) / 1000000
            
            print(f"💰 OpenAI API使用统计:")
            print(f"   🔢 总Tokens消耗: {total_tokens_used:,}")
            print(f"   💵 预估费用: ${estimated_cost:.4f} USD")
            print(f"   📝 模型: gpt-4o-mini")
            print(f"   🔍 过滤调用: ~{filtering_stats.get('spam_ai', 0) + filtering_stats.get('informative_ai', 0)} 次")
            print(f"   📊 分析调用: ~{len(tweet_analyses)} 次")
            if price_stats.get('price_data_available'):
                print(f"   💰 价格感知增强: {price_stats['price_influenced_count']} 条推文")
            print(f"\n{'='*80}")
        """