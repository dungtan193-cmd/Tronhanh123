# -*- coding: utf-8 -*-
import streamlit as st
import json
import uuid
from pathlib import Path

st.set_page_config(
    page_title="Tronhanh123 - Tìm phòng trọ",
    page_icon="🏠",
    layout="wide"
)

# =========================
# KHỞI TẠO TRẠNG THÁI
# =========================
if "phong_da_luu" not in st.session_state:
    st.session_state.phong_da_luu = []

if "dang_nhap" not in st.session_state:
    st.session_state.dang_nhap = False

if "user" not in st.session_state:
    st.session_state.user = None

if "trang" not in st.session_state:
    st.session_state.trang = "Trang chủ"

# Dữ liệu mẫu để trang chủ vẫn có phòng khi database chưa có tin được duyệt.
phong_mau = [
    {
        "id": "mau_1",
        "ten": "Phòng trọ khép kín gần Đại học Quốc gia",
        "gia": 3.2,
        "dien_tich": 25,
        "dia_chi": "Mỹ Đình, Nam Từ Liêm, Hà Nội",
        "mo_ta": "Đầy đủ nội thất, có điều hòa, nóng lạnh, ban công."
    },
    {
        "id": "mau_2",
        "ten": "Phòng mới xây, có ban công thoáng mát",
        "gia": 4.0,
        "dien_tich": 30,
        "dia_chi": "Phú Mỹ, Nam Từ Liêm, Hà Nội",
        "mo_ta": "Có thang máy, máy giặt riêng, chỗ để xe."
    },
    {
        "id": "mau_3",
        "ten": "Phòng trọ giá rẻ dành cho sinh viên",
        "gia": 2.5,
        "dien_tich": 20,
        "dia_chi": "Cầu Diễn, Nam Từ Liêm, Hà Nội",
        "mo_ta": "Phòng sạch sẽ, an ninh tốt, gần chợ và trường học."
    }
]

