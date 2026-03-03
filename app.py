import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from io import BytesIO
from datetime import datetime
import os

# PDF için
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.units import cm


# -----------------------------
# TÜRKÇE FONT KURULUMU (KÖK DİZİNDEN OKUR)
# Streamlit Cloud / Windows / Mac hepsinde çalışır.
# Font açılamazsa uygulama çökmesin diye "safe" şekilde kaydediyoruz.
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

REGULAR_FONT_PATH = os.path.join(BASE_DIR, "DejaVuSans.ttf")
BOLD_FONT_PATH    = os.path.join(BASE_DIR, "DejaVuSans-Bold.ttf")

def safe_register_font(font_name: str, font_path: str) -> bool:
    try:
        if os.path.exists(font_path) and os.path.getsize(font_path) > 1000:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            return True
        return False
    except Exception:
        return False

HAS_REGULAR = safe_register_font("DejaVu", REGULAR_FONT_PATH)
HAS_BOLD    = safe_register_font("DejaVu-Bold", BOLD_FONT_PATH)


# -----------------------------
# SABİT BİLGİLER (Sergi/Jüri için)
# -----------------------------
OKUL_ADI = "Kandıra Bozburun Ortaokulu"
PROJE_ADI = "Karbon Sıfır Okul: Enerji Tüketimi ve Denge Planı"


# -----------------------------
# 1) HESAPLAMA KATSAYILARI
# (Bu katsayılar araştırma kısmının kalbidir.)
# -----------------------------
K_KOMUR = 2.42    # kg CO2 / kg kömür (yaklaşık)
K_GAZ   = 2.03    # kg CO2 / m³ doğalgaz (yaklaşık)
K_ELEK  = 0.43    # kg CO2 / kWh elektrik (yaklaşık)
K_SU    = 0.34    # kg CO2 / m³ su (yaklaşık)
K_AGAC  = 22      # 1 ağacın yılda tuttuğu CO2 (kg) (yaklaşık)


