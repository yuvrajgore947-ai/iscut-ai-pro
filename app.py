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
            try:
                # --- स्टेप १: OpenAI कडून स्क्रिप्ट मिळवणे ---
                url = "https://openai.com"
                headers = {
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                prompt = (
                    f"You are a short video script writer. Output a single JSON object. "
                    f"Write a short video script about '{topic}' in language code '{lang}'. "
                    f"Keep it under {duration} seconds. "
                    f"IMPORTANT: Provide a matching short search 'keyword' in strict ENGLISH language for Pexels video search. "
                    f"Output MUST be a JSON object with exactly two keys: 'script' and 'keyword'."
                )
                
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": { "type": "json_object" }
                }
                
                response = requests.post(url, headers=headers, json=payload)
                res_json = response.json()
                
                raw_content = res_json['choices'][0]['message']['content']
                
                if raw_content.startswith("```json"):
                    raw_content = raw_content[7:-3].strip()
                elif raw_content.startswith("```"):
                    raw_content = raw_content[3:-3].strip()
                    
                data = json.loads(raw_content)
                script_text = data.get("script", "")
                keyword = data.get("keyword", "nature")
                
                st.info(f"**मजकूर तयार झाला आहे:** {script_text}")
                st.info(f"**शोधलेला कीवर्ड (Pexels साठी):** {keyword}")

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
                    st.warning("⚠️ मुख्य कीवर्डवर व्हिडिओ सापडला नाही, बॅकअप व्हिडिओ वापरत आहे...")
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

                st.session_state["user_credits"] -= 1
                st.success("🎉 तुमचा हाय-प्रॉफिट व्हिडिओ यशस्वीरीत्या तयार झाला आहे!")

                with open(final_out, "rb") as file:
                    st.video(file)
                    st.download_button(label="📥 व्हिडिओ डाउनलोड करा", data=file.read(), file_name="desicut_video.mp4", mime="video/mp4")

            except Exception as e:
                st.error(f"❌ व्हिडिओ मिक्सिंगमध्ये एरर आला: {str(e)}")

            finally:
                for f in [voice_f, srt_f, broll_f, final_out]:
                    if os.path.exists(f):
                        try:
                            os.remove(f)
                        except Exception:
                            pass
