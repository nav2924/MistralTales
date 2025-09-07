# frontend/branching.py
import os
import time
import requests
import streamlit as st

API = os.getenv("API", "http://localhost:8000")

st.set_page_config(page_title="StoryGen – Branching", layout="wide")
st.title("🌿 Branching Story Mode")

# -------------- helpers --------------
def _start_session(seed: str, genre: str, tone: str, audience: str, scenes: int):
    r = requests.post(
        f"{API}/story/start",
        json={
            "prompt": seed,
            "genre": None if genre == "Any" else genre,
            "tone": None if tone == "Any" else tone,
            "audience": None if audience == "Any" else audience,
            "scenes": scenes,
        },
    )
    if not r.ok:
        st.error(f"Failed to start session: {r.text}")
        return
    data = r.json()
    st.session_state["session_id"] = data["session_id"]
    st.session_state["beats"] = data["beats"] or []
    st.session_state["images"] = []
    st.session_state["current_step"] = 0
    st.session_state["choices_made"] = []  # chosen indices per step
    st.success(f"Session started: {data['session_id']}")

def _branch(choice_idx: int, step: int):
    r = requests.post(
        f"{API}/story/branch",
        json={
            "session_id": st.session_state["session_id"],
            "choice_idx": choice_idx,
            "step": step,
        },
    )
    if not r.ok:
        try:
            st.error(f"Branching failed: {r.json().get('detail')}")
        except Exception:
            st.error(f"Branching failed: {r.text}")
        return False
    data = r.json()
    st.session_state["beats"] = data.get("beats", st.session_state["beats"])
    return True

def _render_images():
    r = requests.post(f"{API}/story/render", params={"session_id": st.session_state["session_id"]})
    if not r.ok:
        st.error(f"Render failed: {r.text}")
        return
    st.session_state["images"] = r.json().get("images", [])

# -------------- sidebar --------------
with st.sidebar:
    seed = st.text_area("Prompt", "A lonely robot finds a flower in a post-apocalyptic city.")
    scenes = st.slider("Scenes", 3, 6, 4)
    genre = st.selectbox("Genre", ["Any", "Fantasy", "Sci-fi", "Mystery"], index=0)
    tone = st.selectbox("Tone", ["Any", "Light", "Dark", "Epic"], index=1)
    audience = st.selectbox("Audience", ["Any", "Kids", "Teens", "Adults"], index=2)

    cols_sb = st.columns(2)
    if cols_sb[0].button("Start Session", use_container_width=True):
        _start_session(seed, genre, tone, audience, scenes)
    if cols_sb[1].button("Reset", use_container_width=True):
        for k in ["session_id", "beats", "images", "current_step", "choices_made"]:
            st.session_state.pop(k, None)
        st.rerun()

# -------------- main flow --------------
if "session_id" not in st.session_state:
    st.info("Start a session from the sidebar.")
else:
    session_id = st.session_state["session_id"]
    beats = st.session_state.get("beats", [])
    step = st.session_state.get("current_step", 0)
    choices_made = st.session_state.get("choices_made", [])

    st.success(f"Session: {session_id}")

    if not beats:
        st.warning("No beats available yet. Try restarting the session.")
        st.stop()

    # Clamp step
    step = max(0, min(step, len(beats) - 1))
    st.session_state["current_step"] = step

    # Progress
    st.progress((step + 1) / max(len(beats), 1))

    # Current scene
    current = beats[step]
    st.markdown(f"### Scene {step + 1}")
    st.write(current.get("text", ""))

    # Choices (interactive, not JSON)
    choices = current.get("choices", [])
    selected_idx = None

    if choices:
        preselect = choices_made[step] if step < len(choices_made) else None
        choice_labels = [str(c) for c in choices]

        selected = st.radio(
            "Choose what happens next:",
            choice_labels,
            index=preselect if preselect is not None else 0,
            key=f"choice_radio_step_{step}",
            horizontal=False,
        )
        selected_idx = choice_labels.index(selected)

    # Nav buttons
    nav_cols = st.columns(3)

    # Back
    if nav_cols[0].button("← Back", disabled=(step <= 0)):
        st.session_state["current_step"] = max(0, step - 1)
        st.rerun()

    # Choose & Continue
    if nav_cols[1].button("Choose & Continue", disabled=(choices == [])):
        ok = _branch(selected_idx if selected_idx is not None else 0, step)
        if ok:
            if step < len(choices_made):
                choices_made[step] = selected_idx
            else:
                choices_made.append(selected_idx)
            st.session_state["choices_made"] = choices_made

            st.session_state["current_step"] = min(step + 1, len(st.session_state["beats"]) - 1)
            st.rerun()

    # Skip to last
    if nav_cols[2].button("Skip to Last Scene"):
        st.session_state["current_step"] = len(st.session_state["beats"]) - 1
        st.rerun()

    st.divider()

    # Render/Export row
    c1, c2, c3 = st.columns(3)
    if c1.button("Render Images (HF)", type="primary"):
        _render_images()

    images = st.session_state.get("images", [])
    if images:
        st.subheader("Illustrations")
        public_urls = [f"{API}/outputs/{os.path.basename(p)}" for p in images]
        time.sleep(1)
        st.image(public_urls, use_container_width=True)

        if c2.button("Export PDF"):
            r = requests.post(f"{API}/export/pdf", params={"session_id": session_id})
            if r.ok:
                pdf_path = r.json().get("pdf")
                st.success(f"PDF saved: {pdf_path}" if pdf_path else "PDF exported.")
            else:
                try:
                    st.error(f"PDF export failed: {r.json().get('detail')}")
                except Exception:
                    st.error(f"PDF export failed: {r.text}")

        if c3.button("Export Video"):
            r = requests.post(f"{API}/export/video", params={"session_id": session_id})
            if r.ok:
                video_path = r.json().get("video")
                st.success(f"Video saved: {video_path}" if video_path else "Video exported.")
            else:
                try:
                    st.error(f"Video export failed: {r.json().get('detail')}")
                except Exception:
                    st.error(f"Video export failed: {r.text}")

    # Choice history
    if choices_made:
        st.divider()
        st.caption("Choices so far:")
        for i, idx in enumerate(choices_made):
            try:
                label = beats[i].get("choices", [])[idx]
                st.write(f"Scene {i+1}: {label}")
            except Exception:
                pass