# -----------------------------
# 2) ÖNERİ MOTORU
# (En yüksek salım kalemine göre önerileri önceliklendirir.)
# -----------------------------
def oneriler_uret(c_komur, c_gaz, c_elek, c_su, toplam):
    kaynaklar = {
        "Kömür": c_komur,
        "Doğalgaz": c_gaz,
        "Elektrik": c_elek,
        "Su": c_su
    }
    en_buyuk = max(kaynaklar, key=kaynaklar.get) if toplam > 0 else None

    genel = [
        "Sınıf ve koridorlar için ‘Enerji Nöbetçisi’ sistemi kurun (ders arası kontrol).",
        "Gereksiz ışıkları azaltmak için sınıf panosuna ‘Çıkış Kontrol Listesi’ asın.",
        "Çift taraflı çıktı + dijital teslim ile kâğıt tüketimini azaltın.",
        "Atıkları kaynağında ayırın; her sınıfa mini ayrıştırma kutusu koyun.",
        "Geri dönüşüm kutularını ‘doğru atık’ görselleriyle etiketleyin.",
        "Musluklara perlatör takın; su tasarrufu için bakım-onarım kontrolü yapın.",
        "Su kaçaklarını erken tespit için haftalık sayaç kontrol çizelgesi oluşturun.",
        "Cihazların (akıllı tahta, bilgisayar) uyku modu ayarlarını standartlaştırın.",
        "Tek kullanımlık plastikleri azaltmak için okul içi hedef belirleyin.",
        "Kantin için ‘az ambalaj–geri dönüşebilir ambalaj’ tercih listesi hazırlayın.",
        "Aylık ‘Yeşil Görev’ takvimi ile davranışları sürdürülebilir hale getirin.",
        "Sınıflar arası ‘tasarruf puanı’ ile oyunlaştırılmış yarışma düzenleyin."
    ]

    elektrik = [
        "LED dönüşüm senaryosu uygulayın (genelde %15–25 tasarruf).",
        "Gün ışığı kullanımını artırmak için perde/oturma düzenini optimize edin.",
        "Koridor/tuvaletlerde sensörlü aydınlatma senaryosu planlayın.",
        "Gün sonunda şarj aletleri ve çoklayıcıları fişten çekme rutini oluşturun.",
        "Akıllı tahta/projeksiyonun gereksiz açık kalma süresini azaltın.",
        "Sınıf bazlı kWh hedefi belirleyip aylık takip grafiği oluşturun."
    ]

    isinma = [
        "Kapı/pencere fitili ve basit yalıtım iyileştirmeleriyle ısı kaybını azaltın.",
        "Sınıf sıcaklık hedefini 20–22°C aralığında belirleyip görünür şekilde duyurun.",
        "Radyatör önü kapanmayacak şekilde sınıf düzeni yapın.",
        "Havalandırmayı kısa-sık yapın (uzun süre pencere açık bırakmayın).",
        "Isıtma saatlerini ders programına göre optimize etmeyi planlayın.",
        "Isı kaybı noktalarını (kapı/pencere) sınıf sınıf işaretleyin."
    ]

    su = [
        "Rezervuarlarda tasarruf aparatı kullanımı planlayın.",
        "Lavabolarda ‘musluğu kapat’ görsel hatırlatıcıları kullanın.",
        "Temizlikte kontrollü su kullanımı yönergesi oluşturun.",
        "Yağmur suyu biriktirme (varil/depo) tasarım senaryosu hazırlayın.",
        "Bahçe sulamasını sabah/akşam saatlerine alarak buharlaşma kaybını azaltın.",
        "Haftalık sayaç kontrolüyle anormal artışı tespit edin."
    ]

    komur = [
        "Isınma sistemi bakımı ve ayarlarının verime etkisini dokümanlarla raporlayın.",
        "Yalıtım ve pencere sızdırmazlığı senaryosuyla tüketimi azaltma planı çıkarın.",
        "Sınıf/koridor ısı kaybı noktalarını haritalayın.",
        "Isınma davranış protokolü hazırlayın (kapı açık bırakmama vb.)."
    ]

    if en_buyuk == "Elektrik":
        oncelik = elektrik
    elif en_buyuk == "Doğalgaz":
        oncelik = isinma
    elif en_buyuk == "Su":
        oncelik = su
    elif en_buyuk == "Kömür":
        oncelik = komur
    else:
        oncelik = []

    tum = oncelik + genel
    return tum, en_buyuk


# -----------------------------
# 3) METRİK HESAPLAMA
# -----------------------------
def metrik_hesapla(komur_kg, gaz_m3, elek_kwh, su_m3, azaltim_orani):
    c_komur = komur_kg * K_KOMUR
    c_gaz   = gaz_m3   * K_GAZ
    c_elek  = elek_kwh * K_ELEK
    c_su    = su_m3    * K_SU

    toplam = c_komur + c_gaz + c_elek + c_su
    hedef_toplam = toplam * (1 - azaltim_orani)

    fidan = int(np.ceil(toplam / K_AGAC)) if toplam > 0 else 0
    hedef_fidan = int(np.ceil(hedef_toplam / K_AGAC)) if hedef_toplam > 0 else 0

    return {
        "c_komur": c_komur, "c_gaz": c_gaz, "c_elek": c_elek, "c_su": c_su,
        "toplam": toplam, "hedef_toplam": hedef_toplam,
        "fidan": fidan, "hedef_fidan": hedef_fidan,
        "azaltim_orani": azaltim_orani
    }


