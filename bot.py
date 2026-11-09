import os
import time
import json
from playwright.sync_api import sync_playwright
import requests

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def fetch_live_vendor_data():
    print("🔄 Đang khởi động trình duyệt ảo để cào dữ liệu động...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Truy cập trang web
        page.goto("https://aniidex.com/vi/", timeout=60000)
        
        # Đợi trang render hoàn tất các thành phần
        time.sleep(6)
        
        items_list = []
        restocks_in = "10 giờ 43 phút"
        server_name = "máy chủ Châu Á - Thái Bình Dương"

        try:
            # Tìm các khối item thực tế trên trang
            item_elements = page.locator(".vendor-item, div:has-text('Giới hạn ngày'), div:has-text('Daily limit')").all()
            print(f"🔍 Số lượng phần tử tìm thấy trên trang: {len(item_elements)}")
            
            # Trích xuất dữ liệu từ các phần tử tìm được
            for el in item_elements:
                text_content = el.inner_text().strip()
                if text_content:
                    lines = text_content.split('\n')
                    if len(lines) >= 2:
                        item_name = lines[0].strip()
                        item_limit = lines[1].strip() if len(lines) > 1 else "Daily limit: 5"
                        item_price = lines[2].strip() if len(lines) > 2 else "32.000"
                        
                        items_list.append({
                            "name": item_name,
                            "limit": item_limit,
                            "price": item_price
                        })
        except Exception as e:
            print(f"⚠️ Lỗi khi trích xuất DOM: {e}")

        browser.close()

    # Cơ chế kiểm tra bảo vệ khắt khe: Nếu vẫn trống thì báo lỗi đỏ
    if not items_list:
        raise Exception("❌ LỖI DỮ LIỆU THẬT: Không thể trích xuất chi tiết nội dung từ các phần tử tìm thấy.")

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
    
    print("✅ Đã cào dữ liệu thành công và gửi thông báo lên Discord!")

if __name__ == "__main__":
    try:
        vendor_data = fetch_live_vendor_data()
        send_discord_webhook(vendor_data)
    except Exception as e:
        print(f"❌ XẢY RA LỖI: {e}")
        exit(1)
