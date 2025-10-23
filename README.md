# Generate Images via the new Flux Schnell (fast) or Fast SDXL (high-quality) models via Fal AI on DigitalOcean!

A simple Streamlit app that generates images, text-to-speech, and music text-to-audio (all from 1 prompt) using DigitalOcean's AI models via Fal AI.


## Setup

1. **Get a DigitalOcean Model Access Key**
   - Visit [DigitalOcean AI Model Access Keys](https://cloud.digitalocean.com/gen-ai/model-access-keys)
   - Create a new access key

2. **Set Environment Variable**
   ```bash
   export MODEL_ACCESS_KEY="your_access_key_here"
   ```

3. **Install Dependencies**
   ```bash
   pip install streamlit requests
   ```

4. **Run the App**
   ```bash
   streamlit run app.py
   ```

## Usage

1. Select your preferred AI model (Flux Schnell or Fast SDXL)
2. Enter your image prompt
3. Click "Generate Image"
4. ✨magic🪄
