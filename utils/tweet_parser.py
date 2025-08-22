# utils/tweet_parser.py
"""
Tweet data parsing utilities
"""


class TweetParser:
    def __init__(self):
        pass
    
    def parse_tweet_data(self, tweet):
        """Parse tweet data - enhanced for error handling"""
        try:
            legacy = tweet.get('legacy', {})
            
            parsed = {
                'tweet_id': legacy.get('id_str', tweet.get('rest_id', 'N/A')),
                'text': legacy.get('full_text', legacy.get('text', 'N/A')),
                'created_at': legacy.get('created_at', 'N/A')
            }
            
            core = tweet.get('core', {})
            user_results = core.get('user_results', {})
            user_result = user_results.get('result', {})
            user_legacy = user_result.get('legacy', {})
            
            parsed['user'] = {
                'username': user_legacy.get('screen_name', 'N/A'),
                'display_name': user_legacy.get('name', 'N/A'),
                'followers_count': user_legacy.get('followers_count', 0),
                'verified': user_legacy.get('verified', False),
                'blue_verified': user_result.get('is_blue_verified', False)
            }
            
            parsed['metrics'] = {
                'likes': legacy.get('favorite_count', 0),
                'retweets': legacy.get('retweet_count', 0),
                'replies': legacy.get('reply_count', 0),
                'quotes': legacy.get('quote_count', 0),
                'bookmarks': legacy.get('bookmark_count', 0),
                'views': tweet.get('views', {}).get('count', 0)
            }
            
            entities = legacy.get('entities', {})
            parsed['hashtags'] = [tag['text'] for tag in entities.get('hashtags', [])]
            parsed['mentions'] = [mention['screen_name'] for mention in entities.get('user_mentions', [])]
            parsed['urls'] = [url['expanded_url'] for url in entities.get('urls', []) if url.get('expanded_url')]
            
            return parsed
            
        except Exception as e:
            return {
                'tweet_id': 'ERROR',
                'text': f'Error parsing tweet: {str(e)}',
                'user': {'username': 'ERROR', 'display_name': 'ERROR', 'followers_count': 0, 'verified': False, 'blue_verified': False},
                'metrics': {'likes': 0, 'retweets': 0, 'replies': 0, 'quotes': 0, 'bookmarks': 0, 'views': 0},
                'hashtags': [], 'mentions': [], 'urls': []
            }
    
    def extract_tweet_id_for_link(self, tweet):
        """Extract the full tweet ID for creating links"""
        try:
            return (
                tweet.get('rest_id') or 
                tweet.get('legacy', {}).get('id_str') or
                tweet.get('id_str') or
                'N/A'
            )
        except:
            return 'N/A'
    
    def create_tweet_link(self, tweet_id):
        """Create Twitter/X link from tweet ID"""
        if tweet_id and tweet_id != 'N/A' and tweet_id != 'ERROR':
            return f"https://x.com/i/status/{tweet_id}"
        return "无法获取"