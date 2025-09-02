import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from io import BytesIO
from PIL import Image
import base64

# ======================
# Page Config
# ======================
st.set_page_config(page_title="Interactive PDF Signer", layout="wide")

# ======================
# Title
# ======================
st.title("✍️ Interactive PDF Signer")

# ======================
# Sidebar Uploads
# ======================
st.sidebar.header("📂 Upload Files")
pdf_file = st.sidebar.file_uploader("Upload your PDF", type=["pdf"])
sig_file = st.sidebar.file_uploader("Upload your Signature (PNG/JPG)", type=["png", "jpg", "jpeg"])

# ======================
# Instructions (Auto-open first time)
# ======================
if "help_shown" not in st.session_state:
    st.session_state.help_shown = False

expanded_state = not st.session_state.help_shown

with st.expander("ℹ️ Instructions & Pro Tips", expanded=expanded_state):
    st.markdown("#### Follow these steps to sign your PDF:")

    if st.button("📄 Step 1: Upload your PDF document"):
        st.info("Use the uploader on the left to add your PDF file. Supported type: PDF.")

    if st.button("✍️ Step 2: Upload your signature image"):
        st.info("Upload a PNG/JPG signature (transparent background preferred for best results).")

    if st.button("⚙️ Step 3: Adjust signature position & size per page"):
        st.info("Each page has its own sliders. Adjust separately to place signatures precisely.")

    if st.button("💾 Step 4: Export signed document"):
        st.info("Click **✅ Generate Signed PDF** to create and download your signed document.")

    st.markdown("---")
    st.markdown("#### ✨ Pro Tips")
    st.markdown("""
    ✅ Place signatures consistently near the bottom-right for contracts.  
    🖼️ Use **transparent PNG** signatures for sharper quality.  
    🔍 Always **preview alignment** using the sliders before final export.  
    """)

st.session_state.help_shown = True

# ======================
# Floating Help Button
# ======================
pulse_speed = "1s" if not st.session_state.help_shown else "2s"

st.markdown(f"""
<style>
.help-btn {{
    position: fixed;
    bottom: 20px;
    right: 20px;
    background-color: #2563eb;
    color: white;
    border: none;
    border-radius: 50%;
    width: 55px;
    height: 55px;
    font-size: 26px;
    font-weight: bold;
    box-shadow: 0px 4px 8px rgba(0,0,0,0.25);
    cursor: pointer;
    z-index: 9999;
    transition: all 0.2s ease-in-out;
    animation: pulse {pulse_speed} infinite;
}}
.help-btn:hover {{
    background-color: #1d4ed8;
    transform: scale(1.1);
}}
@keyframes pulse {{
    0% {{ box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.6); }}
    70% {{ box-shadow: 0 0 0 15px rgba(37, 99, 235, 0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(37, 99, 235, 0); }}
}}
</style>
<button onclick="document.querySelectorAll('.streamlit-expanderHeader')[0].click();" class="help-btn">❓</button>
""", unsafe_allow_html=True)

# ======================
# Main Signing Logic + Per-Page Sliders
# ======================
if pdf_file and sig_file:
    pdf_reader = PdfReader(pdf_file)
    num_pages = len(pdf_reader.pages)

    st.markdown("### ⚙️ Adjust Signature Per Page")

    # Ensure state for per-page positions
    if "page_positions" not in st.session_state:
        st.session_state.page_positions = {
            p: {"x": 5.5, "y": 1.0, "w": 2.0} for p in range(num_pages)
        }

    # Show sliders for each page
    for page_num in range(num_pages):
        with st.expander(f"📄 Page {page_num+1} Controls", expanded=(page_num == 0)):
            st.session_state.page_positions[page_num]["x"] = st.slider(
                f"X position (inches) - Page {page_num+1}", 0.0, 8.0,
                st.session_state.page_positions[page_num]["x"], 0.1, key=f"x_{page_num}"
            )
            st.session_state.page_positions[page_num]["y"] = st.slider(
                f"Y position (inches) - Page {page_num+1}", 0.0, 11.0,
                st.session_state.page_positions[page_num]["y"], 0.1, key=f"y_{page_num}"
            )
            st.session_state.page_positions[page_num]["w"] = st.slider(
                f"Signature width (inches) - Page {page_num+1}", 1.0, 4.0,
                st.session_state.page_positions[page_num]["w"], 0.1, key=f"w_{page_num}"
            )

    # ======================
    # Apply signature placement per page
    # ======================
    pdf_writer = PdfWriter()

    sig_img = Image.open(sig_file)
    img_temp = BytesIO()
    sig_img.save(img_temp, format="PNG")
    img_temp.seek(0)
    sig_reader = ImageReader(img_temp)

    for page_num, page in enumerate(pdf_reader.pages):
        pos = st.session_state.page_positions[page_num]
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(8.5 * inch, 11 * inch))
        can.drawImage(sig_reader, pos["x"] * inch, pos["y"] * inch,
                      width=pos["w"] * inch, preserveAspectRatio=True, mask='auto')
        can.save()

        packet.seek(0)
        new_pdf = PdfReader(packet)
        page.merge_page(new_pdf.pages[0])
        pdf_writer.add_page(page)

    # Export final PDF
    output = BytesIO()
    pdf_writer.write(output)
    pdf_bytes = output.getvalue()

    # ======================
    # Preview Signed PDF
    # ======================
    b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown("### 👀 Preview Signed PDF")
    st.markdown(pdf_display, unsafe_allow_html=True)

    # ======================
    # Download button
    # ======================
    st.download_button("✅ Download Signed PDF", data=pdf_bytes,
                       file_name="signed_output.pdf", mime="application/pdf")
