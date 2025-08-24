import os
from bs4 import BeautifulSoup
import re

def extract_head_and_body_body(html_file):
    """提取HTML文件中head和body部分的内容"""
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        
        # 提取head中的样式
        head_styles = []
        if soup.head:
            # 提取所有样式标签
            style_tags = soup.head.find_all('style')
            head_styles = [str(tag) for tag in style_tags]
            
            # 提取所有link标签（外部样式）
            link_tags = soup.head.find_all('link', rel='stylesheet')
            head_styles.extend([str(tag) for tag in link_tags])
        
        # 提取body内容
        body_content = ""
        if soup.body:
            body_content = ''.join(map(str, soup.body.contents))
            
        return '\n'.join(head_styles), body_content

def scope_css_styles(css, scope_selector):
    """
    将CSS样式限制在指定的作用域内
    使用更完善的正则表达式处理各种CSS选择器情况
    """
    # 移除<style>标签
    css = re.sub(r'<style.*?>', '', css)
    css = re.sub(r'</style>', '', css)
    
    # 处理CSS注释
    css = re.sub(r'/\*.*?\*/', lambda m: m.group(0).replace('{', '{\n'), css, flags=re.DOTALL)
    
    # 分割CSS规则（处理各种情况）
    rules = re.split(r'(?<=\})', css)
    
    scoped_rules = []
    for rule in rules:
        rule = rule.strip()
        if not rule:
            continue
            
        # 分离选择器和样式内容
        parts = re.split(r'\{', rule, 1)
        if len(parts) < 2:
            scoped_rules.append(rule)
            continue
            
        selectors_part, styles_part = parts
        selectors = re.split(r',', selectors_part)
        
        # 为每个选择器添加作用域
        scoped_selectors = []
        for selector in selectors:
            selector = selector.strip()
            if not selector:
                continue
                
            # 处理特殊选择器（如媒体查询、伪类等）
            if selector.startswith('@'):
                # 媒体查询等不添加作用域
                scoped_selectors.append(selector)
            elif selector == ':root':
                # :root选择器替换为作用域选择器
                scoped_selectors.append(scope_selector)
            else:
                # 普通选择器添加作用域
                scoped_selectors.append(f'{scope_selector} {selector}')
        
        # 重新组合选择器和样式
        if scoped_selectors:
            scoped_rule = f"{', '.join(scoped_selectors)} {{{styles_part}"
            scoped_rules.append(scoped_rule)
    
    return '\n'.join(scoped_rules)

def generate_index_html(slide_files, output_file='index.html'):
    """
    生成包含所有幻灯片的index.html文件，修复样式丢失问题
    """
    # 读取所有幻灯片内容和样式
    slide_data = []
    for i, slide_file in enumerate(slide_files):
        slide_styles, slide_content = extract_head_and_body_body(slide_file)
        slide_id = f"slide{i+1}"
        slide_data.append({
            'id': slide_id,
            'styles': slide_styles,
            'content': slide_content
        })
    
    # 生成幻灯片HTML部分
    slide_contents = []
    for data in slide_data:
        # 创建更精确的作用域选择器
        scope_selector = f'#{data["id"]}'
        # 应用样式作用域
        scoped_styles = scope_css_styles(data['styles'], scope_selector)
        
        wrapped_content = f'''<div class="slide" id="{data["id"]}">
            <style>
                {scoped_styles}
            </style>
            {data["content"]}
        </div>'''
        slide_contents.append(wrapped_content)
    
    # 生成导航按钮
    nav_buttons = []
    for i in range(len(slide_files)):
        active_class = "active" if i == 0 else ""
        nav_buttons.append(f'<button class="nav-button {active_class}" data-slide="{i}"></button>')
    nav_html = '\n'.join(nav_buttons)
    
    # HTML模板（保持不变）
    html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智能汽车销售问题分析 - 完整报告</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css">
    <style>
        /* 全局幻灯片容器样式 */
        .presentation-container {{
            position: relative;
            width: 100%;
            height: 720px;
            overflow: hidden;
        }}
        
        /* 幻灯片切换按钮 */
        .slide-navigation {{
            position: fixed;
            bottom: 20px;
            left: 0;
            right: 0;
            display: flex;
            justify-content: center;
            gap: 10px;
            z-index: 100;
        }}
        
        .nav-button {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            border: 2px solid #333;
            background: transparent;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .nav-button.active {{
            background: #333;
        }}
        
        /* 幻灯片切换基础样式 */
        .slide {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0;
            transition: opacity 0.5s ease;
        }}
        
        .slide.active {{
            opacity: 1;
            z-index: 10;
        }}
    </style>
</head>
<body>
    <div class="presentation-container">
        {''.join(slide_contents)}
    </div>
    
    <!-- 导航按钮 -->
    <div class="slide-navigation">
        {nav_html}
    </div>

    <script>
        // 幻灯片切换功能
        const slides = document.querySelectorAll('.slide');
        const navButtons = document.querySelectorAll('.nav-button');
        let currentSlide = 0;
        
        function showSlide(index) {{
            // 隐藏所有幻灯片
            slides.forEach(slide => slide.classList.remove('active'));
            // 移除所有按钮的活跃状态
            navButtons.forEach(btn => btn.classList.remove('active'));
            
            // 显示指定幻灯片
            slides[index].classList.add('active');
            // 激活对应按钮
            navButtons[index].classList.add('active');
            
            currentSlide = index;
        }}
        
        // 为每个导航按钮添加点击事件
        navButtons.forEach((button, index) => {{
            button.addEventListener('click', () => {{
                showSlide(index);
            }});
        }});
        
        // 支持键盘左右箭头切换
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowRight') {{
                // 下一张
                const nextSlide = (currentSlide + 1) % slides.length;
                showSlide(nextSlide);
            }} else if (e.key === 'ArrowLeft') {{
                // 上一张
                const prevSlide = (currentSlide - 1 + slides.length) % slides.length;
                showSlide(prevSlide);
            }}
        }});

        // 初始化显示第一张幻灯片
        showSlide(0);
    </script>
</body>
</html>'''
    
    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"已成功生成 {output_file}，包含 {len(slide_files)} 个幻灯片")

if __name__ == "__main__":
    # 幻灯片文件列表，按顺序排列
    # 动态获取当前目录下所有 slide*.html 文件，并按数字顺序排序
    slide_files = sorted(
        [f for f in os.listdir('.') if f.startswith('slide') and f.endswith('.html')],
        key=lambda x: int(''.join(filter(str.isdigit, x)) or 0)
    )
    
    # 检查文件是否存在
    for file in slide_files:
        if not os.path.exists(file):
            print(f"错误：文件 {file} 不存在")
            exit(1)
    
    # 生成index.html
    generate_index_html(slide_files)
    