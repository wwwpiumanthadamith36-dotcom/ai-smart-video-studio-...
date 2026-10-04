import PIL.Image
# Pillow 10+ Compatibility Fix
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

import streamlit as st
import google.generativeai as genai
import yt_dlp
import whisper
import gtts
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips
import moviepy.video.fx.all as vfx
import os
import tempfile

# Page Config
st.set_page_config(page_title="AI Smart Video Studio Pro 🇱🇰", page_icon="🇱🇰", layout="wide")

# Custom CSS for UI & Flag Banner
st.markdown("""
    <style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .flag-header {
        text-align: center;
        padding: 12px;
        background: linear-gradient(90deg, #ffbe00 0%, #8d0000 50%, #006600 100%);
        border-radius: 10px;
        margin-bottom: 20px;
        color: white;
        font-size: 28px;
        font-weight: bold;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
    }
    .stButton>button {
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
        color: white;
        border-radius: 8px;
        height: 3em;
        width: 100%;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #4f46e5 0%, #9333ea 100%);
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #020617;
        color: #94a3b8;
        text-align: center;
        padding: 8px;
        font-size: 14px;
        border-top: 1px solid #1e293b;
        z-index: 999;
    }
    </style>
""", unsafe_allow_html=True)

# 🇱🇰 Sri Lanka Flag Header 🇱🇰
st.markdown('<div class="flag-header">🇱🇰 AI Smart Video Studio Pro 🇱🇰</div>', unsafe_allow_html=True)
st.caption("Perfect Auto-Sync | Dynamic Male & Female Voice Pitch | Google Gemini SEO Pack")

# Session State for Auto Saving API Key
if "gemini_api_key" not in st.session_state:
    st.session_state["gemini_api_key"] = ""

# Languages Database
LANGUAGES = {
    "Sinhala (සිංහල - Sri Lanka)": "si",
    "English (United States)": "en",
    "English (United Kingdom)": "en-uk",
    "Hindi (हिन्दी - India)": "hi",
    "Tamil (தமிழ் - Sri Lanka/India)": "ta",
    "Japanese (日本語 - Japan)": "ja",
    "Korean (한국어 - Korea)": "ko",
    "Spanish (Español - Spain)": "es",
    "French (Français - France)": "fr",
    "German (Deutsch - Germany)": "de",
    "Chinese (Mandarin - China)": "zh-CN",
    "Arabic (العربية - Middle East)": "ar",
    "Russian (Русский - Russia)": "ru",
    "Portuguese (Português - Brazil)": "pt"
}

COUNTRIES = [
    "India 🇮🇳",
    "Sri Lanka 🇱🇰",
    "Worldwide (Global Audience) 🌐",
    "United States (USA) 🇺🇸",
    "United Kingdom (UK) 🇬🇧",
    "Australia 🇦🇺",
    "Canada 🇨🇦",
    "United Arab Emirates (UAE) 🇦🇪",
    "Germany 🇩🇪",
    "Japan 🇯🇵"
]

# Sidebar Settings
with st.sidebar:
    st.header("⚙️ Settings / සැකසුම්")
    
    api_key_input = st.text_input(
        "Google Gemini API Key",
        value=st.session_state["gemini_api_key"],
        type="password",
        help="ඔබගේ API Key එක auto-save වේ."
    )
    if api_key_input:
        st.session_state["gemini_api_key"] = api_key_input
    
    api_key = st.session_state["gemini_api_key"]

    st.subheader("🔊 Multi-Language & Voice Settings")
    selected_lang_label = st.selectbox("Target Language (තෝරාගන්නා භාෂාව)", list(LANGUAGES.keys()))
    lang_code = LANGUAGES[selected_lang_label]
    
    # Male / Female Selection
    voice_gender = st.radio("Voice Gender (හඬ වර්ගය)", ["👩 Female (ස්ත්‍රී හඬ)", "👨 Male (පුරුෂ හඬ)"])
    
    multi_character_mode = st.checkbox("🎭 Multi-Character Auto Sync (චරිත ගොඩක් සිටී නම් Multi-Voice Auto-Detect)", value=True)
    
    voice_tone = st.selectbox("Voice Style / Tone (කතාකරන විලාසය)", [
        "Normal Storyteller", 
        "Cheerful & Energetic", 
        "Dramatic Movie Style", 
        "Newsreader Professional"
    ])

    st.subheader("🌍 Target Country SEO Pack")
    target_country = st.selectbox("Target Country (ඉලක්කගත රට)", COUNTRIES)

