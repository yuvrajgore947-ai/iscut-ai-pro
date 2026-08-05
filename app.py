import streamlit as st
import os
import time
import requests
import asyncio
import edge_tts
import json
import subprocess

# --- à¥§. à¤®à¥à¤–à¥à¤¯ à¤•à¥‰à¤¨à¥à¤«à¤¿à¤—à¤°à¥‡à¤¶à¤¨ à¤†à¤£à¤¿ à¤¸à¥à¤°à¤•à¥à¤·à¤¾ ---
st.set_page_config(page_title="DesiCut AI Pro", page_icon="ðŸŽ¬", layout="centered")

# API à¤•à¥€ à¤¸à¥à¤°à¤•à¥à¤·à¤¿à¤¤à¤ªà¤£à¥‡ à¤®à¤¿à¤³à¤µà¤£à¥‡
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    PEXELS_API_KEY = st.secrets["PEXELS_API_KEY"]
except Exception:
    st.error("ðŸš¨ à¤¤à¥à¤°à¥à¤Ÿà¥€: à¤•à¥ƒà¤ªà¤¯à¤¾ Hugging Face Settings à¤®à¤§à¥à¤¯à¥‡ à¤¤à¥à¤®à¤šà¥à¤¯à¤¾ API Keys à¤¸à¥‡à¤Ÿ à¤•à¤°à¤¾!")
    st.stop()

st.title("ðŸŽ¬ DesiCut AI - à¤¨à¤‚à¤¬à¤° à¥§ à¤¹à¤¾à¤¯-à¤ªà¥à¤°à¥‰à¤«à¤¿à¤Ÿ à¤Ÿà¥‚à¤²")
st.write("à¤«à¤•à¥à¤¤ à¥§ à¤•à¥à¤²à¤¿à¤•à¤®à¤§à¥à¤¯à¥‡ à¤µà¥à¤¹à¤¿à¤¡à¤¿à¤“ à¤¤à¤¯à¤¾à¤° à¤•à¤°à¤¾ à¤†à¤£à¤¿ à¤¸à¥‹à¤¶à¤² à¤®à¥€à¤¡à¤¿à¤¯à¤¾à¤µà¤°à¥‚à¤¨ à¤ªà¥ˆà¤¸à¥‡ à¤•à¤®à¤µà¤¾!")

# --- à¥¨. à¤¯à¥à¤à¤° à¤¡à¥…à¤¶à¤¬à¥‹à¤°à¥à¤¡ (Sidebar) ---
if "user_credits" not in st.session_state:
    st.session_state["user_credits"] = 5

st.sidebar.header("ðŸ‘¤  à¤¤à¥à¤®à¤šà¥‡ à¤–à¤¾à¤¤à¥‡ (à¤®à¥‹à¤¬à¤¾à¤ˆà¤²)")
user_id = st.sidebar.text_input("à¤¯à¥à¤à¤° à¤†à¤¯à¤¡à¥€:", value="pro_user_india")
st.sidebar.write(f"ðŸª™ à¤¶à¤¿à¤²à¥à¤²à¤• à¤µà¥à¤¹à¤¿à¤¡à¤¿à¤“ à¤•à¥à¤°à¥‡à¤¡à¤¿à¤Ÿà¥à¤¸: **{st.session_state['user_credits']}**")

if st.sidebar.button("ðŸŽ à¤«à¥à¤°à¥€ à¤•à¥à¤°à¥‡à¤¡à¤¿à¤Ÿà¥à¤¸ à¤œà¥‹à¤¡à¤¾ (+à¥«)"):
    st.session_state["user_credits"] += 5
    st.sidebar.success("à¥« à¤•à¥à¤°à¥‡à¤¡à¤¿à¤Ÿà¥à¤¸ à¤¯à¤¶à¤¸à¥à¤µà¥€à¤°à¤¿à¤¤à¥à¤¯à¤¾ à¤œà¥‹à¤¡à¤²à¥‡ à¤—à¥‡à¤²à¥‡!")

st.sidebar.markdown("---")
st.sidebar.subheader("ðŸ’Ž à¤ªà¥à¤°à¥€à¤®à¤¿à¤¯à¤® à¤ªà¥à¤²à¥…à¤¨ à¤°à¤¿à¤šà¤¾à¤°à¥à¤œ")
st.sidebar.write("ðŸ’³ UPI ID: `yourupi@okaxis`")
st.sidebar.write("ðŸ’¬ [WhatsApp à¤•à¤°à¤¾](https://wa.me) à¤†à¤£à¤¿ à¤…à¤®à¤°à¥à¤¯à¤¾à¤¦ à¤•à¥à¤°à¥‡à¤¡à¤¿à¤Ÿà¥à¤¸ à¤®à¤¿à¤³à¤µà¤¾.")

