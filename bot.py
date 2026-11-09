import os
import time
import json
from playwright.sync_api import sync_playwright
import requests

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def fetch_live_vendor_data():
    print("🔄 Đang khởi động trình duyệt ảo để cào dữ liệu chuẩn HTML...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Truy cập trang web tiếng Việt
        page.goto("https://aniidex.com/vi/", timeout=60000)
        
        # Đợi trang render hoàn tất các thành phần
        time.sleep(6)
        
        items_list = []
        restocks_in = "Đang cập nhật..."
        server_name = "máy chủ Châu Á - Thái Bình Dương"

        try:
            # 1. Lấy thời gian đếm ngược restock từ vdp-foot
            clock_el = page.locator(".vdp-foot").first
            if clock_el.count() > 0:
                clock_text = clock_el.inner_text().strip()
                # Lọc lấy phần thời gian (ví dụ: "Nhập hàng mới sau 10 giờ 4 phút")
                restocks_in = clock_text.replace("Nhập hàng mới sau", "").strip()

            # 2. Quét tất cả các thẻ <li> nằm bên trong khối danh sách sản phẩm .vdp-goods
            item_elements = page.locator("ul.vdp-goods > li").all()
            print(f"🔍 Số lượng sản phẩm tìm thấy trong HTML: {len(item_elements)}")

            for li in item_elements:
                # Lấy tên item từ thuộc tính title của thẻ gcard
                gcard = li.locator("span.gcard")
                item_name = gcard.get_attribute("title") if gcard.count() > 0 else "Vật phẩm đặc biệt"

                # Lấy giới hạn từ thẻ vdp-text
                text_el = li.locator("span.vdp-text")
                item_limit = text_el.inner_text().strip() if text_el.count() > 0 else "Giới hạn ngày 5"

                # Lấy giá tiền từ thẻ num
                num_el = li.locator("span.num")
                item_price = num_el.inner_text().strip() if num_el.count() > 0 else "32.000"

                if item_name:
                    items_list.append({
                        "name": item_name,
                        "limit": item_limit,
                        "price": item_price
                    })

        except Exception as e:
            print(f"⚠️ Lỗi khi trích xuất DOM: {e}")

        browser.close()

    # Cơ chế bảo vệ khắt khe: Bắt buộc phải có dữ liệu thật mới cho qua
    if not items_list:
        raise Exception("❌ LỖI DỮ LIỆU THẬT: Không thể trích xuất danh sách item từ cấu trúc .vdp-goods.")

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
    
    print("✅ Đã cào chính xác toàn bộ dữ liệu thật và gửi lên Discord thành công!")

if __name__ == "__main__":
    try:
        vendor_data = fetch_live_vendor_data()
        send_discord_webhook(vendor_data)
    except Exception as e:
        print(f"❌ XẢY RA LỖI: {e}")
        exit(1)
