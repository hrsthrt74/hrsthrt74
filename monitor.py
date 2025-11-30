import requests
import os
import datetime

# --- 配置字典 ---

# 1. 设备代号与实际名称的映射
DEVICE_NAMES = {
    "p65": "REDMI Watch 6",
    "o66": "Xiaomi Band 10",
    "n67": "Xiaomi Band 9 Pro",
}

# 2. 设备屏幕比例映射 (宽度 W, 高度 H)
DEVICE_DIMENSIONS = {
    "p65": (432, 514),
    "o66": (212, 520),
    "n67": (336, 480),
}

# 3. 邮件中图片显示的固定宽度 (单位: px)
DISPLAY_WIDTH = 80 

# 4. 设备原始圆角数据 R (Req 1: 存储原始像素值)
DEVICE_CORNERS_RAW = {
    "p65": 102,  
    "o66": 223,  
    "n67": 48,   
}
# --- 结束配置 ---


# 配置 API URL
URL = "https://www.mibandtool.club:9073/watchface/listbytag/0/1/20/9999"

# 从环境变量获取需要监控的设备列表
TARGET_TYPES_STR = os.environ.get("TARGET_TYPES", "p65,o66,n67")
TARGET_TYPES = [t.strip() for t in TARGET_TYPES_STR.split(",") if t.strip()]

def fetch_data(device_type):
    """
    抓取指定设备类型的数据
    """
    headers = {
        'type': device_type,
        'User-Agent': 'Mozilla/5.0'
    }
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[{device_type}] 请求失败: {e}")
        return None

def format_ts(ts):
    if not ts: return "N/A"
    return datetime.datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d %H:%M')

def get_image_style(device_type):
    """
    根据设备代号计算图片的显示样式 (包含尺寸和比例圆角)
    """
    # 尺寸计算
    w_raw, h_raw = DEVICE_DIMENSIONS.get(device_type, (1, 1))
    display_height = int(DISPLAY_WIDTH * h_raw / w_raw) 
    size_style = f"width: {DISPLAY_WIDTH}px; height: {display_height}px;"
    
    # --- 圆角比例计算 (核心修复) ---
    r_raw = DEVICE_CORNERS_RAW.get(device_type, 4) # 原始圆角 R
    
    # 使用宽度 W 作为基准计算比例: Ratio = R / W_raw
    if w_raw > 0:
        radius_ratio = r_raw / w_raw
        # 将比例应用于显示宽度: New_Radius = Ratio * DISPLAY_WIDTH
        new_radius_px = radius_ratio * DISPLAY_WIDTH
        # 保留两位小数，确保平滑
        corner_style = f"border-radius: {new_radius_px:.2f}px;" 
    else:
        # 兜底
        corner_style = "border-radius: 4px;"

    return f"{size_style} {corner_style}"


def generate_html(all_data):
    # --- 样式美化和边距优化 (Req 2) ---
    css = """
    <style>
        /* 增加最大宽度到 90%，减少左右 body padding */
        body { 
            font-family: 'PingFang SC', 'Helvetica Neue', Arial, sans-serif; 
            color: #333; 
            max-width: 90%; /* 适应不同客户端宽度 */
            margin: 0 auto; 
            background-color: #f4f7f6; 
            padding: 10px; /* 减少边距 */
        } 
        /* 容器内边距和投影 */
        .container { 
            background-color: #ffffff; 
            border-radius: 12px; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.05); 
            padding: 10px; /* 进一步减少容器内边距 */
        } 
        .device-header { background: #e8f0ff; color: #004d99; padding: 10px 15px; border-radius: 8px; margin: 25px 0 15px 0; font-size: 18px; font-weight: bold; border-left: 5px solid #007bff; }
        .card { border-bottom: 1px solid #eee; padding: 15px 0; display: flex; align-items: flex-start; transition: background-color 0.3s;}
        .card:last-child { border-bottom: none; }
        .cover { object-fit: cover; margin-right: 20px; background-color: #f0f0f0; border: 1px solid #ddd; } /* border-radius 已在行内 style 覆盖 */
        .content { flex: 1; }
        .title { font-size: 16px; font-weight: 600; margin: 0 0 5px 0; color: #333; }
        .meta { font-size: 13px; color: #666; line-height: 1.6; }
        .stat-badge { display: inline-block; padding: 3px 8px; background: #eaf8f4; color: #00a680; border-radius: 12px; font-weight: bold; font-size: 11px; margin-right: 10px;}
        .signature { text-align: center; font-size: 11px; color: #a0a0a0; margin-top: 30px; padding-top: 15px; border-top: 1px solid #eee; }
    </style>
    """
    
    html = f"<html><head>{css}</head><body><div class='container'>"
    html += f"<h2 style='text-align:center; color: #34495e; margin-bottom: 25px;'>⌚ 表盘上新监控日报 ({datetime.datetime.now().strftime('%Y-%m-%d')})</h2>"

    has_content = False

    for dtype, items in all_data.items():
        if not items:
            continue
        
        has_content = True
        
        device_name = DEVICE_NAMES.get(dtype, dtype) 
        
        # 获取图片的动态样式 (尺寸 + 比例圆角)
        image_style = get_image_style(dtype)

        html += f"<div class='device-header'>📱 {device_name} (代号: {dtype})</div>"
        
        for item in items:
            name = item.get('name', 'Unknown')
            nick = item.get('nickname', 'Unknown')
            preview = item.get('preview', '')
            dl = item.get('downloadTimes', 0)
            views = item.get('views', 0)
            time_str = format_ts(item.get('updatedAt'))
            
            # 使用新的卡片布局
            html += f"""
            <div class="card">
                <img src="{preview}" class="cover" style="{image_style}" alt="{name}">
                <div class="content">
                    <p class="title">{name}</p>
                    <div class="meta">
                        <span class="stat-badge">作者: {nick}</span>
                        <span class="stat-badge" style="background: #fff0e6; color: #e67e22;">更新: {time_str}</span>
                        <p style="margin: 5px 0 0 0;">
                            📥 下载: <strong style="color: #007bff;">{dl}</strong> | 👀 浏览: <strong style="color: #007bff;">{views}</strong>
                        </p>
                    </div>
                </div>
            </div>
            """
            
    # 署名
    html += """
        </div>
        <p class="signature">
            Powered by GitHub Actions | 🤖 报告生成者：Gemini
        </p>
    </body>
    </html>
    """
    return html if has_content else None


# --- 保持 main 函数和执行逻辑不变 ---
def main():
    results = {}
    for dtype in TARGET_TYPES:
        data = fetch_data(dtype)
        if data and data.get('code') == 0:
            results[dtype] = data.get('data', [])
        else:
            results[dtype] = []

    html_content = generate_html(results)

    if html_content:
        with open("email_body.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("✅ 报告已生成。")
    else:
        with open("email_body.html", "w", encoding="utf-8") as f:
            f.write("<h3>今日无新表盘数据</h3>")

if __name__ == "__main__":
    main()
