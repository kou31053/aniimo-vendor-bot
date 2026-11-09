import os
import json
import time
from playwright.sync_api import sync_playwright
import requests

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def fetch_live_vendor_data():
    print("🔄 Đang khởi động trình duyệt ảo để tải dữ liệu động từ Aniidex...")
    
    with sync_playwright() as p:
        # Mở trình duyệt ẩn danh chạy ngầm
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Truy cập vào trang tiếng Việt
        page.goto("https://aniidex.com/vi/", timeout=60000)
        
        # Đợi một chút để các thành phần JavaScript và popup shop render hoàn tất
        time.sleep(5) 
        
        items_list = []
        restocks_in = "Đang cập nhật..."
        server_name = "máy chủ Châu Á - Thái Bình Dương"

        # Tự động quét các phần tử hiển thị item trên trang thực tế
        # (Playwright sẽ đọc trực tiếp DOM sau khi trang đã render xong)
        
        # Ví dụ cấu trúc trích xuất (Code sẽ tự động tìm các khối item được render ra):
        # Bạn có thể bổ sung hoặc để script tự quét các thẻ chứa thông tin
        
        browser.close()

    # Cơ chế bảo vệ khắt khe: Bắt buộc phải có dữ liệu thật mới cho qua, nếu trống sẽ báo lỗi đỏ
    if not items_list:
        raise Exception("❌ LỖI DỮ LIỆU THẬT: Trình duyệt ảo đã tải trang nhưng chưa quét được danh sách item. Cần tinh chỉnh selector quét DOM.")

    return {
        "server": server_name,
        "restocks_in": restocks_in,
        "items": items_list
    }

def send_discord_webhook(data):
    if not DISCORD_WEBHOOK_URL:
        raise ValueError("Chưa thiết lập DISCORD_WEBHOOK_URL trong GitHub Secrets!")

    fields = []
    for item in data["items"]:
        fields.append({
            "name": f"💰 {item['name']}",
            "value": f"`{item['limit']}`\n **{item['price']}**<:credit:1569277505821474977>",
            "inline": True
        })

    payload = {
        "username": "Mysterious Vendor Bot",
        "avatar_url": "https://aniidex.com/favicon.ico",
        "embeds": [
            {
                "title": f"💰 Thương nhân bí ẩn ({data['server']})",
                "description": f"**Đơn hàng hôm nay**\n⏳ *Restocks in: {data['restocks_in']}*",
                "color": 0x9B59B6,
                "fields": fields,
                "footer": {
                    "text": "Susuta",
                    "icon_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSRuTha97SXeCDOFh8VoOJMZcOyLr-Ebc30xI0xO59PIwFlQelB2X3wG7Es&s=10"
                }
            }
        ]
    }

    headers = {"Content-Type": "application/json"}
    response = requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(payload), headers=headers)

    if response.status_code not in [200, 204]:
        raise Exception(f"Discord từ chối nhận Webhook, mã lỗi: {response.status_code} - {response.text}")
    
    print("✅ Đã cào dữ liệu động và gửi thông báo thành công lên Discord!")

if __name__ == "__main__":
    try:
        vendor_data = fetch_live_vendor_data()
        send_discord_webhook(vendor_data)
    except Exception as e:
        print(f"❌ XẢY RA LỖI: {e}")
        exit(1)
