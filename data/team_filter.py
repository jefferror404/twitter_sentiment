# data/team_filter.py
"""
Team filtering logic using Excel data to exclude project team accounts
"""

import pandas as pd
import os
from typing import Set, Optional


class TeamFilter:
    def __init__(self, excel_file_path: str = 'data/project_twitter.xlsx', silent_mode: bool = False):
        self.excel_file_path = excel_file_path
        self.team_accounts_db = {}  # ticker -> set of usernames
        self.is_loaded = False
        self.silent_mode = silent_mode
        self.load_team_data()
    
    def load_team_data(self):
        """Load team account data from Excel file"""
        try:
            # Check if file exists
            if not os.path.exists(self.excel_file_path):
                if not self.silent_mode:
                    print(f"⚠️ 团队账户数据文件未找到: {self.excel_file_path}")
                    print("   将跳过团队账户过滤")
                return
            
            # Load Excel file
            df = pd.read_excel(self.excel_file_path)
            
            # Validate required columns
            required_columns = ['ticker', 'tw_usernames']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                if not self.silent_mode:
                    print(f"⚠️ Excel文件缺少必需列: {missing_columns}")
                return
            
            # Process data
            loaded_count = 0
            for _, row in df.iterrows():
                ticker = str(row['ticker']).upper().strip()
                usernames_str = str(row['tw_usernames']).strip()
                
                # Skip empty or NaN usernames
                if pd.isna(row['tw_usernames']) or usernames_str == 'nan' or usernames_str == '':
                    continue
                
                # Handle multiple usernames (if separated by comma, semicolon, etc.)
                usernames = set()
                
                # Split by common separators and clean
                for separator in [',', ';', '|', '\n']:
                    if separator in usernames_str:
                        usernames_str = usernames_str.replace(separator, ',')
                
                # Extract usernames
                for username in usernames_str.split(','):
                    username = username.strip().lower()
                    if username and username != 'nan':
                        # Remove @ symbol if present
                        username = username.lstrip('@')
                        usernames.add(username)
                
                if usernames:
                    self.team_accounts_db[ticker] = usernames
                    loaded_count += 1
            
            self.is_loaded = True
            
            # 🆕 Only show loading info if not in silent mode
            if not self.silent_mode:
                print(f"✅ 成功加载团队账户数据:")
                print(f"   📊 总项目数: {len(df)} 个")
                print(f"   👥 有效团队账户: {loaded_count} 个项目")
                print(f"   📄 数据文件: {self.excel_file_path}")
                
                # Show some examples
                if loaded_count > 0:
                    print("   💡 示例数据:")
                    for i, (ticker, usernames) in enumerate(list(self.team_accounts_db.items())[:3]):
                        usernames_list = list(usernames)[:3]  # Show first 3 usernames
                        more_indicator = f" (+{len(usernames)-3})" if len(usernames) > 3 else ""
                        print(f"      {ticker}: @{', @'.join(usernames_list)}{more_indicator}")
            
        except Exception as e:
            if not self.silent_mode:
                print(f"❌ 加载团队账户数据时出错: {e}")
                print("   将跳过团队账户过滤")
    
    def is_team_account(self, username: str, token_symbol: str) -> bool:
        """Check if username belongs to the project team"""
        if not self.is_loaded:
            return False
        
        if not username or username == 'N/A':
            return False
        
        # Normalize inputs
        username = username.lower().replace('@', '').strip()
        token_symbol = token_symbol.upper().strip()
        
        # Check if we have team data for this token
        team_usernames = self.team_accounts_db.get(token_symbol, set())
        
        return username in team_usernames
    
    def get_team_usernames(self, token_symbol: str) -> Set[str]:
        """Get all team usernames for a specific token"""
        if not self.is_loaded:
            return set()
        
        token_symbol = token_symbol.upper().strip()
        return self.team_accounts_db.get(token_symbol, set())
    
    def get_filtering_stats(self) -> dict:
        """Get statistics about loaded team data"""
        if not self.is_loaded:
            return {
                'is_loaded': False,
                'total_projects': 0,
                'projects_with_accounts': 0,
                'total_team_accounts': 0
            }
        
        total_accounts = sum(len(usernames) for usernames in self.team_accounts_db.values())
        
        return {
            'is_loaded': True,
            'total_projects': len(self.team_accounts_db),
            'projects_with_accounts': len(self.team_accounts_db),
            'total_team_accounts': total_accounts,
            'file_path': self.excel_file_path
        }
    
    def show_team_accounts_for_token(self, token_symbol: str):
        """Display team accounts for a specific token (for debugging)"""
        team_usernames = self.get_team_usernames(token_symbol)
        
        if team_usernames:
            print(f"\n👥 {token_symbol} 项目团队账户:")
            for username in sorted(team_usernames):
                print(f"   @{username}")
        else:
            print(f"\n👥 {token_symbol}: 未找到团队账户数据")
    
    def validate_token_coverage(self, token_symbol: str) -> bool:
        """Check if we have team data for the given token"""
        token_symbol = token_symbol.upper().strip()
        has_data = token_symbol in self.team_accounts_db
        
        if has_data:
            team_count = len(self.team_accounts_db[token_symbol])
            print(f"✅ 找到 {token_symbol} 团队账户: {team_count} 个")
        else:
            print(f"⚠️ 未找到 {token_symbol} 团队账户数据，将跳过团队过滤")
        
        return has_data
    
    def validate_token_coverage_silent(self, token_symbol: str) -> bool:
        """🆕 Silent version of validate_token_coverage"""
        token_symbol = token_symbol.upper().strip()
        return token_symbol in self.team_accounts_db