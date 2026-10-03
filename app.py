import ast
import base64
import os

import requests
import streamlit as st
from anthropic import Anthropic

# beyin.py'yi yapay zeka değiştirir. Bozulursa son çalışan yedeğe dönülür.
try:
    import beyin
except Exception:
    import beyin_yedek as beyin

KLASOR = os.path.dirname(os.path.abspath(__file__))
MODEL = "claude-sonnet-5-5"  # kendini değiştirirken kullanılan model (sabit)


def sir(ad):
    try:
        return st.secrets[ad]
    except Exception:
        return None


client = Anthropic(api_key=sir("ANTHROPIC_API_KEY"))
SIFRE = sir("SAHIP_SIFRESI")
DEPO = sir("GITHUB_DEPO")  # örnek: kullaniciadi/bozbeyai
TOKEN = sir("GITHUB_TOKEN")


def izinli(sifre):
    return bool(SIFRE) and sifre == SIFRE


def github_yaz(dosya, icerik, mesaj):
    url = f"https://api.github.com/repos/{DEPO}/contents/{dosya}"
    basliklar = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}
    mevcut = requests.get(url, headers=basliklar, timeout=30)
    veri = {"message": mesaj, "content": base64.b64encode(icerik.encode("utf-8")).decode()}
    if mevcut.status_code == 200:
        veri["sha"] = mevcut.json()["sha"]
    requests.put(url, headers=basliklar, json=veri, timeout=30).raise_for_status()


def kendini_degistir(sifre, istek):
    if not izinli(sifre):
        return "Şifre yanlış."
    eski = open(os.path.join(KLASOR, "beyin.py"), encoding="utf-8").read()
    istek = istek.strip() or "Kendini nasıl geliştireceğine kendin karar ver."
    r = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=(
            "Sen bozbeyAI'sın ve kendi beyin.py dosyanı değiştiriyorsun. "
            "Dosyada cevap_ver(client, mesajlar) fonksiyonu mutlaka kalmalı. "
            "Sadece dosyanın tam yeni halini ver. Açıklama veya ``` işareti yazma."
        ),
        messages=[{"role": "user", "content": f"Mevcut beyin.py:\n{eski}\n\nİstek: {istek}"}],
    )
    yeni = r.content[0].text.strip()
    if yeni.startswith("```"):
        yeni = yeni.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        agac = ast.parse(yeni)
        adlar = {n.name for n in agac.body if isinstance(n, ast.FunctionDef)}
        if "cevap_ver" not in adlar:
            return "Yeni kodda cevap_ver yok, uygulanmadı."
        github_yaz("beyin_yedek.py", eski, "bozbeyAI yedek aldı")
        github_yaz("beyin.py", yeni, f"bozbeyAI kendini değiştirdi: {istek[:60]}")
    except Exception as e:
        return f"Uygulanmadı: {e}"
    return "Uygulandı! Site 1-2 dakika içinde yeni haliyle açılır."


def geri_al(sifre):
    if not izinli(sifre):
        return "Şifre yanlış."
    try:
        yedek = open(os.path.join(KLASOR, "beyin_yedek.py"), encoding="utf-8").read()
        github_yaz("beyin.py", yedek, "bozbeyAI eski haline döndü")
    except Exception as e:
        return f"Geri alınamadı: {e}"
    return "Eski sürüme dönüldü. Site 1-2 dakika içinde yenilenir."


st.set_page_config(page_title="bozbeyAI")
st.title("bozbeyAI")

with st.sidebar:
    st.subheader("Kendini değiştir (sahip)")
    st.caption("Boş bırakırsan bozbeyAI nasıl gelişeceğine kendi karar verir.")
    sifre = st.text_input("Şifre", type="password")
    istek = st.text_input("Kendini nasıl değiştirsin? (boş olabilir)")
    if st.button("Değiştir"):
        with st.spinner("bozbeyAI kendini yazıyor..."):
            st.info(kendini_degistir(sifre, istek))
    if st.button("Geri al"):
        st.info(geri_al(sifre))

if "mesajlar" not in st.session_state:
    st.session_state.mesajlar = []

for m in st.session_state.mesajlar:
    with st.chat_message(m["role"]):
        st.write(m["content"])

soru = st.chat_input("bozbeyAI'ya bir şey yaz")
if soru:
    st.session_state.mesajlar.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.write(soru)
    with st.chat_message("assistant"):
        try:
            cevap = beyin.cevap_ver(client, st.session_state.mesajlar)
        except Exception:
            cevap = "Şu an cevap veremiyorum, biraz sonra tekrar dene."
        st.write(cevap)
    st.session_state.mesajlar.append({"role": "assistant", "content": cevap})
