import os
import requests
from bs4 import BeautifulSoup
import re
import tkinter as tk
from tkinter import filedialog
import urllib.parse
from urllib.parse import urljoin
import random

# 请将完整的User-Agent列表填充到下面
USER_AGENT_LIST = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60",
    "Opera/8.0 (Windows NT 5.1; U; en)",
    "Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10",
    "Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11",
    "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.50",
    "Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0",
    " Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv,2.0.1) Gecko/20100101 Firefox/4.0.1",
    "Mozilla/5.0 (Windows NT 6.1; rv,2.0.1) Gecko/20100101 Firefox/4.0.1"
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:97.0) Gecko/20100101 Firefox/97.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 15_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-A515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.101 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; ONEPLUS A6013) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.101 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60",
    "Opera/8.0 (Windows NT 5.1; U; en)"
]

# 验证URL函数，强制要求URL包含 http:// 或 https://
def is_valid_url(url):
    regex = re.compile(
        r'^https?://'  # 强制匹配 http:// 或 https://
        r'(\w+\.)*'    # 匹配域名
        r'(\w+)'       # 匹配顶级域
        r'(\/[^\s]*)?$',  # 匹配可选的路径
        re.IGNORECASE
    )
    return re.match(regex, url) is not None

# 获取小说信息函数
def get_novel_info(novel_directory_url):
    try:
        headers = {'User-Agent': random.choice(USER_AGENT_LIST)}
        response = requests.get(novel_directory_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        chapter_selector = 'div.chapter-item a.chapter-item-title'
        chapters = soup.select(chapter_selector)
        chapter_urls = [urljoin(novel_directory_url, a['href']) for a in chapters if 'href' in a.attrs]
        chapter_names = [a.get_text(strip=True) for a in chapters]
        return chapter_urls, chapter_names
    except requests.RequestException as e:
        print(f"无法获取小说信息: {e}")
        return [], []

# 下载单个章节函数
def download_single_chapter(chapter_url, chapter_name, file):
    try:
        headers = {'User-Agent': random.choice(USER_AGENT_LIST)}
        response = requests.get(chapter_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.find('div', id='content')
        if content:
            text = content.get_text(strip=True)
            file.write(f"{chapter_name}\n{text}\n")
        else:
            print(f"章节内容未找到: {chapter_url}")
    except requests.RequestException as e:
        print(f"下载章节出错: {e}")

# 下载章节函数
def download_chapters(novel_directory_url, chapter_urls, chapter_names, output_dir, mode):
    total_chapters = len(chapter_urls)
    downloaded_chapters = 0

    def update_progress():
        nonlocal downloaded_chapters
        downloaded_chapters += 1
        progress = (downloaded_chapters / total_chapters) * 100
        print(f"下载进度: {progress:.2f}% ({downloaded_chapters}/{total_chapters})", end="\r")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if mode == 'complete':
        novel_filename = os.path.join(output_dir, "novel.txt")
        with open(novel_filename, 'w', encoding='utf-8') as file:
            for chapter_url, chapter_name in zip(chapter_urls, chapter_names):
                full_url = urllib.parse.urljoin(novel_directory_url, chapter_url)
                download_single_chapter(full_url, chapter_name, file)

    elif mode == 'separate':
        for chapter_url, chapter_name in zip(chapter_urls, chapter_names):
            full_url = urllib.parse.urljoin(novel_directory_url, chapter_url)
            chapter_filename = os.path.join(output_dir, f"{chapter_name}.txt")
            with open(chapter_filename, 'w', encoding='utf-8') as file:
                download_single_chapter(full_url, chapter_name, file)

    print(f"\n所有章节已成功下载到 {output_dir}。")

# 用户选择保存位置
def get_save_directory():
    root = tk.Tk()
    root.withdraw()  # 不显示根窗口
    return filedialog.askdirectory(title="选择保存目录")

# Debug模式函数


# 主函数
def main():
    while True:
        print("请选择以下操作：")
        print("1. 进入正常模式 - 下载整本小说到一个文件")
        print("2. 进入分章保存模式 - 每个章节保存为单独的文件")
        print("3. 退出程序")
        user_input = input("请输入您的选择（1~3）:（默认“1”）").strip()

        # 默认选择为1
        if user_input == '':
            user_input = '1'

        # 确保输入是数字，并且转换为整数
        if user_input.isdigit():
            user_input = int(user_input)
        else:
            print("输入错误，请输入1到3之间的数字。")
            continue

        # 确保输入在允许的范围内
        if user_input < 1 or user_input > 3:
            print("无效的输入，请输入1到3之间的数字。")
            continue

        # 获取小说目录网址链接
        novel_directory_url = input("请输入小说目录网址链接（包含http://或https://）: ")
        # 验证URL
        while not is_valid_url(novel_directory_url):
            print("无效的网址链接，请重新输入。")
            novel_directory_url = input("请输入小说目录网址链接（包含http://或https://）: ")

        # 获取章节信息
        chapter_urls, chapter_names = get_novel_info(novel_directory_url)
        if not chapter_urls or not chapter_names:
            print("无法获取小说章节信息，请检查网址是否正确。")
            continue

        # 打印章节信息并等待用户确认
        print("\n以下是解析后的小说章节：")
        for i, (url, name) in enumerate(zip(chapter_urls, chapter_names), start=1):
            print(f"{i}. {name}")

        input("\n按下Enter键继续下载...")

        # 用户选择保存目录
        output_dir = get_save_directory()
        if not output_dir:
            print("保存目录选择已取消，退出程序。")
            break

        # 根据用户选择的模式下载章节
        if user_input == 1:
            download_chapters(novel_directory_url, chapter_urls, chapter_names, output_dir, 'complete')
        elif user_input == 2:
            download_chapters(novel_directory_url, chapter_urls, chapter_names, output_dir, 'separate')

        print("下载完成。")

if __name__ == "__main__":
    main()