import streamlit as st
import sys
import io
import pandas as pd
from contextlib import redirect_stdout, redirect_stderr
import traceback

# Import your existing modules
from api.twitter_api import TwitterAPI
from analysis.sentiment import CryptoSentimentAnalyzer
from config import ANALYSIS_CONFIG, OPENAI_API_KEY

# Page configuration
st.set_page_config(
    page_title="Crypto Sentiment Analyzer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .analysis-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .sentiment-positive {
        color: #43946c;
        font-weight: bold;
    }
    .sentiment-negative {
        color: #dc3545;
        font-weight: bold;
    }
    .sentiment-neutral {
        color: #6c757d;
        font-weight: bold;
    }
    
    /* Custom button styling */
    .stButton > button {
        background-color: #43946c !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }
    .stButton > button:hover {
        background-color: #367a55 !important;
        color: white !important;
    }
    .stButton > button:focus {
        background-color: #43946c !important;
        color: white !important;
        box-shadow: none !important;
    }
    
    /* Enhanced sentiment bar styling */
    .sentiment-bar {
        height: 50px;
        border-radius: 12px;
        overflow: hidden;
        display: flex;
        margin: 15px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        border: 2px solid #e9ecef;
    }
    .sentiment-positive-bar {
        background-color: #43946c;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 14px;
        padding: 0 8px;
        text-align: center;
        min-width: 0;
        white-space: nowrap;
        overflow: hidden;
    }
    .sentiment-negative-bar {
        background-color: #dc3545;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 14px;
        padding: 0 8px;
        text-align: center;
        min-width: 0;
        white-space: nowrap;
        overflow: hidden;
    }
    .sentiment-neutral-bar {
        background-color: #6c757d;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 14px;
        padding: 0 8px;
        text-align: center;
        min-width: 0;
        white-space: nowrap;
        overflow: hidden;
    }
    
    /* 🔧 FIX: Sidebar toggle button - hide the "keyboard_double_arrow_right" text */
    button[data-testid="baseButton-header"] span {
        display: none !important;
    }
    
    /* Replace with proper arrow using CSS */
    button[data-testid="baseButton-header"] {
        position: relative !important;
        width: 2.25rem !important;
        height: 2.25rem !important;
    }
    
    button[data-testid="baseButton-header"]:after {
        content: "»" !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        font-size: 18px !important;
        font-weight: bold !important;
        color: #666 !important;
        font-family: system-ui, -apple-system, sans-serif !important;
    }
    
    /* When sidebar is open, show left arrow */
    .css-1d391kg button[data-testid="baseButton-header"]:after {
        content: "«" !important;
    }
    
    /* 🔧 FIX: Expander arrow icons - hide the problematic arrows */
    .streamlit-expanderHeader svg {
        display: none !important;
    }
    
    /* Add custom arrows for expanders */
    .streamlit-expanderHeader:after {
        content: "▶" !important;
        margin-left: 0.5rem !important;
        font-size: 14px !important;
        transition: transform 0.2s ease !important;
        color: #666 !important;
    }
    
    details[open] .streamlit-expanderHeader:after {
        content: "▼" !important;
        transform: none !important;
    }
    
    /* Alternative sidebar toggle selectors (in case the above doesn't work) */
    button[kind="header"] span,
    button[title*="sidebar"] span {
        display: none !important;
    }
    
    button[kind="header"]:after,
    button[title*="Open"]:after {
        content: "»" !important;
        font-size: 18px !important;
        font-weight: bold !important;
        color: #666 !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
    }
    
    button[title*="Close"]:after {
        content: "«" !important;
        font-size: 18px !important;
        font-weight: bold !important;
        color: #666 !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .sentiment-positive-bar, .sentiment-negative-bar, .sentiment-neutral-bar {
            font-size: 12px;
        }
    }
    
    /* Remove the problematic small bar text hiding - we'll handle this programmatically */
    /* No more width-based text hiding rules */
