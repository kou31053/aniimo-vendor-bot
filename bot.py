import os
import json
import time
from playwright.sync_api import sync_playwright
import requests

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def fetch_live_vendor_data():
    print("🔄 Đang khởi động trình duyệt ảo để cào dữ liệu động...")
    
    with sync_playwright() as p:
        # Chạy trình duyệt ẩn danh
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Truy cập trang web
        page.goto("https://aniidex.com/vi/", timeout=60000)
        
        # Đợi trang tải xong và bấm vào mục Thương Nhân Bí Ân nếu cần thiết, 
        # hoặc chờ các thẻ item xuất hiện trên DOM
        time.sleep(6)
        
        items_list = []
        restocks_in = "Đang cập nhật..."
        server_name = "máy chủ Châu Á - Thái Bình Dương"

        # Quét các phần tử hiển thị item trên giao diện tiếng Việt thực tế
        # Thử tìm các khối chứa thông tin sản phẩm
        try:
            # Code quét tự động các item card trên trang sau khi JS đã render
            # (Chúng ta sẽ trích xuất text trực tiếp từ các thẻ HTML hiển thị)
            item_elements = page.locator(".vendor-item, div:has-text('Giới hạn ngày'), div:has-text('Daily limit')").all()
            
            # Nếu tìm thấy các phần tử, tiến hành bóc tách
            # (Tạm thời in ra số lượng tìm thấy để kiểm tra trên log)
            print(f"🔍 Số lượng phần tử tìm thấy trên trang: {len(item_elements)}")
            
        except Exception as e:
            print(f"⚠️ Chưa quét được DOM: {e}")

        browser.close()

    # Cơ chế bảo vệ khắt khe: Bắt buộc phải có dữ liệu thật mới cho qua
    if not items_list:
        raise Exception("❌ LỖI DỮ LIỆU THẬT: Trình duyệt ảo đã chạy nhưng danh sách item đang trống. Hãy kiểm tra lại logic quét selector.")

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
    
    print("✅ Đã gửi thông báo thành công lên Discord!")

if __name__ == "__main__":
    try:
        vendor_data = fetch_live_vendor_data()
        send_discord_webhook(vendor_data)
    except Exception as e:
        print(f"❌ XẢY RA LỖI: {e}")
        exit(1)
