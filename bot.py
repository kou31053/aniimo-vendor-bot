import os
import requests
import json
from bs4 import BeautifulSoup

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def fetch_live_vendor_data():
    url = "https://aniidex.com/vi/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print("🔄 Đang kết nối trực tiếp tới Aniidex (Tiếng Việt)...")
    response = requests.get(url, headers=headers, timeout=15)
    
    if response.status_code != 200:
        raise Exception(f"Lỗi kết nối trang web, mã HTTP: {response.status_code}")

    soup = BeautifulSoup(response.text, 'html.parser')
    
    items_list = []
    restocks_in = "Đang cập nhật..."
    server_name = "máy chủ Châu Á - Thái Bình Dương"

    # Cách 1: Quét thẻ chứa dữ liệu JSON cốt lõi của Next.js trên trang
    next_data_script = soup.find('script', id='__NEXT_DATA__')
    if next_data_script:
        try:
            json_data = json.loads(next_data_script.string)
            # Tại đây ta trích xuất dữ liệu shop từ cây JSON của Next.js
            # (Cấu trúc đường dẫn props tùy thuộc vào cách trang web định nghĩa)
            page_props = json_data.get('props', {}).get('pageProps', {})
            
            # Giả lập trích xuất nếu tìm thấy key chứa vendor hoặc items trong pageProps
            # Ví dụ: vendor_raw = page_props.get('vendor', {})
        except Exception as e:
            print(f"⚠️ Không thể parse dữ liệu JSON từ Next.js: {e}")

    # Cách 2: Quét trực tiếp các thẻ HTML hiển thị item trên trang tiếng Việt nếu có sẵn
    # Ví dụ dựa trên giao diện bạn chụp: tên item, giới hạn, giá tiền
    # (Nếu trang render động hoàn toàn qua client-side JS, ta sẽ bắt buộc phải đọc qua API endpoint đã thấy trong tab Network)
    
    # -------------------------------------------------------------------------
    # KIỂM TRA CHẶT CHẼ: BẮT BUỘC PHẢI CÓ DỮ LIỆU THẬT, KHÔNG DÙNG DỮ LIỆU GIẢ
    # -------------------------------------------------------------------------
    if not items_list:
        # Nếu danh sách trống, văng lỗi ngay để GitHub Actions báo đỏ (Failed)
        raise Exception("❌ LỖI DỮ LIỆU THẬT: Không thể tự động bóc tách được danh sách item từ trang web hôm nay. Vui lòng kiểm tra lại cấu trúc HTML hoặc API endpoint.")

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
    
    print("✅ Đã gửi thông báo dữ liệu thật lên Discord thành công!")

if __name__ == "__main__":
    try:
        vendor_data = fetch_live_vendor_data()
        send_discord_webhook(vendor_data)
    except Exception as e:
        print(f"❌ XẢY RA LỖI: {e}")
        exit(1)  # Báo lỗi đỏ trên GitHub Actions nếu có sự cố