</style>
""", unsafe_allow_html=True)

def capture_analysis_output(token_symbol):
    """Capture the output from the analysis function"""
    # Create string buffers to capture output
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    
    try:
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            # Configuration
            target_days = ANALYSIS_CONFIG['target_days']
            max_pages_per_call = ANALYSIS_CONFIG['max_pages_per_call']
            
            # Initialize components
            twitter_api = TwitterAPI()
            analyzer = CryptoSentimentAnalyzer(openai_api_key=OPENAI_API_KEY, silent_mode=True)
            
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
                # Run analysis
                analysis_result = analyzer.comprehensive_analysis_silent(
                    all_tweets, token_symbol, target_days
                )
                
                if not analysis_result:
                    # Handle case where filtering removes all tweets
                    print(f'🔍 "{token_symbol}" 近{target_days}天推文情感分析')
                    print(f"原获取推文数量: {len(all_tweets)}; 过滤后有效推文: 0")
                    print("❌ 过滤后无可分析推文，請檢查其他社群資訊")
                    return None, stdout_buffer.getvalue()
                
                return analysis_result, stdout_buffer.getvalue()
            else:
                # Handle case where no tweets found
                print(f'🔍 "{token_symbol}" 近{target_days}天推文情感分析')
                print(f"原获取推文数量: 0; 过滤后有效推文: 0")
                print("❌ 过滤后无可分析推文，請檢查其他社群資訊")
                return None, stdout_buffer.getvalue()
                
    except Exception as e:
        error_msg = f"💥 分析过程中出现错误: {str(e)}\n{traceback.format_exc()}"
        return None, error_msg

def create_enhanced_sentiment_bar_chart(sentiment_summary):
    """🆕 Create an enhanced proportional sentiment bar chart with smart text display"""
    total = sum(sentiment_summary.values())
    if total == 0:
        return ""
    
    pos_count = sentiment_summary.get('POSITIVE', 0)
    neg_count = sentiment_summary.get('NEGATIVE', 0)
    neu_count = sentiment_summary.get('NEUTRAL', 0)
    
    pos_pct = (pos_count / total * 100)
    neg_pct = (neg_count / total * 100)
    neu_pct = (neu_count / total * 100)
    
    # Smart text display - only show full text if percentage is above 8%
    def get_bar_text(emoji, label, count, pct, min_threshold=8):
        if pct >= min_threshold:
            return f"{emoji} {label}: {count} 条 ({pct:.1f}%)"
        elif pct > 0:
            return f"{emoji}"  # Just emoji for small bars
        else:
            return ""
    
    pos_text = get_bar_text("✅", "正面", pos_count, pos_pct)
    neg_text = get_bar_text("❌", "负面", neg_count, neg_pct)
    neu_text = get_bar_text("⚪", "中性", neu_count, neu_pct)
    
    # Create the bar chart
    bar_html = f"""
    <div class="sentiment-bar">
        <div class="sentiment-positive-bar" style="width: {pos_pct}%;">
            {pos_text}
        </div>
        <div class="sentiment-negative-bar" style="width: {neg_pct}%;">
            {neg_text}
        </div>
        <div class="sentiment-neutral-bar" style="width: {neu_pct}%;">
            {neu_text}
        </div>
    </div>
    """
    
    # Add summary text below for clarity
    summary_parts = []
    if pos_count > 0: summary_parts.append(f"✅ 正面: {pos_count} 条 ({pos_pct:.1f}%)")
    if neg_count > 0: summary_parts.append(f"❌ 负面: {neg_count} 条 ({neg_pct:.1f}%)")
    if neu_count > 0: summary_parts.append(f"⚪ 中性: {neu_count} 条 ({neu_pct:.1f}%)")
    
    summary_html = f"""
    <div style="text-align: center; margin-top: 10px; font-size: 14px; color: #666; padding: 10px; background-color: #f8f9fa; border-radius: 8px;">
        {" | ".join(summary_parts)}
    </div>
    """
    
    return bar_html + summary_html

def parse_table_from_output(output_text, table_title):
    """🆕 Parse table data directly from raw output text"""
    lines = output_text.split('\n')
    table_data = []
    in_table = False
    headers = []
    
    for i, line in enumerate(lines):
        # Find the table start
        if table_title in line:
            in_table = True
            # Look for header line (next few lines)
            for j in range(i+1, min(i+5, len(lines))):
                if '|' in lines[j] and '用户名' in lines[j]:
                    header_line = lines[j].strip()
                    headers = [h.strip() for h in header_line.split('|')]
                    break
            continue
        
        # Process table rows
        if in_table and line.strip():
            # Stop when we hit next section
            if line.startswith('👑') or line.startswith('🔍') or line.startswith('💰') or line.startswith('==='):
                break
            
            # Skip separator lines
            if '---' in line or '===' in line:
                continue
            
            # Process data rows
            if '|' in line and '@' in line and 'https://' in line:
                row_data = [cell.strip() for cell in line.split('|')]
                if len(row_data) >= 7:  # Ensure we have enough columns
                    table_data.append(row_data)
    
    return headers, table_data

def display_analysis_results(analysis_result, output_text):
    """Display the analysis results in a structured format"""
    if not analysis_result:
        st.error("分析失败或没有有效数据")
        if output_text:
            st.text(output_text)
        return
    
    # Parse the output text to extract key information
    lines = output_text.split('\n')
    
    # Extract basic info
    header_line = next((line for line in lines if '近7天推文情感分析' in line), '')
    tweet_count_line = next((line for line in lines if '原获取推文数量' in line), '')
    
    if header_line and tweet_count_line:
        st.markdown(f"## {header_line}")
        st.info(tweet_count_line)
    
    # Display price data
    price_section_started = False
    price_info = []
    for line in lines:
        if '💰 站内数据总览:' in line:
            price_section_started = True
            continue
        elif price_section_started and line.strip().startswith('   '):
            price_info.append(line.strip())
        elif price_section_started and not line.strip().startswith('   ') and line.strip():
            break
    
    if price_info:
        st.markdown("### 💰 价格数据")
        for info in price_info:
            st.text(info)
    
    # 🆕 Display enhanced sentiment distribution (only bar chart)
    sentiment_summary = analysis_result.get('sentiment_summary', {})
    if sentiment_summary:
        st.markdown("### 🎭 情绪分布")
        
        # Only show the enhanced bar chart with detailed text inside
        enhanced_bar_chart_html = create_enhanced_sentiment_bar_chart(sentiment_summary)
        st.markdown(enhanced_bar_chart_html, unsafe_allow_html=True)
    
    # Display AI summary
    ai_summary_started = False
    ai_summary_lines = []
    for line in lines:
        if '🤖 AI 智能分析摘要:' in line:
            ai_summary_started = True
            continue
        elif ai_summary_started and '======' in line:
            continue
        elif ai_summary_started and line.strip() and not line.startswith('📈'):
            ai_summary_lines.append(line.strip())
        elif ai_summary_started and line.startswith('📈'):
            break
    
    if ai_summary_lines:
        st.markdown("### 🤖 AI 智能分析摘要")
        with st.expander("查看详细分析", expanded=True):
            for line in ai_summary_lines:
                if line.startswith('   ') and any(char.isdigit() for char in line[:5]):
                    st.markdown(f"**{line.strip()}**")
                elif line.strip():
                    st.write(line.strip())
    
    # Display topic analysis
    topics_started = False
    topic_lines = []
    for line in lines:
        if '📈 热门话题榜:' in line:
            topics_started = True
            continue
        elif topics_started and '🔥' in line:
            break
        elif topics_started and line.strip():
            topic_lines.append(line.strip())
    
    if topic_lines:
        st.markdown("### 📈 热门话题榜")
        for line in topic_lines:
            if 'AI智能话题分析:' in line:
                continue
            elif line and any(char.isdigit() for char in line[:5]):
                st.text(line)
    
    # 🆕 Parse and display viral tweets directly from raw output
    st.markdown("### 🔥 病毒式传播推文")
    viral_headers, viral_data = parse_table_from_output(output_text, "🔥 病毒式传播推文")
    
    if viral_data:
        # Convert to DataFrame
        df_viral = pd.DataFrame(viral_data, columns=viral_headers if viral_headers else 
                               ['用户名', '传播力', '点赞', '转推', '回复', '情绪', '话题', '推文链接'])
        
        # 🆕 Display with clickable links using st.dataframe with column configuration
        st.dataframe(
            df_viral,
            use_container_width=True,
            column_config={
                "推文链接": st.column_config.LinkColumn(
                    "推文链接",
                    help="点击查看原推文",
                    display_text="查看推文"
                )
            }
        )
    else:
        st.info("暂无符合条件的病毒式传播推文")
    
    # 🆕 Parse and display high influence tweets directly from raw output
    st.markdown("### 👑 高影响力用户动态")
    influence_headers, influence_data = parse_table_from_output(output_text, "👑 高影响力用户动态")
    
    if influence_data:
        # Convert to DataFrame
        df_influence = pd.DataFrame(influence_data, columns=influence_headers if influence_headers else 
                                  ['用户名', '影响力', '粉丝数', '情绪', '传播力', '话题', '推文链接'])
        
        # 🆕 Display with clickable links using st.dataframe with column configuration
        st.dataframe(
            df_influence,
            use_container_width=True,
            column_config={
                "推文链接": st.column_config.LinkColumn(
                    "推文链接", 
                    help="点击查看原推文",
                    display_text="查看推文"
                )
            }
        )
    else:
        st.info("暂无符合条件的高影响力用户推文")

def extract_tweet_link_from_output(output_text, username):
    """Extract tweet link for a specific user from the raw output"""
    lines = output_text.split('\n')
    
    # Look for lines containing the username and extract the link
    for i, line in enumerate(lines):
        if f"@{username}" in line and "https://x.com" in line:
            # Extract the link from the line
            parts = line.split('|')
            for part in parts:
                part = part.strip()
                if part.startswith('https://x.com'):
                    return part
    
    return "N/A"

def main():
    # Header
    st.title("🚀 加密货币推文情感分析工具")
    st.markdown("---")
    
    # Sidebar info
    with st.sidebar:
        st.markdown("### ℹ️ 关于工具")
        st.markdown("""
        此工具分析加密货币相关推文的情感，提供：
        - 📊 情感分布统计
        - 💰 价格数据概览  
        - 🤖 AI智能摘要
        - 🔥 病毒式传播推文
        - 👑 高影响力用户动态
        """)
        
        st.markdown("### ⚙️ 分析设置")
        st.info("分析时间范围: 近7天")
        st.info("数据来源: Twitter API")
        st.info("AI模型: GPT-4o-mini")
    
    # Main input section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        token_symbol = st.text_input(
            "请输入代币符号 (如: BTC, ETH, PUNDIAI)",
            placeholder="例如: BTC",
            help="输入您想要分析的加密货币代币符号"
        ).strip().upper()
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
        analyze_button = st.button("🔍 开始分析", type="primary", use_container_width=True)
    
    # Analysis section
    if analyze_button and token_symbol:
        if len(token_symbol) < 2 or len(token_symbol) > 10:
            st.error("请输入有效的代币符号 (2-10个字符)")
            return
        
        # Show progress
        with st.spinner(f'正在分析 {token_symbol} 的推文情感...'):
            progress_text = st.empty()
            progress_text.text("📡 正在获取推文数据...")
            
            # Run analysis
            analysis_result, output_text = capture_analysis_output(token_symbol)
            
            progress_text.text("🤖 正在进行AI分析...")
            
        # Display results
        st.markdown("---")
        display_analysis_results(analysis_result, output_text)
        
        # Show raw output in expandable section for debugging
        with st.expander("🔍 查看原始分析输出"):
            st.text(output_text)
    
    elif analyze_button and not token_symbol:
        st.error("请输入代币符号")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "🚀 Crypto Twitter Sentiment Analyzer | Powered by Terminode"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