# -----------------------------
# 4) GRAFİK OLUŞTURMA (Matplotlib)
# -----------------------------
def fig_olustur(rapor_baslik, met):
    labels = ["Kömür", "Doğalgaz", "Elektrik", "Su"]
    vals   = [met["c_komur"], met["c_gaz"], met["c_elek"], met["c_su"]]

    fig = plt.figure(figsize=(12, 8), facecolor="#F8FAFC")

    fig.text(0.5, 0.95, rapor_baslik, fontsize=18, fontweight="bold",
             ha="center", color="#0F172A")
    fig.text(0.5, 0.915, "Sorumlu Üretim ve Tüketim | Karbon Analizi",
             fontsize=11, ha="center", color="#64748B")

    # Donut grafik
    ax1 = plt.subplot2grid((2, 2), (0, 0), rowspan=2)
    filtered = [(l, v) for l, v in zip(labels, vals) if v > 0]
    if filtered:
        f_l, f_v = zip(*filtered)
        ax1.pie(
            f_v, labels=f_l, autopct="%1.1f%%", startangle=140,
            colors=["#475569", "#94A3B8", "#F59E0B", "#0EA5E9"],
            pctdistance=0.75, wedgeprops=dict(width=0.4, edgecolor="w")
        )
    else:
        ax1.text(0.5, 0.5, "Veri Yok", ha="center", va="center", fontsize=14)
    ax1.set_title("Salım Dağılımı", fontsize=13, fontweight="bold", pad=12)

    # Mevcut vs Hedef
    ax2 = plt.subplot2grid((2, 2), (0, 1))
    bars = ax2.barh(
        ["Mevcut", "Hedef"],
        [met["toplam"], met["hedef_toplam"]],
        color=["#94A3B8", "#10B981"],
        height=0.5
    )
    ax2.set_title("Toplam Karbon (kg CO₂)", fontsize=12, fontweight="bold")
    for b in bars:
        ax2.text(b.get_width(), b.get_y() + b.get_height()/2,
                 f" {int(b.get_width()):,} kg", va="center", fontweight="bold")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    # Fidan kutusu
    ax3 = plt.subplot2grid((2, 2), (1, 1))
    ax3.axis("off")
    res = (
        f"🌳 DOĞAYA BORCUNUZ: {met['fidan']} FİDAN\n"
        f"Plan uygulanırsa borç {met['hedef_fidan']} fidana düşebilir!"
    )
    ax3.text(
        0.5, 0.5, res, fontsize=14, fontweight="bold",
        ha="center", va="center", color="#065F46",
        bbox=dict(facecolor="#ECFDF5", edgecolor="#10B981",
                  boxstyle="round,pad=1.2", linewidth=2)
    )

    plt.tight_layout(rect=[0.04, 0.04, 0.96, 0.90])
    return fig


