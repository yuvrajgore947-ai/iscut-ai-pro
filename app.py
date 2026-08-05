import streamlit as st
import os
import time
import requests
import asyncio
import edge_tts
import json
import subprocess

# --- १. मुख्य कॉन्फिगरेशन आणि सुरक्षा ---
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

if not PEXELS_API_KEY:
    st.error("🚨 त्रुटी: सर्व्हरवर PEXELS_API_KEY सापडली नाही! कृपया Render Environment Variables तपासा.")
    st.stop()

st.title("🎬 DesiCut AI - नंबर १ हाय-प्रॉफिट टूल")
st.write("फक्त १ क्लिकमध्ये व्हिडिओ तयार करा आणि सोशल मीडियावरून पैसे कमवा!")

# --- २. युझर डॅशबोर्ड (Sidebar) ---
if "user_credits" not in st.session_state:
    st.session_state["user_credits"] = 5

st.sidebar.header("👤  तुमचे खाते (मोबाईल)")
user_id = st.sidebar.text_input("युझर आयडी:", value="pro_user_india")
st.sidebar.write(f"🪙  शिल्लक व्हिडिओ क्रेडिट्स: **{st.session_state['user_credits']}**")

if st.sidebar.button("🎁  फ्री क्रेडिट्स जोडा (+५)"):
    st.session_state["user_credits"] += 5
    st.sidebar.success("🎉  क्रेडिट्स यशस्वीरीत्या जोडले गेले!")

st.sidebar.markdown("---")
st.sidebar.subheader("💎  प्रीमियम प्लॅन रिचार्ज")
st.sidebar.write("💳  UPI ID: `yourupi@okaxis`")
st.sidebar.write("💬  [WhatsApp करा](https://wa.me) आणि अमर्याद क्रेडिट्स मिळवा.")

# --- ३. इनपुट फॉर्म आणि लांबी गार्ड ---
topic = st.text_input("तुमच्या व्हिडिओचा विषय लिहा (उदा. भारतातील ३ रहस्यमयी किल्ले):")
lang = st.selectbox("व्हिडिओची भाषा निवडा:", ["mr", "hi", "en"], format_func=lambda x: "मराठी" if x=="mr" else "हिंदी" if x=="hi" else "English")
duration = st.slider("व्हिडिओची लांबी (सेकंद):", min_value=15, max_value=60, value=30)

def legal_safety_guard(text):
    bad_words = ["scam", "hack", "riot", "adult", "दंगा", "अश्लील", "घोटाळा"]
    for word in bad_words:
        if word in text.lower():
            return False
    return True

# --- ४. आवाज निर्मिती (Edge-TTS) ---
async def generate_edge_voice(text, output_path, lang_code):
    voice_map = {"mr": "mr-IN-NeerjaNeural", "hi": "hi-IN-MadhuramNeural", "en": "en-US-GuyNeural"}
    chosen_voice = voice_map.get(lang_code, "hi-IN-MadhuramNeural")
    communicate = edge_tts.Communicate(text, chosen_voice)
    await communicate.save(output_path)

