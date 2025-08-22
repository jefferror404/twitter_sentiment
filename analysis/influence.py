# analysis/influence.py
"""
User influence scoring and viral index calculation
"""

import math
from config import INFLUENCE_TIERS, VERIFICATION_BONUS


class InfluenceCalculator:
    def __init__(self):
        self.influence_tiers = INFLUENCE_TIERS
        self.verification_bonus = VERIFICATION_BONUS
    
    def calculate_influence_score(self, user_data):
        """Calculate user influence score based on followers and verification"""
        followers = user_data.get('followers_count', 0)
        is_verified = user_data.get('verified', False)
        is_blue_verified = user_data.get('blue_verified', False)
        
        base_weight = 0.5
        for tier_name, tier_info in self.influence_tiers.items():
            if followers >= tier_info['min_followers']:
                base_weight = tier_info['weight']
                break
        
        multiplier = 1.0
        if is_verified:
            multiplier *= self.verification_bonus['legacy_verified']
        if is_blue_verified:
            multiplier *= self.verification_bonus['blue_verified']
        
        influence_score = base_weight * multiplier
        
        return {
            'influence_score': round(influence_score, 2),
            'base_weight': base_weight,
            'verification_multiplier': round(multiplier, 2),
            'followers_tier': self._get_followers_tier(followers)
        }

    def _get_followers_tier(self, followers):
        """Get readable follower tier description"""
        if followers >= 100000:
            return f"Tier 1 (100K+): {followers:,}"
        elif followers >= 10000:
            return f"Tier 2 (10K+): {followers:,}"
        elif followers >= 1000:
            return f"Tier 3 (1K+): {followers:,}"
        else:
            return f"Tier 4 (<1K): {followers:,}"

    def calculate_viral_index(self, metrics):
        """Calculate viral/propagation index using engagement metrics"""
        retweets = metrics.get('retweets', 0)
        likes = metrics.get('likes', 0)
        replies = metrics.get('replies', 0)
        views = metrics.get('views', 0)
        
        if isinstance(views, str) and views != 'N/A':
            try:
                views = int(views.replace(',', ''))
            except:
                views = 0
        elif views == 'N/A':
            views = 0
        
        viral_index = (
            math.log(retweets + 1) * 0.4 +
            math.log(likes + 1) * 0.3 +
            math.log(replies + 1) * 0.3
        )
        
        if views > 0:
            views_bonus = math.log(views + 1) * 0.1
            viral_index += views_bonus
        
        return {
            'viral_index': round(viral_index, 2),
            'engagement_breakdown': {
                'retweets_score': round(math.log(retweets + 1) * 0.4, 2),
                'likes_score': round(math.log(likes + 1) * 0.3, 2),
                'replies_score': round(math.log(replies + 1) * 0.3, 2),
                'views_bonus': round(math.log(views + 1) * 0.1, 2) if views > 0 else 0
            },
            'raw_engagement': {
                'retweets': retweets,
                'likes': likes,
                'replies': replies,
                'views': views
            }
        }

    def calculate_weighted_sentiment_impact(self, sentiment_result, influence_score, viral_index):
        """Calculate the weighted impact of a tweet on overall sentiment"""
        base_sentiment = sentiment_result['sentiment_score']
        confidence = sentiment_result['confidence']
        
        weighted_impact = base_sentiment * influence_score * (1 + viral_index/10) * (1 + confidence/5)
        
        return {
            'weighted_impact': round(weighted_impact, 2),
            'impact_factors': {
                'base_sentiment': base_sentiment,
                'influence_multiplier': influence_score,
                'viral_multiplier': round(1 + viral_index/10, 2),
                'confidence_multiplier': round(1 + confidence/5, 2)
            }
        }