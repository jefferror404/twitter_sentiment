# main.py (Enhanced with User Input & Clean Output)
"""
Enhanced main execution script with user input and simplified output
"""

import sys
from api.twitter_api import TwitterAPI
from analysis.sentiment import CryptoSentimentAnalyzer
from config import ANALYSIS_CONFIG, OPENAI_API_KEY, SMART_SEARCH_CONFIG
from utils.helpers import calculate_percentage


def get_token_input():
    """Get token symbol from user input (simplified)"""
    # Check if token provided as command line argument
    if len(sys.argv) > 1:
        token_symbol = sys.argv[1].upper().strip()
        return token_symbol
    
    # Interactive input if no argument provided
    while True:
        try:
            token_symbol = input("请输入要分析的代币符号 (如 BTC, ETH, PUNDIAI): ").strip().upper()
            if token_symbol:
                return token_symbol
            else:
                print("❌ 请输入有效的代币符号")
        except KeyboardInterrupt:
            print("\n👋 分析已取消")
            sys.exit(0)
        except Exception as e:
            print(f"❌ 输入错误: {e}")


def main():
    try:
        # 🆕 Get token symbol from user (no verbose startup messages)
        token_symbol = get_token_input()
        
        # Configuration
        target_days = ANALYSIS_CONFIG['target_days']
        max_pages_per_call = ANALYSIS_CONFIG['max_pages_per_call']
        
        # Initialize Twitter API and analyzer (silent mode)
        twitter_api = TwitterAPI()
        analyzer = CryptoSentimentAnalyzer(openai_api_key=OPENAI_API_KEY, silent_mode=True)
        
        # Create smart querystring (silent mode)
        base_querystring = twitter_api.create_smart_querystring_silent(
            token_symbol,
            additional_filters={}
        )
        
        # Get tweets (silent mode)
        all_tweets = twitter_api.get_tweets_multi_timeframe_silent(
            base_querystring, 
            total_days=target_days, 
            max_pages_per_call=max_pages_per_call
        )
        
        if all_tweets:
            # Run analysis (silent mode)
            analysis_result = analyzer.comprehensive_analysis_silent(all_tweets, token_symbol, target_days)
            
            if analysis_result:
                # Analysis successful - output is handled in the analyzer
                pass
            else:
                # 🆕 Handle case where filtering removes all tweets
                print(f'🔍 "{token_symbol}" 近{target_days}天推文情感分析')
                print(f"原获取推文数量: {len(all_tweets)}; 过滤后有效推文: 0")
                print("❌ 过滤后无可分析推文，请检查其他社群资讯")
            
        else:
            # 🆕 Handle case where no tweets found
            print(f'🔍 "{token_symbol}" 近{target_days}天推文情感分析')
            print(f"原获取推文数量: 0; 过滤后有效推文: 0")
            print("❌ 过滤后无可分析推文，请检查其他社群资讯")
            
    except Exception as e:
        print(f"💥 程序执行出错: {e}")
        print(f"错误类型: {type(e).__name__}")


def quick_test():
    """Quick test function for multiple tokens"""
    tokens = ["BTC", "ETH", "SOL", "PUNDIAI"]
    
    for token in tokens:
        print(f"\n{'='*60}")
        print(f"🧪 测试分析: {token}")
        print('='*60)
        
        try:
            twitter_api = TwitterAPI()
            analyzer = CryptoSentimentAnalyzer(openai_api_key=OPENAI_API_KEY)
            
            # Create querystring
            base_querystring = twitter_api.create_smart_querystring_silent(token)
            
            # Get tweets
            tweets = twitter_api.get_tweets_multi_timeframe_silent(
                base_querystring, 
                total_days=3,  # Shorter for testing
                max_pages_per_call=2
            )
            
            if tweets:
                # Run analysis
                result = analyzer.comprehensive_analysis_silent(tweets, token, 3)
                if result:
                    print(f"✅ {token} 分析成功")
                else:
                    print(f"❌ {token} 分析失败")
            else:
                print(f"❌ {token} 无推文")
                
        except Exception as e:
            print(f"❌ {token} 测试失败: {e}")


if __name__ == "__main__":
    # Check if running in test mode
    if len(sys.argv) > 1 and sys.argv[1].lower() == "test":
        quick_test()
    else:
        main()
    
    # Usage examples:
    # python3 main.py              # Interactive mode
    # python3 main.py BTC          # Direct analysis of BTC
    # python3 main.py PUNDIAI      # Direct analysis of PUNDIAI  
    # python3 main.py test         # Test multiple tokens