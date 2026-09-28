# Sentiment Analysis API (Thai) with LLM

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-REST%20API-000000?logo=flask&logoColor=white)
![LLM](https://img.shields.io/badge/Qwen2--VL--72B--Instruct--AWQ-LLM-6E56CF)
![ngrok](https://img.shields.io/badge/ngrok-Public%20URL-1F1E37?logo=ngrok&logoColor=white)

REST API สำหรับ **วิเคราะห์ความคิดเห็น (Sentiment Analysis) ภาษาไทย** ด้วย **Large Language Model** (`Qwen/Qwen2-VL-72B-Instruct-AWQ`) แทนการเทรนโมเดลจำแนกข้อความเอง ใช้ **Prompt Engineering** และ **Few-shot examples** ให้ LLM วิเคราะห์ข้อความรีวิวหรือความคิดเห็นของลูกค้า แล้วตอบกลับเป็น JSON ที่นำไปใช้ต่อได้ทันที มี 2 แบบ:

| API | Endpoint | ผลลัพธ์ |
| --- | --- | --- |
| **Topic / Intent / Sentiment** ([`sentiment_text.py`](sentiment_text.py)) | `POST /analyze_sentiment` | หัวข้อที่พูดถึง (Topic), เจตนาของผู้เขียน (Intent) และความรู้สึก (Positive / Neutral / Negative) |
| **Custom Classification** ([`sentiment.py`](sentiment.py)) | `POST /sentiment` | จัดข้อความเข้าหมวดที่ผู้เรียกกำหนดเองในแต่ละ request เช่น `strongly positive`, `weakly negative` |

## สารบัญ

- [ภาพรวม](#ภาพรวม)
- [Workflow](#workflow)
- [API Reference](#api-reference)
- [Prompt Engineering](#prompt-engineering)
- [Tech Stack](#tech-stack)
- [โครงสร้างโปรเจกต์](#โครงสร้างโปรเจกต์)
- [Environment Variables](#environment-variables)
- [วิธีใช้งาน](#วิธีใช้งาน)
- [หมายเหตุและสิ่งที่ควรพัฒนาต่อ](#หมายเหตุและสิ่งที่ควรพัฒนาต่อ)

## ภาพรวม

การวิเคราะห์ Sentiment แบบดั้งเดิมต้องเก็บข้อมูลและ label เพื่อเทรนโมเดล และมักได้แค่ Positive/Negative โปรเจกต์นี้ใช้ LLM ซึ่งเข้าใจภาษาไทยรวมถึงภาษาพูด คำสะกดผิด และคำลากเสียง (เช่น "ชอบบบ", "ค้าบบบ") ได้โดยไม่ต้องเทรน และให้ข้อมูลเชิงลึกเพิ่มเติม:

- **Topic** — ลูกค้าพูดถึงเรื่องอะไร เช่น คุณภาพสินค้า การจัดส่ง การบริการหลังการขาย
- **Intent** — ลูกค้าต้องการให้เกิดอะไรขึ้น เช่น ขอเปลี่ยนสินค้า ขอชดเชย ขอคำชี้แจง
- **Sentiment** — ความรู้สึกโดยรวม

ตัวอย่างการใช้งาน: วิเคราะห์รีวิวสินค้าบน e-commerce, จัดลำดับเรื่องร้องเรียนของ Call Center, สรุปความคิดเห็นลูกค้าเป็น dashboard

## Workflow

### `POST /analyze_sentiment` (Topic / Intent / Sentiment)

```text
Client ── POST /analyze_sentiment {"text": "..."} ──▶ Flask (sentiment_text.py)
                                                          │
                                                          ▼
                                   ตรวจว่ามี "text" หรือไม่ → ไม่มี: 400 {"error": "Missing text file"}
                                                          │
                                                          ▼
                                   analyze_sentiment_llm(text)
                                     messages = [
                                       system: บทบาทผู้เชี่ยวชาญ + นิยาม Topic/Intent/Sentiment
                                               + รูปแบบ JSON + 6 ตัวอย่าง + ตัวอย่างที่ถูก/ผิด,
                                       user:   ข้อความที่ต้องการวิเคราะห์
                                     ]
                                                          │
                                                          ▼
                                   POST → LLM API (OpenAI-compatible Chat Completions)
                                     model: Qwen/Qwen2-VL-72B-Instruct-AWQ, max_tokens: 500
                                     Authorization: Basic <API_KEY>, timeout 60 วินาที
                                                          │
                                                          ▼
                                   choices[0].message.content
                                                          │
                                                          ▼
                                   parse_llm_output()
                                     1) regex หา {...} → json.loads()
                                     2) ถ้าไม่ใช่ JSON → regex ดึง "Topic: ...", "Intent: ...", "Sentiment: ..."
                                     3) ถ้าไม่เจอเลย → {"raw": ข้อความดิบ}
                                                          │
Client ◀── {"results": {"Topic": ..., "Intent": ..., "Sentiment": ...}} ──┘  (ensure_ascii=False)
```

### `POST /sentiment` (Custom Classification)

```text
Client ── POST /sentiment {"text": "...", "classifly": ["strongly positive", ...]} ──▶ Flask (sentiment.py)
                                                          │
                                                          ▼
                                   model_ai(text, classification)
                                     system: "Classify the text into [labels] ... ตอบเป็น JSON เท่านั้น"
                                             + ตัวอย่าง 1 ข้อ (ร้องเรียนการติดตั้งอินเทอร์เน็ตบ้าน)
                                     user:   "Text: ..."
                                     temperature: 0, max_tokens: 500
                                                          │
                                                          ▼
                                   extract_json_from_text()
                                     ตัดตั้งแต่ '{' ตัวแรกถึง '}' ตัวสุดท้าย → json.loads()
                                                          │
Client ◀── {"Result": {...}}  หรือ  {"error": "No valid JSON found in the response."} ──┘
```

### เปิด API สู่อินเทอร์เน็ตด้วย ngrok

```text
python start_ngrok.py
   ├─ import app จาก sentiment_text.py (โหลด .env)
   ├─ ตั้งค่า ngrok auth token จาก NGROK_AUTHTOKEN
   ├─ ngrok.connect(8000) → ได้ public URL เช่น https://xxxx.ngrok-free.app
   └─ app.run(port=8000)
```

## API Reference

### 1. `POST /analyze_sentiment`

**Request**

```bash
curl -X POST http://127.0.0.1:8000/analyze_sentiment \
  -H "Content-Type: application/json" \
  -d '{"text": "ส่งของไวมาก แต่ราคาขึ้นลงบ่อยมา ต้องเข้ามาเช็คราคาบ่อยๆ แต่คุ้มแน่นอนค่ะ"}'
```

| Field | Type | Required | คำอธิบาย |
| --- | --- | --- | --- |
| `text` | string | ✅ | ข้อความที่ต้องการวิเคราะห์ |

**Response** (`200 OK`)

```json
{
  "results": {
    "Topic": "การส่งสินค้าและการเปลี่ยนแปลงราคา",
    "Intent": "แสดงความพึงพอใจในบริการส่งสินค้าแต่แสดงความกังวลเรื่องการเปลี่ยนแปลงราคาสินค้า",
    "Sentiment": "Neutral"
  }
}
```

> ตัวอย่าง response นำมาจาก few-shot example ใน prompt ผลลัพธ์จริงขึ้นอยู่กับคำตอบของโมเดล

**Error** (`400 Bad Request`) เมื่อไม่ส่ง `text`:

```json
{"error": "Missing text file"}
```

### 2. `POST /sentiment`

**Request** (ตัวอย่างจาก [`sentiment_api.txt`](sentiment_api.txt))

```bash
curl --location http://127.0.0.1:8000/sentiment \
  -H "Content-Type: application/json" \
  -d '{
    "text": "สินค้าน่ารักแบบมากๆๆๆเบยค้าบ ปุ๊กปิ๊กมาก ผ้าดี มีบุซับใน ทำดี สมราคาค้าบบบบ แพ็คดี จัดส่งรววเร็ว ชอบบบ",
    "classifly": ["strongly positive", "strongly negative", "weakly positive", "weakly negative"]
  }'
```

| Field | Type | Required | คำอธิบาย |
| --- | --- | --- | --- |
| `text` | string | ✅ | ข้อความที่ต้องการวิเคราะห์ |
| `classifly` | array of string | แนะนำ | รายการหมวดที่ต้องการให้จัดเข้า (ชื่อ field สะกดตามโค้ด) |

**Response**

```json
{
  "Result": { "...": "JSON ที่โมเดลสร้างขึ้น เช่น Topic, Intent, Sentiment" }
}
```

หรือเมื่อแยก JSON จากคำตอบไม่ได้:

```json
{"error": "No valid JSON found in the response."}
```

## Prompt Engineering

### `sentiment_text.py` — Prompt ภาษาไทยแบบละเอียด

System prompt ออกแบบให้ได้ผลลัพธ์ที่ **เฉพาะเจาะจงและใช้งานได้จริง** โดยกำหนด:

| ส่วน | รายละเอียด |
| --- | --- |
| **บทบาท** | ผู้เชี่ยวชาญด้านการวิเคราะห์ข้อความ (รีวิวลูกค้า ความคิดเห็นเกี่ยวกับสินค้า/บริการ) |
| **นิยาม Topic** | หัวข้อที่จับต้องได้และเป็นกลาง เช่น คุณภาพสินค้า การจัดส่ง ราคาและโปรโมชั่น การคืน/เคลมสินค้า รวมหลายหัวข้อได้ และห้ามใช้คำคลุมเครืออย่าง "ความมั่นใจ", "ความรู้สึก" |
| **นิยาม Intent** | เป้าหมายที่ผู้เขียนต้องการให้เกิดขึ้นจริง (แก้ไข ชดเชย รับผิดชอบ อธิบาย) ไม่ใช่แค่ "ไม่พอใจ" และต้องสะท้อนการเรียกร้อง เช่น เปลี่ยนสินค้า คืนเงิน |
| **Sentiment** | Positive / Neutral / Negative |
| **รูปแบบผลลัพธ์** | JSON ที่มี 3 key: `Topic`, `Intent`, `Sentiment` |
| **คุณภาพภาษา** | ใช้ภาษาไทยถูกไวยากรณ์ ห้ามสะกดผิด และแก้คำผิดจากต้นฉบับในผลลัพธ์ |
| **Few-shot** | ตัวอย่างข้อความและผลลัพธ์ 6 ตัวอย่าง ครอบคลุม Positive, Negative, Neutral และข้อความที่มีหลายประเด็น |
| **ตัวอย่างที่ถูก/ผิด** | รายการ Topic และ Intent ที่ถูกต้อง และคำที่ควรหลีกเลี่ยง (negative examples) |

### `sentiment.py` — Prompt แบบกำหนดหมวดเอง

- ใส่รายการหมวดจาก request ลงใน prompt (`Classify the text into {classification}`)
- สั่งให้ตอบเป็น JSON เท่านั้น ห้ามมีคำอธิบายเพิ่ม
- มีตัวอย่าง 1 ข้อ (one-shot)
- `temperature: 0` ให้ผลลัพธ์คงที่

## Tech Stack

| หมวด | เทคโนโลยี | หน้าที่ในโปรเจกต์ |
| --- | --- | --- |
| ภาษา | **Python 3.12** | ภาษาหลัก |
| Web Framework | **Flask** | สร้าง REST API (`/analyze_sentiment`, `/sentiment`) |
| LLM | **Qwen2-VL-72B-Instruct-AWQ** | วิเคราะห์ข้อความภาษาไทย |
| LLM API | OpenAI-compatible Chat Completions API | endpoint ที่ให้บริการโมเดล (กำหนดผ่าน `API_LLM`) |
| HTTP Client | **requests** | เรียก LLM API |
| Parsing | `re`, `json` (Standard Library) | แยก JSON จากคำตอบของ LLM |
| Configuration | **python-dotenv** | โหลด API endpoint และ API key จาก `.env` |
| Tunneling | **pyngrok** | สร้าง public URL ให้ API ที่รันบนเครื่อง |
| Testing | **curl** / Postman | ทดสอบ API |

## โครงสร้างโปรเจกต์

```text
Sentiment-Analysis/
├── sentiment_text.py    # API หลัก: POST /analyze_sentiment → Topic / Intent / Sentiment
├── sentiment.py         # API ทางเลือก: POST /sentiment → จัดหมวดตามที่ผู้เรียกกำหนด
├── start_ngrok.py       # เปิด sentiment_text.py ผ่าน ngrok tunnel
├── sentiment_api.txt    # ตัวอย่างคำสั่ง curl สำหรับ /sentiment
├── .env                 # (ต้องสร้างเอง) API_LLM, API_KEY, NGROK_AUTHTOKEN
├── .gitignore
└── README.md
```

### ฟังก์ชันสำคัญ

| ไฟล์ | ฟังก์ชัน | หน้าที่ |
| --- | --- | --- |
| `sentiment_text.py` | `analyze_sentiment_llm(text)` | สร้าง messages (system prompt + ข้อความ) แล้วเรียก LLM API |
| `sentiment_text.py` | `parse_llm_output(output_text)` | แยก JSON จากคำตอบ ถ้าไม่ได้ใช้ regex ดึงทีละ key หรือคืนข้อความดิบ |
| `sentiment_text.py` | `analyze_sentiment_api()` | Route `POST /analyze_sentiment` |
| `sentiment.py` | `model_ai(text, classification)` | สร้าง prompt ตามหมวดที่กำหนดและเรียก LLM API |
| `sentiment.py` | `extract_json_from_text(text)` | ตัดข้อความระหว่าง `{` แรกถึง `}` สุดท้ายแล้ว `json.loads()` |
| `sentiment.py` | `analyze()` | Route `POST /sentiment` |

## Environment Variables

สร้างไฟล์ `.env` ที่ root ของโปรเจกต์:

```env
API_LLM=https://your-llm-provider.example.com/v1/chat/completions
API_KEY=your_base64_credentials
NGROK_AUTHTOKEN=your_ngrok_authtoken
```

| ตัวแปร | ใช้ใน | คำอธิบาย |
| --- | --- | --- |
| `API_LLM` | `sentiment.py`, `sentiment_text.py` | URL ของ Chat Completions endpoint |
| `API_KEY` | `sentiment.py`, `sentiment_text.py` | ค่าที่ใช้ใน header `Authorization: Basic <API_KEY>` (Base64 ของ `username:password`) |
| `NGROK_AUTHTOKEN` | `start_ngrok.py` | Auth token จาก [ngrok dashboard](https://dashboard.ngrok.com/get-started/your-authtoken) |

> ก่อน commit ต้องแน่ใจว่า `.gitignore` กันไฟล์ `.env` ได้จริง (ดู [หมายเหตุ](#หมายเหตุและสิ่งที่ควรพัฒนาต่อ))

## วิธีใช้งาน

### 1. ติดตั้ง dependencies

```bash
cd Sentiment-Analysis
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install flask requests python-dotenv pyngrok
```

### 2. ตั้งค่า `.env`

ดูหัวข้อ [Environment Variables](#environment-variables)

### 3. รัน API

ทั้งสองไฟล์ใช้พอร์ต `8000` จึงรันได้ทีละไฟล์

```bash
# API หลัก (Topic / Intent / Sentiment)
python sentiment_text.py

# หรือ API แบบกำหนดหมวดเอง
python sentiment.py
```

### 4. (ทางเลือก) เปิดให้เข้าถึงจากภายนอกด้วย ngrok

```bash
python start_ngrok.py
# * ngrok tunnel: NgrokTunnel: "https://xxxx.ngrok-free.app" -> "http://localhost:8000"
```

แล้วเรียก `https://xxxx.ngrok-free.app/analyze_sentiment` แทน `http://127.0.0.1:8000`

### 5. ทดสอบ

ใช้คำสั่ง `curl` ในหัวข้อ [API Reference](#api-reference) หรือ Postman

## หมายเหตุและสิ่งที่ควรพัฒนาต่อ

### ความปลอดภัย

- **`.gitignore` บันทึกเป็น UTF-16** ซึ่ง git อ่านไม่ได้ ไฟล์ `.env` จึง **ไม่ถูกกัน** และจะถูก commit ขึ้นไปพร้อม API key ต้องบันทึก `.gitignore` ใหม่เป็น **UTF-8** ก่อน commit
- **อย่าเขียน token ไว้ในโค้ด แม้จะเป็น comment** — ใช้ `os.getenv()` อ่านจาก `.env` อย่างเดียว ถ้าเคยเขียน token ลงในไฟล์ที่ commit หรือแชร์ไปแล้ว ให้ revoke แล้วออก token ใหม่
- **`debug=True` ร่วมกับ `host='0.0.0.0'`** เปิด Werkzeug debugger ให้เครื่องอื่นในเครือข่ายเข้าถึงได้ ซึ่งรันโค้ดบนเซิร์ฟเวอร์ได้ ควรปิด debug เมื่อเปิดให้คนอื่นใช้ และใช้ WSGI server อย่าง Gunicorn/Waitress แทน `app.run()`
- API ยังไม่มีการยืนยันตัวตนหรือจำกัดจำนวน request เมื่อเปิดผ่าน ngrok ใครที่รู้ URL ก็เรียกใช้โควต้า LLM ได้

### ปัญหาที่พบในโค้ด

- **`sentiment_text.py`** — เมื่อเรียก LLM ไม่สำเร็จ `analyze_sentiment_llm()` คืนค่าเป็น dict (`{"error": ...}`) แต่ `parse_llm_output()` ใช้ `re.search` กับค่านั้น ทำให้เกิด `TypeError` และตอบ HTTP 500 แทนที่จะบอกสาเหตุ
- **`sentiment.py`** — ถ้าไม่ส่ง `classifly` prompt จะกลายเป็น `Classify the text into []` ควรใช้ค่าเริ่มต้น `["positive", "neutral", "negative"]` เหมือนที่ประกาศไว้ใน `model_ai()`
- **`sentiment.py`** — ส่งข้อความ `"set_response"` ต่อท้าย user message ซึ่งไม่ได้ใช้ และใช้ `except:` แบบไม่ระบุชนิด ทำให้ซ่อนสาเหตุของ error
- **ชื่อ field `classifly`** สะกดผิด (ควรเป็น `classify` หรือ `labels`) ถ้าแก้ต้องแก้ทั้งโค้ดและตัวอย่างใน `sentiment_api.txt`
- **ชื่อ key ไม่สม่ำเสมอ** — endpoint หนึ่งตอบ `results` อีกอันตอบ `Result`
- ยังไม่มี `requirements.txt`

### แนวทางพัฒนาต่อ

- รองรับ **Batch** (ส่งหลายข้อความใน request เดียว) และ export ผลเป็น CSV
- ใช้ **Structured Output / JSON mode** ของ LLM (ถ้า API รองรับ) แทนการแยก JSON ด้วย regex และ validate ผลด้วย Pydantic
- จำกัดค่า `Sentiment` ให้เป็น enum และเพิ่ม **confidence score**
- สร้างชุดข้อมูลทดสอบที่มี label เพื่อวัดความแม่นยำ (accuracy, F1) ของ prompt แต่ละเวอร์ชัน
- ทำ Dashboard สรุป Topic และ Sentiment ของรีวิวทั้งหมด
- ใส่ Docker และ deploy บนเซิร์ฟเวอร์จริงแทน ngrok