# =========================
# CSS GIAO DIỆN
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Be Vietnam Pro', sans-serif; }
.stApp { background: #f6f8fb; color: #263238; }
header[data-testid="stHeader"] { background: rgba(255,255,255,.94); }
.main .block-container { max-width: 1440px; padding-top: 1rem; padding-bottom: 2rem; }
.logo { font-size: 30px; font-weight: 800; letter-spacing: -1px; color: #e53935; }
.logo span { color: #263238; }
.slogan { color: #78838f; font-size: 12px; margin-top: -4px; }
.menu { background: white; padding: 14px 18px; border-radius: 12px; margin: 12px 0 22px; border: 1px solid #e9edf2; color: #46515d; font-weight: 600; box-shadow: 0 3px 12px rgba(25,40,60,.03); }
.room { background: white; padding: 18px; border-radius: 14px; margin-bottom: 16px; border: 1px solid #e9edf2; box-shadow: 0 5px 18px rgba(30,50,70,.045); }
.room h4 { color: #263238; font-size: 17px; margin-bottom: 8px; }
.price { color: #e53935; font-size: 20px; font-weight: 800; }
.sidebar-box { background: white; padding: 16px; border-radius: 14px; border: 1px solid #e9edf2; margin-bottom: 15px; box-shadow: 0 4px 14px rgba(30,50,70,.035); }
.small-text { color: #7b8794; font-size: 12px; }
.hero { background: linear-gradient(115deg,#991b1f 0%,#e53935 58%,#ff796d 100%); color: white; border-radius: 20px; padding: 30px 32px; margin: 10px 0 22px; box-shadow: 0 12px 28px rgba(190,45,45,.16); }
.hero h1 { color: white; font-size: 30px; line-height: 1.35; margin: 0 0 8px; }
.hero p { color: #ffeded; font-size: 14px; margin: 0; }
div[data-testid="stButton"] button { border-radius: 9px; font-weight: 600; min-height: 40px; }
div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] > div { border-radius: 9px; }
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# =========================
# PHẦN ĐẦU TRANG
# =========================
header1, header2 = st.columns([2, 3])

with header1:
    st.markdown(
        '<div class="logo">TRỌ<span>NHANH123</span></div>'
        '<div class="slogan">Tìm phòng trọ nhanh chóng - An tâm lựa chọn</div>',
        unsafe_allow_html=True
    )

with header2:
    if st.session_state.dang_nhap:
        user = st.session_state.user
        if user and user.get("role") == "quan_tri":
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                if st.button("🏠 Trang chủ", use_container_width=True):
                    st.session_state.trang = "Trang chủ"
                    st.rerun()
            with c2:
                if st.button("📝 Đăng tin", use_container_width=True):
                    st.session_state.trang = "Đăng tin"
                    st.rerun()
            with c3:
                if st.button("🛠️ Duyệt tin", use_container_width=True):
                    st.session_state.trang = "Duyệt tin"
                    st.rerun()
            with c4:
                if st.button("🚪 Đăng xuất", use_container_width=True):
                    st.session_state.dang_nhap = False
                    st.session_state.user = None
                    st.session_state.trang = "Trang chủ"
                    st.rerun()
        else:
            c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1.5])
            with c1:
                if st.button("🏠 Trang chủ", use_container_width=True):
                    st.session_state.trang = "Trang chủ"
                    st.rerun()
            with c2:
                if st.button("❤️ Phòng đã lưu", use_container_width=True):
                    st.session_state.trang = "Phòng đã lưu"
                    st.rerun()
            with c3:
                if st.button("📝 Đăng tin", use_container_width=True):
                    st.session_state.trang = "Đăng tin"
                    st.rerun()
            with c4:
                st.write(f"👤 {user.get('full_name') or user.get('username', 'Tài khoản')}")
            with c5:
                if st.button("🚪 Đăng xuất", use_container_width=True):
                    st.session_state.dang_nhap = False
                    st.session_state.user = None
                    st.session_state.trang = "Trang chủ"
                    st.rerun()
    else:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("🏠 Trang chủ", use_container_width=True):
                st.session_state.trang = "Trang chủ"
                st.rerun()
        with c2:
            if st.button("❤️ Phòng đã lưu", use_container_width=True):
                st.session_state.trang = "Phòng đã lưu"
                st.rerun()
        with c3:
            if st.button("🔐 Đăng nhập", use_container_width=True):
                st.session_state.trang = "Đăng nhập"
                st.rerun()
        with c4:
            if st.button("📝 Đăng ký", use_container_width=True):
                st.session_state.trang = "Đăng ký"
                st.rerun()

st.markdown("---")

st.markdown("""
<div class="menu">
🏠 Cho thuê phòng trọ　 |　 🏢 Nhà nguyên căn　 |　
🏘️ Căn hộ chung cư　 |　 🏬 Ở ghép　 |　 📍 Bản đồ phòng trọ
</div>
""", unsafe_allow_html=True)

# =========================
# TÌM KIẾM
# =========================
st.subheader("Tìm phòng trọ phù hợp với bạn")
search1, search2, search3, search4 = st.columns([2, 2, 1, 1])

with search1:
    tu_khoa = st.text_input("Từ khóa", placeholder="Nhập tên phòng hoặc khu vực...")
with search2:
    khu_vuc = st.selectbox(
        "Khu vực",
        ["Tất cả khu vực", "Nam Từ Liêm", "Cầu Giấy", "Bắc Từ Liêm",
         "Đống Đa", "Thanh Xuân", "Hà Đông", "Hoàng Mai"]
    )
with search3:
    gia_max = st.selectbox("Giá tối đa", [3, 4, 5, 7, 10],
                           format_func=lambda x: f"{x} triệu")
with search4:
    dien_tich_min = st.selectbox("Diện tích từ", [0, 15, 20, 25, 30],
                                 format_func=lambda x: f"{x} m²")

st.markdown("---")

# =========================
# XỬ LÝ CÁC TRANG
# =========================
trang = st.session_state.trang

if trang == "Đăng ký":
    from database.auth import dang_ky

    st.subheader("📝 Đăng ký tài khoản Tronhanh123")
    with st.form("form_dang_ky"):
        full_name = st.text_input("Họ và tên")
        username = st.text_input("Tên đăng nhập")
        email = st.text_input("Địa chỉ email")
        phone = st.text_input("Số điện thoại")
        password = st.text_input("Mật khẩu", type="password")
        confirm_password = st.text_input("Nhập lại mật khẩu", type="password")
        submitted = st.form_submit_button("Đăng ký tài khoản", use_container_width=True)

        if submitted:
            if not all([full_name.strip(), username.strip(), email.strip(), password]):
                st.error("Vui lòng nhập đầy đủ thông tin bắt buộc!")
            elif password != confirm_password:
                st.error("Mật khẩu nhập lại không khớp!")
            elif len(password) < 8:
                st.error("Mật khẩu phải có ít nhất 8 ký tự!")
            else:
                success, message = dang_ky(
                    full_name.strip(), username.strip(), email.strip().lower(),
                    phone.strip(), password
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)

elif trang == "Đăng nhập":
    from database.auth import dang_nhap

    st.subheader("🔐 Đăng nhập Tronhanh123")
    with st.form("form_dang_nhap"):
        username_email = st.text_input("Tên đăng nhập hoặc email")
        mat_khau = st.text_input("Mật khẩu", type="password")
        submitted = st.form_submit_button("Đăng nhập", use_container_width=True)

        if submitted:
            if not username_email or not mat_khau:
                st.error("Vui lòng nhập đầy đủ thông tin!")
            else:
                success, message, user = dang_nhap(username_email.strip(), mat_khau)
                if success:
                    st.session_state.dang_nhap = True
                    st.session_state.user = user
                    st.session_state.trang = "Trang chủ"
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

elif trang == "Đăng tin":
    st.subheader("📝 Đăng tin cho thuê phòng trọ")

    # Tất cả tài khoản đã đăng nhập đều được gửi tin.
    # Tin mới luôn ở trạng thái chờ duyệt; chưa hiển thị công khai.
    if not st.session_state.dang_nhap or not st.session_state.user:
        st.warning("Bạn cần đăng nhập thành công trước khi đăng tin.")
        if st.button("Đăng nhập ngay"):
            st.session_state.trang = "Đăng nhập"
            st.rerun()
    else:
        from database.rooms import them_phong

        user = st.session_state.user
        with st.form("form_dang_tin"):
            tieu_de = st.text_input("Tiêu đề phòng trọ")
            dia_chi = st.text_input("Địa chỉ cụ thể")
            quan_huyen = st.selectbox(
                "Quận/Huyện",
                ["Nam Từ Liêm", "Cầu Giấy", "Bắc Từ Liêm", "Thanh Xuân",
                 "Đống Đa", "Hà Đông", "Hai Bà Trưng", "Hoàng Mai",
                 "Long Biên", "Ba Đình", "Tây Hồ", "Hoàn Kiếm",
                 "Gia Lâm", "Đông Anh", "Thanh Trì"]
            )
            gia = st.number_input("Giá thuê (triệu đồng/tháng)",
                                  min_value=0.1, value=2.5, step=0.1)
            dien_tich = st.number_input("Diện tích (m²)",
                                        min_value=1.0, value=20.0, step=1.0)
            mo_ta = st.text_area("Mô tả phòng trọ")

            st.markdown("#### 📷 Hình ảnh phòng trọ")
            hinh_anh = st.file_uploader(
                "Chọn hình ảnh (có thể chọn nhiều ảnh)",
                type=["jpg", "jpeg", "png", "webp"],
                accept_multiple_files=True,
                help="Định dạng JPG, PNG hoặc WEBP."
            )

            st.markdown("#### 🎥 Video phòng trọ")
            video = st.file_uploader(
                "Chọn video giới thiệu phòng",
                type=["mp4", "mov", "avi"],
                accept_multiple_files=False,
                help="Định dạng MP4, MOV hoặc AVI. Nên dùng video ngắn để tải lên nhanh."
            )

            gui_tin = st.form_submit_button(
                "Gửi tin chờ duyệt", use_container_width=True
            )

            if gui_tin:
                if not tieu_de.strip() or not dia_chi.strip():
                    st.error("Vui lòng nhập tiêu đề và địa chỉ!")
                elif not hinh_anh:
                    st.error("Vui lòng tải lên ít nhất một hình ảnh phòng trọ!")
                else:
                    # Lưu tệp vào thư mục uploads trong project.
                    thu_muc_upload = Path(__file__).parent / "uploads"
                    thu_muc_upload.mkdir(parents=True, exist_ok=True)

                    danh_sach_anh = []
                    duong_dan_video = None

                    try:
                        for anh in hinh_anh:
                            ten_file = f"{uuid.uuid4().hex}_{Path(anh.name).name}"
                            duong_dan = thu_muc_upload / ten_file
                            duong_dan.write_bytes(anh.getbuffer())
                            danh_sach_anh.append(f"uploads/{ten_file}")

                        if video is not None:
                            ten_video = f"{uuid.uuid4().hex}_{Path(video.name).name}"
                            duong_dan_video = thu_muc_upload / ten_video
                            duong_dan_video.write_bytes(video.getbuffer())
                            duong_dan_video = f"uploads/{ten_video}"

                        thanh_cong, thong_bao = them_phong(
                            user["id"], tieu_de.strip(), dia_chi.strip(),
                            quan_huyen, gia, dien_tich, mo_ta.strip(),
                            danh_sach_anh, duong_dan_video
                        )

                        if thanh_cong:
                            st.success(thong_bao)
                        else:
                            st.error(thong_bao)
                    except Exception as e:
                        st.error(f"Không thể lưu hình ảnh hoặc video: {e}")

elif trang == "Duyệt tin":
    st.subheader("🛠️ Quản lý và duyệt tin đăng")

    if not st.session_state.dang_nhap or not st.session_state.user:
        st.warning("Bạn cần đăng nhập để sử dụng chức năng này.")
    elif st.session_state.user.get("role") != "quan_tri":
        st.error("Bạn không có quyền truy cập trang quản trị.")
    else:
        from database.rooms import lay_phong_cho_duyet, cap_nhat_trang_thai

        danh_sach_cho_duyet = lay_phong_cho_duyet()
        if not danh_sach_cho_duyet:
            st.info("Hiện không có tin đăng nào đang chờ duyệt.")
        else:
            for p in danh_sach_cho_duyet:
                with st.container(border=True):
                    st.markdown(f"### {p['title']}")
                    st.write(f"📍 Địa chỉ: {p['address']}, {p.get('district') or ''}")
                    st.write(f"💰 Giá: {p['price']} triệu đồng/tháng")
                    st.write(f"📐 Diện tích: {p['area']} m²")
                    st.write(f"📝 Mô tả: {p.get('description') or 'Chưa có mô tả'}")
                    if p.get("images"):
                        st.write("📷 Hình ảnh:")
                        cot_anh = st.columns(min(len(p["images"]), 3))
                        for i, duong_dan_anh in enumerate(p["images"]):
                            with cot_anh[i % len(cot_anh)]:
                                if Path(duong_dan_anh).exists():
                                    st.image(duong_dan_anh, use_container_width=True)
                    if p.get("video") and Path(p["video"]).exists():
                        st.write("🎥 Video:")
                        st.video(p["video"])
                    st.caption(f"Mã tin: {p['id']} | Người đăng: {p.get('username') or 'Không rõ'}")
                    a1, a2 = st.columns(2)
                    with a1:
                        if st.button("✅ Duyệt tin", key=f"duyet_{p['id']}",
                                     use_container_width=True):
                            ok, msg = cap_nhat_trang_thai(p["id"], "da_duyet")
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    with a2:
                        if st.button("❌ Từ chối", key=f"tuchoi_{p['id']}",
                                     use_container_width=True):
                            ok, msg = cap_nhat_trang_thai(p["id"], "tu_choi")
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

elif trang == "Phòng đã lưu":
    st.subheader("❤️ Danh sách phòng đã lưu")
    danh_sach_luu = [p for p in phong_mau if p["id"] in st.session_state.phong_da_luu]
    if not danh_sach_luu:
        st.info("Bạn chưa lưu phòng trọ nào.")
    else:
        for p in danh_sach_luu:
            st.markdown(f"""
            <div class="room">
                <h4>{p['ten']}</h4>
                <div class="price">{p['gia']} triệu/tháng</div>
                <p>📐 {p['dien_tich']} m²</p>
                <p>📍 {p['dia_chi']}</p>
                <p>{p['mo_ta']}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Bỏ lưu", key=f"bo_luu_{p['id']}"):
                st.session_state.phong_da_luu.remove(p["id"])
                st.rerun()

else:
    # Trang chủ: hiển thị dữ liệu mẫu và các tin đã được admin duyệt.
    st.markdown("""
    <div class="hero">
        <h1>Tìm phòng trọ phù hợp, bắt đầu cuộc sống mới dễ dàng hơn</h1>
        <p>Khám phá phòng trọ tại Hà Nội · Thông tin rõ ràng · Hình ảnh thực tế</p>
    </div>
    """, unsafe_allow_html=True)
    danh_sach_phong = list(phong_mau)
    try:
        from database.rooms import lay_phong_da_duyet
        for p in lay_phong_da_duyet():
            danh_sach_phong.append({
                "id": f"db_{p['id']}",
                "ten": p["title"],
                "gia": float(p["price"]),
                "dien_tich": float(p["area"]),
                "dia_chi": f"{p['address']}, {p.get('district') or ''}",
                "mo_ta": p.get("description") or "",
                "images": p.get("images") or [],
                "video": p.get("video")
            })
    except Exception as e:
        st.warning(f"Chưa tải được tin từ cơ sở dữ liệu: {e}")

    left, center, right = st.columns([1, 2.3, 1])

    with left:
        st.markdown("### 📢 Khu vực quảng cáo")
        st.markdown("""
        <div class="sidebar-box">
            <h4>Tronhanh123</h4>
            <p>Tìm kiếm phòng trọ phù hợp với nhu cầu của bạn.</p>
            <p class="small-text">Thông tin phòng trọ được cập nhật thường xuyên.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("### 📌 Khu vực phổ biến")
        st.write("• Nam Từ Liêm")
        st.write("• Cầu Giấy")
        st.write("• Bắc Từ Liêm")
        st.write("• Đống Đa")

    with center:
        st.markdown("### 🏠 Phòng trọ dành cho bạn")
        st.caption("Khám phá các tin đã được duyệt và những lựa chọn phòng trọ tham khảo.")
        ket_qua = []
        for p in danh_sach_phong:
            if p["gia"] > gia_max or p["dien_tich"] < dien_tich_min:
                continue
            if khu_vuc != "Tất cả khu vực" and khu_vuc.lower() not in p["dia_chi"].lower():
                continue
            if tu_khoa and tu_khoa.lower() not in (
                p["ten"] + " " + p["dia_chi"] + " " + p["mo_ta"]
            ).lower():
                continue
            ket_qua.append(p)

        st.caption(f"Tìm thấy {len(ket_qua)} phòng trọ phù hợp")
        if not ket_qua:
            st.warning("Không tìm thấy phòng trọ phù hợp.")
        else:
            for p in ket_qua:
                st.markdown("🏡 **Thông tin phòng trọ**")
                st.markdown(f"""
                <div class="room">
                    <h4>{p['ten']}</h4>
                    <div class="price">{p['gia']} triệu/tháng</div>
                    <p>📐 Diện tích: {p['dien_tich']} m²</p>
                    <p>📍 Địa chỉ: {p['dia_chi']}</p>
                    <p>{p['mo_ta']}</p>
                </div>
                """, unsafe_allow_html=True)
                if p.get("images"):
                    st.write("📷 Hình ảnh phòng:")
                    cot_anh = st.columns(min(len(p["images"]), 3))
                    for i, duong_dan_anh in enumerate(p["images"]):
                        with cot_anh[i % len(cot_anh)]:
                            if Path(duong_dan_anh).exists():
                                st.image(duong_dan_anh, use_container_width=True)
                if p.get("video") and Path(p["video"]).exists():
                    st.video(p["video"])

                if p["id"] in st.session_state.phong_da_luu:
                    if st.button("❤️ Đã lưu", key=f"luu_{p['id']}"):
                        st.session_state.phong_da_luu.remove(p["id"])
                        st.rerun()
                else:
                    if st.button("♡ Lưu phòng này", key=f"luu_{p['id']}"):
                        st.session_state.phong_da_luu.append(p["id"])
                        st.rerun()

    with right:
        st.markdown("### 🔎 Bộ lọc tìm kiếm")
        st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
        st.write("**Loại hình phòng trọ**")
        st.checkbox("Phòng trọ")
        st.checkbox("Căn hộ mini")
        st.checkbox("Ở ghép")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
        st.write("**Tiện ích**")
        st.checkbox("Có điều hòa")
        st.checkbox("Có nóng lạnh")
        st.checkbox("Có ban công")
        st.checkbox("Có thang máy")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="sidebar-box">', unsafe_allow_html=True)
        st.write("**Thông tin liên hệ**")
        st.write("Bạn có phòng trọ cần cho thuê?")
        if st.button("Đăng tin cho thuê", use_container_width=True):
            if st.session_state.dang_nhap:
                st.session_state.trang = "Đăng tin"
            else:
                st.session_state.trang = "Đăng nhập"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# =========================
# CHÂN TRANG
# =========================
st.markdown("---")
st.markdown(
    "<center>© 2026 Tronhanh123 - Website tìm kiếm phòng trọ tại Hà Nội</center>",
    unsafe_allow_html=True
)
