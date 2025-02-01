from flask import Flask, request, jsonify
from linebot import LineBotApi
from linebot.models import TextSendMessage
import json
import os
from firebase import firebase
import google.generativeai as genai

# 使用環境變數讀取憑證
genai.configure(api_key=os.getenv('GPT_API_KEY'))
token = os.getenv('LINE_BOT_TOKEN')
secret = os.getenv('LINE_BOT_SECRET')
firebase_url = os.getenv('FIREBASE_URL')

def linebot(request):
    body = request.get_data(as_text=True)
    try:
        json_data = json.loads(body)  # JSON 解析
    except json.JSONDecodeError as e:
        print(f"JSON 解析錯誤：{e}")
        return 'OK'

    try:
        line_bot_api = LineBotApi(token)
        event = json_data['events'][0]
        tk = event['replyToken']
        user_id = event['source']['userId']
        msg_type = event['message']['type']

        fdb = firebase.FirebaseApplication(firebase_url, None)
        user_chat_path = f'chat/{user_id}'

        chat_history = fdb.get(user_chat_path, user_id) or {}
        if isinstance(chat_history, dict):  # 判斷 chat_history 是否為字典
            chat_history = list(chat_history.values())  # 將字典的值轉換為列表

        if msg_type == 'text':
            msg = event['message']['text']

            if msg == '!':
                reply_msg = TextSendMessage(text='對話歷史紀錄已經清空！')
                try:
                    fdb.delete(user_chat_path, None)  # Firebase 刪除
                    chat_history = []
                except Exception as e:
                    print(f"Firebase 刪除錯誤：{e}")
            else:
                chat_history.append({"role": "user", "content": msg})
                try:
                    model = genai.GenerativeModel("gemini-pro")

                    # 偵錯：印出完整的 chat_history
                    print("完整的 chat_history (除錯用)：", chat_history)

                    messages = [
                         {'content': "請用繁體中文回答", 'role': 'user'}  # 在使用者訊息中加入引導
                    ]
                    for i, m in enumerate(chat_history):
                        print(f"第 {i} 條訊息：{m}")  # 印出每條訊息
                        try:
                            if isinstance(m, list):  # 檢查 m 是否為列表
                                m = m[0]
                            if "content" not in m:
                                print(f"警告：第 {i} 條訊息缺少 'content' 鍵。跳過此訊息。")
                                continue  # 跳過此訊息
                            messages.append(m)
                        except Exception as e:
                            print(f"錯誤：提取第 {i} 條訊息的內容時發生錯誤：{e}")
                            print(f"有問題的訊息是：{m}")
                            continue # 或者 raise 中斷執行

                    print("傳送給 Gemini 的訊息：", messages) # 印出傳送給 Gemini 的訊息

                    response = model.generate_content(messages)

                    content = response.candidates[0].content
                    # 檢查 content 是否包含 parts 屬性
                    if hasattr(content, 'parts'):
                        text_content = ""
                        for part in content.parts:
                            # 檢查 part 是否包含 text 屬性
                            if hasattr(part, 'text'):
                                text_content += part.text
                        print(text_content)
                        start = text_content.find("text:") + 5  # 找到 "text:" 的位置，並加上 6 個字元（"text: "）
                        end = text_content.find("}", start)  # 找到下一個 "}" 的位置
                        text = text_content[start:end].strip()  # 提取 "text" 部分的內容，並去除前後的空白

                        chat_history.append({"role": "assistant", "content": text})
                        reply_msg = TextSendMessage(text=text)
                    else:
                        # 處理 content 不包含 parts 屬性的情況
                        print("Error: content does not have 'parts' attribute.")
                        chat_history.append({"role": "assistant", "content": str(content)})
                        reply_msg = TextSendMessage(text=str(content))

                    try:
                        fdb.put(user_chat_path, user_id, {str(i): {"role": m.get("role"), "content": m.get("content")} for i, m in enumerate(chat_history)})
                    except Exception as e:
                        print(f"Firebase 寫入錯誤：{e}")
                except Exception as e:
                    print(f"GPT API 錯誤：{e}")

            line_bot_api.reply_message(tk, reply_msg)
        else:
            line_bot_api.reply_message(tk, TextSendMessage(text='你傳的不是文字訊息呦'))

    except Exception as e:
        print(f"程式碼其他部分錯誤：{e}")
    return 'OK'

app = Flask(__name__)

# 測試 API
@app.route('/TEST', methods=['GET'])
def hello_http():
    return f"Hello World!"

# LINEBOT API
@app.route('/linebot', methods=['POST'])
def linebot_endpoint():
    return linebot(request)

# Cloud Run 入口點
def main(request):  
    return app  # Cloud Run 會透過這個回傳的 `app` 來處理請求

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)  # 只在本地運行