# --- ५. मुख्य रेंडरिंग इंजिन ---
if st.button("🎬 व्हिडिओ जनरेट करा"):
    if not topic:
        st.warning("⚠️ कृपया आधी विषय लिहा!")
    elif not legal_safety_guard(topic):
        st.error("❌ सुरक्षा ब्लॉक: हा विषय आमच्या कायदेशीर धोरणांचे उल्लंघन करतो!")
    elif st.session_state["user_credits"] <= 0:
        st.error("❌ अपुरे क्रेडिट्स! कृपया पुढे जाण्यासाठी रिचार्ज करा.")
    else:
        timestamp = int(time.time())
        voice_f = f"voice_{user_id}_{timestamp}.mp3"
        srt_f = f"captions_{user_id}_{timestamp}.srt"
        broll_f = f"broll_{user_id}_{timestamp}.mp4"
        final_out = f"final_{user_id}_{timestamp}.mp4"

        with st.spinner("⏳ सिस्टीम बॅकएंडला काम करत आहे... कृपया १ मिनिट थांबा..."):
            script_text = ""
            keyword = "nature"
            
            # --- स्टेप १: स्क्रिप्ट मिळवणे (OpenAI सह, अयशस्वी झाल्यास फ्री बॅकअप एआय) ---
            try:
                if not OPENAI_API_KEY:
                    raise ValueError("OpenAI Key missing, switching to backup AI.")
                
                url = "https://openai.com"
                headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
                prompt = (
                    f"Write a short video script about '{topic}' in language code '{lang}'. "
                    f"Keep it under {duration} seconds. Provide a single matching search 'keyword' in strict ENGLISH for video search. "
                    f"Output MUST be a valid JSON with exactly two keys: 'script' and 'keyword'."
                )
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": { "type": "json_object" }
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=15)
                res_json = response.json()
                
                if "error" in res_json or "choices" not in res_json:
                    raise ValueError("OpenAI Quota Exceeded or Error, switching to backup AI.")
                    
                raw_content = res_json['choices']['message']['content'].strip()
                if raw_content.startswith("```json"): raw_content = raw_content[7:-3].strip()
                elif raw_content.startswith("```"): raw_content = raw_content[3:-3].strip()
                
                data = json.loads(raw_content)
                script_text = data.get("script", "")
                keyword = data.get("keyword", "nature")
                
            except Exception as openai_err:
                # जर OpenAI चे क्रेडिट्स संपले असतील तर हा फ्री बॅकअप एआय सुरू होईल
                st.warning("⚠️ OpenAI लायसन्स/क्रेडिट मर्यादा आली आहे. फ्री बॅकअप AI वापरून स्क्रिप्ट बनवत आहे...")
                try:
                    hf_url = "https://huggingface.co"
                    hf_prompt = f"<|im_start|>user\nWrite a short video script about '{topic}' in language code '{lang}'. Keep it simple. Then provide a matching English search keyword for video. Format your answer as a JSON object with keys 'script' and 'keyword'. Do not write anything else.<|im_end|>\n<|im_start|>assistant\n"
                    
                    hf_res = requests.post(hf_url, json={"inputs": hf_prompt, "parameters": {"max_new_tokens": 300}}, timeout=20)
                    hf_json = hf_res.json()
                    
                    generated_text = hf_json[0]['generated_text'].split("<|im_start|>assistant\n")[-1].strip()
                    if generated_text.startswith("```json"): generated_text = generated_text[7:-3].strip()
                    elif generated_text.startswith("```"): generated_text = generated_text[3:-3].strip()
                    
                    data = json.loads(generated_text)
                    script_text = data.get("script", f"व्हिडिओ विषय: {topic}")
                    keyword = data.get("keyword", "nature")
                except Exception as hf_err:
                    st.error("❌ सर्व AI सर्व्हर व्यस्त आहेत. कृपया थोड्या वेळाने प्रयत्न करा.")
                    st.stop()

            st.info(f"**मजकूर तयार झाला आहे:** {script_text}")
            st.info(f"**शोधलेला कीवर्ड (Pexels साठी):** {keyword}")

            try:
                # --- STEP २: ऑडिओ तयार करणे ---
                try:
                    asyncio.run(generate_edge_voice(script_text, voice_f, lang))
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(generate_edge_voice(script_text, voice_f, lang))

                # --- STEP ३: सबटायटल्स (SRT) तयार करणे ---
                with open(srt_f, "w", encoding="utf-8") as f:
                    f.write("1\n")
                    f.write(f"00:00:00,000 --> 00:00:{int(duration):02d},000\n")
                    f.write(f"{script_text}\n\n")

                # --- STEP ४: Pexels कडून व्हिडिओ मिळवणे ---
                pex_url = f"https://pexels.com{keyword}&per_page=1&orientation=portrait"
                pex_headers = {"Authorization": PEXELS_API_KEY}
                
                res_pex_raw = requests.get(pex_url, headers=pex_headers, timeout=15)
                res_pex = res_pex_raw.json()

                video_download_url = None

                if "videos" in res_pex and len(res_pex["videos"]) > 0:
                    first_video = res_pex["videos"][0]
                    files = first_video.get("video_files", [])
                    for f_item in files:
                        if f_item.get("file_type") == "video/mp4" or "link" in f_item:
                            video_download_url = f_item.get("link")
                            break

                if not video_download_url:
                    st.warning("⚠️  मुख्य कीवर्डवर व्हिडिओ सापडला नाही, बॅकअप व्हिडिओ वापरत आहे...")
                    backup_url = "https://pexels.comnature&per_page=1&orientation=portrait"
                    res_back_raw = requests.get(backup_url, headers=pex_headers, timeout=15)
                    res_back = res_back_raw.json()
                    if "videos" in res_back and len(res_back["videos"]) > 0:
                        first_video = res_back["videos"][0]
                        files = first_video.get("video_files", [])
                        for f_item in files:
                            if f_item.get("file_type") == "video/mp4" or "link" in f_item:
                                video_download_url = f_item.get("link")
                                break

                if video_download_url:
                    video_data = requests.get(video_download_url, timeout=30).content
                    with open(broll_f, "wb") as f:
                        f.write(video_data)
                else:
                    st.error("❌ Pexels कडून कोणताही व्हिडिओ डाउनलोड करता आला नाही.")
                    st.stop()

                # --- STEP ५: FFmpeg मिक्सिंग आणि रेंडर ---
                safe_srt_f = srt_f.replace("\\", "/")
                
                cmd = [
                    "ffmpeg", "-y",
                    "-i", broll_f,
                    "-i", voice_f,
                    "-vf", f"scale=1080:1920,subtitles='{safe_srt_f}':force_style='Alignment=4,FontSize=18,PrimaryColour=&HFFFFFF&'",
                    "-map", "0:v:0", "-map", "1:a:0",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-shortest", final_out
                ]

                subprocess.run(cmd, check=True)