# Layout Tabs
tab1, tab2 = st.tabs(["📤 File Upload (Up to 2GB)", "🔗 Video URL Download"])

video_path = None

with tab1:
    uploaded_file = st.file_uploader("වීඩියෝ එක Upload කරන්න (Up to 2GB)", type=["mp4", "mov", "avi", "mkv"])
    if uploaded_file is not None:
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, uploaded_file.name)
        with open(video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"Uploaded: {uploaded_file.name}")

with tab2:
    video_url = st.text_input("YouTube / TikTok / Facebook Video URL එක මෙතැනට Paste කරන්න")
    if st.button("Download Video"):
        if video_url:
            url_progress_bar = st.progress(0)
            st.info("Downloading Video from URL...")
            
            def my_hook(d):
                if d['status'] == 'downloading':
                    p = d.get('_percent_str', '0.0%').strip()
                    try:
                        clean_p = float(p.replace('%', '')) / 100.0
                        url_progress_bar.progress(min(max(clean_p, 0.0), 1.0))
                    except:
                        pass
                elif d['status'] == 'finished':
                    url_progress_bar.progress(1.0)

            try:
                ydl_opts = {
                    'outtmpl': 'downloaded_video.mp4', 
                    'format': 'best',
                    'progress_hooks': [my_hook]
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])
                video_path = "downloaded_video.mp4"
                st.success("Download Completed Successfully!")
            except Exception as e:
                st.error(f"Download Error: {e}")

st.divider()

st.subheader("📝 Custom Script / Text (අවශ්‍ය නම් පමණක් Type කරන්න)")
custom_text_input = st.text_area(
    "ඔබට වෙනස් කිරීමට අවශ්‍ය Script එක මෙතැන Type කරන්න (හිස්ව තැබුවොත් Video එකෙන් Auto අරගනී):",
    height=120,
    placeholder="ඔබගේ Script එක මෙතැන ඇතුළත් කරන්න..."
)

# Improved Multi-Voice Audio Generation with Male/Female Pitch Modifier
def generate_multi_voice_audio(text, lang, is_multi_char, gender):
    audio_clips = []
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if not lines:
        lines = [text]

    is_male = "Male" in gender

    for idx, line in enumerate(lines):
        temp_audio_name = f"temp_part_{idx}.mp3"
        try:
            # Male voice tuning using TLD accent & speed
            tld_val = 'co.uk' if (is_male and lang == 'en') else 'com'
            slow_flag = True if (is_male or (is_multi_char and idx % 2 == 1)) else False
            
            tts = gtts.gTTS(line, lang=lang, tld=tld_val, slow=slow_flag)
            tts.save(temp_audio_name)
            
            clip = AudioFileClip(temp_audio_name)
            
            # Male Pitch & Tone Adjustment using Audio Speed Adjustment
            if is_male:
                clip = clip.fx(vfx.speedx, 0.90) # Lower pitch effect for male
                
            audio_clips.append(clip)
        except Exception:
            pass
    
    if audio_clips:
        final_audio = concatenate_audioclips(audio_clips)
        out_path = "final_generated_voice.mp3"
        final_audio.write_audiofile(out_path)
        return out_path
    else:
        tts = gtts.gTTS(text, lang=lang, slow=is_male)
        out_path = "final_generated_voice.mp3"
        tts.save(out_path)
        return out_path

# Helper Function for Gemini API
def call_gemini(api_key, prompt):
    genai.configure(api_key=api_key)
    candidate_models = [
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-2.0-flash',
        'gemini-pro',
        'models/gemini-1.5-flash',
        'models/gemini-pro'
    ]
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(model_name)
            res = model.generate_content(prompt)
            if res and res.text:
                return res.text
        except Exception:
            continue
    return None