# --- à¥©. à¤‡à¤¨à¤ªà¥à¤Ÿ à¤«à¥‰à¤°à¥à¤® à¤†à¤£à¤¿ à¤¸à¥‡à¤«à¥à¤Ÿà¥€ à¤—à¤¾à¤°à¥à¤¡ ---
topic = st.text_input("à¤¤à¥à¤®à¥à¤¹à¤¾à¤šà¥à¤¯à¤¾ à¤µà¥à¤¹à¤¿à¤¡à¤¿à¤“à¤šà¤¾ à¤µà¤¿à¤·à¤¯ à¤²à¤¿à¤¹à¤¾ (à¤‰à¤¦à¤¾. à¤­à¤¾à¤°à¤¤à¤¾à¤¤à¥€à¤² à¥© à¤°à¤¹à¤¸à¥à¤¯à¤®à¤¯à¥€ à¤•à¤¿à¤²à¥à¤²à¥‡):")
lang = st.selectbox("à¤µà¥à¤¹à¤¿à¤¡à¤¿à¤“à¤šà¥€ à¤­à¤¾à¤·à¤¾ à¤¨à¤¿à¤µà¤¡à¤¾:", ["mr", "hi", "en"], format_func=lambda x: {"mr": "à¤®à¤°à¤¾à¤ à¥€", "hi": "à¤¹à¤¿à¤‚à¤¦à¥€", "en": "English"}[x])
duration = st.slider("à¤µà¥à¤¹à¤¿à¤¡à¤¿à¤“à¤šà¥€ à¤²à¤¾à¤‚à¤¬à¥€ (à¤¸à¥‡à¤•à¤‚à¤¦):", 15, 30, 60, value=30)

def legal_safety_guard(text):
    bad_words = ["scam", "hack", "riot", "adult", "à¤¦à¤‚à¤—à¤²", "à¤…à¤¶à¥à¤²à¥€à¤²", "à¤˜à¥‹à¤Ÿà¤¾à¤³à¤¾", "à¤¹à¥…à¤•", "à¤®à¤°à¥à¤¡à¤°", "à¤•à¥à¤°à¥…à¤¶"]
    for word in bad_words:
        if word in text.lower():
            return False
    return True

# --- à¥ª. à¤†à¤µà¤¾à¤œ à¤¨à¤¿à¤°à¥à¤®à¤¿à¤¤à¥€ (Edge-TTS) ---
async def generate_edge_voice(text, output_path, lang_code):
    voice_map = {"mr": "mr-IN-NeerjaNeural", "hi": "hi-IN-MadhuramNeural", "en": "en-IN-NeerjaNeural"}
    chosen_voice = voice_map.get(lang_code, "hi-IN-MadhuramNeural")
    communicate = edge_tts.Communicate(text, chosen_voice)
    await communicate.save(output_path)

