import os
import requests
import json

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def fetch_live_vendor_data():
    # Sử dụng endpoint API hoặc trang dữ liệu gốc của Aniidex
    # Thường các web kiểu này sẽ gọi các tệp dữ liệu dạng JSON trực tiếp hoặc qua API endpoint
    api_url = "https://aniidex.com/vi/" 
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html,application/xhtml+xml"
    }
    
    print("🔄 Đang kết nối trực tiếp tới máy chủ Aniidex...")
    response = requests.get(api_url, headers=headers, timeout=15)
    
    if response.status_code != 200:
        raise Exception(f"Lỗi kết nối trang web, mã HTTP: {response.status_code}")

    # Giả lập trích xuất dữ liệu thực tế từ luồng API/phản hồi của trang
    items_list = []
    restocks_in = "10 giờ 43 phút" # Lấy từ thực tế hiển thị trên web
    server_name = "máy chủ Châu Á - Thái Bình Dương"

    # --- Nếu trang trả về HTML, ta tìm dữ liệu text hoặc cấu trúc shop ---
    # Vì trang load động, ta sẽ cấu trúc hàm để bắt buộc phải lấy được ít nhất dữ liệu item
    # (Nếu items_list rỗng, script sẽ chủ động báo lỗi đỏ để kiểm soát tính chính xác tuyệt đối)
    
    # Dưới đây là khung kiểm tra dữ liệu thật:
    if not items_list:
        # Nếu chưa map được mảng dữ liệu tự động từ API, ta in ra thông báo để tinh chỉnh
        raise Exception("❌ LỖI: Chưa trích xuất được danh sách item từ phản hồi của trang web.")

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
    
    print("✅ Đã gửi thông báo tự động thành công lên Discord!")

if __name__ == "__main__":
    try:
        vendor_data = fetch_live_vendor_data()
        send_discord_webhook(vendor_data)
    except Exception as e:
        print(f"❌ XẢY RA LỖI: {e}")
        exit(1)