# Processing Section
if video_path and st.button("🚀 Process Video & Generate SEO Pack"):
    if not api_key:
        st.error("කරුණාකර Sidebar එකේ Google Gemini API Key එක ඇතුළත් කරන්න!")
    else:
        try:
            main_progress = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Text Extract
            status_text.info("1/5: Extracting Audio & Transcribing Text...")
            main_progress.progress(15)
            
            if custom_text_input.strip():
                original_text = custom_text_input.strip()
            else:
                model = whisper.load_model("base")
                result = model.transcribe(video_path)
                original_text = result['text']
            
            st.write("**Original Source Text:**", original_text)

            # Step 2: Translate & Adapt Script
            status_text.info(f"2/5: Adapting Script for {selected_lang_label} ({voice_gender})...")
            main_progress.progress(35)
            
            translate_prompt = f"Translate and rewrite the following video transcript into {selected_lang_label} with a {voice_tone} style for a {voice_gender} voice. Format line by line clearly:\n\n{original_text}"
            translated_text = call_gemini(api_key, translate_prompt)
            
            if not translated_text:
                translated_text = original_text

            st.write("**Final Character-Synced Script:**", translated_text)

            # Step 3: Multi-Character Voiceover Generation
            status_text.info(f"3/5: Generating Voiceover ({voice_gender}) & Auto-Syncing...")
            main_progress.progress(55)
            
            audio_path = generate_multi_voice_audio(translated_text, lang_code, multi_character_mode, voice_gender)

            # Step 4: Video Syncing & Export (Exact Duration Match)
            status_text.info("4/5: Matching Video Speed Perfectly to Audio Duration...")
            main_progress.progress(75)
            
            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(audio_path)
            
            # Calculate EXACT speed multiplier for 100% perfect auto-sync
            video_duration = video_clip.duration
            audio_duration = audio_clip.duration
            
            exact_speed_factor = video_duration / audio_duration
            
            # Match Video speed strictly to audio duration
            adjusted_video = video_clip.fx(vfx.speedx, exact_speed_factor)
            
            # Dimension alignment fix
            w, h = adjusted_video.size
            if w % 2 != 0: w -= 1
            if h % 2 != 0: h -= 1
            adjusted_video = adjusted_video.resize((w, h))

            final_clip = adjusted_video.set_audio(audio_clip)
            
            output_video_path = os.path.abspath("final_output.mp4")
            
            final_clip.write_videofile(
                "final_output.mp4",
                codec="libx264",
                audio_codec="aac",
                preset="medium",
                threads=2,
                bitrate="2000k"
            )

            # Step 5: SEO Pack Generation
            status_text.info(f"5/5: Auto-Generating Social Media SEO Pack for {target_country}...")
            main_progress.progress(90)
            
            seo_prompt = f"""
            Based on this video script:
            "{translated_text}"

            Create a viral Social Media SEO Pack targeted for audience in {target_country}.
            Format as:
            📌 **3 VIRAL TITLES (YouTube/TikTok/Reels)**
            1. ...
            2. ...
            3. ...

            📝 **SEO DESCRIPTION (High Ranking)**
            ...

            🔥 **TOP 15 HASHTAGS**
            #...
            """
            
            seo_pack_result = call_gemini(api_key, seo_prompt)

            if not seo_pack_result:
                seo_pack_result = f"""📌 3 VIRAL TITLES ({target_country})
1. Amazing Viral Video - Must Watch!
2. Trending Short Story ({target_country} Edition)
3. Do Not Miss This Incredible Video!

📝 SEO DESCRIPTION
Watch this amazing story crafted for audience in {target_country}. Like, share, and subscribe for more viral content!

🔥 TOP 15 HASHTAGS
#Viral #{target_country.split()[0]} #Trending #Shorts #Reels #TikTok #VideoOfTheDay #MustWatch #AIStudio #ContentCreator #SEO #ExplorePage #FYP #DailyContent #PiumanthaDamith"""

            main_progress.progress(100)
            status_text.success("🎉 Processing & 100% Exact Auto Sync Completed Successfully!")

            # Final Output & Saved Path Section
            st.divider()
            st.subheader("🎬 Final Video Output & Saved Path")
            st.video("final_output.mp4")
            
            st.subheader("📁 Saved Video File Path Bar")
            st.code(output_video_path, language="text")

            col1, col2 = st.columns([1, 1])
            with col1:
                with open("final_output.mp4", "rb") as file:
                    st.download_button(
                        label="📥 Download Processed Video (MP4)",
                        data=file,
                        file_name="Final_AI_Studio_Video.mp4",
                        mime="video/mp4"
                    )

            # SEO Pack Display
            st.divider()
            st.subheader(f"🚀 Social Media SEO Pack (Target Country: {target_country})")
            st.text_area("Auto Generated SEO Result:", seo_pack_result, height=280)

        except Exception as e:
            st.error(f"Error occurred: {str(e)}")

# Footer Credit
st.markdown('<div class="footer">Owner: @piumantha damith | 🇱🇰 Made in Sri Lanka</div>', unsafe_allow_html=True)