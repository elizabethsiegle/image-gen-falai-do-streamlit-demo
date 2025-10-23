import os
import time
import requests
import streamlit as st

st.set_page_config(page_title="DO AI Multi-Modal AI Generator", page_icon="🌊", layout="centered")
st.title("DigitalOcean🌊 Multi-Modal AI Generator")
st.markdown("*Generate images, text-to-speech, and audio from a single prompt!*")

MODEL_ACCESS_KEY = os.getenv("MODEL_ACCESS_KEY")
if not MODEL_ACCESS_KEY:
    st.error("Missing MODEL_ACCESS_KEY environment variable. Get one at https://cloud.digitalocean.com/gen-ai/model-access-keys")
    st.stop()

# Model selection
model_options = {
    "fal-ai/flux/schnell (Fast)": "fal-ai/flux/schnell",
    "fal-ai/fast-sdxl (High Quality)": "fal-ai/fast-sdxl"
}

selected_model = st.selectbox("Choose AI Image-Gen Model:", list(model_options.keys()))
model_id = model_options[selected_model]

# Audio duration selection
audio_duration = st.selectbox(
    "Choose audio clip duration:", 
    [10, 20, 30, 40],
    help="Longer audio takes more time to generate"
)

prompt = st.text_area("Enter your prompt:", 
    "A whimsical illustration of Pikachu playing tennis in front of the Golden Gate Bridge in a tennis skirt with a visor.",
    help="This prompt will be used to generate an image, text-to-speech audio, and a musical interpretation!")

st.info("**What you'll get:** Image + Text-to-Speech + Musical Audio (all from your prompt!)")
st.markdown(f"*Audio clips will be {audio_duration} seconds long. Longer clips take longer to make*")


def generate_audio_content(prompt_text, model_id, content_type, audio_duration=10):
    """Generate audio content (TTS or text-to-audio) for the given prompt"""
    if model_id == "fal-ai/elevenlabs/tts/multilingual-v2":
        input_data = {"text": prompt_text}
    else:  # stable-audio-25
        input_data = {"prompt": prompt_text, "seconds_total": audio_duration}
    
    response = requests.post(
        "https://inference.do-ai.run/v1/async-invoke",
        headers={"Authorization": f"Bearer {MODEL_ACCESS_KEY}", "Content-Type": "application/json"},
        json={
            "model_id": model_id,
            "input": input_data,
            "tags": [{"key": "type", "value": "test"}]
        }
    )
    
    if response.status_code != 200:
        st.error(f"❌ {content_type} request failed ({response.status_code}): {response.text}")
        st.json({"request_payload": {"model_id": model_id, "input": input_data}})
        return None
    
    request_id = response.json().get("id") or response.json().get("request_id")
    if not request_id:
        st.error(f"❌ No request ID returned for {content_type}")
        return None
    
    result_url = f"https://inference.do-ai.run/v1/async-invoke/{request_id}"
    headers = {"Authorization": f"Bearer {MODEL_ACCESS_KEY}"}
    
    # Poll for completion with longer timeout for audio generation
    max_attempts = 60 if "audio" in model_id.lower() else 30  # 3 minutes for audio, 90s for TTS
    
    for attempt in range(max_attempts):
        time.sleep(3)
        poll = requests.get(result_url, headers=headers)
        
        if poll.status_code != 200:
            continue
            
        result = poll.json()
        status = result.get("status", "").lower()
        
        if status == "completed":
            output = result.get("output", {})
            
            # Try different possible audio URL keys and handle nested structures
            audio_url = None
            
            # Direct URL keys
            if output.get("audio_url"):
                audio_url = output.get("audio_url")
            elif output.get("url"):
                audio_url = output.get("url")
            elif output.get("file_url"):
                audio_url = output.get("file_url")
            # Handle nested audio object (common with ElevenLabs)
            elif output.get("audio"):
                audio_obj = output.get("audio")
                if isinstance(audio_obj, dict):
                    audio_url = (audio_obj.get("url") or 
                               audio_obj.get("audio_url") or 
                               audio_obj.get("file_url") or
                               audio_obj.get("download_url"))
                elif isinstance(audio_obj, str):
                    audio_url = audio_obj
            
            if audio_url:
                return audio_url
            else:
                st.error(f"❌ No audio URL found in {content_type} output")
                st.json(output)
                return None
                
        elif status in ["failed", "error"]:
            st.error(f"❌ {content_type} generation failed with status: {status}")
            st.json(result)
            return None
    
    # Show appropriate timeout message based on model
    timeout_seconds = max_attempts * 3
    st.warning(f"⏱️ {content_type} generation timed out after {timeout_seconds} seconds")
    return None

