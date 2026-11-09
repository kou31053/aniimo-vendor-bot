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
    
    print("🔄 Đang kết nối trực tiếp tới Aniidex (Tiếng Việt) để lấy dữ liệu tự động...")
    response = requests.get(url, headers=headers, timeout=15)
    
    if response.status_code != 200:
        raise Exception(f"Lỗi kết nối trang web, mã HTTP: {response.status_code}")

    soup = BeautifulSoup(response.text, 'html.parser')
    
    items_list = []
    restocks_in = "Đang cập nhật..."
    server_name = "máy chủ Châu Á - Thái Bình Dương"

    # Trích xuất cục dữ liệu JSON ẩn (__NEXT_DATA__) mà trang web Next.js sử dụng
    next_data_script = soup.find('script', id='__NEXT_DATA__')
    if not next_data_script:
        raise Exception("❌ Không tìm thấy khối dữ liệu cấu trúc __NEXT_DATA__ trên trang web.")

    try:
        json_data = json.loads(next_data_script.string)
        page_props = json_data.get('props', {}).get('pageProps', {})
        
        # In ra log GitHub toàn bộ cấu trúc keys để kiểm tra dữ liệu thực tế bên trong web
        print(f"🔍 Dữ liệu thô từ trang web: {list(page_props.keys())}")
        
        # Code sẽ tự động dò tìm dữ liệu shop bên trong page_props tại đây
        # (Ví dụ: duyệt qua các nhánh để lấy tên item, limit, price)
        
    except Exception as e:
        raise Exception(f"❌ Lỗi giải mã dữ liệu JSON từ trang web: {e}")

    # Cơ chế bảo vệ: Bắt buộc phải có dữ liệu thật mới gửi, nếu trống sẽ báo lỗi đỏ
    if not items_list:
        raise Exception("❌ LỖI: Bot đã kết nối thành công nhưng danh sách item đang trống. Hãy kiểm tra tab Log của GitHub Actions để xem cấu trúc dữ liệu thô vừa được in ra.")

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
    
    print("✅ Đã tự động cào và gửi thông tin thành công lên Discord!")

if __name__ == "__main__":
    try:
        vendor_data = fetch_live_vendor_data()
        send_discord_webhook(vendor_data)
    except Exception as e:
        print(f"❌ XẢY RA LỖI: {e}")
        exit(1)
