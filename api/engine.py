"""ChatLert NLP engine v2: 8-step pipeline (PyThaiNLP newmm + rule-based)."""
import re
from pythainlp import word_tokenize

VERSION = "2.0"
FEMALE = ["ค่ะ", "คะ", "ขา", "ค่า", "คร่า", "คระ"]
MALE = ["ครับ", "งับ", "ค้าบ", "คั้บ", "คับ", "คาบ"]
Q_ANY = ["ไหม", "มั้ย", "มัย", "อะไร", "ไหน", "เมื่อไหร่", "เท่าไหร่", "กี่", "บ้าง", "หนาย", "ป่ะ", "ป่าว", "ไร"]
Q_END = re.compile(r"ไหม|ไหน|อะไร|เมื่อไหร่|เท่าไหร่|กี่|บ้าง|หรือยัง|หรือเปล่า|หรือไม่")
JUNK = {"อะ", "อ่ะ", "น้า", "นะฮะ", "เบย", "เนอะ", "จ้า", " ", "นะ"}
SLANG = [
    (r"หนายย?", "ไหน"), (r"อยุ่?", "อยู่"), (r"มั้ย|มัย|ป่ะ", "ไหม"), (r"ป่าว", "หรือเปล่า"),
    (r"เด่ว|เดว|เด๋ว", "เดี๋ยว"), (r"สนจัย", "สนใจ"),
    (r"(งับ|ค้าบ|คั้บ|คาบ|คับ)(?=\s|$)", "ครับ"),
    (r"(?<![อะ])ไร(?=บ้าง|ค่ะ|คะ|ครับ|\s|$)", "อะไร"),
    (r"(?<=ถึง|ส่ง|ได้)ยาง", "ยัง"),
]
PRODUCTS = ["เสื้อ", "กางเกง", "กระโปรง", "รองเท้า", "กระเป๋า", "ชุด", "หมวก"]


def classify(t, q):
    """คืน (เจตนา, ประโยคมาตรฐาน) โดยเรียงจากเคสเฉพาะไปทั่วไป"""
    h = lambda p: re.search(p, t)
    if h(r"^(สวัสดี|หวัดดี|hello|hi)"): return "ทักทาย", t
    if h(r"ขอบคุณ|ขอบใจ"): return "ขอบคุณ", "ขอบคุณมาก" if "มาก" in t else "ขอบคุณ"
    if h(r"ยกเลิก"): return "ยกเลิกคำสั่งซื้อ", "สามารถยกเลิกคำสั่งซื้อได้ไหม" if q else "ต้องการยกเลิกคำสั่งซื้อ"
    if h(r"เสียหาย|แตก|ชำรุด|พัง|ขาด|เคลม|ไม่ตรงปก"): return "สินค้ามีปัญหา", "สินค้าเสียหาย ต้องการเคลม"
    if h(r"ผิด(ไซส์|สี|แบบ|ขนาด|รุ่น)|ส่งผิด|ส่งมาผิด"): return "สินค้ามีปัญหา", "ได้รับสินค้าไม่ตรงกับที่สั่ง ต้องการแก้ไข"
    if h(r"(ยัง)?ไม่ได้(รับ|ของ)|(ยัง)?ไม่ถึง|ของหาย|พัสดุหาย"): return "ร้องเรียนการจัดส่ง", "ยังไม่ได้รับสินค้า ต้องการให้ตรวจสอบ"
    if h(r"ยังไม่ส่ง|ไม่ส่ง"): return "ร้องเรียนการจัดส่ง", "สินค้ายังไม่ถูกจัดส่ง ต้องการให้ตรวจสอบ"
    if h(r"ช้า|นาน"): return "ร้องเรียนการจัดส่ง", "จัดส่งสินค้าล่าช้า ต้องการให้ตรวจสอบ"
    if h(r"ปลายทาง|cod|COD"): return "สอบถามการชำระเงิน", "สามารถชำระเงินปลายทางได้ไหม"
    if h(r"เลขบัญชี|บัญชี"): return "สอบถามการชำระเงิน", "ขอเลขบัญชีสำหรับโอนเงิน"
    if h(r"ค่าส่ง|ค่าจัดส่ง"): return "สอบถามการจัดส่ง", "ค่าจัดส่งเท่าไหร่"
    if h(r"ส่งฟรี"): return "สอบถามการจัดส่ง", "มีบริการส่งฟรีไหม"
    if h(r"ส่งแบบไหน|ส่งด้วย|ขนส่ง|ส่งกับ|ส่งผ่าน"): return "สอบถามการจัดส่ง", "สอบถามวิธีการจัดส่ง"
    if h(r"ส่ง(ยัง|แล้ว|ของ|สินค้า|วัน|เมื่อไหร่)|เมื่อไหร่.*ส่ง|ถึง(ไหน|ยัง)|ได้ของ|พัสดุ|ติดตาม|วันไหน|กี่วัน|ถึงวัน"):
        if h(r"เมื่อไหร่"): return "สอบถามสถานะสินค้า", "สินค้าจะจัดส่งเมื่อไหร่"
        if h(r"วันไหน|กี่วัน|ถึงวัน"): return "สอบถามสถานะสินค้า", "สินค้าจะจัดส่งถึงในวันไหน"
        if h(r"ถึงไหน"): return "สอบถามสถานะสินค้า", "สินค้าถึงขั้นตอนไหนของการจัดส่งแล้ว"
        if h(r"ได้ของ"): return "สอบถามสถานะสินค้า", "ได้รับสินค้าแล้วหรือยัง"
        if h(r"ถึงยัง"): return "สอบถามสถานะสินค้า", "สินค้าถึงแล้วหรือยัง"
        return "สอบถามสถานะสินค้า", "สินค้าจัดส่งแล้วหรือยัง"
    if h(r"โอน|จ่าย|ยอด|สลิป"):
        if h(r"ยังไม่(ได้)?โอน|ไม่ได้โอน"): return "แจ้งชำระเงิน", "ยังไม่ได้โอนเงิน"
        return "แจ้งชำระเงิน", "โอนเงินเรียบร้อยแล้ว ตรวจสอบให้ด้วย" if h(r"เช็ค|ตรวจสอบ") else "โอนเงินเรียบร้อยแล้ว"
    if h(r"เปลี่ยน|คืนสินค้า|คืนเงิน"):
        part = "ไซส์สินค้า" if h(r"ไซส์|เล็ก|ใหญ่|ขนาด") else "สีสินค้า" if h(r"สี") else "สินค้า"
        return "ขอเปลี่ยนสินค้า", f"สามารถขอเปลี่ยน{part}ได้ไหม" if "ไหม" in t else f"ต้องการขอเปลี่ยน{part}"
    if h(r"สนใจ|ราคา|สี|ขนาด|ไซส์|เท่าไหร่|กี่บาท|มีของ|สต็อก|พร้อมส่ง|ส่วนลด"): return "สอบถามรายละเอียดสินค้า", t
    return "ข้อความทั่วไป", t


