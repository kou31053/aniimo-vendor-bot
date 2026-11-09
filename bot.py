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
            # Chọn đúng các thẻ chứa thông tin chi tiết từng món đồ bên trong danh sách shop
            # Thay vì quét toàn trang, ta tìm các khối item cụ thể
            product_cards = page.locator(".grid > div, .vendor-item, div:has-text('Giới hạn ngày')").all()
            
            for card in product_cards:
                text_content = card.inner_text().strip()
                # Lọc chỉ lấy các khối chứa thông tin item thực sự (có chứa chữ giới hạn hoặc giá)
                if text_content and ("Giới hạn" in text_content or "Daily limit" in text_content):
                    lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                    
                    if len(lines) >= 3:
                        # Dòng chứa tên item (thường là dòng phía trên chữ giới hạn)
                        item_name = lines[0]
                        if "Thương Nhân" in item_name or "Asia" in item_name:
                            item_name = lines[1] if len(lines) > 1 else "Vật phẩm đặc biệt"
                            
                        item_limit = lines[-2] if len(lines) >= 2 else "Daily limit: 5"
                        item_price = lines[-1] if len(lines) >= 1 else "32.000"
                        
                        items_list.append({
                            "name": item_name,
                            "limit": item_limit,
                            "price": item_price
                        })
            
            # Nếu bộ lọc trên chưa bắt được, ta ép lấy danh sách các thẻ sản phẩm cụ thể qua cấu trúc tên
            if not items_list:
                # Quét các thẻ có chứa tên vật phẩm game thực tế
                all_divs = page.locator("div").all()
                for d in all_divs:
                    t = d.inner_text().strip()
                    if "Lõi Hành Trang" in t or "Cát Sao" in t or "Tình Thế Vô Định" in t:
                        lines = [l.strip() for l in t.split('\n') if l.strip()]
                        if len(lines) >= 3:
                            items_list.append({
                                "name": lines[0],
                                "limit": lines[1],
                                "price": lines[2]
                            })
                            break
                            
        except Exception as e:
            print(f"⚠️ Lỗi khi trích xuất DOM: {e}")

        browser.close()

    # Nếu vẫn chưa lấy được, báo lỗi để kiểm tra log
    if not items_list:
        raise Exception("❌ LỖI DỮ LIỆU THẬT: Không thể trích xuất tên item chính xác từ trang web.")

    return {
        "server": server_name,
        "restocks_in": restocks_in,
        "items": items_list[:3] # Lấy đúng 3 món đầu tiên
    }

def send_discord_webhook(data):
    if not DISCORD_WEBHOOK_URL:
        raise ValueError("Chưa thiết lập DISCORD_WEBHOOK_URL trong GitHub Secrets!")

    fields = []
    for item in data["items"]:
        fields.append({
            "name": f"✨ {item['name']}",
            "value": f"🛒 `{item['limit']}`\n **{item['price']}**<:credit:1569277505821474977>",
            "inline": True
        })

    payload = {
        "username": "Mysterious Vendor Bot",
        "avatar_url": "https://aniidex.com/favicon.ico",
        "embeds": [
            {
                "title": f"🛍️ Thương nhân bí ẩn ({data['server']})",
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
    
    print("✅ Đã cập nhật và gửi tên item chuẩn xác lên Discord!")

if __name__ == "__main__":
    try:
        vendor_data = fetch_live_vendor_data()
        send_discord_webhook(vendor_data)
    except Exception as e:
        print(f"❌ XẢY RA LỖI: {e}")
        exit(1)
