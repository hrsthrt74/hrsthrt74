import requests
import os
import datetime

# API 地址
URL = "https://www.mibandtool.club:9073/watchface/listbytag/0/1/20/9999"

# 从环境变量获取设备列表。如果 YAML 里没传，就默认用这三个。
TARGET_TYPES_STR = os.environ.get("TARGET_TYPES", "p65,o66,n67")
TARGET_TYPES = [t.strip() for t in TARGET_TYPES_STR.split(",") if t.strip()]

def fetch_data(device_type):
    headers = {
        'type': device_type, # 必填 header
        'User-Agent': 'Mozilla/5.0'
    }
    try:
        # print(f"正在抓取: {device_type}") # 调试用，GitHub Actions 日志里能看到
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[{device_type}] 抓取失败: {e}")
        return None

def format_ts(ts):
    if not ts: return "N/A"
    return datetime.datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d %H:%M')

def generate_html(all_data):
    # 邮件样式 CSS
    css = """
    <style>
        body { font-family: -apple-system, sans-serif; color: #333; max-width: 600px; margin: 0 auto; }
        .card { border: 1px solid #eee; border-radius: 8px; padding: 10px; margin-bottom: 10px; display: flex; align-items: flex-start; }
        .cover { width: 80px; height: 80px; object-fit: cover; border-radius: 6px; margin-right: 15px; background: #f0f0f0; }
        .content { flex: 1; }
        .title { font-size: 16px; font-weight: bold; margin: 0 0 5px 0; color: #2c3e50; }
        .meta { font-size: 12px; color: #666; line-height: 1.5; }
        .badge { display: inline-block; padding: 2px 6px; background: #eef2f5; color: #555; border-radius: 4px; font-size: 10px; margin-right: 5px;}
        .stat { color: #e67e22; font-weight: bold; }
        .device-header { background: #f8f9fa; padding: 8px 10px; border-left: 4px solid #0366d6; margin: 20px 0 10px 0; font-weight: bold; }
    </style>
    """
    
    html = f"<html><head>{css}</head><body>"
    html += f"<h3>⌚ 表盘上新监控 ({datetime.datetime.now().strftime('%m-%d')})</h3>"

    has_content = False

    for dtype, items in all_data.items():
        if not items:
            continue # 如果这个设备没数据，就不显示这一段
        
        has_content = True
        html += f"<div class='device-header'>📱 设备型号: {dtype}</div>"
        
        for item in items:
            name = item.get('name', 'Unknown')
            nick = item.get('nickname', 'Unknown')
            preview = item.get('preview', '')
            dl = item.get('downloadTimes', 0)
            views = item.get('views', 0)
            time_str = format_ts(item.get('updatedAt'))

            html += f"""
            <div class="card">
                <img src="{preview}" class="cover" alt="preview">
                <div class="content">
                    <div class="title">{name}</div>
                    <div class="meta">
                        <span class="badge">作者: {nick}</span>
                        <span class="badge">更新: {time_str}</span>
                        <br>
                        🔥 下载: <span class="stat">{dl}</span> | 浏览: {views}
                    </div>
                </div>
            </div>
            """
            
    html += "<p style='text-align:center; font-size:10px; color:#999;'>GitHub Actions 自动发送</p></body></html>"
    return html if has_content else None

def main():
    results = {}
    for dtype in TARGET_TYPES:
        data = fetch_data(dtype)
        if data and data.get('code') == 0:
            results[dtype] = data.get('data', [])
        else:
            results[dtype] = []

    # 生成 HTML
    html_content = generate_html(results)

    if html_content:
        # 写入文件供 Actions 发送
        with open("email_body.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("✅ 发现数据，报告已生成。")
    else:
        print("⚠️ 所有设备均无数据，不生成报告。")
        # 如果你想没数据时不发邮件，可以删掉 email_body.html 或者在 Actions 里判断
        # 这里为了演示，我们还是生成一个空提示
        with open("email_body.html", "w", encoding="utf-8") as f:
            f.write("<h3>今日无新表盘数据</h3>")

if __name__ == "__main__":
    main()
