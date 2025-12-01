"""
修复 web_ui/index.html 中的 API_URL
将硬编码的 localhost 改为自动适配的 window.location.origin
"""
import re

html_file = r"c:\Users\User\Desktop\trading_terminal\web_ui\index.html"

# 读取文件
with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 查找并替换
old_pattern = r"const API_URL = 'http://localhost:8000/api';"
new_code = "// 自动适配 ngrok 或 localhost\n        const API_URL = window.location.origin + '/api';"

if old_pattern in content:
    content = content.replace(old_pattern, new_code)
    print("✅ 找到并替换了硬编码的API_URL")
else:
    print("⚠️ 未找到目标代码，可能已被修改")
    print("正在搜索其他可能的模式...")
    
    # 尝试其他可能的格式
    patterns = [
        r"const API_URL = \"http://localhost:8000/api\";",
        r"const API_URL='http://localhost:8000/api';",
    ]
    
    for pattern in patterns:
        if pattern in content:
            content = content.replace(pattern, new_code)
            print(f"✅ 使用备用模式修复成功")
            break

# 写回文件
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✅ 文件已更新: {html_file}")
print("\n现在ngrok访问时应该能正常登录了！")
