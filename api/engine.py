import re
from pythainlp import word_tokenize

class ChatLertEngine:
    def __init__(self):
        self.junk_tokens = {"อะ", "น้า", "นะฮะ", "เบย", " ", "นะ"}

    def reduce_repeated(self, text):
        return re.sub(r'(.)\1+', r'\1', text)

    def process(self, raw_text):
        female_suffixes = ["ค่ะ", "คะ", "ขา", "ค่า", "คร่า", "คระ"]
        male_suffixes = ["ครับ", "งับ", "ค้าบ", "คั้บ", "คับ", "คาบ"]
        
        has_polite_suffix = any(s in raw_text for s in female_suffixes + male_suffixes)
        is_female = any(s in raw_text for s in female_suffixes)

        step1 = re.sub(r'[^\u0E00-\u0E7Fa-zA-Z0-9\s]', '', raw_text)
        step2 = self.reduce_repeated(step1)
        
        original_is_question = any(word in step2 for word in ["ไหม", "อะไร", "ไหน", "ยัง", "เมื่อไหร่", "กี่", "มั้ย", "มัย", "หนาย", "ไร", "บ้าง", "ยาง"])

        step3 = step2
        correct_kha_step3 = "คะ" if original_is_question else "ค่ะ"
        for slang_kha in ["คระ", "ค่า", "คร่า"]:
            if slang_kha in step3:
                step3 = step3.replace(slang_kha, correct_kha_step3)
                
        slang_replacements = [
            ("หนายย", "ไหน"), ("หนาย", "ไหน"),
            ("อยุ่", "อยู่"), ("อยุ", "อยู่"), ("ยุ", "อยู่"),
            ("มั้ย", "ไหม"), ("มัย", "ไหม"),
            ("เด่ว", "เดี๋ยว"), ("เดว", "เดี๋ยว"),
            ("สนจัย", "สนใจ"),
            ("งับ", "ครับ"), ("ค้าบ", "ครับ"), ("คั้บ", "ครับ"), ("คาบ", "ครับ"), ("คับ", "ครับ"),
            ("ไร", "อะไร"),
            ("ถึงยาง", "ถึงยัง"), ("ส่งยาง", "ส่งยัง"), ("ได้ยาง", "ได้ยัง") 
        ]
        
        for slang, formal in slang_replacements:
            step3 = step3.replace(slang, formal)
            
        step3 = step3.replace("ออะไร", "อะไร")
        step3 = step3.replace("ออยู่", "อยู่")

        text_for_tokenize = step3.replace("ไหนคะ", "ไหน คะ").replace("ไหมคะ", "ไหม คะ")
            
        raw_tokens = word_tokenize(text_for_tokenize, engine="newmm")
        
        step5_tokens = [t.strip() for t in raw_tokens if t not in self.junk_tokens and t.strip() != ""]
        step5_text = "".join(step5_tokens)

        intent = "ข้อความทั่วไป"
        adjusted = step5_text

        if any(word in step5_text for word in ["ส่ง", "ถึงไหน", "ได้ของ", "พัสดุ", "วันไหน", "ถึงยัง", "ส่งยัง"]):
            intent = "สอบถามสถานะสินค้า"
            if "วัน" in step5_text:
                adjusted = "สินค้าจะจัดส่งถึงในวันไหน"
            elif "ถึงไหน" in step5_text:
                adjusted = "สินค้าถึงขั้นตอนไหนของการจัดส่งแล้ว"
            elif "ได้ของ" in step5_text:
                adjusted = "ได้รับสินค้าแล้วหรือยัง"
            else:
                adjusted = "สินค้าจัดส่งแล้วหรือยัง"
                
        elif any(word in step5_text for word in ["โอน", "จ่าย", "ยอด", "สลิป"]):
            intent = "แจ้งชำระเงิน"
            if "เช็ค" in step5_text or "ตรวจสอบ" in step5_text:
                adjusted = "โอนเงินเรียบร้อยแล้ว ตรวจสอบให้ด้วย"
            else:
                adjusted = "โอนเงินเรียบร้อยแล้ว"
                
        elif "เปลี่ยน" in step5_text or "เคลม" in step5_text:
            intent = "ขอเปลี่ยนสินค้า"
            if any(word in step5_text for word in ["ไซส์", "เล็ก", "ใหญ่", "ขนาด"]):
                adjusted = "ต้องการขอเปลี่ยนไซส์สินค้า"
            else:
                adjusted = "ต้องการขอเปลี่ยนสินค้า"
                
        elif any(word in step5_text for word in ["สนใจ", "ราคา", "สี", "ขนาด", "ไซส์", "เท่าไหร่", "กี่บาท"]):
            intent = "สอบถามรายละเอียดสินค้า"
            adjusted = step5_text

        info_product = "-"
        info_attr = "-"
        if "เสื้อ" in step5_text: info_product = "เสื้อ"
        if "กางเกง" in step5_text: info_product = "กางเกง"
        
        if "สี" in step5_text: info_attr = "สี (Color)"
        elif "ไซส์" in step5_text or "ขนาด" in step5_text: info_attr = "ไซส์ (Size)"
        elif "ราคา" in step5_text or "เท่าไหร่" in step5_text: info_attr = "ราคา (Price)"

        if has_polite_suffix:
            final_is_question = any(word in adjusted for word in ["ไหน", "ยัง", "ไหม", "อะไร", "เท่าไหร่", "กี่", "บ้าง"])
            if is_female:
                polite_word = "คะ" if final_is_question else "ค่ะ"
            else:
                polite_word = "ครับ"
            
            base_sentence = adjusted.rstrip("ครับคะค่ะ")
            final_output = f"{base_sentence}{polite_word}"
        else:
            final_output = adjusted

        return {
            "step_5_1": step1,
            "step_5_2": step2,
            "step_5_3": step3,
            "step_5_4": raw_tokens,
            "step_5_5": step5_tokens,
            "step_5_6": adjusted,
            "step_5_7": final_output,
            "step_5_8": intent,
            "product": info_product, "attr": info_attr, "has_suffix": has_polite_suffix
        }

