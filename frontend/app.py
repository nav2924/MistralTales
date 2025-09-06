# frontend/app.py

import streamlit as st
import requests
import time

API_URL = "http://localhost:8000/generate_story"

st.set_page_config(page_title="Text-to-Image Story Generator", layout="centered")
st.title("📖 Text-to-Image Story Generator")

st.markdown("Enter a story idea and watch it come to life with AI-generated images!")

with st.form("story_form"):
    prompt = st.text_area("Story Idea", "A lonely robot finds a flower in a post-apocalyptic city.")
    genre = st.selectbox("Genre", ["Fantasy", "Sci-fi", "Mystery", "Comedy"])
    tone = st.selectbox("Tone", ["Lighthearted", "Dark", "Epic", "Hopeful"])
    audience = st.selectbox("Target Audience", ["Kids", "Teens", "Adults"])
    submitted = st.form_submit_button("Generate Story")

if submitted:
    with st.spinner("Generating story and images..."):
        response = requests.post(API_URL, json={
            "prompt": prompt,
            "genre": genre,
            "tone": tone,
            "audience": audience
        })

        if response.status_code == 200:
            story_data = response.json()
            for i, scene in enumerate(story_data["scenes"], start=1):
                st.subheader(f"Scene {i}")
                st.write(scene["text"])

                try:
                    if scene.get("image_path"):
                        image_url = scene["image_path"].strip()
                        time.sleep(1)  # 👈 Delay to ensure image is ready
                        st.image(image_url, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not load image from: {scene['image_path']}. Error: {e}")
        else:
            st.error("Failed to generate story. Please check your backend.")
