import streamlit as st
import re
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

# --- Helper Functions ---

def extract_video_id(url):
    """
    Extracts the YouTube Video ID from various URL formats.
    Supported formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    """
    regex = r"(?:v=|/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    return None

def get_transcript_text(video_id):
    """
    Fetches the transcript for a given video ID using a robust fallback strategy.
    Prioritizes: Manual Ko/En -> Auto Ko/En -> Any (Translated to Ko).
    """
    try:
        # Get the list of all available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        transcript = None
        
        # Priority 1: Manual Korean or English
        try:
            transcript = transcript_list.find_manually_created_transcript(['ko', 'en'])
        except:
            # Priority 2: Auto-generated Korean or English
            try:
                transcript = transcript_list.find_generated_transcript(['ko', 'en'])
            except:
                # Priority 3: Fallback to ANY available transcript and translate to Korean
                try:
                    transcript = next(iter(transcript_list))
                    transcript = transcript.translate('ko')
                except:
                    return None

        # Fetch the actual transcript data
        fetched_transcript = transcript.fetch()
        
        # Format to text
        formatter = TextFormatter()
        return formatter.format_transcript(fetched_transcript)

    except Exception as e:
        # print(f"Error fetching transcript for {video_id}: {e}")
        return None

def generate_coaching_report(api_key, full_transcript):
    """
    Sends the transcript to Google Gemini to generate the lifestyle coaching report.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""
        You are an expert Lifestyle Coach and Productivity Consultant.
        The user shares YouTube videos they found inspiring.
        Your task is to analyze the following video transcripts and provide a structured coaching plan.

        **Language Requirement:** The final response **MUST be written in Korean (한국어)**.

        **Output Structure:**
        1. **핵심 통찰 (Core Insight):** What is the one key philosophy or lesson from these videos? (1 sentence)
        2. **주요 요약 (Key Takeaways):** Summarize 3 major points relevant to lifestyle or mindset.
        3. **실천 가이드 (Action Plan):** Provide 3 concrete, actionable steps the user can do *tomorrow* to apply this knowledge.
        4. **동기 부여 (Motivation):** A short, encouraging quote or message based on the content.

        **Video Transcripts:**
        {full_transcript}
        """

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error connecting to Gemini API: {str(e)}"

# --- Streamlit UI ---

st.set_page_config(page_title="YouTube Lifestyle Coach", page_icon="🧘", layout="wide")

# Sidebar for API Key
with st.sidebar:
    st.header("⚙️ 설정 (Settings)")
    api_key = st.text_input("Google API Key 입력", type="password", help="Get your API key from https://aistudio.google.com/")
    st.markdown("---")
    st.info("이 앱은 YouTube 영상의 자막을 분석하여 맞춤형 라이프스타일 코칭을 제공합니다.")

# Main Content
st.title("🧘 YouTube Driven Lifestyle Coach")
st.subheader("powered by Google Gemini")

st.markdown("""
영감을 받은 YouTube 영상 링크를 입력하세요.  
Gemini가 내용을 분석하여 **핵심 통찰**과 **실천 가이드**를 드립니다.
""")

# Input Area
video_urls_input = st.text_area("YouTube URL 입력 (한 줄에 하나씩)", height=150, placeholder="https://www.youtube.com/watch?v=...\nhttps://youtu.be/...")

if st.button("Analyze & Coach Me ✨", type="primary"):
    if not api_key:
        st.error("⚠️ Google API Key를 사이드바에 입력해주세요.")
    elif not video_urls_input.strip():
        st.warning("⚠️ 분석할 YouTube URL을 입력해주세요.")
    else:
        urls = [url.strip() for url in video_urls_input.split('\n') if url.strip()]
        
        all_transcripts = ""
        valid_video_count = 0

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, url in enumerate(urls):
            status_text.text(f"영상 처리 중... ({i+1}/{len(urls)})")
            
            video_id = extract_video_id(url)
            if video_id:
                transcript = get_transcript_text(video_id)
                if transcript:
                    all_transcripts += f"\n\n--- Video ID: {video_id} ---\n{transcript}"
                    valid_video_count += 1
                else:
                    st.warning(f"⚠️ 자막을 가져올 수 없습니다: {url} (자막이 없거나 접근이 제한됨)")
            else:
                st.warning(f"⚠️ 유효하지 않은 URL입니다: {url}")
            
            progress_bar.progress((i + 1) / len(urls))

        status_text.empty()
        progress_bar.empty()

        if valid_video_count > 0:
            with st.spinner("🤖 Gemini가 영상을 분석하고 코칭 리포트를 작성 중입니다..."):
                report = generate_coaching_report(api_key, all_transcripts)
            
            st.divider()
            st.markdown("## 📋 라이프스타일 코칭 리포트")
            st.markdown(report)
            
            st.success("분석이 완료되었습니다! 오늘 하루도 성장하세요! 🌱")
        else:
            st.error("분석할 수 있는 영상 내용이 없습니다. URL과 자막 여부를 확인해주세요.")