# -----------------------------
# 5) PDF ÜRETİMİ (TTF HATASINA KARŞI GÜVENLİ)
# -----------------------------
def pdf_uret(okul_adi, proje_adi, met, oneriler, en_buyuk, fig, girisler):
    buffer = BytesIO()

    # Font adları (yukarıda safe şekilde kaydedildi)
    FONT   = "DejaVu" if HAS_REGULAR else "Helvetica"
    FONT_B = "DejaVu-Bold" if HAS_BOLD else FONT

    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Üst bant
    c.setFillColor(colors.HexColor("#0F766E"))
    c.rect(0, height - 3.2*cm, width, 3.2*cm, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont(FONT_B, 16)
    c.drawString(2*cm, height - 1.4*cm, okul_adi)

    c.setFont(FONT, 12)
    c.drawString(2*cm, height - 2.2*cm, proje_adi)

    c.setFont(FONT, 9)
    c.drawRightString(width - 2*cm, height - 2.2*cm, f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    y = height - 3.8*cm

    # KPI kutuları
    def kpi_row(y):
        cards = [
            ("Mevcut Toplam", f"{int(met['toplam']):,} kg CO₂"),
            ("Hedef Toplam", f"{int(met['hedef_toplam']):,} kg CO₂"),
            ("Azaltım", f"%{int(met['azaltim_orani']*100)}"),
            ("En Büyük Kaynak", en_buyuk if en_buyuk else "—"),
        ]
        x0 = 2*cm
        card_w = (width - 4*cm - 3*(0.6*cm)) / 4
        card_h = 2.2*cm
        gap = 0.6*cm

        for i, (t, v) in enumerate(cards):
            x = x0 + i*(card_w + gap)
            c.setFillColor(colors.white)
            c.setStrokeColor(colors.HexColor("#CBD5E1"))
            c.roundRect(x, y-card_h, card_w, card_h, 10, fill=1, stroke=1)

            c.setFillColor(colors.HexColor("#334155"))
            c.setFont(FONT, 9)
            c.drawString(x+10, y-18, t)

            c.setFillColor(colors.HexColor("#0F172A"))
            c.setFont(FONT_B, 11)
            c.drawString(x+10, y-36, v)

        return y - card_h - 12

    y = kpi_row(y)

    # Girdi değerleri
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont(FONT_B, 12)
    c.drawString(2*cm, y, "Girdi Değerleri")
    y -= 16
    c.setFont(FONT, 10)

    rows = [
        ("Kömür (kg)", str(girisler["komur"])),
        ("Doğalgaz (m³)", str(girisler["gaz"])),
        ("Elektrik (kWh)", str(girisler["elek"])),
        ("Su (m³)", str(girisler["su"])),
        ("Hedef Azaltım", f"%{girisler['azaltim']}"),
    ]
    for k, v in rows:
        c.setFillColor(colors.HexColor("#334155"))
        c.drawString(2*cm, y, k)
        c.setFillColor(colors.HexColor("#0F172A"))
        c.drawRightString(width-2*cm, y, v)
        y -= 14

    y -= 6

    # Grafik görseli
    c.setFont(FONT_B, 12)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.drawString(2*cm, y, "Grafik Özeti")
    y -= 10

    img_buf = BytesIO()
    fig.savefig(img_buf, format="png", dpi=170, bbox_inches="tight")
    img_buf.seek(0)
    img = ImageReader(img_buf)

    img_w = width - 4*cm
    img_h = 8.2*cm
    c.drawImage(img, 2*cm, y - img_h, width=img_w, height=img_h, preserveAspectRatio=True, anchor="sw")
    y -= img_h + 16

    # Öneriler
    c.setFont(FONT_B, 12)
    c.drawString(2*cm, y, "Öneriler (Sorumlu Üretim ve Tüketim)")
    y -= 16
    c.setFont(FONT, 10)

    def wrap_text(text, max_width):
        words = text.split()
        lines, line = [], ""
        for w in words:
            test = (line + " " + w).strip()
            if pdfmetrics.stringWidth(test, FONT, 10) <= max_width:
                line = test
            else:
                if line:
                    lines.append(line)
                line = w
        if line:
            lines.append(line)
        return lines

    max_w = width - 4*cm
    for i, o in enumerate(oneriler[:18], start=1):
        lines = wrap_text(f"{i}. {o}", max_w)
        for ln in lines:
            if y < 2.2*cm:
                c.showPage()
                c.setFont(FONT_B, 14)
                c.setFillColor(colors.HexColor("#0F172A"))
                c.drawString(2*cm, height-2*cm, "Öneriler (Devam)")
                y = height - 3*cm
                c.setFont(FONT, 10)
            c.setFillColor(colors.HexColor("#0F172A"))
            c.drawString(2*cm, y, ln)
            y -= 13
        y -= 2

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


# -----------------------------
# 6) STREAMLIT ARAYÜZ
# -----------------------------
st.set_page_config(page_title="Karbon Sıfır Okul", layout="wide")
st.title("🌍 Karbon Sıfır Okul – Karbon Analiz Paneli")
st.caption(f"🏫 {OKUL_ADI} | 📌 {PROJE_ADI}")

DEFAULTS = {
    "komur": 0.0,
    "gaz": 0.0,
    "elek": 0.0,
    "su": 0.0,
    "azaltim": 35,
    "uzun_oneri": False
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

top1, top2, top3 = st.columns([1, 1, 2])
with top1:
    if st.button("🧹 Temizle"):
        for k, v in DEFAULTS.items():
            st.session_state[k] = v
        st.rerun()
with top2:
    st.session_state["uzun_oneri"] = st.toggle("📌 Önerileri uzun göster", value=st.session_state["uzun_oneri"])
with top3:
    st.info("Bu uygulama anket/ölçek kullanmaz. Hesaplama + senaryo modellemesi ile çalışır.")

st.divider()

with st.form("form"):
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])
    with c1:
        st.session_state["komur"] = st.number_input("Kömür (kg) (opsiyonel)", min_value=0.0, value=float(st.session_state["komur"]), step=10.0)
    with c2:
        st.session_state["gaz"] = st.number_input("Doğalgaz (m³)", min_value=0.0, value=float(st.session_state["gaz"]), step=10.0)
    with c3:
        st.session_state["elek"] = st.number_input("Elektrik (kWh)", min_value=0.0, value=float(st.session_state["elek"]), step=100.0)
    with c4:
        st.session_state["su"] = st.number_input("Su (m³)", min_value=0.0, value=float(st.session_state["su"]), step=10.0)
    with c5:
        st.session_state["azaltim"] = st.number_input("Hedef Azaltım (%)", min_value=0, max_value=90, value=int(st.session_state["azaltim"]), step=5)

    run = st.form_submit_button("✅ Raporu Oluştur")

if run:
    azaltim_orani = st.session_state["azaltim"] / 100.0

    met = metrik_hesapla(
        st.session_state["komur"],
        st.session_state["gaz"],
        st.session_state["elek"],
        st.session_state["su"],
        azaltim_orani
    )

    tum_oneriler, en_buyuk = oneriler_uret(
        met["c_komur"], met["c_gaz"], met["c_elek"], met["c_su"], met["toplam"]
    )
    oneriler = tum_oneriler if st.session_state["uzun_oneri"] else tum_oneriler[:14]

    # KPI kartları
    a, b, c_, d = st.columns(4)
    a.metric("Mevcut Toplam (kg CO₂)", f"{int(met['toplam']):,}")
    b.metric("Hedef Toplam (kg CO₂)", f"{int(met['hedef_toplam']):,}")
    c_.metric("Azaltım (%)", f"%{int(met['azaltim_orani']*100)}")
    d.metric("En Büyük Kaynak", en_buyuk if en_buyuk else "—")

    fig = fig_olustur(f"{OKUL_ADI} – Karbon Analizi", met)
    st.pyplot(fig)

    st.subheader("💡 Öneriler")
    st.caption("Öneriler, en büyük salım kaynağına göre önceliklendirilir.")

    # Önerileri kart tasarımla göster
    left, right = st.columns(2)
    half = int(np.ceil(len(oneriler) / 2))
    sol = oneriler[:half]
    sag = oneriler[half:]

    def onerikart(liste, container):
        for i, o in enumerate(liste, start=1):
            container.markdown(
                f"""
                <div style="
                    background:#FFFFFF;
                    border:1px solid #E2E8F0;
                    border-left:6px solid #10B981;
                    border-radius:14px;
                    padding:12px 14px;
                    margin-bottom:10px;">
                    <div style="font-weight:700;color:#0F172A;">Öneri</div>
                    <div style="color:#334155;margin-top:6px;line-height:1.4;">{o}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    onerikart(sol, left)
    onerikart(sag, right)

    # PDF indir
    girisler = {
        "komur": st.session_state["komur"],
        "gaz": st.session_state["gaz"],
        "elek": st.session_state["elek"],
        "su": st.session_state["su"],
        "azaltim": st.session_state["azaltim"]
    }

    pdf_bytes = pdf_uret(
        okul_adi=OKUL_ADI,
        proje_adi=PROJE_ADI,
        met=met,
        oneriler=tum_oneriler,   # PDF'e uzun öneri koyuyoruz
        en_buyuk=en_buyuk,
        fig=fig,
        girisler=girisler
    )

    st.download_button(
        label="⬇️ PDF Raporunu İndir",
        data=pdf_bytes,
        file_name="Karbon_Sifir_Okul_Raporu_Kandira_Bozburun_Ortaokulu.pdf",
        mime="application/pdf"
    )
else:
    st.info("Değerleri girip **Raporu Oluştur** butonuna basın.")
