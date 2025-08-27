import streamlit as st
import sys
import io
import pandas as pd
from contextlib import redirect_stdout, redirect_stderr
import traceback
import os

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
    
    /* Enhanced horizontal sentiment bars - stacked vertically */
    .sentiment-bars-container {
        margin: 20px 0;
        background: #f8f9fa;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e9ecef;
    }
    
    .sentiment-bar-row {
        display: flex;
        align-items: center;
        margin-bottom: 12px;
        min-height: 40px;
    }
    
    .sentiment-bar-row:last-child {
        margin-bottom: 0;
    }
    
    .sentiment-bar-single {
        height: 35px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        padding: 0 12px;
        margin-right: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: white;
        font-weight: bold;
        font-size: 14px;
        min-width: 50px;
        flex-shrink: 0;
    }
    
    .sentiment-positive-single {
        background-color: #43946c;
    }
    
    .sentiment-negative-single {
        background-color: #dc3545;
    }
    
    .sentiment-neutral-single {
        background-color: #6c757d;
    }
    
    .sentiment-bar-text {
        font-size: 16px;
        font-weight: 500;
        color: #333;
        display: flex;
        align-items: center;
    }
    
    .sentiment-emoji {
        font-size: 18px;
        margin-right: 8px;
    }
    
    /* Price data styling */
    .price-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        color: white;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .price-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin-top: 15px;
    }
    
    .price-item {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .price-label {
        font-size: 14px;
        opacity: 0.8;
        margin-bottom: 5px;
    }
    
    .price-value {
        font-size: 18px;
        font-weight: bold;
        color: #fff;
    }
    
    .price-positive {
        color: #4ade80 !important;
    }
    
    .price-negative {
        color: #f87171 !important;
    }
    
    /* AI Summary consistent text formatting */
    .ai-summary-container {
        background: #ffffff;
        border: 1px solid #e1e8ed;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
    }
    
    .ai-summary-container p,
    .ai-summary-container div {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
        color: #333333 !important;
        margin: 8px 0 !important;
    }
    
    .ai-summary-container strong {
        font-weight: 600 !important;
        color: #1f2937 !important;
    }
    
    .ai-summary-title {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        color: #1f2937 !important;
        margin-bottom: 12px !important;
    }
    
    /* Force consistent text styling for all content within expander */
    .streamlit-expanderContent div,
    .streamlit-expanderContent p {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
        color: #333333 !important;
    }
    
    /* Fix: Sidebar toggle button - hide the problematic text */
    button[data-testid="baseButton-header"] span {
        display: none !important;
    }
    
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
    
    /* Fix: Expander arrow icons */
    .streamlit-expanderHeader svg {
        display: none !important;
    }
    
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
    
    /* Responsive design */
    @media (max-width: 768px) {
        .sentiment-bar-single {
            font-size: 12px;
            padding: 0 8px;
        }
        .sentiment-bar-text {
            font-size: 14px;
        }
        .price-grid {
            grid-template-columns: 1fr;
        }
        .sentiment-bar-row {
            flex-direction: column;
            align-items: flex-start;
        }
        .sentiment-bar-single {
            margin-right: 0;
            margin-bottom: 8px;
        }
    }
</style>
""", unsafe_allow_html=True)

def get_api_params(model_name):
    """Get correct API parameters based on model version"""
    base_params = {
        'temperature': 0.3,
        'timeout': 20
    }
    
    # GPT-5 models use max_completion_tokens instead of max_tokens
    if model_name.startswith('gpt-5'):
        base_params['max_completion_tokens'] = 800
    else:
        base_params['max_tokens'] = 800
    
    return base_params

def capture_analysis_output(token_symbol):
    """Capture the output from the analysis function with GPT-5 support"""
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    
    try:
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            # Configuration
            target_days = ANALYSIS_CONFIG['target_days']
            max_pages_per_call = ANALYSIS_CONFIG['max_pages_per_call']
            model_name = ANALYSIS_CONFIG['openai_model']
            
            # Initialize components with model support
            twitter_api = TwitterAPI()
            analyzer = CryptoSentimentAnalyzer(
                openai_api_key=OPENAI_API_KEY, 
                model_name=model_name,
                silent_mode=True
            )
            
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
                # Run analysis with proper model support
                analysis_result = analyzer.comprehensive_analysis_silent(
                    all_tweets, token_symbol, target_days
                )
                
                if not analysis_result:
                    print(f'🔍 "{token_symbol}" 近{target_days}天推文情感分析')
                    print(f"原获取推文数量: {len(all_tweets)}; 过滤后有效推文: 0")
                    print("❌ 过滤后无可分析推文，請檢查其他社群資訊")
                    return None, stdout_buffer.getvalue()
                
                return analysis_result, stdout_buffer.getvalue()
            else:
                print(f'🔍 "{token_symbol}" 近{target_days}天推文情感分析')
                print(f"原获取推文数量: 0; 过滤后有效推文: 0")
                print("❌ 过滤后无可分析推文，請檢查其他社群資訊")
                return None, stdout_buffer.getvalue()
                
    except Exception as e:
        error_msg = f"💥 分析过程中出现错误: {str(e)}\n{traceback.format_exc()}"
        return None, error_msg

def parse_and_display_price_data(output_text):
    """Parse price data from raw output and display in a nice format"""
    lines = output_text.split('\n')
    
    price_data = {}
    price_section_started = False
    
    for line in lines:
        if '💰 站内数据总览:' in line:
            price_section_started = True
            continue
        elif price_section_started and line.strip().startswith('💵 当前价格:'):
            current_price = line.split('💵 当前价格:')[1].strip()
            price_data['current_price'] = current_price
        elif price_section_started and ('📈 24H变化:' in line or '📉 24H变化:' in line):
            if '📈 24H变化:' in line:
                change_24h = line.split('📈 24H变化:')[1].strip()
                price_data['change_24h'] = change_24h
                price_data['change_icon'] = '📈'
            elif '📉 24H变化:' in line:
                change_24h = line.split('📉 24H变化:')[1].strip()
                price_data['change_24h'] = change_24h
                price_data['change_icon'] = '📉'
        elif price_section_started and line.strip().startswith('💧 24H交易量:'):
            volume_24h = line.split('💧 24H交易量:')[1].strip()
            price_data['volume_24h'] = volume_24h
        elif price_section_started and line.strip() and not line.strip().startswith('   '):
            break
    
    if not price_data:
        return None
    
    current_price = price_data.get('current_price', 'N/A')
    change_24h = price_data.get('change_24h', 'N/A')
    volume_24h = price_data.get('volume_24h', 'N/A')
    change_icon = price_data.get('change_icon', '📉')
    
    change_class = "price-negative" if change_24h.startswith('-') else "price-positive"
    
    price_html = f"""
    <div class="price-container">
        <h4 style="margin: 0 0 15px 0; text-align: center;">💰站内价格数据总览</h4>
        <div class="price-grid">
            <div class="price-item">
                <div class="price-label">💵 当前价格</div>
                <div class="price-value">{current_price}</div>
            </div>
            <div class="price-item">
                <div class="price-label">{change_icon} 24小时变化</div>
                <div class="price-value {change_class}">{change_24h}</div>
            </div>
            <div class="price-item">
                <div class="price-label">💧 24小时交易量</div>
                <div class="price-value">{volume_24h}</div>
            </div>
        </div>
    </div>
    """
    
    return price_html

def create_vertical_sentiment_bars_from_output(output_text):
    """Create vertical stacked sentiment bars from raw output text - FIXED VERSION"""
    lines = output_text.split('\n')
    
    sentiment_data = {}
    sentiment_section_started = False
    
    for line in lines:
        if '🎭 情绪分布:' in line:
            sentiment_section_started = True
            continue
        elif sentiment_section_started and line.strip().startswith('✅ 正面:'):
            try:
                pos_text = line.split('✅ 正面:')[1].strip()
                pos_count = int(pos_text.split('条')[0].strip())
                pos_pct_text = pos_text.split('(')[1].split(')')[0]
                sentiment_data['POSITIVE'] = {
                    'count': pos_count,
                    'percentage': pos_pct_text
                }
            except Exception as e:
                print(f"Error parsing positive sentiment: {e}")
                sentiment_data['POSITIVE'] = {'count': 0, 'percentage': '0.0%'}
        elif sentiment_section_started and line.strip().startswith('❌ 负面:'):
            try:
                neg_text = line.split('❌ 负面:')[1].strip()
                neg_count = int(neg_text.split('条')[0].strip())
                neg_pct_text = neg_text.split('(')[1].split(')')[0]
                sentiment_data['NEGATIVE'] = {
                    'count': neg_count,
                    'percentage': neg_pct_text
                }
            except Exception as e:
                print(f"Error parsing negative sentiment: {e}")
                sentiment_data['NEGATIVE'] = {'count': 0, 'percentage': '0.0%'}
        elif sentiment_section_started and line.strip().startswith('⚪ 中性:'):
            try:
                neu_text = line.split('⚪ 中性:')[1].strip()
                neu_count = int(neu_text.split('条')[0].strip())
                neu_pct_text = neu_text.split('(')[1].split(')')[0]
                sentiment_data['NEUTRAL'] = {
                    'count': neu_count,
                    'percentage': neu_pct_text
                }
            except Exception as e:
                print(f"Error parsing neutral sentiment: {e}")
                sentiment_data['NEUTRAL'] = {'count': 0, 'percentage': '0.0%'}
        elif sentiment_section_started and line.strip() and not line.strip().startswith('   ') and ('🤖' in line or '📈' in line):
            break
    
    # Debug output
    print(f"Parsed sentiment_data: {sentiment_data}")
    
    if not sentiment_data:
        print("No sentiment data found")
        return ""
    
    # Get data with defaults
    pos_data = sentiment_data.get('POSITIVE', {'count': 0, 'percentage': '0.0%'})
    neg_data = sentiment_data.get('NEGATIVE', {'count': 0, 'percentage': '0.0%'})
    neu_data = sentiment_data.get('NEUTRAL', {'count': 0, 'percentage': '0.0%'})
    
    total = pos_data['count'] + neg_data['count'] + neu_data['count']
    if total == 0:
        print("Total count is 0")
        return ""
    
    # Calculate bar widths (max 300px, min 50px for visibility)
    max_width = 300
    pos_width = max(50, int((pos_data['count'] / total) * max_width)) if pos_data['count'] > 0 else 50
    neg_width = max(50, int((neg_data['count'] / total) * max_width)) if neg_data['count'] > 0 else 50
    neu_width = max(50, int((neu_data['count'] / total) * max_width)) if neu_data['count'] > 0 else 50
    
    # Create the vertical stacked bars HTML
    bars_html = f"""
    <div class="sentiment-bars-container">
        <div class="sentiment-bar-row">
            <div class="sentiment-bar-single sentiment-positive-single" style="width: {pos_width}px;">
                ✅
            </div>
            <div class="sentiment-bar-text">
                <span class="sentiment-emoji">✅</span>
                <strong>正面:</strong> {pos_data['count']} 条 ({pos_data['percentage']})
            </div>
        </div>
        
        <div class="sentiment-bar-row">
            <div class="sentiment-bar-single sentiment-negative-single" style="width: {neg_width}px;">
                ❌
            </div>
            <div class="sentiment-bar-text">
                <span class="sentiment-emoji">❌</span>
                <strong>负面:</strong> {neg_data['count']} 条 ({neg_data['percentage']})
            </div>
        </div>
        
        <div class="sentiment-bar-row">
            <div class="sentiment-bar-single sentiment-neutral-single" style="width: {neu_width}px;">
                ⚪
            </div>
            <div class="sentiment-bar-text">
                <span class="sentiment-emoji">⚪</span>
                <strong>中性:</strong> {neu_data['count']} 条 ({neu_data['percentage']})
            </div>
        </div>
    </div>
    """
    
    print(f"Generated bars_html length: {len(bars_html)}")
    return bars_html

def parse_table_from_output(output_text, table_title):
    """Parse table data directly from raw output text"""
    lines = output_text.split('\n')
    table_data = []
    in_table = False
    headers = []
    
    for i, line in enumerate(lines):
        if table_title in line:
            in_table = True
            # Look for header line
            for j in range(i+1, min(i+5, len(lines))):
                if '|' in lines[j] and '用户名' in lines[j]:
                    header_line = lines[j].strip()
                    headers = [h.strip() for h in header_line.split('|')]
                    break
            continue
        
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
                if len(row_data) >= 7:
                    table_data.append(row_data)
    
    return headers, table_data

def display_ai_summary_section(lines):
    """Display AI summary with consistent formatting"""
    ai_summary_started = False
    ai_summary_lines = []
    
    for line in lines:
        if '🤖 AI 智能分析摘要:' in line:
            ai_summary_started = True
            continue
        elif ai_summary_started and '======' in line:
            continue
        elif ai_summary_started and '摘要生成失败:' in line:
            # Handle error case
            st.error(f"AI分析失败: {line.strip()}")
            return
        elif ai_summary_started and line.strip() and not line.startswith('📈'):
            ai_summary_lines.append(line.strip())
        elif ai_summary_started and line.startswith('📈'):
            break
    
    if ai_summary_lines:
        st.markdown("### 🤖 AI 智能分析摘要")
        
        with st.expander("查看详细分析", expanded=True):
            summary_html = '<div class="ai-summary-container">'
            
            for line in ai_summary_lines:
                if line.startswith('   ') and any(char.isdigit() for char in line[:5]):
                    clean_line = line.strip()
                    summary_html += f'<p><strong>{clean_line}</strong></p>'
                elif line.strip():
                    clean_line = line.strip()
                    summary_html += f'<p>{clean_line}</p>'
            
            summary_html += '</div>'
            st.markdown(summary_html, unsafe_allow_html=True)
    else:
        st.warning("无AI分析摘要数据")

def display_analysis_results(analysis_result, output_text):
    """Display the analysis results with all fixes applied"""
    if not analysis_result:
        st.error("分析失败或没有有效数据")
        if output_text:
            st.text(output_text)
        return
    
    # Parse the output text
    lines = output_text.split('\n')
    
    # Extract basic info
    header_line = next((line for line in lines if '近7天推文情感分析' in line), '')
    tweet_count_line = next((line for line in lines if '原获取推文数量' in line), '')
    
    if header_line and tweet_count_line:
        st.markdown(f"## {header_line}")
        st.info(tweet_count_line)
    
    # Display price data
    price_html = parse_and_display_price_data(output_text)
    if price_html:
        st.markdown(price_html, unsafe_allow_html=True)
    else:
        st.warning("⚠️ 未找到价格数据")
    
    # Display sentiment distribution - FIXED
    st.markdown("### 🎭 情绪分布")
    
    # Check if we have sentiment data
    has_sentiment_data = any('✅ 正面:' in line or '❌ 负面:' in line or '⚪ 中性:' in line for line in lines)
    
    if has_sentiment_data:
        vertical_bars_html = create_vertical_sentiment_bars_from_output(output_text)
        if vertical_bars_html and vertical_bars_html.strip():
            # CRITICAL: Use unsafe_allow_html=True
            st.markdown(vertical_bars_html, unsafe_allow_html=True)
        else:
            st.warning("无法解析情感数据")
            # Fallback: Show raw sentiment data
            for line in lines:
                if '✅ 正面:' in line or '❌ 负面:' in line or '⚪ 中性:' in line:
                    st.text(line.strip())
    else:
        st.warning("未找到情感分析数据")
    
    # Display AI summary
    display_ai_summary_section(lines)
    
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
    
    # Parse and display viral tweets
    st.markdown("### 🔥 病毒式传播推文")
    viral_headers, viral_data = parse_table_from_output(output_text, "🔥 病毒式传播推文")
    
    if viral_data:
        df_viral = pd.DataFrame(viral_data, columns=viral_headers if viral_headers else 
                               ['用户名', '传播力', '点赞', '转推', '回复', '情绪', '话题', '推文链接'])
        
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
    
    # Parse and display high influence tweets
    st.markdown("### 👑 高影响力用户动态")
    influence_headers, influence_data = parse_table_from_output(output_text, "👑 高影响力用户动态")
    
    if influence_data:
        df_influence = pd.DataFrame(influence_data, columns=influence_headers if influence_headers else 
                                  ['用户名', '影响力', '粉丝数', '情绪', '传播力', '话题', '推文链接'])
        
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
        current_model = ANALYSIS_CONFIG.get('openai_model', 'gpt-4o-mini')
        st.info(f"分析时间范围: 近{ANALYSIS_CONFIG['target_days']}天")
        st.info("数据来源: Twitter API")
        st.info(f"AI模型: {current_model}")
    
    # Main input section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        token_symbol = st.text_input(
            "请输入代币符号 (如: BTC, ETH, PUNDIAI)",
            placeholder="例如: BTC",
            help="输入您想要分析的加密货币代币符号"
        ).strip().upper()
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
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
            
        # Clear progress
        progress_text.empty()
        
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
