import requests
import json
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv

load_dotenv()

api_llm = os.getenv("API_LLM")
api_key = os.getenv("API_KEY")

app = Flask(__name__)

def model_ai(text_input, classification=["positive", "neutral", "negative"]):

    url = api_llm


    payload = json.dumps({
        "model": "Qwen/Qwen2-VL-72B-Instruct-AWQ",
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Classify the text into {classification} โดยให้เก็บ Result และแสดงผลลัพธ์เป็น JSON file เท่านั้น **ห้าม**มีคำอธิบายหรือข้อความเพิ่มเติม \n
                                    Text: นัดติดตั้งอินเตอร์เน็ตบ้าน แต่ช่างไม่มาติดตั้งแล้วเลื่อน
                                        ไม่อยากได้ลูกค้า หรือคะ ???
                                        ไม่ได้รับการติดต่อ บอกจะโทรมาโทรหาคอลเซ็นเตอร์สองถึง
                                        สามครั้ง ก็ไม่มีใครโทรมา
                                        ครั้งแรกเลื่อนบอกว่ารับงานนอกแบบนี้ก็ได้หรอคะ ต้องลางาน
                                        นะคะไม่ได้ว่างรอคุณตลอดนัดแล้วไม่มา คุณภาพบริการสวน
                                        ทางมากเลยค่ะ \n
        
                                    Result:
                                        "Topic": "การติดตั้งบริการอินเตอร์เน็ตบ้าน"
                                        "Intent": "แสดงความไม่พอใจและขอให้แก้ไขปัญหา"
                                        "Sentiment": "Negative"
                                    """

                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Text: {text_input}"
                    },
                    {
                        "type": "text",
                        "text": """set_response"""
                    }
                ]
            }
        ],
        "temperature": 0,
        "max_tokens": 500,
    })

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Basic {api_key}",
        'Cookie': 'Path=/'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"Error: {response.status_code} - {response.text}"
    except:
        return "Error: Unable to connect to the AI model."
    
    return None

def extract_json_from_text(text):
    try:
        # Find the start and end index of the JSON string
        start_index = text.find('{')
        end_index = text.rfind('}')

        if start_index == -1 or end_index == -1 or start_index > end_index:
            print("No JSON object found in the text.")
            return None

        json_string = text[start_index : end_index + 1]

        print("Extracted JSON string:")
        print(json_string)  # <--- print string to inspect

        # Attempt to parse the JSON string
        parsed_json = json.loads(json_string)
        return parsed_json

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

@app.route('/sentiment', methods=['POST'])
def analyze():
    data = request.get_json()
    text_input = data.get('text', '')
    classification = data.get('classifly', [])
    response = model_ai(text_input, classification)
    print("Response from AI model:", response)

    result = extract_json_from_text(response)

    return jsonify({
        "Result": result
        }) if result else jsonify({"error": "No valid JSON found in the response."})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)