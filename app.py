import streamlit as st
import re
import time
import json
import datetime
from google import genai
from google.genai import types
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from ics import Calendar, Event

# --- Helper Functions ---

def extract_video_id(url):
    """
    Extracts the YouTube Video ID from various URL formats.
    """
    regex = r"(?:v=|/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    return None

def get_transcript_text(video_id):
    """
    Fetches the transcript for a given video ID using a robust fallback strategy.
    """
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list_transcripts(video_id)
        
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

        fetched_transcript = transcript.fetch()
        formatter = TextFormatter()
        return formatter.format_transcript(fetched_transcript)

    except Exception as e:
        return None

def clean_json_string(json_str):
    """
    Cleans the JSON string by removing markdown code blocks if present.
    """
    cleaned = json_str.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()

def generate_coaching_data(api_key, full_transcript):
    """
    Sends the transcript to Google Gemini to generate the lifestyle coaching data in JSON.
    """
    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are an expert Lifestyle Coach and Productivity Consultant.
    The user shares YouTube videos they found inspiring.
    Your task is to analyze the video transcripts and translate the insights into a concrete, actionable schedule and resource list.

    **Language Requirement:**
    - The content MUST be in **Korean (한국어)**.
    - JSON keys must remain in English as specified below.

    **Output Format:**
    - You must return ONLY a valid JSON object.
    - Do not include markdown formatting like ```json ... ``` at the start or end. Just the raw JSON.

    **JSON Structure:**
    {{
      "analysis": "A comprehensive analysis of the video's logic, philosophy, and mindset. Summarize the key points clearly. (Korean)",
      "routine_items": [
        {{
            "activity": "Name of the activity (e.g., Morning Meditation)",
            "time": "HH:MM (24-hour format, e.g., 07:00)",
            "duration_minutes": 10,
            "notes": "Specific instructions or focus points"
        }}
      ],
      "recommended_resources": [
        {{
            "item_name": "Name of book, tool, or concept",
            "type": "Book / Tool / App / Video / Etc"
        }}
      ]
    }}

    **Video Transcripts:**
    {full_transcript}
    """

    max_retries = 3
    base_delay = 5

    for attempt in range(max_retries):
        try:
            # Request explicit JSON response if supported by the model, otherwise prompt relies on text
            # Using 'application/json' mime type hint for Gemini 1.5/2.0 models if available
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type='application/json')
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                wait_time = base_delay * (2 ** attempt)
                match = re.search(r"retry in (\d+(?:\.\d+)?)s", error_str)
                if match:
                    wait_time = float(match.group(1)) + 1.0
                time.sleep(wait_time)
                continue
            return None
            
    return None

def create_ics_file(routine_items):
    """
    Generates an ICS (iCalendar) file content from routine items.
    Defaults to 'Tomorrow'.
    """
    c = Calendar()
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    
    for item in routine_items:
        try:
            # Parse time "HH:MM"
            h, m = map(int, item['time'].split(':'))
            start_dt = datetime.datetime.combine(tomorrow, datetime.time(hour=h, minute=m))
            duration = datetime.timedelta(minutes=int(item.get('duration_minutes', 30)))
            
            e = Event()
            e.name = item['activity']
            e.begin = start_dt
            e.duration = duration
            e.description = item.get('notes', '')
            c.events.add(e)
        except Exception:
            continue # Skip malformed items

    return c.serialize()

# --- Streamlit UI ---

st.set_page_config(page_title="Action-Oriented Lifestyle Agent", page_icon="⚡", layout="wide")

# Sidebar
with st.sidebar:
    st.header("⚙️ 설정 (Settings)")
    api_key = st.text_input("Google API Key 입력", type="password", help="https://aistudio.google.com/")
    st.markdown("---")
    st.info("YouTube 영상의 지혜를 내일의 스케줄로 만들어드립니다.")

# Main Header
st.title("⚡ Action-Oriented Lifestyle Agent")
st.subheader("YouTube Wisdom → Concrete Action")

st.markdown("""
영감을 받은 YouTube 영상 링크를 입력하세요.  
**분석 리포트**, **구체적인 스케줄(.ics)**, 그리고 **실행 도구**를 제공합니다.
""")

# Input Area
video_urls_input = st.text_area("YouTube URL 입력 (한 줄에 하나씩)", height=150, placeholder="https://www.youtube.com/watch?v=...\nhttps://youtu.be/...")

if st.button("Generate Action Plan 🚀", type="primary"):
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
                    st.warning(f"⚠️ 자막 실패: {url}")
            
            progress_bar.progress((i + 1) / len(urls))

        status_text.empty()
        progress_bar.empty()

        if valid_video_count > 0:
            with st.spinner("🤖 Gemini가 인사이트를 실행 계획으로 변환 중입니다..."):
                raw_response = generate_coaching_data(api_key, all_transcripts)
            
            if raw_response:
                try:
                    # Clean and Parse JSON
                    cleaned_json = clean_json_string(raw_response)
                    data = json.loads(cleaned_json)
                    
                    st.success("분석 완료! 아래 탭에서 결과를 확인하세요.")
                    st.divider()

                    # Tabs
                    tab1, tab2, tab3 = st.tabs(["📊 분석 리포트", "🗓️ 내 스케줄", "🔗 관련 자료"])

                    # Tab 1: Analysis
                    with tab1:
                        st.markdown("### 🧠 핵심 로직 및 마인드셋")
                        st.write(data.get("analysis", "분석 내용이 없습니다."))

                    # Tab 2: Schedule & ICS
                    with tab2:
                        st.markdown("### ⚡ 내일의 실행 루틴")
                        routines = data.get("routine_items", [])
                        
                        if routines:
                            # Display as a nicely formatted list or table
                            for item in routines:
                                with st.container():
                                    cols = st.columns([1, 4, 2])
                                    cols[0].markdown(f"**{item.get('time', '??:??')}**")
                                    cols[1].markdown(f"**{item.get('activity')}**")
                                    cols[2].caption(f"{item.get('duration_minutes')} min | {item.get('notes')}")
                                    st.divider()
                            
                            # Generate ICS
                            ics_content = create_ics_file(routines)
                            st.download_button(
                                label="📅 캘린더 파일 다운로드 (.ics)",
                                data=ics_content,
                                file_name="my_lifestyle_routine.ics",
                                mime="text/calendar"
                            )
                        else:
                            st.info("추출된 루틴이 없습니다.")

                    # Tab 3: Resources
                    with tab3:
                        st.markdown("### 🛠️ 추천 도구 및 자료")
                        resources = data.get("recommended_resources", [])
                        
                        if resources:
                            for res in resources:
                                name = res.get("item_name", "Unknown")
                                r_type = res.get("type", "Resource")
                                search_url = f"https://www.google.com/search?q={name.replace(' ', '+')}"
                                
                                st.markdown(f"- **[{r_type}] {name}**")
                                st.link_button(f"🔍 '{name}' 검색하기", search_url)
                        else:
                            st.info("추천된 자료가 없습니다.")

                except json.JSONDecodeError:
                    st.error("데이터 변환 중 오류가 발생했습니다. (JSON Parsing Error)")
                    with st.expander("Raw Response (Debug)"):
                        st.text(raw_response)
            else:
                st.error("API 응답을 받지 못했습니다.")
        else:
            st.error("분석할 수 있는 자막이 없습니다.")