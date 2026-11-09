import os
import requests
import json

# Lấy Webhook URL từ kho bảo mật GitHub Secrets
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def send_mysterious_vendor_notification():
    if not DISCORD_WEBHOOK_URL:
        print("❌ Chưa cấu hình Webhook URL!")
        return

    # Thông tin các món đồ từ Mysterious Vendor (Asia-Pacific server)
    vendor_data = {
        "server": "Asia-Pacific server",
        "restocks_in": "12h 32m",
        "items": [
            {
                "name": "Common Held Item Core",
                "limit": "Daily limit: 5",
                "price": "32,000"
            },
            {
                "name": "Star Sand",
                "limit": "Daily limit: 5",
                "price": "32,000"
            },
            {
                "name": "Flux Crystal",
                "limit": "Daily limit: 5",
                "price": "48,000"
            }
        ]
    }

    # Tạo các ô hiển thị vật phẩm (Fields) giống hệt giao diện game
    fields = []
    for item in vendor_data["items"]:
        fields.append({
            "name": f"✨ {item['name']}",
            "value": f"🛒 `{item['limit']}`\n💰 **{item['price']}** Gold",
            "inline": True
        })

    # Đóng gói tin nhắn dạng Embed màu tím đặc trưng
    payload = {
        "username": "Mysterious Vendor Bot",
        "avatar_url": "https://aniidex.com/favicon.ico",
        "embeds": [
            {
                "title": f"🛍️ Mysterious Vendor ({vendor_data['server']})",
                "description": f"**Today's Best Buys**\n⏳ *Restocks in: {vendor_data['restocks_in']}*",
                "color": 0x9B59B6,  # Màu tím
                "fields": fields,
                "footer": {
                    "text": "Aniimo Helper Bot",
                    "icon_url": "https://aniidex.com/favicon.ico"
                }
            }
        ]
    }

    headers = {"Content-Type": "application/json"}
    response = requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(payload), headers=headers)

    if response.status_code in [200, 204]:
        print("✅ Gửi thông báo thành công lên Discord!")
    else:
        print(f"❌ Gửi thất bại: {response.text}")

if __name__ == "__main__":
    send_mysterious_vendor_notification()
