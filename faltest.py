import os
import time
import requests
import streamlit as st

st.set_page_config(page_title="🎨 DO AI Image Generator", page_icon="🎨", layout="centered")
st.title("🎨 DigitalOcean AI Image Generator")

MODEL_ACCESS_KEY = os.getenv("MODEL_ACCESS_KEY")
if not MODEL_ACCESS_KEY:
    st.error("Missing MODEL_ACCESS_KEY environment variable. Get one at https://cloud.digitalocean.com/gen-ai/model-access-keys")
    st.stop()

# Model selection
model_options = {
    "Flux Schnell (Fast)": "fal-ai/flux/schnell",
    "Fast SDXL (High Quality)": "fal-ai/fast-sdxl"
}

selected_model = st.selectbox("Choose AI Model:", list(model_options.keys()))
model_id = model_options[selected_model]

prompt = st.text_area("Enter your image prompt:", 
    "A whimsical illustration of Pikachu playing tennis in front of the Golden Gate Bridge in a tennis skirt with a visor.")

if st.button("Generate Image"):
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
                if image_url:
                    st.success("✅ Image ready!")
                    st.image(image_url, caption=prompt, width='stretch')
                    break
            elif status in ["failed", "error"]:
                st.error("❌ Image generation failed")
                st.json(result)
                break
        else:
            st.warning("Timed out waiting for image.")

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
