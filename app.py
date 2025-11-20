import streamlit as st
import requests
import json

API_URL = "http://localhost:8000/analyze"  # سنعدله لاحقاً بعد النشر

st.set_page_config(page_title="Hawsa AI Web", layout="wide")

st.title("🔥 Hawsa AI – Web Interface")
st.write("اكتب أي شيء وسيتم إرساله لمحرك Hawsa AI Core")

user_text = st.text_area("🔽 أدخل رسالتك هنا:")

if st.button("تحليل"):
    if user_text.strip():
        response = requests.post(
            API_URL,
            headers={"Content-Type": "application/json"},
            json={"user_id": "web_user_1", "message": user_text}
        )

        result = response.json()

        st.subheader("📌 رد Hawsa AI:")
        st.write(result["response"]["text"])

        st.subheader("🧠 السياق المستخدم:")
        st.write(result["context_used"])

        st.subheader("⚙️ بيانات تقنية:")
        st.json(result["analytics"])
    else:
        st.warning("رجاءً اكتب نصاً ليتم تحليله.")