if st.button("Generate Image + Audio 🪄"):
    # First, generate the image
    with st.spinner("Generating image..."):
        # Submit request
        response = requests.post(
            "https://inference.do-ai.run/v1/async-invoke",
            headers={"Authorization": f"Bearer {MODEL_ACCESS_KEY}", "Content-Type": "application/json"},
            json={"model_id": model_id, "input": {"prompt": prompt}}
        )
        
        if response.status_code != 200:
            st.error(f"Request failed ({response.status_code}): {response.text}")
            st.stop()

        request_id = response.json().get("id") or response.json().get("request_id")

        # Poll for completion
        result_url = f"https://inference.do-ai.run/v1/async-invoke/{request_id}"
        headers = {"Authorization": f"Bearer {MODEL_ACCESS_KEY}"}
        
        image_url = None
        for _ in range(30):  # 30 attempts, 3s each = 90s max
            time.sleep(3)
            poll = requests.get(result_url, headers=headers)
            
            if poll.status_code != 200:
                continue
                
            result = poll.json()
            status = result.get("status", "").lower()
            
            if status =="completed":
                output = result.get("output", {})
                print(output)
                image_url = output.get("images", [{}])[0].get("url")
                break
            elif status in ["failed", "error"]:
                st.error("❌ Image generation failed")
                st.json(result)
                break
        else:
            st.warning("Timed out waiting for image.")
    
    # Display the image if successful
    if image_url:
        st.success("✅ Image ready!")
        st.image(image_url, caption=prompt, width='stretch')
        
        # Generate audio content after image is ready
        st.divider()
        st.subheader("Generated Audio")
        
        # Create columns for TTS and Text-to-Audio
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🗣️ Text-to-Speech (TTS) w/ fal-ai/elevenlabs/tts/multilingual-v2**")
            with st.spinner("Generating TTS..."):
                # Use a shorter, simpler text for TTS
                tts_text = f"Here is your image: {prompt[:100]}..." if len(prompt) > 100 else prompt
                tts_url = generate_audio_content(
                    tts_text, 
                    "fal-ai/elevenlabs/tts/multilingual-v2", 
                    "TTS",
                    audio_duration
                )
            
            if tts_url:
                st.audio(tts_url, format="audio/wav")
            else:
                st.error("❌ TTS generation failed")
        
        with col2:
            st.write("**🎼 Text-to-Audio w/ fal-ai/stable-audio-25/text-to-audio**")
            with st.spinner("Generating audio..."):
                # Use a more musical prompt for audio generation
                audio_prompt = f"Epic cinematic music inspired by: {prompt[:50]}"
                audio_url = generate_audio_content(
                    audio_prompt, 
                    "fal-ai/stable-audio-25/text-to-audio", 
                    "Text-to-Audio",
                    audio_duration
                )
            
            if audio_url:
                st.audio(audio_url, format="audio/wav")
            else:
                st.error("❌ Audio generation failed")

# Sticky footer
st.markdown("""
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: #0e1117;
    color: white;
    text-align: center;
    padding: 10px;
    border-top: 1px solid #262730;
    font-size: 14px;
}
</style>
<div class="footer">
    made w/ ❤️ in sf🌉 | view code👩🏻‍💻: <a href="https://github.com/elizabethsiegle/image-gen-falai-do-streamlit-demo" target="_blank" style="color: #ff6b6b;">on github</a>
</div>
""", unsafe_allow_html=True)
