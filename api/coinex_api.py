# api/coinex_api.py
"""
CoinEx API integration for fetching price data
"""

import requests
from config import COINEX_API_URL


class CoinExAPI:
    def __init__(self):
        self.base_url = COINEX_API_URL
    
    def get_price_context(self, token_symbol):
        """Get price context from CoinEx API"""
        try:
            url = f"{self.base_url}/{token_symbol.upper()}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 and 'data' in data:
                    price_info = data['data']
                    price_context = {
                        'token': price_info.get('short_name', token_symbol),
                        'price_usd': float(price_info.get('price_usd', 0)),
                        'change_rate': float(price_info.get('change_rate', 0)),
                        'volume_usd': float(price_info.get('volume_usd', 0)),
                        'circulation_usd': float(price_info.get('circulation_usd', 0))
                    }
                    
                    print(f"💰 获取价格数据: ${price_context['price_usd']:.6f} (24H: {price_context['change_rate']:+.2%})")
                    
                    # Show price movement significance
                    abs_change = abs(price_context['change_rate'])
                    if abs_change > 0.1:
                        print(f"⚡ 检测到剧烈价格波动 (>10%)，将显著影响情感解读")
                    elif abs_change > 0.05:
                        print(f"📈 检测到明显价格波动 (>5%)，将适度影响情感解读")
                    elif abs_change < 0.02:
                        print(f"😐 价格相对稳定 (<2%)，主要基于原始情感分析")
                    
                    return price_context
                else:
                    print(f"❌ CoinEx API返回错误: {data.get('message', 'Unknown error')}")
            else:
                print(f"❌ CoinEx API请求失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ 无法获取价格数据: {e}")
        
        print("📊 将使用标准情感分析（无价格增强）")
        return None
    
    def analyze_price_movement_significance(self, price_context):
        """Analyze the significance of price movement"""
        if not price_context:
            return None
        
        abs_change = abs(price_context['change_rate'])
        
        if abs_change > 0.1:
            return {
                'significance': 'high',
                'description': '剧烈波动',
                'impact_level': 'significant'
            }
        elif abs_change > 0.05:
            return {
                'significance': 'medium',
                'description': '明显波动',
                'impact_level': 'moderate'
            }
        elif abs_change > 0.02:
            return {
                'significance': 'low',
                'description': '轻微波动',
                'impact_level': 'minimal'
            }
        else:
            return {
                'significance': 'none',
                'description': '基本稳定',
                'impact_level': 'none'
            }
        
    def get_price_context_silent(self, token_symbol):
        """Silent version of get_price_context"""
        try:
            url = f"{self.base_url}/{token_symbol.upper()}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 and 'data' in data:
                    price_info = data['data']
                    price_context = {
                        'token': price_info.get('short_name', token_symbol),
                        'price_usd': float(price_info.get('price_usd', 0)),
                        'change_rate': float(price_info.get('change_rate', 0)),
                        'volume_usd': float(price_info.get('volume_usd', 0)),
                        'circulation_usd': float(price_info.get('circulation_usd', 0))
                    }
                    return price_context
        except Exception:
            pass
        
        return None
        

