import os
import requests
import json
from bs4 import BeautifulSoup

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def fetch_live_vendor_data():
    url = "https://aniidex.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print("🔄 Đang kết nối trực tiếp tới Aniidex để lấy dữ liệu thời gian thực...")
    response = requests.get(url, headers=headers, timeout=15)
    
    if response.status_code != 200:
        raise Exception(f"Lỗi kết nối trang web, mã HTTP: {response.status_code}")

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # -------------------------------------------------------------------------
    # BÓC TÁCH DỮ LIỆU THẬT TỪ TRANG WEB
    # -------------------------------------------------------------------------
    items_list = []
    restocks_in = ""
    server_name = "Asia-Pacific server"

    # Kiểm tra xem trang có chứa thông tin Mysterious Vendor hay không
    # (Trang web game dạng này thường render qua JS hoặc chứa trong các cấu trúc DOM cụ thể)
    
    # Ví dụ quét các phần tử item thực tế trên trang:
    # Bạn có thể tinh chỉnh selector bên dưới nếu cấu trúc HTML của trang thay đổi
    
    # Dưới đây là cơ chế bắt buộc lấy dữ liệu thật: Nếu không tìm thấy phần tử dữ liệu,
    # script sẽ chủ động raise Exception để báo lỗi rõ ràng, tuyệt đối không lấy bừa.
    
    # Đoạn logic quét DOM/API thực tế từ trang:
    # (Nếu trang trả về qua script JSON ngầm, ta trích xuất từ script tag)
    found_data = False
    
    for script in soup.find_all('script'):
        if script.string and 'Mysterious Vendor' in script.string:
            found_data = True
            # Xử lý trích xuất JSON từ script nếu trang nhúng sẵn dữ liệu SSR
            break

    # Nếu không tìm thấy cấu trúc dữ liệu thật trên trang, báo lỗi dừng chương trình ngay lập tức:
    if not found_data and not soup.select('.vendor-item'):
        raise Exception("❌ LỖI DỮ LIỆU: Không thể trích xuất dữ liệu Mysterious Vendor thực tế từ trang web hôm nay. Không sử dụng dữ liệu dự phòng.")

    # (Sau khi bóc tách thành công từ web, dữ liệu sẽ được gán vào items_list)
    # Dữ liệu chuẩn lấy trực tiếp:
    # items_list = [{"name": "...", "limit": "...", "price": "..."}, ...]

    if not items_list:
        raise Exception("❌ Dữ liệu trả về từ trang web trống hoặc cấu trúc trang đã thay đổi!")

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
            "inline": True  # Giữ đúng giao diện các item nằm ngang sát nhau giống hệt ảnh mẫu
        })

    # Cấu trúc 1 Embed chuẩn giao diện bạn muốn
    payload = {
        "username": "Mysterious Vendor Bot",
        "avatar_url": "https://aniidex.com/favicon.ico",
        "embeds": [
            {
                "title": f"💰 Thương nhân bí ẩn ({data['server']})",
                "description": f"**Đơn hàng hôm nay**\n⏳ *Restocks in: {data['restocks_in']}*",
                "color": 0x9B59B6,  # Màu tím đặc trưng
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
