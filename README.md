# 🧘 YouTube Driven Lifestyle Coach powered by Gemini

이 프로젝트는 YouTube 영상의 자막을 추출하고 Google Gemini API를 사용하여 사용자의 삶에 적용할 수 있는 **"라이프스타일 코칭 리포트"**를 생성하는 Streamlit 웹 애플리케이션입니다.

## 🚀 주요 기능

- **YouTube 자막 추출**: 여러 개의 YouTube URL에서 한국어 또는 영어 자막을 자동으로 가져옵니다.
- **AI 분석**: Google Gemini 1.5 Flash 모델을 사용하여 영상의 핵심 내용을 분석합니다.
- **맞춤형 코칭**: 단순한 요약을 넘어 핵심 통찰, 구체적인 실천 가이드, 동기 부여 메시지를 한국어로 제공합니다.
- **직관적인 UI**: Streamlit을 활용한 깔끔하고 사용하기 쉬운 인터페이스를 제공합니다.

## 🛠 기술 스택

- **언어**: Python 3.9+
- **프레임워크**: Streamlit
- **자막 추출**: YouTube Transcript API
- **LLM**: Google Generative AI (Gemini)

## 📦 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/youtube_lifestyle_coach.git
cd youtube_lifestyle_coach
```

### 2. Quick Setup (Recommended)
We provide a convenient script to set up the environment and install dependencies automatically.

```bash
./setup.sh
```
*Note: You might need to make it executable first with `chmod +x setup.sh`*

### 3. Manual Setup
If you prefer to set it up manually:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Run the App
```bash
streamlit run app.py
```

## 💡 사용 방법

1. 브라우저에서 실행된 앱 화면의 사이드바에서 **Google API Key**를 입력합니다.
   - API 키는 [Google AI Studio](https://aistudio.google.com/)에서 무료로 발급받을 수 있습니다.
2. 메인 화면의 텍스트 영역에 영감을 받은 **YouTube 영상 URL**들을 입력합니다 (한 줄에 하나씩).
3. **"Analyze & Coach Me ✨"** 버튼을 클릭합니다.
4. 잠시 기다리면 Gemini가 생성한 코칭 리포트가 화면에 표시됩니다.

## ⚠️ 주의 사항
- 자막(Subtitles)이 활성화되어 있지 않은 영상은 분석이 불가능합니다.
- 개인정보 보호를 위해 입력한 API 키는 세션 동안만 사용되며 저장되지 않습니다.
# youtube_lifestyle_coach