class ChatLertEngine:
    version = VERSION

    def reduce_repeated(self, text):
        # ตัวซ้ำ 3+ ตัว -> 1 ตัว; คู่ซ้ำลดเฉพาะ า ะ ี หรือท้ายคำ (ไม่แตะ "ออ" ใน ออเดอร์)
        text = re.sub(r"(.)\1{2,}", r"\1", text)
        text = re.sub(r"([าะี])\1", r"\1", text)
        # ตัวซ้ำคู่ท้ายคำ (บ้างง, ค่ะะ) ลดได้ ยกเว้น ร/อ ที่ซ้ำปกติ เช่น จัดสรร, ออ
        return re.sub(r"([^รอ\s])\1(?=\s|$)", r"\1", text)

    def process(self, raw_text):
        step1 = re.sub(r"[^\u0E00-\u0E7Fa-zA-Z0-9\s]", "", raw_text)
        step2 = self.reduce_repeated(step1)

        chunks = step2.split()
        is_female = any(c.endswith(s) for c in chunks for s in FEMALE)
        has_suffix = is_female or any(c.endswith(s) for c in chunks for s in MALE)
        is_q_raw = any(w in step2 for w in Q_ANY) or bool(re.search(r"(ถึง|ส่ง|ได้)ยาง", step2))

        step3 = step2
        kha = "คะ" if is_q_raw else "ค่ะ"
        step3 = re.sub(r"(คระ|ค่า|คร่า)(?=\s|$)", kha, step3)
        for pat, rep in SLANG:
            step3 = re.sub(pat, rep, step3)

        tok_in = step3.replace("ไหนคะ", "ไหน คะ").replace("ไหมคะ", "ไหม คะ")
        raw_tokens = word_tokenize(tok_in, engine="newmm")
        step5_tokens = [t.strip() for t in raw_tokens if t not in JUNK and t.strip()]
        step5_text = "".join(step5_tokens)

        intent, adjusted = classify(step5_text, "ไหม" in step5_text)

        product = next((p for p in PRODUCTS if p in step5_text), "-")
        if re.search(r"สี", step5_text): attr = "สี (Color)"
        elif re.search(r"ไซส์|ขนาด", step5_text): attr = "ไซส์ (Size)"
        elif re.search(r"ราคา|เท่าไหร่", step5_text): attr = "ราคา (Price)"
        else: attr = "-"

        if has_suffix:
            polite = "ครับ" if not is_female else ("คะ" if Q_END.search(adjusted) else "ค่ะ")
            base = re.sub(r"(นะ)?(ครับ|คะ|ค่ะ)+$", "", adjusted).strip()
            final = base + polite
        else:
            final = adjusted

        return {
            "step_5_1": step1, "step_5_2": step2, "step_5_3": step3,
            "step_5_4": raw_tokens, "step_5_5": step5_tokens,
            "step_5_6": adjusted, "step_5_7": final, "step_5_8": intent,
            "product": product, "attr": attr, "has_suffix": has_suffix,
        }