# --- à¥«. à¤®à¥à¤–à¥à¤¯ à¤°à¥‡à¤‚à¤¡à¤°à¤¿à¤‚à¤— à¤‡à¤‚à¤œà¤¿à¤¨ ---
if st.button("ðŸš€ à¤µà¥à¤¹à¤¿à¤¡à¤¿à¤“ à¤œà¤¨à¤°à¥‡à¤Ÿ à¤•à¤°à¤¾"):
    if not topic:
        st.warning("âš ï¸ à¤•à¥ƒà¤ªà¤¯à¤¾ à¤†à¤§à¥€ à¤µà¤¿à¤·à¤¯ à¤²à¤¿à¤¹à¤¾!")
    elif not legal_safety_guard(topic):
        st.error("ðŸš¨ à¤¸à¥à¤°à¤•à¥à¤·à¤¾ à¤¬à¥à¤²à¥‰à¤•: à¤¹à¤¾ à¤µà¤¿à¤·à¤¯ à¤†à¤®à¤šà¥à¤¯à¤¾ à¤•à¤¾à¤¯à¤¦à¥‡à¤¶à¥€à¤° à¤§à¥‹à¤°à¤£à¤¾à¤‚à¤šà¥‡ à¤‰à¤²à¥à¤²à¤‚à¤˜à¤¨ à¤•à¤°à¤¤à¥‹!")
    elif st.session_state["user_credits"] <= 0:
        st.error("âŒ à¤…à¤ªà¥à¤°à¥‡ à¤•à¥à¤°à¥‡à¤¡à¤¿à¤Ÿà¥à¤¸! à¤•à¥ƒà¤ªà¤¯à¤¾ à¤ªà¥à¤¢à¥‡ à¤œà¤¾à¤£à¥à¤¯à¤¾à¤¸à¤¾à¤ à¥€ à¤°à¤¿à¤šà¤¾à¤°à¥à¤œ à¤•à¤°à¤¾.")
    else:
        timestamp = int(time.time())
        voice_f = f"voice_{user_id}_{timestamp}.mp3"
        srt_f = f"captions_{user_id}_{timestamp}.srt"
        broll_f = f"broll_{user_id}_{timestamp}.mp4"
        final_out = f"final_{user_id}_{timestamp}.mp4"
        
        with st.spinner("â³ à¤¸à¤¿à¤¸à¥à¤Ÿà¥€à¤® à¤¬à¥…à¤•à¤à¤‚à¤¡à¤²à¤¾ à¤•à¤¾à¤® à¤•à¤°à¤¤ à¤†à¤¹à¥‡... à¤•à¥ƒà¤ªà¤¯à¤¾ à¥§ à¤®à¤¿à¤¨à¤¿à¤Ÿ à¤¥à¤¾à¤‚à¤¬à¤¾..."):
            try:
                # --- à¤¸à¥à¤Ÿà¥‡à¤ª à¥§: OpenAI à¤•à¤¡à¥‚à¤¨ à¤¸à¥à¤•à¥à¤°à¤¿à¤ªà¥à¤Ÿ à¤®à¤¿à¤³à¤µà¤£à¥‡ ---
                headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
                prompt = (
                    f"You are a short video script writer. Output a single strict JSON object. "
                    f"Write a short video script about '{topic}' in language code '{lang}'. "
                    f"Keep it under {duration} words. Also provide exactly ONE single English search keyword for background stock footage. "
                    f"Output MUST be a JSON object with keys: 'script' and 'keyword'."
                )
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}
                }
                res_gpt = requests.post("https://openai.com", headers=headers, json=payload, timeout=30).json()
                
                raw_content = res_gpt["choices"][0]["message"]["content"].strip()
                if raw_content.startswith("```json"):
                    raw_content = raw_content[7:-3].strip()
                elif raw_content.startswith("```"):
                    raw_content = raw_content[3:-3].strip()
                
                data = json.loads(raw_content)
                script_text = data["script"]
                keyword = data["keyword"]
                
                st.info(f"ðŸ“‹ **à¤¤à¤¯à¤¾à¤° à¤à¤¾à¤²à¥‡à¤²à¥€ à¤¸à¥à¤•à¥à¤°à¤¿à¤ªà¥à¤Ÿ:** {script_text}")
                st.info(f"ðŸ” **à¤¶à¥‹à¤§à¤²à¥‡à¤²à¤¾ à¤•à¥€à¤µà¤°à¥à¤¡:** {keyword}")

                # --- à¤¸à¥à¤Ÿà¥‡à¤ª à¥¨: à¤‘à¤¡à¤¿à¤“ à¤¤à¤¯à¤¾à¤° à¤•à¤°à¤£à¥‡ ---
                try:
                    asyncio.run(generate_edge_voice(script_text, voice_f, lang))
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(generate_edge_voice(script_text, voice_f, lang))

                # --- à¤¸à¥à¤Ÿà¥‡à¤ª à¥©: à¤¸à¤¬à¤Ÿà¤¾à¤¯à¤Ÿà¤²à¥à¤¸ (SRT) à¤¤à¤¯à¤¾à¤° à¤•à¤°à¤£à¥‡ ---
                words = script_text.split()
                with open(srt_f, "w", encoding="utf-8") as f:
                    f.write("1\n00:00:00,000 --> 00:00:05,000\n" + " ".join(words[:max(1, len(words)//2)]) + "\n\n")
                    f.write("2\n00:00:05,000 --> 00:00:30,000\n" + " ".join(words[max(1, len(words)//2):]) + "\n\n")

                # --- STEP à¥ª: Pexels à¤µà¥à¤¹à¤¿à¤¡à¤¿à¤“ à¤¡à¤¾à¤Šà¤¨à¤²à¥‹à¤¡ à¤•à¤°à¤£à¥‡ ---
                pex_url = f"https://pexels.com{keyword}&per_page=1&orientation=portrait"
                pex_headers = {"Authorization": PEXELS_API_KEY}
                res_pex = requests.get(pex_url, headers=pex_headers, timeout=30).json()

                video_download_url = None
                
                if "videos" in res_pex and len(res_pex["videos"]) > 0:
                    first_video = res_pex["videos"][0]
                    files = first_video.get("video_files", [])
                    if len(files) > 0:
                        video_download_url = files[0]["link"]
                else:
                    st.warning("âš ï¸ à¤®à¥à¤–à¥à¤¯ à¤•à¥€à¤µà¤°à¥à¤¡à¤µà¤° à¤µà¥à¤¹à¤¿à¤¡à¤¿à¤“ à¤¸à¤¾à¤ªà¤¡à¤²à¤¾ à¤¨à¤¾à¤¹à¥€, 'nature' à¤µà¤°à¥‚à¤¨ à¤µà¥à¤¹à¤¿à¤¡à¤¿à¤“ à¤˜à¥‡à¤¤à¤²à¤¾ à¤œà¤¾à¤¤ à¤†à¤¹à¥‡.")
                    backup_url = "https://pexels.comnature&per_page=1&orientation=portrait"
                    res_back = requests.get(backup_url, headers=pex_headers, timeout=30).json()
                    if "videos" in res_back and len(res_back["videos"]) > 0:
                        first_video = res_back["videos"][0]
                        files = first_video.get("video_files", [])
                        if len(files) > 0:
                            video_download_url = files[0]["link"]

                if video_download_url:
                    video_data = requests.get(video_download_url, timeout=30).content
                    with open(broll_f, "wb") as f:
                        f.write(video_data)
                else:
                    st.error("âŒ Pexels à¤•à¤¡à¥‚à¤¨ à¤•à¥‹à¤£à¤¤à¤¾à¤¹à¥€ à¤µà¥à¤¹à¤¿à¤¡à¤¿à¤“ à¤¡à¤¾à¤Šà¤¨à¤²à¥‹à¤¡ à¤•à¤°à¤¤à¤¾ à¤†à¤²à¤¾ à¤¨à¤¾à¤¹à¥€.")
                    st.stop()

                # --- à¤¸à¥à¤Ÿà¥‡à¤ª à¥«: FFmpeg à¤®à¤¿à¤•à¥à¤¸à¤¿à¤‚à¤— à¤†à¤£à¤¿ à¤°à¥‡à¤‚à¤¡à¤°à¤¿à¤‚à¤— ---
                safe_srt_f = srt_f.replace('\\', '/')
                sub_style = "force_style='Alignment=6,FontSize=18,PrimaryColour=&H0000FFFF,FontName=Impact'"
                
                cmd = [
                    "ffmpeg", "-y", 
                    "-i", broll_f, 
                    "-i", voice_f, 
                    "-vf", f"scale=1080:1920,subtitles='{safe_srt_f}':{sub_style}", 
                    "-map", "0:v:0", "-map", "1:a:0", 
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", 
                    "-c:a", "aac", "-shortest", final_out
                ]
                
                subprocess.run(cmd, check=True)

                st.session_state["user_credits"] -= 1
                st.success("ðŸŽ‰ à¤¤à¥à¤®à¤šà¤¾ à¤¹à¤¾à¤¯-à¤•à¥à¤µà¤¾à¤²à¤¿à¤Ÿà¥€ à¤µà¥à¤¹à¤¿à¤¡à¤¿à¤“ à¤¯à¤¶à¤¸à¥à¤µà¥€à¤°à¤¿à¤¤à¥à¤¯à¤¾ à¤¤à¤¯à¤¾à¤° à¤à¤¾à¤²à¤¾ à¤†à¤¹à¥‡!")
                
                with open(final_out, "rb") as file:
                    st.video(file)
                    st.download_button(label="ðŸ“¥ à¤…à¤‚à¤¤à¤¿à¤® à¤µà¥à¤¹à¤¿à¤¡à¤¿à¤“ à¤¡à¤¾à¤Šà¤¨à¤²à¥‹à¤¡ à¤•à¤°à¤¾", data=file, file_name="desicut_viral_short.mp4", mime="video/mp4")

            except Exception as e:
                st.error(f"âŒ à¤¸à¤¿à¤¸à¥à¤Ÿà¥€à¤®à¤®à¤§à¥à¤¯à¥‡ à¤à¤°à¤° à¤†à¤²à¥€ à¤†à¤¹à¥‡: {str(e)}")
            
            finally:
                # --- à¥¬. à¤•à¤šà¤°à¤¾ à¤«à¤¾à¤ˆà¤²à¥à¤¸ à¤¸à¤¾à¤« à¤•à¤°à¤£à¥‡ ---
                for f in [voice_f, srt_f, broll_f, final_out]:
                    if os.path.exists(f):
                        try:
                            os.remove(f)
                        except Exception:
                            pass

# --- à¥­. Footer ---
st.markdown("---")
st.caption("***AI Disclaimer:** This video, voice, and script are generated using artificial intelligence automated systems via Edge-TTS and OpenAI. Users must manually review all content before uploading to social media platforms. DesiCut AI holds no liability for user-generated media.")
