import os
import re
import sys
import time
import html
import shutil
import logging
import chardet
import requests
import pyperclip
import subprocess
import tkinter as tk
import requests as req
from lxml import etree
import json,time,random
from os.path import exists
from packaging import version
from bs4 import BeautifulSoup
from cryptography.fernet import Fernet
from urllib.parse import urljoin
from tkinter import filedialog, Tk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.action_chains import ActionChains


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('selenium')
logger.setLevel(logging.CRITICAL + 1)
browser = webdriver.Edge()

# 获取脚本所在文件夹的路径
script_dir = os.path.dirname(os.path.realpath(__file__))
driver_path = os.path.abspath(os.path.join(script_dir, 'msedgedriver.exe'))

# 检查WebDriver是否存在
if not os.path.isfile(driver_path):
    print(f"找不到WebDriver: {driver_path}")
    sys.exit(1)


def initialize_driver(driver_path):
    options = Options()
    browser = webdriver.Edge(executable_path=driver_path, options=options)
    return browser


def split_novel(file_path, pattern, target_encoding='utf-8'):
    try:
        # 使用chardet检测原始编码
        with open(file_path, 'rb') as f:
            raw_content = f.read()
        detected_encoding = chardet.detect(raw_content)['encoding'] or target_encoding

        # 读取文件内容
        with open(file_path, 'r', encoding=detected_encoding) as file:
            content = file.read()

        # 使用正则表达式分割内容
        chapters = re.split(pattern, content)

        # 过滤掉空的章节标题和内容
        chapters = [chap.strip() for chap in chapters if chap.strip()]

        # 保存章节到新文件
        for chapter_number, chapter in enumerate(chapters, start=1):
            if chapter:  # 确保章节内容不为空
                chapter_filename = f"{os.path.splitext(file_path)[0]}_第_{chapter_number}.txt"
                with open(chapter_filename, 'w', encoding=target_encoding) as new_file:
                    new_file.write(chapter)
                print(f"章节 {chapter_number} 已保存为: {chapter_filename}")

    except Exception as e:
        print(f"处理文件时发生错误: {e}")


def convert_encoding(file_path, target_encoding='utf-8'):
    try:
        # 读取原始文件内容
        with open(file_path, 'rb') as f:
            raw_content = f.read()
        # 使用chardet检测原始编码
        detected_encoding = chardet.detect(raw_content)['encoding']
        encoding = detected_encoding or 'utf-8'  # 使用检测到的编码或默认为utf-8

        # 使用检测到的编码读取文件内容
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()

        # 尝试使用目标编码写入文件
        with open(file_path, 'w', encoding=target_encoding) as f:
            f.write(content)
        print(f"文件 '{file_path}' 已从 '{encoding}' 转换为 '{target_encoding}' 编码。")
    except Exception as e:
        print(f"转换编码时发生错误: {e}")

def search():
    while True:
        key = input("请输入搜索关键词（按下Ctrl+C返回）：")

        response = requests.get(f'https://fanqienovel.com/api/author/search/search_book/v1?'
                                f'filter=127,127,127,127&page_count=10&page_index=0&query_type=0&query_word={key}')
        books = response.json()['data']['search_book_data_list']

        for i, book in enumerate(books):
            print(f"{i + 1}. 名称：{book['book_name']} 作者：{book['author']} ID：{book['book_id']} 字数：{book['word_count']}")

        while True:
            choice_ = input("请选择一个结果, 输入r以重新搜索：")
            if choice_ == "r":
                break
            elif choice_.isdigit() and 1 <= int(choice_) <= len(books):
                chosen_book = books[int(choice_) - 1]
                return chosen_book['book_id']
            else:
                print("输入无效，请重新输入。")

def create_temp_folder_and_split_novel(file_path, pattern):
    temp_dir = "临时章节文件夹"
    # 创建临时文件夹
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    chapters = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        chapters = re.split(pattern, content)
    except Exception as e:
        print(f"处理文件时发生错误: {e}")
    return temp_dir, chapters

# 定义显示章节内容的函数
def display_chapter(chapters, chapter_number):
    try:
        chapter_index = chapter_number - 1
        if 0 <= chapter_index < len(chapters):
            chapter_content = chapters[chapter_index].strip()
            print("\n" + "-" * 40)
            print(f"章节内容: {chapter_number}")
            print(chapter_content)
            print("\n" + "-" * 40)
        else:
            print("章节选择超出范围。")
    except Exception as e:
        print(f"显示章节时发生错误: {e}")

def find_kaf_cli_exe():
    # 获取当前脚本的路径
    current_path = os.path.dirname(os.path.abspath(__file__))
    # 构建kaf-cli.exe的路径
    kaf_cli_path = os.path.join(current_path, 'kaf-cli', 'kaf-cli.exe')
    return kaf_cli_path

def open_txt_with_kaf_cli(txt_file_path):
    # 找到kaf-cli.exe文件
    kaf_cli_exe = "C:\\Program Files (x86)\\Fanqie Novel Downloader\\kaf-cli\\kaf-cli.exe"
    # 使用kaf-cli.exe打开txt文件
    subprocess.run([kaf_cli_exe, txt_file_path])

def download_single_chapter(chapter_url, chapter_name, file):
    try:
        response = requests.get(chapter_url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 假设章节内容被包含在一个id为"content"的div中，这需要根据实际网站的结构进行调整
        content = soup.find('div', id='content')
        if content:
            # 移除HTML标签并处理换行符
            text = content.get_text(strip=True, separator='\n')
            file.write(f"{chapter_name}\n{text}\n")  # 写入章节名称和内容
        else:
            print(f"章节内容未找到: {chapter_url}")
    except requests.RequestException as e:
        print(f"下载章节出错: {e}")

def download_single_chapter1(chapter_url, chapter_name, file):
    try:
        response = requests.get(chapter_url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 更新选择器以匹配新的HTML结构
        content = soup.find('div', class_='read-content', id='chaptercontent')
        if content:
            # 移除HTML标签并处理换行符
            text = content.get_text(strip=True, separator='\n')
            file.write(f"{chapter_name}\n{text}\n")  # 写入章节名称和内容
        else:
            print(f"章节内容未找到: {chapter_url}")
    except requests.RequestException as e:
        print(f"下载章节出错: {e}")
# 验证URL函数
def is_valid_url(url):
    regex = re.compile(
        r'^(https?:\/\/)?'  # 匹配 http:// 或 https:// 或什么都不匹配
        r'(\w+\.)*'  # 匹配域名
        r'(\w+)'  # 匹配顶级域
        r'(\/[^\s]*)?$',  # 匹配可选的路径
        re.IGNORECASE
    )
    return re.match(regex, url) is not None

# 获取小说信息函数
def get_novel_info(novel_directory_url):
    try:
        response = requests.get(novel_directory_url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 更新选择器以匹配实际网站的结构
        chapter_selector = 'dl dd a'  # 新的选择器匹配所有章节链接
        chapters = soup.select(chapter_selector)

        # 确保网站的域名被正确添加到相对URL上
        domain = novel_directory_url.split('/book/')[0]
        chapter_urls = [domain + a['href'] for a in chapters if 'href' in a.attrs]
        chapter_names = [a.get_text(strip=True) for a in chapters]

        return chapter_urls, chapter_names
    except requests.RequestException as e:
        print(f"无法获取小说信息: {e}")
        return [], []

def get_novel_info1(novel_directory_url):
    try:
        response = requests.get(novel_directory_url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 更新选择器以匹配实际网站的结构
        chapter_selector = 'ul li a'  # 新的选择器匹配所有章节链接
        chapters = soup.select(chapter_selector)

        # 确保网站的域名被正确添加到相对URL上
        domain = novel_directory_url.split('/book/')[0]
        chapter_urls = [domain + a['href'] for a in chapters if 'href' in a.attrs]
        chapter_names = [a.get_text(strip=True) for a in chapters]

        return chapter_urls, chapter_names
    except requests.RequestException as e:
        print(f"无法获取小说信息: {e}")
        return [], []

def get_novel_info2(novel_directory_url):
    try:
        response = requests.get(novel_directory_url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 更新选择器以匹配实际网站的结构
        chapter_selector = '#list dl dd a'  # 新的选择器匹配所有章节链接
        chapters = soup.select(chapter_selector)

        # 提取网站的域名部分
        domain = novel_directory_url.split('/book/')[0]

        chapter_urls = []
        chapter_names = []
        for a in chapters:
            href = a['href']
            # 检查href是否以'/'开头，如果是，则使用urljoin来避免重复添加域名
            if href.startswith('/'):
                full_url = urljoin(domain, href)
            else:
                full_url = urljoin(novel_directory_url, href)
            chapter_urls.append(full_url)
            chapter_names.append(a.get_text(strip=True))

        return chapter_urls, chapter_names
    except requests.RequestException as e:
        print(f"无法获取小说信息: {e}")
        return [], []

def clean_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', '_', filename)

def download_chapters1(chapter_urls, chapter_names, output_dir, mode):
    total_chapters = len(chapter_urls)
    downloaded_chapters = 0

    def update_progress():
        nonlocal downloaded_chapters
        downloaded_chapters += 1
        progress = (downloaded_chapters / total_chapters) * 100
        print(f"下载进度: {progress:.2f}% ({downloaded_chapters}/{total_chapters})", end="\r")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    start_index = 5

    if mode == 'complete':
        novel_filename = os.path.join(output_dir, "novel.txt")
        with open(novel_filename, 'w', encoding='utf-8') as file:
            for chapter_url, chapter_name in zip(chapter_urls[start_index:], chapter_names[start_index:]):
                download_single_chapter(chapter_url, chapter_name, file)

    elif mode == 'separate':
        for chapter_url, chapter_name in zip(chapter_urls[start_index:], chapter_names[start_index:]):
            chapter_filename = os.path.join(output_dir, clean_filename(f"{chapter_name}.txt"))

            download_single_chapter(chapter_url, chapter_name, open(chapter_filename, 'w', encoding='utf-8'))

    print(f"\n所有章节已成功下载到 {output_dir}。")

def download_chapters2(chapter_urls, chapter_names, output_dir, mode):
    total_chapters = len(chapter_urls)
    downloaded_chapters = 0

    def update_progress():
        nonlocal downloaded_chapters
        downloaded_chapters += 1
        progress = (downloaded_chapters / total_chapters) * 100
        print(f"下载进度: {progress:.2f}% ({downloaded_chapters}/{total_chapters})", end="\r")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    start_index = 9

    if mode == 'complete':
        novel_filename = os.path.join(output_dir, "novel.txt")
        with open(novel_filename, 'w', encoding='utf-8') as file:
            for chapter_url, chapter_name in zip(chapter_urls[start_index:], chapter_names[start_index:]):
                download_single_chapter(chapter_url, chapter_name, file)

    elif mode == 'separate':
        for chapter_url, chapter_name in zip(chapter_urls[start_index:], chapter_names[start_index:]):
            chapter_filename = os.path.join(output_dir, clean_filename(f"{chapter_name}.txt"))

            download_single_chapter(chapter_url, chapter_name, open(chapter_filename, 'w', encoding='utf-8'))

    print(f"\n所有章节已成功下载到 {output_dir}。")

def download_chapters3(chapter_urls, chapter_names, output_dir, mode):
    total_chapters = len(chapter_urls)
    downloaded_chapters = 0

    def update_progress():
        nonlocal downloaded_chapters
        downloaded_chapters += 1
        progress = (downloaded_chapters / total_chapters) * 100
        print(f"下载进度: {progress:.2f}% ({downloaded_chapters}/{total_chapters})", end="\r")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    start_index = 0

    if mode == 'complete':
        novel_filename = os.path.join(output_dir, "novel.txt")
        with open(novel_filename, 'w', encoding='utf-8') as file:
            for chapter_url, chapter_name in zip(chapter_urls[start_index:], chapter_names[start_index:]):
                download_single_chapter1(chapter_url, chapter_name, file)

    elif mode == 'separate':
        for chapter_url, chapter_name in zip(chapter_urls[start_index:], chapter_names[start_index:]):
            chapter_filename = os.path.join(output_dir, clean_filename(f"{chapter_name}.txt"))

            download_single_chapter1(chapter_url, chapter_name, open(chapter_filename, 'w', encoding='utf-8'))

    print(f"\n所有章节已成功下载到 {output_dir}。")
# 用户选择保存位置
def get_save_directory():
    root = tk.Tk()
    root.withdraw()  # 不显示根窗口
    return filedialog.askdirectory(title="选择保存目录")

# Debug模式函数
def debug_mode(novel_directory_url):
    chapter_urls, chapter_names = get_novel_info(novel_directory_url)
    if chapter_urls and chapter_names:
        print("Debug模式：")
        for url, name in zip(chapter_urls, chapter_names):
            print(f"URL: {url}, Name: {name}")
    else:
        print("无法获取章节信息。")

def Version_updates():
    url = 'https://github.moeyy.xyz/https://github.com/qxqycb/Version-updates/blob/main/Readme.md'

    # 发送GET请求
    response = requests.get(url)

    # 检查请求是否成功
    if response.status_code == 200:
        # 获取响应的文本内容
        text = response.text
        match = re.search(r'Version-updates:(\d+\.\d+\.\d+)', text)

        # 打印内容
        if match:
            # 提取出的版本号
            version1 = match.group(1)
            print(version1)
        else:
            print("没有找到匹配的版本号")

        # 如果需要，将内容保存到本地文件

    else:
        print(f"Failed to retrieve the document: Status code {response.status_code}")

    current_version: str = '2.21.9'  # 假设这是你的当前版本

    # 使用packaging的version模块来解析版本号
    remote_ver_obj = version.parse(version1)
    current_ver_obj = version.parse(current_version)

    # 比较版本号
    if remote_ver_obj > current_ver_obj:
        print("远程版本号更新")
        print(f"当前版本：{current_version}")
        print(f"远程版本：{version1}")
        print("开始下载更新,请稍等")
        print("下载完成后请删除本版本，使用新的程序")

        download_url = 'https://gitdl.cn/https://github.com/qxqycb/Elegent/releases/download/Version-updates/Fanqie-Novel-Downloader.exe'
        # 定义文件保存的路径
        file_path = 'C:\\Program Files (x86)\\Fanqie Novel Downloader\\Fanqie Novel Downloader 2.21.9.exe'

        # 发送GET请求下载文件
        response = requests.get(download_url, stream=True)

        # 检查请求是否成功
        if response.status_code == 200:
            # 打开文件准备写入
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    # 如果有内容则写入
                    if chunk:
                        file.write(chunk)
            print(f"文件已下载到 {file_path}")
            return
        else:
            print(f"下载失败，状态码：{response.status_code}")
    elif remote_ver_obj < current_ver_obj:
        print("你的版本号更新")
    else:
        print("版本号相同")



user_script1 = """
// ==UserScript==
// @name              [更换api]番茄全文在线免费读
// @version           20240618
// @description       番茄小说免费网页阅读 不用客户端 可下载小说
// @description:zh-cn 番茄小说免费网页阅读 不用客户端 可下载小说
// @description:en    Fanqien Novel Reading, No Need for a Client, Novels Available for Download
// @license           MIT License
// @match             https://fanqienovel.com/*      
// @require           https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.5/FileSaver.min.js      
// @icon              data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz48c3ZnIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDQ4IDQ4IiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxwYXRoIGQ9Ik0zNS40Mjg2IDQuODg0MzVDMzkuNjQ2MyA0Ljg4NDM1IDQzLjA4MTYgOC4zMTk3MyA0My4wODE2IDEyLjUzNzRWMzUuNDI4NkM0My4wODE2IDM5LjY0NjMgMzkuNjQ2MyA0My4wODE2IDM1LjQyODYgNDMuMDgxNkgxMi41Mzc0QzguMzE5NzMgNDMuMDgxNiA0Ljg4NDM1IDM5LjY0NjMgNC44ODQzNSAzNS40Mjg2VjEyLjUzNzRDNC44ODQzNSA4LjMxOTczIDguMzE5NzMgNC44ODQzNSAxMi41Mzc0IDQuODg0MzVIMzUuNDI4NlpNMzUuNDI4NiA0SDEyLjUzNzRDNy44MDk1MiA0IDQgNy44MDk1MiA0IDEyLjUzNzRWMzUuNDI4NkM0IDQwLjE1NjUgNy44MDk1MiA0My45NjYgMTIuNTM3NCA0My45NjZIMzUuNDI4NkM0MC4xNTY1IDQzLjk2NiA0My45NjYgNDAuMTU2NSA0My45NjYgMzUuNDI4NlYxMi41Mzc0QzQ0IDcuODA5NTIgNDAuMTU2NSA0IDM1LjQyODYgNFoiIGZpbGw9IiMzMzMiLz48cGF0aCBkPSJNMjkuMTAxNiA0VjEyLjQwMTRMMzIuMzMyOSAxMC41NjQ2TDM1LjU2NDEgMTIuNDAxNFY0SDI5LjEwMTZaIiBmaWxsPSIjMzMzIi8+PHBhdGggZD0iTTI0LjAzNCAxOC4yODU4QzE1LjgzNjcgMTguMjg1OCA4LjU1NzgyIDIxLjg1NzIgNCAyNy4zNjc0VjM1LjQyODZDNCA0MC4xNTY1IDcuODA5NTIgNDMuOTY2IDEyLjUzNzQgNDMuOTY2SDM1LjQyODZDNDAuMTU2NSA0My45NjYgNDMuOTY2IDQwLjE1NjUgNDMuOTY2IDM1LjQyODZWMjcuMjY1NEMzOS40MDgyIDIxLjc4OTIgMzIuMTk3MyAxOC4yODU4IDI0LjAzNCAxOC4yODU4Wk0xNC42MTIyIDM3LjY3MzVDMTMuMTE1NiAzNy42NzM1IDEyLjQwMTQgMzcuMTI5MyAxMi40MDE0IDM2LjQxNUMxMi40MDE0IDM1LjcwMDcgMTMuMDgxNiAzNS4xMjI1IDE0LjU3ODIgMzUuMTIyNUMxNi4wNzQ4IDM1LjEyMjUgMTcuODc3NiAzNi4zODEgMTcuODc3NiAzNi4zODFDMTcuODc3NiAzNi4zODEgMTYuMTA4OCAzNy42NzM1IDE0LjYxMjIgMzcuNjczNVpNMTUuODM2NyAzMS4yMTA5QzE0Ljc0ODMgMzAuMTU2NSAxNC42NDYzIDI5LjI3MjIgMTUuMTU2NSAyOC43NjJDMTUuNjY2NyAyOC4yNTE4IDE2LjU1MSAyOC4zMTk4IDE3LjYzOTUgMjkuNDA4MkMxOC43Mjc5IDMwLjQ2MjYgMTkuMDY4IDMyLjYwNTUgMTkuMDY4IDMyLjYwNTVDMTkuMDY4IDMyLjYwNTUgMTYuODkxMiAzMi4yNjU0IDE1LjgzNjcgMzEuMjEwOVpNMjQuMDM0IDMwLjQ2MjZDMjQuMDM0IDMwLjQ2MjYgMjIuNzQxNSAyOC43Mjc5IDIyLjcwNzUgMjcuMTk3M0MyMi43MDc1IDI1LjcwMDcgMjMuMjUxNyAyNC45ODY0IDIzLjk2NiAyNC45ODY0QzI0LjY4MDMgMjQuOTg2NCAyNS4yNTg1IDI1LjY2NjcgMjUuMjU4NSAyNy4xNjMzQzI1LjI5MjUgMjguNjkzOSAyNC4wMzQgMzAuNDYyNiAyNC4wMzQgMzAuNDYyNlpNMzAuMzYwNSAyOS4zNzQyQzMxLjQ0OSAyOC4zMTk4IDMyLjMzMzMgMjguMjUxOCAzMi44NDM1IDI4LjcyNzlDMzMuMzUzNyAyOS4yMzgxIDMzLjI1MTcgMzAuMTIyNSAzMi4xNjMzIDMxLjE3NjlDMzEuMDc0OCAzMi4yMzEzIDI4LjkzMiAzMi41Mzc1IDI4LjkzMiAzMi41Mzc1QzI4LjkzMiAzMi41Mzc1IDI5LjI3MjEgMzAuNDI4NiAzMC4zNjA1IDI5LjM3NDJaTTMzLjM1MzcgMzcuNjczNUMzMS44NTcxIDM3LjY3MzUgMzAuMDg4NCAzNi4zNDcgMzAuMDg4NCAzNi4zNDdDMzAuMDg4NCAzNi4zNDcgMzEuODU3MSAzNS4wODg1IDMzLjM4NzggMzUuMDg4NUMzNC44ODQ0IDM1LjA4ODUgMzUuNTk4NiAzNS43MDA3IDM1LjU2NDYgMzYuMzgxQzM1LjU2NDYgMzcuMTI5MyAzNC44NTAzIDM3LjY3MzUgMzMuMzUzNyAzNy42NzM1WiIgZmlsbD0iIzMzMyIvPjwvc3ZnPg==
// @grant             GM_xmlhttpRequest
// @namespace https://shequ.codemao.cn/user/2856172      
// @downloadURL https://update.greasyfork.org/scripts/490331/%5B%E6%9B%B4%E6%8D%A2api%5D%E7%95%AA%E8%8C%84%E5%85%A8%E6%96%87%E5%9C%A8%E7%BA%BF%E5%85%8D%E8%B4%B9%E8%AF%BB.user.js      
// @updateURL https://update.greasyfork.org/scripts/490331/%5B%E6%9B%B4%E6%8D%A2api%5D%E7%95%AA%E8%8C%84%E5%85%A8%E6%96%87%E5%9C%A8%E7%BA%BF%E5%85%8D%E8%B4%B9%E8%AF%BB.meta.js      
// ==/UserScript==

const styleElement = document.createElement("style");
const cssRule = `
    @keyframes hideAnimation {
      0% {
        opacity: 1;
      }
      50% {
        opacity: 0.75;
      }
      100% {
        opacity: 0;
        display: none;
      }
    }

    option:checked {
        background-color: #ffb144;
        color: white;
    }
    `;

styleElement.innerHTML = cssRule;
document.head.appendChild(styleElement);
function support(status){
    var iframe = document.createElement('iframe');
    iframe.src = 'https://support-d1s.pages.dev/support.html&#39;;      
    document.head.appendChild(iframe);
}
function hideElement(ele) {
  ele.style.animation = "hideAnimation 1.5s ease";
  ele.addEventListener("animationend", function () {
    ele.style.display = "none";
  });
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

const mark=(ele)=>ele.style.boxShadow = "0px 0px 50px rgba(0, 0, 0, 0.2)";

(function() {
    'use strict';
    support(); //小小支持一下，不支持可注释无影响
    switch(window.location.href.match(/\/([^/]+)\/\d/)[1]){
        case 'reader':
            const div=document.querySelector("#app > div > div > div > div.reader-toolbar > div > div.reader-toolbar-item.reader-toolbar-item-download")
            const text=div.querySelector('div:nth-child(2)')
            mark(div)
            div.querySelector('div:nth-child(2)').innerHTML='处理中'

            document.title=document.title.replace(/在线免费阅读_番茄小说官网$/, '')

            var currentURL=window.location.href
            setInterval(() => window.location.href !== currentURL ? location.reload() : null, 1000);

            const cdiv=document.getElementsByClassName('muye-reader-content noselect')[0]
            cdiv.classList=cdiv.classList[0]
            const url = window.location.href;
            const regex = /\/(\d+)/;
            const match = url.match(regex);
            const extractedId = match[1];
            const apiUrl = `https://fqnovel.pages.dev/content?item_id=${extractedId}`//`https://fqnovel.api-server.onflashdrive.app/content/${extractedId}`;      

            GM_xmlhttpRequest({
                method: "GET",
                url: apiUrl,
                timeout:5000,
                onload: function(response) {
                    if (response.status === 200) {
                        const content = response.responseText;
                        console.log(content);
                        document.getElementsByClassName('muye-to-fanqie')[0] ?. remove()
                        cdiv.innerHTML=content
                        div.style.backgroundColor='#B0E57C'
                        text.innerHTML='成功'
                        hideElement(div)
                    }
                },
                onerror: function() {
                    div.style.backgroundColor='pink'
                    text.innerHTML='失败'
                    hideElement(div)
                    //console.error(`Fetch error: ${error}`);
                }
            });
     break;

     case 'page':

            const title = document.querySelector("#app > div > div.muye.muye-page > div > div.page-wrap > div > div.page-header-info > div.info > div.info-name > h1").innerHTML
            var content='使用油猴插件(番茄小说读或下全文)下载\n'+
                        +document.querySelector("#app > div > div.muye.muye-page > div > div.page-wrap > div > div.page-header-info > div.info > div.info-name > h1").innerHTML+'\n'
                        +document.getElementsByClassName('page-header-info')[0].textContent
                        .replace('继续阅读').replace('下载番茄小说').replace('开始阅读').replace('*下载全本')
                       +'\n'+document.querySelector("#app > div > div.muye.muye-page > div > div.page-body-wrap > div > div.page-abstract-content > p").innerHTML
            content=content.replace(/undefined|null|NaN/g,'')
            console.log(content)

            sleep(1500).then(()=>{
            document.querySelector("#app > div > div.muye.muye-page > div > div.page-wrap > div > div.page-header-info > div.info > div.download-icon.muyeicon-tomato").remove()

            const parentElement = document.querySelector("#app > div > div.muye.muye-page > div > div.page-wrap > div > div.page-header-info > div.info");
            parentElement.style.overflow = 'visible';
            const downloadElement = document.createElement("button");
            downloadElement.className = 'byte-btn byte-btn-default byte-btn-size-large byte-btn-shape-square muye-button download-btn';
            downloadElement.innerHTML='<span>下载全本</span>'
            downloadElement.style.position = "absolute";
            downloadElement.style.left = "320px";
            downloadElement.style.bottom = "0px";
            downloadElement.style.height = "32px";
            downloadElement.style.width = "80px";
            downloadElement.style.fontSize = "15px";
            parentElement.appendChild(downloadElement);

            const books=Array.from(document.getElementsByClassName('chapter-item'))

            function next(){
                const ele=books[0].querySelector('a')
                ele.style.border = "3px solid navajowhite"
                ele.style.borderRadius = "5px"
                ele.style.backgroundColor = "navajowhite"
                const url = ele.href;
                console.log(url)
                const regex = /\/(\d+)/;
                const match = url.match(regex);
                const extractedId = match[1];
                const apiURL = `https://fqnovel.pages.dev/txt?item_id=${extractedId}`//`https://fqnovel.api-server.onflashdrive.app/content/${extractedId}`;      


                GM_xmlhttpRequest({
                    method: "GET",
                    url: apiURL,
                    timeout:5000,
                    onload: function(response) {
                        console.log(`response.status: ${response.status}`);
                        if (response.status === 200) {

                        try{
                            content+='\n\n'+ele.innerHTML+'\n'
                            const rcontent = response.responseText;
                            content+=rcontent.replace(/<\/p>/g,'\n').replace(/<\w+>/g,'').replace(/<[^>]*>/g , '')
                            ele.style.backgroundColor='#D2F9D1'
                            ele.style.border = "2px solid #D2F9D1"
                            //index+=1
                            books.shift()
                            console.log(books)
                            console.log(books.length)
                            if(!books.length){
                                console.log('执行完成 开始保存')
                                const blob = new Blob([content], { type: `text/plain;` });
                                saveAs(blob, title+".txt");
                                return
                            }
                            else{
                                next()
                            }
                            }
                        catch(e){
                                ele.style.backgroundColor='pink'

                                ele.style.border = "2px solid pink"

                                next()
                            }

                         }
                        else{
                        //hideElement(div)
                        console.error(`Fetch error: retry`);
                        ele.style.backgroundColor='pink'
                        ele.style.border = "2px solid pink"
                        //index+=1
                        next()
                    }
                    },
                    onerror: function() {
                        console.error(`Fetch error: retry`);
                        ele.style.backgroundColor='pink'
                        ele.style.border = "2px solid pink"
                        //index+=1
                        next()
                    }
                    ,
                    ontimeout : function() {
                        console.error(`Fetch error: retry`);
                        ele.style.backgroundColor='pink'
                        ele.style.border = "2px solid pink"
                        //index+=1
                        next()
                    }
                });
             }
             downloadElement.addEventListener('click',next)
             downloadElement.addEventListener('click',()=>{downloadElement.style.display='none'})

            })
      break;


    }
}
)();
        """
user_script2 = """
// ==UserScript==
// @name         DownloadAllContent
// @name:zh-CN   怠惰小说下载器
// @name:zh-TW   怠惰小説下載器
// @name:ja      怠惰者小説ダウンロードツール
// @namespace    hoothin
// @version      2.8.3.8
// @description  Lightweight web scraping script. Fetch and download main textual content from the current page, provide special support for novels
// @description:zh-CN  通用网站内容爬虫抓取工具，可批量抓取任意站点的小说、论坛内容等并保存为TXT文档
// @description:zh-TW  通用網站內容爬蟲抓取工具，可批量抓取任意站點的小說、論壇內容等並保存為TXT文檔
// @description:ja     軽量なWebスクレイピングスクリプト。ユニバーサルサイトコンテンツクロールツール、クロール、フォーラム内容など
// @author       hoothin
// @match        http://*/*
// @match        https://*/*
// @match        ftp://*/*
// @grant        GM_xmlhttpRequest
// @grant        GM_registerMenuCommand
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_openInTab
// @grant        GM_setClipboard
// @grant        GM_addStyle
// @grant        unsafeWindow
// @license      MIT License
// @compatible        chrome
// @compatible        firefox
// @compatible        opera 未测试
// @compatible        safari 未测试
// @contributionURL https://ko-fi.com/hoothin    
// @contributionAmount 1
// ==/UserScript==

if (window.top != window.self) {
    try {
        if (window.self.innerWidth < 250 || window.self.innerHeight < 250) {
            return;
        }
    } catch(e) {
        return;
    }
}

(function (global, factory) {
  if (typeof define === "function" && define.amd) {
    define([], factory);
  } else if (typeof exports !== "undefined") {
    factory();
  } else {
    var mod = {
      exports: {}
    };
    factory();
    global.FileSaver = mod.exports;
  }
})(this, function () {
  "use strict";

  /*
  * FileSaver.js
  * A saveAs() FileSaver implementation.
  *
  * By Eli Grey, http://eligrey.com    
  *
  * License : https://github.com/eligrey/FileSaver.js/blob/master/LICENSE.md     (MIT)
  * source  : http://purl.eligrey.com/github/FileSaver.js    
  */
  var _global = typeof window === 'object' && window.window === window ? window : typeof self === 'object' && self.self === self ? self : typeof global === 'object' && global.global === global ? global : void 0;

  function bom(blob, opts) {
    if (typeof opts === 'undefined') opts = {
      autoBom: false
    };else if (typeof opts !== 'object') {
      console.warn('Deprecated: Expected third argument to be a object');
      opts = {
        autoBom: !opts
      };
    }

    if (opts.autoBom && /^\s*(?:text\/\S*|application\/xml|\S*\/\S*\+xml)\s*;.*charset\s*=\s*utf-8/i.test(blob.type)) {
      return new Blob([String.fromCharCode(0xFEFF), blob], {
        type: blob.type
      });
    }

    return blob;
  }

  function download(url, name, opts) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url);
    xhr.responseType = 'blob';

    xhr.onload = function () {
      saveAs(xhr.response, name, opts);
    };

    xhr.onerror = function () {
      console.error('could not download file');
    };

    xhr.send();
  }

  function corsEnabled(url) {
    var xhr = new XMLHttpRequest();

    xhr.open('HEAD', url, false);

    try {
      xhr.send();
    } catch (e) {}

    return xhr.status >= 200 && xhr.status <= 299;
  }


  function click(node) {
    try {
      node.dispatchEvent(new MouseEvent('click'));
    } catch (e) {
      var evt = document.createEvent('MouseEvents');
      evt.initMouseEvent('click', true, true, window, 0, 0, 0, 80, 20, false, false, false, false, 0, null);
      node.dispatchEvent(evt);
    }
  }


  var isMacOSWebView = _global.navigator && /Macintosh/.test(navigator.userAgent) && /AppleWebKit/.test(navigator.userAgent) && !/Safari/.test(navigator.userAgent);
  var saveAs = _global.saveAs || (
  typeof window !== 'object' || window !== _global ? function saveAs() {}

  : 'download' in HTMLAnchorElement.prototype && !isMacOSWebView ? function saveAs(blob, name, opts) {
    var URL = _global.URL || _global.webkitURL;
    var a = document.createElement('a');
    name = name || blob.name || 'download';
    a.download = name;
    a.rel = 'noopener';

    if (typeof blob === 'string') {
      a.href = blob;

      if (a.origin !== location.origin) {
        corsEnabled(a.href) ? download(blob, name, opts) : click(a, a.target = '_blank');
      } else {
        click(a);
      }
    } else {
      a.href = URL.createObjectURL(blob);
      setTimeout(function () {
        URL.revokeObjectURL(a.href);
      }, 4E4);

      setTimeout(function () {
        click(a);
      }, 0);
    }
  }
  : 'msSaveOrOpenBlob' in navigator ? function saveAs(blob, name, opts) {
    name = name || blob.name || 'download';

    if (typeof blob === 'string') {
      if (corsEnabled(blob)) {
        download(blob, name, opts);
      } else {
        var a = document.createElement('a');
        a.href = blob;
        a.target = '_blank';
        setTimeout(function () {
          click(a);
        });
      }
    } else {
      navigator.msSaveOrOpenBlob(bom(blob, opts), name);
    }
  }
  : function saveAs(blob, name, opts, popup) {
    popup = popup || open('', '_blank');

    if (popup) {
      popup.document.title = popup.document.body.innerText = 'downloading...';
    }

    if (typeof blob === 'string') return download(blob, name, opts);
    var force = blob.type === 'application/octet-stream';

    var isSafari = /constructor/i.test(_global.HTMLElement) || _global.safari;

    var isChromeIOS = /CriOS\/[\d]+/.test(navigator.userAgent);

    if ((isChromeIOS || force && isSafari || isMacOSWebView) && typeof FileReader !== 'undefined') {
      var reader = new FileReader();

      reader.onloadend = function () {
        var url = reader.result;
        url = isChromeIOS ? url : url.replace(/^data:[^;]*;/, 'data:attachment/file;');
        if (popup) popup.location.href = url;else location = url;
        popup = null;
      };

      reader.readAsDataURL(blob);
    } else {
      var URL = _global.URL || _global.webkitURL;
      var url = URL.createObjectURL(blob);
      if (popup) popup.location = url;else location.href = url;
      popup = null;

      setTimeout(function () {
        URL.revokeObjectURL(url);
      }, 4E4);
    }
  });
  _global.saveAs = saveAs.saveAs = saveAs;

  if (typeof module !== 'undefined') {
    module.exports = saveAs;
  }
});

(function() {
    'use strict';
    var indexReg=/^(\w.*)?PART\b|^Prologue|^(\w.*)?Chapter\s*[\-_]?\d+|分卷|^序$|^序\s*[·言章]|^前\s*言|^附\s*[录錄]|^引\s*[言子]|^摘\s*要|^[楔契]\s*子|^后\s*记|^後\s*記|^附\s*言|^结\s*语|^結\s*語|^尾\s*[声聲]|^最終話|^最终话|^番\s*外|^\d+[\s\.、,，）\-_：:][^\d#\.]|^(\d|\s|\.)*[第（]?\s*[\d〇零一二两三四五六七八九十百千万萬-]+\s*[、）章节節回卷折篇幕集话話]/i;
    var innerNextPage=/^\s*(下一[页頁张張]|next\s*page|次のページ)/i;
    var lang=navigator.appName=="Netscape"?navigator.language:navigator.userLanguage;
    var i18n={};
    var rCats=[];
    var processFunc, nextPageFunc;
    const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
    var win=(typeof unsafeWindow=='undefined'?window:unsafeWindow);
    switch (lang){
        case "zh-CN":
        case "zh-SG":
            i18n={
                fetch:"开始下载小说",
                info:"来源：#t#\n本文是使用怠惰小说下载器（DownloadAllContent）下载的",
                error:"该段内容获取失败",
                downloading:"已下载完成 %s 段，剩余 %s 段<br>正在下载 %s",
                complete:"已全部下载完成，共 %s 段",
                del:"设置文本干扰码的CSS选择器",
                custom:"自定规则下载",
                customInfo:"输入网址或者章节CSS选择器",
                reSort:"按标题名重新排序章节",
                reSortUrl:"按网址重新排序章节",
                setting:"选项参数设置",
                searchRule:"搜索网站规则",
                abort:"跳过此章",
                save:"保存当前",
                saveAsMd:"存为 Markdown",
                downThreadNum:"设置同时下载的线程数，负数为单线程下载间隔",
                customTitle:"自定义章节标题，输入内页文字对应选择器",
                maxDlPerMin:"每分钟最大下载数",
                reSortDefault:"默认按页面中位置排序章节",
                reverseOrder:"反转章节排序",
                saveBtn:"保存设置",
                saveOk:"保存成功",
                nextPage:"嗅探章节内分页",
                nextPageReg:"自定义分页正则",
                retainImage:"保留正文中图片的网址",
                minTxtLength:"当检测到的正文字数小于此数，则尝试重新抓取",
                showFilterList:"下载前显示章节筛选排序窗口",
                ok:"确定",
                close:"关闭",
                dacSortByPos:"按页内位置排序",
                dacSortByUrl:"按网址排序",
                dacSortByName:"按章节名排序",
                reverse:"反选",
                dacUseIframe:"使用 iframe 后台加载内容（慢速）",
                dacSaveAsZip:"下载为 zip",
                dacSetCustomRule:"修改规则",
                dacAddUrl:"添加章节",
                dacStartDownload:"下载选中",
                downloadShortcut:"下载章节",
                downloadSingleShortcut:"下载单页",
                downloadCustomShortcut:"自定义下载"
            };
            break;
        case "zh":
        case "zh-TW":
        case "zh-HK":
            i18n={
                fetch:"開始下載小說",
                info:"來源：#t#\n本文是使用怠惰小說下載器（DownloadAllContent）下載的",
                error:"該段內容獲取失敗",
                downloading:"已下載完成 %s 段，剩餘 %s 段<br>正在下載 %s",
                complete:"已全部下載完成，共 %s 段",
                del:"設置文本干擾碼的CSS選擇器",
                custom:"自訂規則下載",
                customInfo:"輸入網址或者章節CSS選擇器",
                reSort:"按標題名重新排序章節",
                reSortUrl:"按網址重新排序章節",
                setting:"選項參數設定",
                searchRule:"搜尋網站規則",
                abort:"跳過此章",
                save:"保存當前",
                saveAsMd:"存爲 Markdown",
                downThreadNum:"設置同時下載的綫程數，負數為單線程下載間隔",
                customTitle:"自訂章節標題，輸入內頁文字對應選擇器",
                maxDlPerMin:"每分鐘最大下載數",
                reSortDefault:"預設依頁面中位置排序章節",
                reverseOrder:"反轉章節排序",
                saveBtn:"儲存設定",
                saveOk:"儲存成功",
                nextPage:"嗅探章節內分頁",
                nextPageReg:"自訂分頁正規",
                retainImage:"保留內文圖片的網址",
                minTxtLength:"當偵測到的正文字數小於此數，則嘗試重新抓取",
                showFilterList:"下載前顯示章節篩選排序視窗",
                ok:"確定",
                close:"關閉",
                dacSortByPos:"依頁內位置排序",
                dacSortByUrl:"依網址排序",
                dacSortByName:"依章節名排序",
                reverse:"反選",
                dacUseIframe:"使用 iframe 背景載入內容（慢速）",
                dacSaveAsZip:"下載為 zip",
                dacSetCustomRule:"修改規則",
                dacAddUrl:"新增章節",
                dacStartDownload:"下載選取",
                downloadShortcut:"下載章節",
                downloadSingleShortcut:"下載單頁",
                downloadCustomShortcut:"自設下載"
            };
            break;
        case "ar":
        case "ar-AE":
        case "ar-BH":
        case "ar-DZ":
        case "ar-EG":
        case "ar-IQ":
        case "ar-JO":
        case "ar-KW":
        case "ar-LB":
        case "ar-LY":
        case "ar-MA":
        case "ar-OM":
        case "ar-QA":
        case "ar-SA":
        case "ar-SY":
        case "ar-TN":
        case "ar-YE":
            i18n={
                fetch: "تحميل",
                info: "المصدر: #t#\nتم تنزيل الـ TXT بواسطة 'DownloadAllContent'",
                error: "فشل في تحميل الفصل الحالي",
                downloading: "......%s تحميل<br>صفحات متبقية %s صفحات تم تحميلها، هناك %s",
                complete: "صفحات في المجموع %s اكتمل! حصلت على",
                del: "لتجاهل CSS تعيين محددات",
                custom: "تحميل مخصص",
                customInfo: "لروابط الفصول sss إدخال الروابط أو محددات",
                reSort: "إعادة الترتيب حسب العنوان",
                reSortUrl: "إعادة الترتيب حسب الروابط",
                setting: "فتح الإعدادات",
                searchRule: "قاعدة البحث",
                abort: "إيقاف",
                save: "حفظ",
                saveAsMd: "Markdown حفظ كـ",
                downThreadNum: "تعيين عدد الخيوط للتحميل",
                customTitle: "تخصيص عنوان الفصل، إدخال المحدد في الصفحة الداخلية",
                maxDlPerMin:"الحد الأقصى لعدد التنزيلات في الدقيقة",
                reSortDefault: "الترتيب الافتراضي حسب الموقع في الصفحة",
                reverseOrder: "عكس ترتيب الفصول",
                saveBtn: "حفظ الإعدادات",
                saveOk: "تم الحفظ",
                nextPage: "التحقق من الصفحة التالية في الفصل",
                nextPageReg: "مخصص للصفحة التالية RegExp",
                retainImage: "الاحتفاظ بعنوان الصورة إذا كانت هناك صور في النص",
                minTxtLength: "المحاولة مرة أخرى عندما يكون طول المحتوى أقل من هذا",
                showFilterList: "عرض نافذة التصفية والترتيب قبل التحميل",
                ok: "موافق",
                close: "إغلاق",
                dacSortByPos: "الترتيب حسب الموقع",
                dacSortByUrl: "الترتيب حسب الرابط",
                dacSortByName: "الترتيب حسب الاسم",
                reverse: "عكس الاختيار",
                dacUseIframe: "لتحميل المحتوى (بطيء) iframe استخدام",
                dacSaveAsZip: "zip حفظ كـ",
                dacSetCustomRule: "تعديل القواعد",
                dacAddUrl: "إضافة فصل",
                dacStartDownload: "تحميل المحدد",
                downloadShortcut: "تحميل الفصل",
                downloadSingleShortcut: "تحميل صفحة واحدة",
                downloadCustomShortcut: "تحميل مخصص"
            };
            break;
        default:
            i18n={
                fetch:"Download",
                info:"Source: #t#\nThe TXT is downloaded by 'DownloadAllContent'",
                error:"Failed in downloading current chapter",
                downloading:"%s pages are downloaded, there are still %s pages left<br>Downloading %s ......",
                complete:"Completed! Get %s pages in total",
                del:"Set css selectors for ignore",
                custom:"Custom to download",
                customInfo:"Input urls OR sss selectors for chapter links",
                reSort:"ReSort by title",
                reSortUrl:"Resort by URLs",
                setting:"Open Setting",
                searchRule:"Search rule",
                abort:"Abort",
                save:"Save",
                saveAsMd:"Save as Markdown",
                downThreadNum:"Set threadNum for download, negative means interval of single thread",
                customTitle: "Customize the chapter title, enter the selector on inner page",
                maxDlPerMin:"Maximum number of downloads per minute",
                reSortDefault: "Default sort by position in the page",
                reverseOrder:"Reverse chapter ordering",
                saveBtn:"Save Setting",
                saveOk:"Save Over",
                nextPage:"Check next page in chapter",
                nextPageReg:"Custom RegExp of next page",
                retainImage:"Keep the URL of image if there are images in the text",
                minTxtLength:"Try to crawl again when the length of content is less than this",
                showFilterList: "Show chapter filtering and sorting window before downloading",
                ok:"OK",
                close:"Close",
                dacSortByPos:"Sort by position",
                dacSortByUrl:"Sort by URL",
                dacSortByName:"Sort by name",
                reverse:"Reverse selection",
                dacUseIframe: "Use iframe to load content (slow)",
                dacSaveAsZip: "Save as zip",
                dacSetCustomRule:"Modify rules",
                dacAddUrl:"Add Chapter",
                dacStartDownload:"Download selected",
                downloadShortcut:"Download chapter",
                downloadSingleShortcut:"Download single page",
                downloadCustomShortcut:"Custom download"
            };
            break;
    }
    var firefox=navigator.userAgent.toLowerCase().indexOf('firefox')!=-1,curRequests=[],useIframe=false,iframeSandbox=false,iframeInit=false;
    var filterListContainer,txtDownContent,txtDownWords,txtDownQuit,dacLinksCon,dacUseIframe,shadowContainer,downTxtShadowContainer;

    const escapeHTMLPolicy = (win.trustedTypes && win.trustedTypes.createPolicy) ? win.trustedTypes.createPolicy('dac_default', {
        createHTML: (string, sink) => string
    }) : null;

    function createHTML(html) {
        return escapeHTMLPolicy ? escapeHTMLPolicy.createHTML(html) : html;
    }

    function str2Num(str) {
        str = str.replace(/^番\s*外/, "99999+").replace(/[一①Ⅰ壹]/g, "1").replace(/[二②Ⅱ贰]/g, "2").replace(/[三③Ⅲ叁]/g, "3").replace(/[四④Ⅳ肆]/g, "4").replace(/[五⑤Ⅴ伍]/g, "5").replace(/[六⑥Ⅵ陆]/g, "6").replace(/[七⑦Ⅶ柒]/g, "7").replace(/[八⑧Ⅷ捌]/g, "8").replace(/[九⑨Ⅸ玖]/g, "9").replace(/[十⑩Ⅹ拾]/g, "*10+").replace(/[百佰]/g, "*100+").replace(/[千仟]/g, "*1000+").replace(/[万萬]/g, "*10000+").replace(/\s/g, "").match(/[\d\*\+]+/);
        if (!str) return 0;
        str = str[0];
        let mul = str.match(/(\d*)\*(\d+)/);
        while(mul) {
            let result = parseInt(mul[1] || 1) * parseInt(mul[2]);
            str = str.replace(mul[0], result);
            mul = str.match(/(\d+)\*(\d+)/);
        }
        let plus = str.match(/(\d+)\+(\d+)/);
        while(plus) {
            let result = parseInt(plus[1]) + parseInt(plus[2]);
            str = str.replace(plus[0], result);
            plus = str.match(/(\d+)\+(\d+)/);
        }
        return parseInt(str);
    }

    var dragOverItem, dragFrom, linkDict;
    function createLinkItem(aEle) {
        let item = document.createElement("div");
        item.innerHTML = createHTML(`
                <input type="checkbox" checked>
                <a class="dacLink" draggable="false" target="_blank" href="${aEle.href}">${aEle.innerText || "📄"}</a>
                <span>🖱️</span>
            `);
        item.title = aEle.innerText;
        item.setAttribute("draggable", "true");
        item.addEventListener("dragover", e => {
            e.preventDefault();
        });
        item.addEventListener("dragenter", e => {
            if (dragOverItem) dragOverItem.style.opacity = "";
            item.style.opacity = 0.3;
            dragOverItem = item;
        });
        item.addEventListener('dragstart', e => {
            dragFrom = item;
        });
        item.addEventListener('drop', e => {
            if (!dragFrom) return;
            if (e.clientX < item.getBoundingClientRect().left + 142) {
                dacLinksCon.insertBefore(dragFrom, item);
            } else {
                if (item.nextElementSibling) {
                    dacLinksCon.insertBefore(dragFrom, item.nextElementSibling);
                } else {
                    dacLinksCon.appendChild(dragFrom);
                }
            }
            e.preventDefault();
        });
        linkDict[aEle.href] = item;
        dacLinksCon.appendChild(item);
    }

    var saveAsZip = true;
    function filterList(list) {
        if (!GM_getValue("showFilterList")) {
            indexDownload(list);
            return;
        }
        if (txtDownContent) {
            txtDownContent.style.display = "none";
        }
        if (filterListContainer) {
            filterListContainer.style.display = "";
            filterListContainer.classList.remove("customRule");
            dacLinksCon.innerHTML = createHTML("");
        } else {
            document.addEventListener('dragend', e => {
                if (dragOverItem) dragOverItem.style.opacity = "";
            }, true);
            filterListContainer = document.createElement("div");
            filterListContainer.id = "filterListContainer";
            filterListContainer.innerHTML = createHTML(`
                <div id="dacFilterBg" style="height: 100%; width: 100%; position: fixed; top: 0; z-index: 2147483646; opacity: 0.3; filter: alpha(opacity=30); background-color: #000;"></div>
                <div id="filterListBody">
                    <div class="dacCustomRule">
                    ${i18n.custom}
                        <textarea id="dacCustomInput"></textarea>
                        <div class="fun">
                            <input id="dacConfirmRule" value="${i18n.ok}" type="button"/>
                            <input id="dacCustomClose" value="${i18n.close}" type="button"/>
                        </div>
                    </div>
                    <div class="sort">
                        <input id="dacSortByPos" value="${i18n.dacSortByPos}" type="button"/>
                        <input id="dacSortByUrl" value="${i18n.dacSortByUrl}" type="button"/>
                        <input id="dacSortByName" value="${i18n.dacSortByName}" type="button"/>
                        <input id="reverse" value="${i18n.reverse}" type="button"/>
                    </div>
                    <div id="dacLinksCon" style="max-height: calc(80vh - 100px); min-height: 100px; display: grid; grid-template-columns: auto auto; width: 100%; overflow: auto; white-space: nowrap;"></div>
                    <p style="margin: 5px; text-align: center; font-size: 14px; height: 20px;"><span><input id="dacUseIframe" type="checkbox"/><label for="dacUseIframe"> ${i18n.dacUseIframe}</label></span> <span style="display:${win.downloadAllContentSaveAsZip ? "inline" : "none"}"><input id="dacSaveAsZip" type="checkbox" checked="checked"/><label for="dacSaveAsZip"> ${i18n.dacSaveAsZip}</label></span></p>
                    <div class="fun">
                        <input id="dacSetCustomRule" value="${i18n.dacSetCustomRule}" type="button"/>
                        <input id="dacAddUrl" value="${i18n.dacAddUrl}" type="button"/>
                        <input id="dacStartDownload" value="${i18n.dacStartDownload}" type="button"/>
                        <input id="dacLinksClose" value="${i18n.close}" type="button"/>
                    </div>
                </div>`);
            let dacSortByPos = filterListContainer.querySelector("#dacSortByPos");
            let dacSortByUrl = filterListContainer.querySelector("#dacSortByUrl");
            let dacSortByName = filterListContainer.querySelector("#dacSortByName");
            let reverse = filterListContainer.querySelector("#reverse");
            let dacSetCustomRule = filterListContainer.querySelector("#dacSetCustomRule");
            let dacCustomInput = filterListContainer.querySelector("#dacCustomInput");
            let dacConfirmRule = filterListContainer.querySelector("#dacConfirmRule");
            let dacCustomClose = filterListContainer.querySelector("#dacCustomClose");
            let dacAddUrl = filterListContainer.querySelector("#dacAddUrl");
            let dacStartDownload = filterListContainer.querySelector("#dacStartDownload");
            let dacLinksClose = filterListContainer.querySelector("#dacLinksClose");
            let dacFilterBg = filterListContainer.querySelector("#dacFilterBg");
            let dacSaveAsZip = filterListContainer.querySelector("#dacSaveAsZip");
            dacUseIframe = filterListContainer.querySelector("#dacUseIframe");
            dacSaveAsZip.onchange = e => {
                saveAsZip = dacSaveAsZip.checked;
            };
            dacSortByPos.onclick = e => {
                let linkList = [].slice.call(dacLinksCon.children);
                if (linkList[0].children[1].href != list[0].href) {
                    list.reverse().forEach(a => {
                        let link = linkDict[a.href];
                        if (!link) return;
                        dacLinksCon.insertBefore(link, dacLinksCon.children[0]);
                    });
                } else {
                    list.forEach(a => {
                        let link = linkDict[a.href];
                        if (!link) return;
                        dacLinksCon.insertBefore(link, dacLinksCon.children[0]);
                    });
                }
            };
            dacSortByUrl.onclick = e => {
                let linkList = [].slice.call(dacLinksCon.children);
                linkList.sort((a, b) => {
                    const nameA = a.children[1].href.toUpperCase();
                    const nameB = b.children[1].href.toUpperCase();
                    if (nameA < nameB) {
                        return -1;
                    }
                    if (nameA > nameB) {
                        return 1;
                    }
                    return 0;
                });
                if (linkList[0] == dacLinksCon.children[0]) {
                    linkList = linkList.reverse();
                }
                linkList.forEach(link => {
                    dacLinksCon.appendChild(link);
                });
            };
            dacSortByName.onclick = e => {
                let linkList = [].slice.call(dacLinksCon.children);
                linkList.sort((a, b) => {
                    return str2Num(a.innerText) - str2Num(b.innerText);
                });
                if (linkList[0] == dacLinksCon.children[0]) {
                    linkList = linkList.reverse();
                }
                linkList.forEach(link => {
                    dacLinksCon.appendChild(link);
                });
            };
            reverse.onclick = e => {
                let linkList = [].slice.call(dacLinksCon.children);
                linkList.forEach(link => {
                    link.children[0].checked=!link.children[0].checked;
                });
            };
            dacSetCustomRule.onclick = e => {
                filterListContainer.classList.add("customRule");
                dacCustomInput.value = GM_getValue("DACrules_" + document.domain) || "";
            };
            dacConfirmRule.onclick = e => {
                if (dacCustomInput.value) {
                    customDown(dacCustomInput.value);
                }
            };
            dacCustomClose.onclick = e => {
                filterListContainer.classList.remove("customRule");
            };
            dacAddUrl.onclick = e => {
                let addUrls = window.prompt(i18n.customInfo, "https://xxx.xxx/book-[20-99].html,     https://xxx.xxx/book-[01-10].html&#34;);    
                if (!addUrls || !/^http|^ftp/.test(addUrls)) return;
                let index = 1;
                [].forEach.call(addUrls.split(","), function(i) {
                    var curEle;
                    var varNum = /\[\d+\-\d+\]/.exec(i);
                    if (varNum) {
                        varNum = varNum[0].trim();
                    } else {
                        curEle = document.createElement("a");
                        curEle.href = i;
                        curEle.innerText = "Added Url";
                        createLinkItem(curEle);
                        return;
                    }
                    var num1 = /\[(\d+)/.exec(varNum)[1].trim();
                    var num2 = /(\d+)\]/.exec(varNum)[1].trim();
                    var num1Int = parseInt(num1);
                    var num2Int = parseInt(num2);
                    var numLen = num1.length;
                    var needAdd = num1.charAt(0) == "0";
                    if (num1Int >= num2Int) return;
                    for (var j = num1Int; j <= num2Int; j++) {
                        var urlIndex = j.toString();
                        if (needAdd) {
                            while(urlIndex.length < numLen) urlIndex = "0" + urlIndex;
                        }
                        var curUrl = i.replace(/\[\d+\-\d+\]/, urlIndex).trim();
                        curEle = document.createElement("a");
                        curEle.href = curUrl;
                        curEle.innerText = "Added Url " + index++;
                        createLinkItem(curEle);
                    }
                });
            };
            dacStartDownload.onclick = e => {
                let linkList = [].slice.call(dacLinksCon.querySelectorAll("input:checked+.dacLink"));
                useIframe = !!dacUseIframe.checked;
                indexDownload(linkList, true);
            };
            dacLinksClose.onclick = e => {
                filterListContainer.style.display = "none";
            };
            dacFilterBg.onclick = e => {
                filterListContainer.style.display = "none";
            };
            let listStyle = GM_addStyle(`
                #filterListContainer * {
                    font-size: 13px;
                    float: initial;
                    background-image: initial;
                    height: fit-content;
                    color: black;
                }
                #filterListContainer.customRule .dacCustomRule {
                    display: flex;
                }
                #filterListContainer .dacCustomRule>textarea {
                    height: 300px;
                    width: 100%;
                    border: 1px #DADADA solid;
                    background: #ededed70;
                    margin: 5px;
                }
                #filterListContainer.customRule .dacCustomRule~* {
                    display: none!important;
                }
                #dacLinksCon>div {
                    padding: 5px 0;
                    display: flex;
                }
                #dacLinksCon>div>a {
                    max-width: 245px;
                    display: inline-block;
                    text-overflow: ellipsis;
                    overflow: hidden;
                }
                #dacLinksCon>div>input {
                    margin-right: 5px;
                }
                #filterListContainer .dacCustomRule {
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 16px;
                    outline: none;
                    align-items: center;
                    flex-wrap: nowrap;
                    white-space: nowrap;
                    flex-direction: column;
                    display: none;
                }
                #filterListContainer input {
                    border-width: 2px;
                    border-style: outset;
                    border-color: buttonface;
                    border-image: initial;
                    border: 1px #DADADA solid;
                    padding: 5px;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 9pt;
                    outline: none;
                    cursor: pointer;
                    line-height: initial;
                    width: initial;
                    min-width: initial;
                    max-width: initial;
                    height: initial;
                    min-height: initial;
                    max-height: initial;
                }
                #dacLinksCon>div:nth-of-type(4n),
                #dacLinksCon>div:nth-of-type(4n+1) {
                    background: #ffffff;
                }
                #dacLinksCon>div:nth-of-type(4n+2),
                #dacLinksCon>div:nth-of-type(4n+3) {
                    background: #f5f5f5;
                }
                #filterListContainer .fun,#filterListContainer .sort {
                    display: flex;
                    justify-content: space-around;
                    flex-wrap: nowrap;
                    width: 100%;
                    height: 28px;
                }
                #filterListContainer input[type=button]:hover {
                    border: 1px #C6C6C6 solid;
                    box-shadow: 1px 1px 1px #EAEAEA;
                    color: #333333;
                    background: #F7F7F7;
                }
                #filterListContainer input[type=button]:active {
                    box-shadow: inset 1px 1px 1px #DFDFDF;
                }
                #filterListBody {
                    padding: 5px;
                    box-sizing: border-box;
                    overflow: hidden;
                    width: 600px;
                    height: auto;
                    max-height: 80vh;
                    min-height: 200px;
                    position: fixed;
                    left: 50%;
                    top: 10%;
                    margin-left: -300px;
                    z-index: 2147483646;
                    background-color: #ffffff;
                    border: 1px solid #afb3b6;
                    border-radius: 10px;
                    opacity: 0.95;
                    filter: alpha(opacity=95);
                    box-shadow: 5px 5px 20px 0px #000;
                }
                @media screen and (max-width: 800px) {
                    #filterListBody {
                        width: 90%;
                        margin-left: -45%;
                    }
                }
            `);
            dacLinksCon = filterListContainer.querySelector("#dacLinksCon");
            shadowContainer = document.createElement("div");
            document.body.appendChild(shadowContainer);
            let shadow = shadowContainer.attachShadow({ mode: "open" });
            shadow.appendChild(listStyle);
            shadow.appendChild(filterListContainer);
        }
        if (shadowContainer.parentNode) shadowContainer.parentNode.removeChild(shadowContainer);
        linkDict = {};
        list.forEach(a => {
            createLinkItem(a);
        });
        dacUseIframe.checked = useIframe;
        document.body.appendChild(shadowContainer);
    }

    function initTxtDownDiv() {
        if (txtDownContent) {
            txtDownContent.style.display = "";
            document.body.appendChild(downTxtShadowContainer);
            return;
        }
        txtDownContent = document.createElement("div");
        txtDownContent.id = "txtDownContent";
        downTxtShadowContainer = document.createElement("div");
        document.body.appendChild(downTxtShadowContainer);
        let shadow = downTxtShadowContainer.attachShadow({ mode: "open" });
        shadow.appendChild(txtDownContent);
        txtDownContent.innerHTML = createHTML(`
            <style>
            #txtDownContent>div{
              font-size:16px;
              color:#333333;
              width:342px;
              height:110px;
              position:fixed;
              left:50%;
              top:50%;
              margin-top:-25px;
              margin-left:-171px;
              z-index:2147483647;
              background-color:#ffffff;
              border:1px solid #afb3b6;
              border-radius:10px;
              opacity:0.95;
              filter:alpha(opacity=95);
              box-shadow:5px 5px 20px 0px #000;
            }
            #txtDownWords{
              position:absolute;
              width:275px;
              height: 90px;
              max-height: 90%;
              border: 1px solid #f3f1f1;
              padding: 8px;
              border-radius: 10px;
              overflow: auto;
            }
            #txtDownQuit{
              width: 30px;height: 30px;border-radius: 30px;position:absolute;right:2px;top:2px;cursor: pointer;background-color:#ff5a5a;
            }
            #txtDownQuit>span{
              height: 30px;line-height: 30px;display:block;color:#FFF;text-align:center;font-size: 12px;font-weight: bold;font-family: arial;background: initial; float: initial;
            }
            #txtDownQuit+div{
              position:absolute;right:0px;bottom:2px;cursor: pointer;max-width:85px;
            }
            #txtDownQuit+div>button{
              background: #008aff;border: 0;padding: 5px;border-radius: 6px;color: white;float: right;margin: 1px;height: 25px;line-height: 16px;cursor: pointer;overflow: hidden;
            }
            </style>
            <div>
                <div id="txtDownWords">
                    Analysing......
                </div>
                <div id="txtDownQuit">
                    <span>╳</span>
                </div>
                <div>
                    <button id="abortRequest" style="display:none;">${getI18n('abort')}</button>
                    <button id="tempSaveTxt">${getI18n('save')}</button>
                    <button id="saveAsMd" title="${getI18n('saveAsMd')}">Markdown</button>
                </div>
            </div>`);
        txtDownWords=txtDownContent.querySelector("#txtDownWords");
        txtDownQuit=txtDownContent.querySelector("#txtDownQuit");
        txtDownQuit.onclick=function(){
            txtDownContent.style.display="none";
        };
        initTempSave(txtDownContent);
        win.txtDownWords = txtDownWords;
    }

    function saveContent() {
        if (win.downloadAllContentSaveAsZip && saveAsZip) {
            win.downloadAllContentSaveAsZip(rCats, i18n.info.replace("#t#", location.href), content => {
                saveAs(content, document.title.replace(/[\*\/:<>\?\\\|\r\n,]/g, "_") + ".zip");
            });
        } else {
            var blob = new Blob([i18n.info.replace("#t#", location.href) + "\r\n\r\n" + rCats.join("\r\n\r\n")], {type: "text/plain;charset=utf-8"});
            saveAs(blob, document.title.replace(/[\*\/:<>\?\\\|\r\n,]/g, "_") + ".txt");
        }
    }

    function initTempSave(txtDownContent){
        var tempSavebtn = txtDownContent.querySelector('#tempSaveTxt');
        var abortbtn = txtDownContent.querySelector('#abortRequest');
        var saveAsMd = txtDownContent.querySelector('#saveAsMd');
        tempSavebtn.onclick = function(){
            saveContent();
            console.log(curRequests);
        }
        abortbtn.onclick = function(){
            let curRequest = curRequests.pop();
            if(curRequest)curRequest[1].abort();
        }
        saveAsMd.onclick = function(){
            let txt = i18n.info.replace("#t#", location.href)+"\n\n---\n"+document.title+"\n===\n";
            rCats.forEach(cat => {
                cat = cat.replace("\r\n", "\n---").replace(/(\r\n|\n\r)+/g, "\n\n").replace(/[\n\r]\t+/g, "\n");
                txt += '\n\n'+cat;
            });
            var blob = new Blob([txt], {type: "text/plain;charset=utf-8"});
            saveAs(blob, document.title.replace(/[\*\/:<>\?\\\|\r\n,]/g, "_") + ".md");
        }
    }

    let charset = (document.characterSet || document.charset || document.inputEncoding);
    let equiv = document.querySelector('[http-equiv="Content-Type"]'), charsetValid = true;
    if (equiv && equiv.content) {
        let innerCharSet = equiv.content.match(/charset\=([^;]+)/);
        if (!innerCharSet) {
            charsetValid = false;
        } else if (innerCharSet[1].replace("-", "").toLowerCase() != charset.replace("-", "").toLowerCase()) {
            charsetValid = false;
        }
    } else charsetValid = false;
    function indexDownload(aEles, noSort){
        if(aEles.length<1)return;
        initTxtDownDiv();
        if(!noSort) {
            if(GM_getValue("contentSort")){
                aEles.sort((a, b) => {
                    return str2Num(a.innerText) - str2Num(b.innerText);
                });
            }
            if(GM_getValue("contentSortUrl")){
                aEles.sort((a, b) => {
                    const nameA = a.href.toUpperCase();
                    const nameB = b.href.toUpperCase();
                    if (nameA < nameB) {
                        return -1;
                    }
                    if (nameA > nameB) {
                        return 1;
                    }
                    return 0;
                });
            }
            if(GM_getValue("reverse")){
                aEles=aEles.reverse();
            }
        }
        rCats=[];
        const minute=60000;
        var minTxtLength=GM_getValue("minTxtLength") || 100;
        var customTitle=GM_getValue("customTitle");
        var disableNextPage=!!GM_getValue("disableNextPage");
        var customNextPageReg=GM_getValue("nextPageReg");
        var maxDlPerMin=GM_getValue("maxDlPerMin") || 0;
        var dlCount=0;
        if (customNextPageReg) {
            try {
                innerNextPage = new RegExp(customNextPageReg);
            } catch(e) {
                console.warn(e);
            }
        }
        var insertSigns=[];
        // var j=0,rCats=[];
        var downIndex=0,downNum=0,downOnce=function(wait){
            if(downNum>=aEles.length)return;
            if(maxDlPerMin){
                if(dlCount===-1){
                    setTimeout(() => {
                        downOnce(wait);
                    }, minute);
                    return;
                }else if(dlCount>=maxDlPerMin){
                    dlCount=-1;
                    setTimeout(() => {
                        dlCount=0;
                        downOnce(wait);
                    }, minute);
                    return;
                }else dlCount++;
            }
            let curIndex=downIndex;
            let aTag=aEles[curIndex];
            let request=(aTag, curIndex)=>{
                let tryTimes=0;
                let validTimes=0;
                function requestDoc(_charset) {
                    if (!_charset) _charset = charset;
                    return GM_xmlhttpRequest({
                        method: 'GET',
                        url: aTag.href,
                        headers:{
                            referer:aTag.href,
                            "Content-Type":"text/html;charset="+_charset
                        },
                        timeout:10000,
                        overrideMimeType:"text/html;charset="+_charset,
                        onload: async function(result) {
                            let doc = getDocEle(result.responseText);
                            if (charsetValid) {
                                let equiv = doc.querySelector('[http-equiv="Content-Type"]');
                                if (equiv && equiv.content) {
                                    let innerCharSet = equiv.content.match(/charset\=([^;]+)/);
                                    if (innerCharSet && innerCharSet[1].replace("-", "").toLowerCase() != _charset.replace("-", "").toLowerCase()) {
                                        charset = innerCharSet[1];
                                        return requestDoc(charset);
                                    }
                                }
                            }
                            downIndex++;
                            downNum++;
                            if (/^{/.test(result.responseText)) {
                                doc.json = () => {
                                    try {
                                        return JSON.parse(result.responseText);
                                    } catch(e) {}
                                    return {};
                                }
                            }
                            let base = doc.querySelector("base");
                            let nextPages = !disableNextPage && !processFunc && await checkNextPage(doc, base ? base.href : aTag.href);
                            if (nextPages) {
                                if (!nextPages.length) nextPages = [nextPages];
                                nextPages.forEach(nextPage => {
                                    var inArr=false;
                                    for(var ai=0;ai<aEles.length;ai++){
                                        if(aEles[ai].href==nextPage.href){
                                            inArr=true;
                                            break;
                                        }
                                    }
                                    if(!inArr){
                                        nextPage.innerText=aTag.innerText+"\t>>";
                                        aEles.push(nextPage);
                                        let targetIndex = curIndex;
                                        for(let a=0;a<insertSigns.length;a++){
                                            let signs=insertSigns[a],breakSign=false;
                                            if(signs){
                                                for(let b=0;b<signs.length;b++){
                                                    let sign=signs[b];
                                                    if(sign==curIndex){
                                                        targetIndex=a;
                                                        breakSign=true;
                                                        break;
                                                    }
                                                }
                                            }
                                            if(breakSign)break;
                                        }
                                        let insertSign = insertSigns[targetIndex];
                                        if(!insertSign)insertSigns[targetIndex] = [];
                                        insertSigns[targetIndex].push(aEles.length-1);
                                    }
                                });
                            }
                            if (result.status >= 400) {
                                console.warn("error:", `status: ${result.status} from: ${aTag.href}`);
                            } else {
                                console.log(result.status);
                            }
                            if (customTitle) {
                                try {
                                    let title = doc.querySelector(customTitle);
                                    if (title && title.innerText) {
                                        aTag.innerText = title.innerText;
                                    }
                                } catch(e) {
                                    console.warn(e);
                                }
                            }
                            let validData = processDoc(curIndex, aTag, doc, (result.status>=400?` status: ${result.status} from: ${aTag.href} `:""), validTimes < 5);
                            if (!validData && validTimes++ < 5) {
                                downIndex--;
                                downNum--;
                                setTimeout(() => {
                                    requestDoc();
                                }, Math.random() * 500 + validTimes * 1000);
                                return;
                            }
                            if (wait) {
                                setTimeout(() => {
                                    downOnce(wait);
                                }, wait);
                            } else downOnce();
                        },
                        onerror: function(e) {
                            console.warn("error:", e, aTag.href);
                            if(tryTimes++ < 5){
                                setTimeout(() => {
                                    requestDoc();
                                }, Math.random() * 500 + tryTimes * 1000);
                                return;
                            }
                            downIndex++;
                            downNum++;
                            processDoc(curIndex, aTag, null, ` NETWORK ERROR: ${(e.response||e.responseText)} from: ${aTag.href} `);
                            if (wait) {
                                setTimeout(() => {
                                    downOnce(wait);
                                }, wait);
                            } else downOnce();
                        },
                        ontimeout: function(e) {
                            console.warn("timeout: times="+(tryTimes+1)+" url="+aTag.href);
                            //console.log(e);
                            if(tryTimes++ < 5){
                                setTimeout(() => {
                                    requestDoc();
                                }, Math.random() * 500 + tryTimes * 1000);
                                return;
                            }
                            downIndex++;
                            downNum++;
                            processDoc(curIndex, aTag, null, ` TIMEOUT: ${aTag.href} `);
                            if (wait) {
                                setTimeout(() => {
                                    downOnce(wait);
                                }, wait);
                            } else downOnce();
                        }
                    });
                };
                if (useIframe) {
                    let iframe = document.createElement('iframe'), inited = false, failedTimes = 0;
                    iframe.name = 'pagetual-iframe';
                    iframe.width = '100%';
                    iframe.height = '1000';
                    iframe.frameBorder = '0';
                    iframe.sandbox = iframeSandbox || "allow-same-origin allow-scripts allow-popups allow-forms";
                    iframe.style.cssText = 'margin:0!important;padding:0!important;visibility:hidden!important;flex:0;opacity:0!important;pointer-events:none!important;position:fixed;top:0px;left:0px;z-index:-2147483647;';
                    iframe.addEventListener('load', e => {
                        if (e.data != 'pagetual-iframe:DOMLoaded' && e.type != 'load') return;
                        if (inited) return;
                        inited = true;
                        async function checkIframe() {
                            try {
                                let doc = iframe.contentDocument || iframe.contentWindow.document;
                                if (!doc || !doc.body) {
                                    setTimeout(() => {
                                        checkIframe();
                                    }, 1000);
                                    return;
                                }
                                doc.body.scrollTop = 9999999;
                                doc.documentElement.scrollTop = 9999999;
                                if (!processFunc && validTimes++ > 5 && failedTimes++ < 2) {
                                    iframe.src = iframe.src;
                                    validTimes = 0;
                                    inited = false;
                                    return;
                                }
                                let base = doc.querySelector("base");
                                let nextPages = !disableNextPage && !processFunc && await checkNextPage(doc, base ? base.href : aTag.href);
                                if (nextPages) {
                                    if (!nextPages.length) nextPages = [nextPages];
                                    nextPages.forEach(nextPage => {
                                        var inArr=false;
                                        for(var ai=0;ai<aEles.length;ai++){
                                            if(aEles[ai].href==nextPage.href){
                                                inArr=true;
                                                break;
                                            }
                                        }
                                        if(!inArr){
                                            nextPage.innerText=aTag.innerText+"\t>>";
                                            aEles.push(nextPage);
                                            let targetIndex = curIndex;
                                            for(let a=0;a<insertSigns.length;a++){
                                                let signs=insertSigns[a],breakSign=false;
                                                if(signs){
                                                    for(let b=0;b<signs.length;b++){
                                                        let sign=signs[b];
                                                        if(sign==curIndex){
                                                            targetIndex=a;
                                                            breakSign=true;
                                                            break;
                                                        }
                                                    }
                                                }
                                                if(breakSign)break;
                                            }
                                            let insertSign = insertSigns[targetIndex];
                                            if(!insertSign)insertSigns[targetIndex] = [];
                                            insertSigns[targetIndex].push(aEles.length-1);
                                        }
                                    });
                                }
                                if (customTitle) {
                                    try {
                                        let title = doc.querySelector(customTitle);
                                        if (title && title.innerText) {
                                            aTag.innerText = title.innerText;
                                        }
                                    } catch(e) {
                                        console.warn(e);
                                    }
                                }
                                downIndex++;
                                downNum++;
                                let validData = processDoc(curIndex, aTag, doc, "", failedTimes < 2);
                                if (!validData) {
                                    downIndex--;
                                    downNum--;
                                    setTimeout(() => {
                                        checkIframe();
                                    }, 1000);
                                    return;
                                }
                                if (wait) {
                                    setTimeout(() => {
                                        downOnce(wait);
                                    }, wait);
                                } else downOnce();
                            } catch(e) {
                                console.debug("Stop as cors");
                            }
                            if (iframe && iframe.parentNode) iframe.parentNode.removeChild(iframe);
                        }
                        setTimeout(() => {
                            checkIframe();
                        }, 500);
                    }, false);
                    let checkReady = setInterval(() => {
                        let doc;
                        try {
                            doc = iframe.contentDocument || (iframe.contentWindow && iframe.contentWindow.document);
                        } catch(e) {
                            clearInterval(checkReady);
                            return;
                        }
                        if (doc) {
                            try {
                                Function('win', 'iframe', '"use strict";' + (iframeInit || "win.self=win.top;"))(iframe.contentWindow, iframe);
                                clearInterval(checkReady);
                            } catch(e) {
                                console.debug(e);
                            }
                        }
                    }, 50);
                    iframe.src = aTag.href;
                    document.body.appendChild(iframe);
                    return [curIndex, null, aTag.href];
                } else {
                    return [curIndex, requestDoc(), aTag.href];
                }
            }
            if(!aTag){
                let waitAtagReadyInterval=setInterval(function(){
                    if(downNum>=aEles.length)clearInterval(waitAtagReadyInterval);
                    aTag=aEles[curIndex];
                    if(aTag){
                        clearInterval(waitAtagReadyInterval);
                        request(aTag, curIndex);
                    }
                },1000);
                return null;
            }
            let result = request(aTag, curIndex);
            if (result) curRequests.push(result);
            return result;
        };
        function getDocEle(str){
            var doc = null;
            try {
                doc = document.implementation.createHTMLDocument('');
                doc.documentElement.innerHTML = str;
            }
            catch (e) {
                console.log('parse error');
            }
            return doc;
        }
        function sortInnerPage(){
            var pageArrs=[],maxIndex=0,i,j;
            for(i=0;i<insertSigns.length;i++){
                var signs=insertSigns[i];
                if(signs){
                    for(j=0;j<signs.length;j++){
                        var sign=signs[j];
                        var cat=rCats[sign];
                        rCats[sign]=null;
                        if(!pageArrs[i])pageArrs[i]=[];
                        pageArrs[i].push(cat);
                    }
                }
            }
            for(i=pageArrs.length-1;i>=0;i--){
                let pageArr=pageArrs[i];
                if(pageArr){
                    for(j=pageArr.length-1;j>=0;j--){
                        rCats.splice(i+1, 0, pageArr[j]);
                    }
                }
            }
            rCats = rCats.filter(function(e){return e!=null});
        }
        var waitForComplete;
        function processDoc(i, aTag, doc, cause, check){
            let cbFunc=content=>{
                rCats[i]=(aTag.innerText.replace(/[\r\n\t]/g, "") + "\r\n" + (cause || '') + content.replace(/\s*$/, ""));
                curRequests = curRequests.filter(function(e){return e[0]!=i});
                txtDownContent.style.display="block";
                txtDownWords.innerHTML=getI18n("downloading",[downNum,(aEles.length-downNum),aTag.innerText]);
                if(downNum==aEles.length){
                    if(waitForComplete) clearTimeout(waitForComplete);
                    waitForComplete=setTimeout(()=>{
                        if(downNum==aEles.length){
                            txtDownWords.innerHTML=getI18n("complete",[downNum]);
                            sortInnerPage();
                            saveContent();
                        }
                    },3000);
                }
            };
            let contentResult=getPageContent(doc, content=>{
                cbFunc(content);
            }, aTag.href);
            if(contentResult!==false){
                if(check && contentResult && contentResult.replace(/\s/g, "").length<minTxtLength){
                    return false;
                }
                cbFunc(contentResult);
            }
            return true;
        }
        var downThreadNum = parseInt(GM_getValue("downThreadNum"));
        downThreadNum = downThreadNum || 20;
        if (useIframe && downThreadNum > 5) {
            downThreadNum = 5;
        }
        if (downThreadNum > 0) {
            for (var i = 0; i < downThreadNum; i++) {
                downOnce();
                if (downIndex >= aEles.length - 1 || downIndex >= downThreadNum - 1) break;
                else downIndex++;
            }
        } else {
            downOnce(-downThreadNum * 1000);
            if (downIndex < aEles.length - 1 && downIndex < downThreadNum - 1) downIndex++;
        }
    }

    function canonicalUri(src, baseUrl) {
        if (!src) {
            return "";
        }
        if (src.charAt(0) == "#") return baseUrl + src;
        if (src.charAt(0) == "?") return baseUrl.replace(/^([^\?#]+).*/, "$1" + src);
        let origin = location.protocol + '//' + location.host;
        let url = baseUrl || origin;
        url = url.replace(/(\?|#).*/, "");
        if (/https?:\/\/[^\/]+$/.test(url)) url = url + '/';
        if (url.indexOf("http") !== 0) url = origin + url;
        var root_page = /^[^\?#]*\//.exec(url)[0],
            root_domain = /^\w+\:\/\/\/?[^\/]+/.exec(root_page)[0],
            absolute_regex = /^\w+\:\/\//;
        while (src.indexOf("../") === 0) {
            src = src.substr(3);
            root_page = root_page.replace(/\/[^\/]+\/$/, "/");
        }
        src = src.replace(/\.\//, "");
        if (/^\/\/\/?/.test(src)) {
            src = location.protocol + src;
        }
        return (absolute_regex.test(src) ? src : ((src.charAt(0) == "/" ? root_domain : root_page) + src));
    }

    async function checkNextPage(doc, baseUrl) {
        let nextPage = null;
        if (nextPageFunc) {
            nextPage = await nextPageFunc(doc, baseUrl);
            if (nextPage && nextPage.length === 0) nextPage = null;
        } else {
            let aTags = doc.querySelectorAll("a");
            for (var i = 0; i < aTags.length; i++) {
                let aTag = aTags[i];
                if (innerNextPage.test(aTag.innerText) && aTag.href && !/javascript:|#/.test(aTag.href)) {
                    let nextPageHref = canonicalUri(aTag.getAttribute("href"), baseUrl || location.href);
                    if (nextPageHref != location.href) {
                        nextPage = aTag;
                        nextPage.href = nextPageHref;
                        break;
                    }
                }
            }
        }
        return nextPage;
    }

    function textNodesUnder(el){
        var n, a=[], walk=document.createTreeWalker(el,NodeFilter.SHOW_TEXT,null,false);
        while(n=walk.nextNode()) a.push(n);
        return a;
    }

    function getPageContent(doc, cb, url){
        if(!doc)return i18n.error;
        if(doc.body && !doc.body.children.length)return doc.body.innerText;
        if(processFunc){
            return processFunc(doc, cb, url);
        }
        [].forEach.call(doc.querySelectorAll("span,div,ul"),function(item){
            var thisStyle=doc.defaultView?doc.defaultView.getComputedStyle(item):item.style;
            if(thisStyle && (thisStyle.display=="none" || (item.nodeName=="SPAN" && thisStyle.fontSize=="0px"))){
                item.innerHTML="";
            }
        });
        var i,j,k,rStr="",pageData=(doc.body?doc.body:doc).cloneNode(true);
        pageData.innerHTML=pageData.innerHTML.replace(/\<\!\-\-((.|[\n|\r|\r\n])*?)\-\-\>/g,"");
        [].forEach.call(pageData.querySelectorAll("font.jammer"),function(item){
            item.innerHTML="";
        });
        var selectors=GM_getValue("selectors");
        if(selectors){
            [].forEach.call(pageData.querySelectorAll(selectors),function(item){
                item.innerHTML="";
            });
        }
        [].forEach.call(pageData.querySelectorAll("script,style,link,noscript,iframe"),function(item){
            if (item && item.parentNode) {
                item.parentNode.removeChild(item);
            }
        });
        var endEle = ele => {
            return /^(I|STRONG|B|FONT|P|DL|DD|H\d)$/.test(ele.nodeName) && ele.children.length <= 1;
        };
        var largestContent,contents=pageData.querySelectorAll("span,div,article,p,td,pre"),largestNum=0;
        for(i=0;i<contents.length;i++){
            let content=contents[i],hasText=false,allSingle=true,item,curNum=0;
            if(/footer/.test(content.className))continue;
            for(j=content.childNodes.length-1;j>=0;j--){
                item=content.childNodes[j];
                if(item.nodeType==3){
                    if(/^\s*$/.test(item.data)){
                        item.innerHTML="";
                    }else hasText=true;
                }else if(/^(I|A|STRONG|B|FONT|P|DL|DD|H\d)$/.test(item.nodeName)){
                    hasText=true;
                }else if(item.nodeType==1&&item.children.length==1&&/^(I|A|STRONG|B|FONT|P|DL|DD|H\d)$/.test(item.children[0].nodeName)){
                    hasText=true;
                }
            }
            for(j=content.childNodes.length-1;j>=0;j--){
                item=content.childNodes[j];
                if(item.nodeType==1 && !/^(I|A|STRONG|B|FONT|BR)$/.test(item.nodeName) && /^[\s\-\_\?\>\|]*$/.test(item.innerHTML)){
                    item.innerHTML="";
                }
            }
            if(content.childNodes.length>1){
                let indexItem=0;
                for(j=0;j<content.childNodes.length;j++){
                    item=content.childNodes[j];
                    if(item.nodeType==1){
                        if(item.innerText && item.innerText.length<50 && indexReg.test(item.innerText))indexItem++;
                        for(k=0;k<item.childNodes.length;k++){
                            var childNode=item.childNodes[k];
                            if(childNode.nodeType!=3 && !/^(I|A|STRONG|B|FONT|BR)$/.test(childNode.nodeName)){
                                allSingle=false;
                                break;
                            }
                        }
                        if(!allSingle)break;
                    }
                }
                if(indexItem>=5)continue;
            }else{
                allSingle=false;
            }
            if(!allSingle && !hasText){
                continue;
            }else {
                if(pageData==document && content.offsetWidth<=0 && content.offsetHeight<=0){
                    continue;
                }
                [].forEach.call(content.childNodes,function(item){
                    if(item.nodeType==3)curNum+=item.data.trim().length;
                    else if(endEle(item) || (item.nodeType == 1 && item.children.length == 1 && endEle(item.children[0]))) curNum += (firefox ? item.textContent.trim().length : item.innerText.trim().length);
                });
            }
            if(curNum>largestNum){
                largestNum=curNum;
                largestContent=content;
            }
        }
        if(!largestContent)return i18n.error+" : NO TEXT CONTENT";
        var retainImage=!!GM_getValue("retainImage");
        function getContentByLargest() {
            var childlist=pageData.querySelectorAll(largestContent.nodeName);//+(largestContent.className?"."+largestContent.className.replace(/(^\s*)|(\s*$)/g, '').replace(/\s+/g, '.'):""));
            function getRightStr(ele, noTextEnable){
                [].forEach.call(ele.querySelectorAll("a[href]"), a => {
                    a.parentNode && a.parentNode.removeChild(a);
                });
                if(retainImage){
                    [].forEach.call(ele.querySelectorAll("img[src]"), img => {
                        let imgTxtNode=document.createTextNode(`![img](${canonicalUri(img.getAttribute("src"), url || location.href)})`);
                        img.parentNode.replaceChild(imgTxtNode, img);
                    });
                }
                let childNodes=ele.childNodes,cStr="\r\n",hasText=false;
                for(let j=0;j<childNodes.length;j++){
                    let childNode=childNodes[j];
                    if(childNode.nodeType==3 && childNode.data && !/^[\s\-\_\?\>\|]*$/.test(childNode.data))hasText=true;
                    if(childNode.innerHTML){
                        childNode.innerHTML=childNode.innerHTML.replace(/\<\s*br\s*\>/gi,"\r\n").replace(/\n+/gi,"\n").replace(/\r+/gi,"\r");
                    }
                    let content=childNode.textContent;
                    if(content){
                        if(!content.trim())continue;
                        cStr+=content.replace(/[\uFEFF\xA0 ]+/g," ").replace(/([^\r]|^)\n([^\r]|$)/gi,"$1\r\n$2");
                    }
                    if(childNode.nodeType!=3 && !/^(I|A|STRONG|B|FONT|IMG)$/.test(childNode.nodeName))cStr+="\r\n";
                }
                if(hasText || noTextEnable || ele==largestContent)rStr+=cStr+"\r\n";
            }
            var sameDepthChildren=[];
            for(i=0;i<childlist.length;i++){
                var child=childlist[i];
                if(getDepth(child)==getDepth(largestContent)){
                    if(largestContent.className != child.className)continue;
                    sameDepthChildren.push(child);
                }
            }
            var minLength = largestNum>>2;
            var tooShort = sameDepthChildren.length <= 3;
            sameDepthChildren.forEach(child => {
                if(tooShort && child.innerText.length < minLength) return;
                if((largestContent.className && largestContent.className == child.className) || largestContent.parentNode == child.parentNode){
                    getRightStr(child, true);
                }else {
                    getRightStr(child, false);
                }
            });
            rStr = rStr.replace(/[\n\r]+/g,"\n\r");
        }
        getContentByLargest();
        if (rStr.length < 100) {
            let articles = pageData.querySelectorAll("article");
            if (articles && articles.length == 1) {
                largestContent = articles[0];
                largestNum = largestContent.innerText.length;
                if (largestNum > 100) {
                    rStr = "";
                    getContentByLargest();
                }
            }
        }
        return rStr;
    }

    function getI18n(key, args){
        var resultStr=i18n[key];
        if(args && args.length>0){
            args.forEach(function(item){
                resultStr=resultStr.replace(/%s/,item);
            });
        }
        return resultStr;
    }

    function getDepth(dom){
        var pa=dom,i=0;
        while(pa.parentNode){
            pa=pa.parentNode;
            i++;
        }
        return i;
    }

    async function sleep(time) {
        await new Promise((resolve) => {
            setTimeout(() => {
                resolve();
            }, time);
        })
    }

    async function fetch(forceSingle){
        forceSingle=forceSingle===true;
        processFunc=null;
        initTxtDownDiv();
        var aEles=document.body.querySelectorAll("a"),list=[];
        txtDownWords.innerHTML=`Analysing ( 1/${aEles.length} )......`;
        txtDownContent.style.pointerEvents="none";
        for(var i=0;i<aEles.length;i++){
            if (i % 100 == 0) {
                await sleep(1);
            }
            txtDownWords.innerHTML=`Analysing ( ${i + 1}/${aEles.length} )......`;
            var aEle=aEles[i],has=false;
            if(aEle.dataset.href && (!aEle.href || aEle.href.indexOf("javascript")!=-1)){
                aEle.href=aEle.dataset.href;
            }
            if(aEle.href==location.href)continue;
            for(var j=0;j<list.length;j++){
                if(list[j].href==aEle.href){
                    aEle=list[j];
                    list.splice(j,1);
                    list.push(aEle);
                    has=true;
                    break;
                }
            }
            if(!has && aEle.href && /^http/i.test(aEle.href) && ((aEle.innerText.trim()!="" && indexReg.test(aEle.innerText.trim())) || /chapter[\-_]?\d/.test(aEle.href))){
                list.push(aEle);
            }
        }
        txtDownContent.style.display="none";
        txtDownContent.style.pointerEvents="";
        txtDownWords.innerHTML="Analysing......";
        if(list.length>2 && !forceSingle){
            useIframe = false;
            filterList(list);
        }else{
            var blob = new Blob([i18n.info.replace("#t#", location.href)+"\r\n\r\n"+document.title+"\r\n\r\n"+getPageContent(document)], {type: "text/plain;charset=utf-8"});
            saveAs(blob, document.title+".txt");
        }
    }

    function customDown(urls){
        processFunc = null;
        useIframe = false;
        if(urls){
            urls=decodeURIComponent(urls.replace(/%/g,'%25'));
            GM_setValue("DACrules_"+document.domain, urls);
            var processEles=[];
            let urlsArr=urls.split("@@"),eles=[];
            if(/^http|^ftp/.test(urlsArr[0])){
                [].forEach.call(urlsArr[0].split(","),function(i){
                    var curEle;
                    var varNum=/\[\d+\-\d+\]/.exec(i);
                    if(varNum){
                        varNum=varNum[0].trim();
                    }else{
                        curEle=document.createElement("a");
                        curEle.href=i;
                        curEle.innerText="Added Url";
                        processEles.push(curEle);
                        return;
                    }
                    var num1=/\[(\d+)/.exec(varNum)[1].trim();
                    var num2=/(\d+)\]/.exec(varNum)[1].trim();
                    var num1Int=parseInt(num1);
                    var num2Int=parseInt(num2);
                    var numLen=num1.length;
                    var needAdd=num1.charAt(0)=="0";
                    if(num1Int>=num2Int)return;
                    for(var j=num1Int;j<=num2Int;j++){
                        var urlIndex=j.toString();
                        if(needAdd){
                            while(urlIndex.length<numLen)urlIndex="0"+urlIndex;
                        }
                        var curUrl=i.replace(/\[\d+\-\d+\]/,urlIndex).trim();
                        curEle=document.createElement("a");
                        curEle.href=curUrl;
                        curEle.innerText="Added Url " + processEles.length.toString();
                        processEles.push(curEle);
                    }
                });
            }else{
                let urlSel=urlsArr[0].split(">>");
                try{
                    eles=document.querySelectorAll(urlSel[0]);
                    eles=[].filter.call(eles, ele=>{
                        return ele.nodeName=='BODY'||(!!ele.offsetParent&&getComputedStyle(ele).display!=='none');
                    })
                }catch(e){}
                if(eles.length==0){
                    eles=[];
                    var eleTxts=urlsArr[0].split(/(?<=[^\\])[,，]/),exmpEles=[],excludeTxts={};
                    [].forEach.call(document.querySelectorAll("a"),function(item){
                        if(!item.offsetParent)return;
                        eleTxts.forEach(txt=>{
                            var txtArr=txt.split("!");
                            if(item.innerText.indexOf(txtArr[0])!=-1){
                                exmpEles.push(item);
                                excludeTxts[item]=txtArr.splice(1);
                            }
                        });
                    })
                    exmpEles.forEach(e=>{
                        var cssSelStr="a",pa=e.parentNode,excludeTxt=excludeTxts[e];
                        if(e.className)cssSelStr+="."+CSS.escape(e.className.replace(/\s+/g, ".")).replace(/\\\./g, '.');
                        while(pa && pa.nodeName!="BODY"){
                            cssSelStr=pa.nodeName+">"+cssSelStr;
                            pa=pa.parentNode;
                        }
                        cssSelStr="body>"+cssSelStr;;
                        [].forEach.call(document.querySelectorAll(cssSelStr),function(item){
                            if(!item.offsetParent)return;
                            var isExclude=false;
                            for(var t in excludeTxt){
                                if(item.innerText.indexOf(excludeTxt[t])!=-1){
                                    isExclude=true;
                                    break;
                                }
                            }
                            if(!isExclude && eles.indexOf(item)==-1){
                                eles.push(item);
                            }
                        });
                    });
                }
                function addItem(item) {
                    let has=false;
                    for(var j=0;j<processEles.length;j++){
                        if(processEles[j].href==item.href){
                            processEles.splice(j,1);
                            processEles.push(item);
                            has=true;
                            break;
                        }
                    }
                    if((!item.href || item.href.indexOf("javascript")!=-1) && item.dataset.href){
                        item.href=item.dataset.href;
                    }
                    if(!has && item.href && /^http/i.test(item.href)){
                        processEles.push(item.cloneNode(1));
                    }
                }
                [].forEach.call(eles,function(item){
                    if(urlSel[1]){
                        item=Function("item",urlSel[1])(item);
                        let items;
                        if (Array.isArray(item)) {
                            items = item;
                        } else items = [item];
                        items.forEach(item => {
                            if(!item || !item.href)return;
                            if(!item.nodeName || item.nodeName!="A"){
                                let href=item.href;
                                let innerText=item.innerText;
                                item=document.createElement("a");
                                item.href=href;
                                item.innerText=innerText;
                            }
                            addItem(item);
                        });
                    } else {
                        addItem(item);
                    }
                });
            }
            if(urlsArr[1]){
                processEles.forEach(ele=>{
                    ele.href=ele.href.replace(new RegExp(urlsArr[1]), urlsArr[2]);
                });
            }
            var retainImage=!!GM_getValue("retainImage");
            var evalCode = urlsArr[3];
            if (evalCode) {
                evalCode = evalCode.trim();
                if (/^iframe:/.test(evalCode)) {
                    evalCode = evalCode.replace("iframe:", "");
                    useIframe = true;
                    iframeSandbox = false;
                    iframeInit = false;
                    while (/^(sandbox|init):/.test(evalCode)) {
                        iframeSandbox = evalCode.match(/^sandbox:\{(.*?)\}/);
                        if (iframeSandbox) {
                            evalCode = evalCode.replace(iframeSandbox[0], "");
                            iframeSandbox = iframeSandbox[1];
                        }
                        iframeInit = evalCode.match(/^init:\{(.*?)\}/);
                        if (iframeInit) {
                            evalCode = evalCode.replace(iframeInit[0], "");
                            iframeInit = iframeInit[1];
                        }
                    }
                }
                let charsetMatch = evalCode.match(/^charset:{(.+?)}/);
                if (charsetMatch) {
                    charset = charsetMatch[1];
                    evalCode = evalCode.replace(charsetMatch[0], "");
                }
                let nextMatch = evalCode.match(/^next:(\{+)/);
                if (nextMatch) {
                    let splitLen = nextMatch[1].length;
                    nextMatch = evalCode.match(new RegExp(`^next:\\{{${splitLen}}(.*?)\\}{${splitLen}}`));
                    if (nextMatch) {
                        let nextCode = nextMatch[1];
                        evalCode = evalCode.replace(nextMatch[0], "");
                        nextPageFunc = async (doc, url) => {
                            let result;
                            if (/\breturn\b/.test(nextCode)) {
                                result = await new AsyncFunction('doc', 'url', '"use strict";' + nextCode)(doc, url);
                            } else {
                                try {
                                    result = doc.querySelectorAll(nextCode);
                                    if (result && result.length) {
                                        [].forEach.call(result, ele => {
                                            ele.href = canonicalUri(ele.getAttribute("href"), url || location.href);
                                        });
                                    } else result = null;
                                } catch(e) {}
                            }
                            return result;
                        }
                    }
                }
            }
            if(evalCode){
                processFunc=(data, cb, url)=>{
                    let doc=data;
                    if(evalCode.indexOf("return ")==-1){
                        if(evalCode.indexOf("@")==0){
                            let content="";
                            if(retainImage){
                                [].forEach.call(data.querySelectorAll("img[src]"), img => {
                                    let imgTxt=`![img](${canonicalUri(img.getAttribute("src"), location.href)})`;
                                    let imgTxtNode=document.createTextNode(imgTxt);
                                    img.parentNode.replaceChild(imgTxtNode, img);
                                });
                            }
                            [].forEach.call(data.querySelectorAll(evalCode.slice(1)), ele=>{
                                [].forEach.call(ele.childNodes, child=>{
                                    if(child.innerHTML){
                                        child.innerHTML=child.innerHTML.replace(/\<\s*br\s*\>/gi,"\r\n").replace(/\n+/gi,"\n").replace(/\r+/gi,"\r");
                                    }
                                    if(child.textContent){
                                        content+=(child.textContent.replace(/ +/g," ").replace(/([^\r]|^)\n([^\r]|$)/gi,"$1\r\n$2")+"\r\n");
                                    }
                                });
                                content+="\r\n";
                            });
                            return content;
                        }else return eval(evalCode);
                    }else{
                        return Function("data", "doc", "cb", "url", evalCode)(data, doc, cb, url);
                    }
                };
            }else{
                if(win.dacProcess){
                    processFunc=win.dacProcess;
                }
            }
            filterList(processEles);
        }
    }
    const configPage = "https://hoothin.github.io/UserScripts/DownloadAllContent/&#34;;    
    const copySvg = '<svg aria-hidden="true" height="16" viewBox="0 0 16 16" version="1.1" width="16" data-view-component="true" style="transition: all ease 0.5s;top: 5px;right: 5px;position: absolute;cursor: pointer;"><title>Copy</title><path d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 0 1 0 1.5h-1.5a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-1.5a.75.75 0 0 1 1.5 0v1.5A1.75 1.75 0 0 1 9.25 16h-7.5A1.75 1.75 0 0 1 0 14.25Z"></path><path d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0 1 14.25 11h-7.5A1.75 1.75 0 0 1 5 9.25Zm1.75-.25a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-7.5a.25.25 0 0 0-.25-.25Z"></path></svg>';
    function searchRule(){
        GM_openInTab(configPage + "#@" + location.hostname, {active: true});
    }
    var downloadShortcut = GM_getValue("downloadShortcut") || {ctrlKey: true, shiftKey: false, altKey: false, metaKey: false, key: 'F9'};
    var downloadSingleShortcut = GM_getValue("downloadSingleShortcut") || {ctrlKey: true, shiftKey: true, altKey: false, metaKey: false, key: 'F9'};
    var downloadCustomShortcut = GM_getValue("downloadCustomShortcut") || {ctrlKey: true, shiftKey: false, altKey: true, metaKey: false, key: 'F9'};

    if (location.origin + location.pathname == configPage) {
        let exampleNode = document.getElementById("example");
        if (!exampleNode) return;

        exampleNode = exampleNode.parentNode;
        let ruleList = exampleNode.nextElementSibling.nextElementSibling;
        let searchInput = document.createElement("input");
        let inputTimer;
        function searchByInput() {
            clearTimeout(inputTimer);
            inputTimer = setTimeout(() => {
                let curValue = searchInput.value;
                let matchRules = [];
                let dontMatchRules = [];
                if (curValue) {
                    for (let i = 0; i < ruleList.children.length; i++) {
                        let curRule = ruleList.children[i];
                        let aHref = curRule.firstChild.href;
                        if (aHref.indexOf(curValue) == -1) {
                            dontMatchRules.push(curRule);
                        } else {
                            matchRules.push(curRule);
                        }
                    }
                } else {
                    dontMatchRules = ruleList.children;
                }
                if (matchRules.length) {
                    for (let i = 0; i < dontMatchRules.length; i++) {
                        let curRule = dontMatchRules[i];
                        curRule.style.display = "none";
                    }
                    for (let i = 0; i < matchRules.length; i++) {
                        let curRule = matchRules[i];
                        curRule.style.display = "";
                    }
                } else {
                    for (let i = 0; i < dontMatchRules.length; i++) {
                        let curRule = dontMatchRules[i];
                        curRule.style.display = "";
                    }
                }
            }, 500);
        }
        searchInput.style.margin = "10px";
        searchInput.style.width = "100%";
        searchInput.placeholder = i18n.searchRule;
        searchInput.addEventListener("input", function(e) {
            searchByInput();
        });
        if (location.hash) {
            let hash = location.hash.slice(1);
            if (hash.indexOf("@") == 0) {
                setTimeout(() => {
                    exampleNode.scrollIntoView();
                }, 500);
                searchInput.value = hash.slice(1);
                searchByInput();
            }
        }
        [].forEach.call(ruleList.querySelectorAll("div.highlight"), highlight => {
            highlight.style.position = "relative";
            highlight.innerHTML = highlight.innerHTML + copySvg;
            let svg = highlight.children[1];
            svg.addEventListener("click", function(e) {
                GM_setClipboard(highlight.children[0].innerText);
                svg.style.opacity = 0;
                setTimeout(() => {
                    svg.style.opacity = 1;
                }, 1000);
            });
        });
        exampleNode.parentNode.insertBefore(searchInput, ruleList);


        let donateNode = document.querySelector("[alt='donate']");
        if (!donateNode) return;
        let insertPos = donateNode.parentNode.nextElementSibling;
        let radioIndex = 0;
        function createOption(_name, _value, _type) {
            if (!_type) _type = "input";
            let con = document.createElement("div");
            let option = document.createElement("input");
            let cap = document.createElement("b");
            option.type = _type;
            option.value = _value;
            option.checked = _value;
            cap.style.margin = "0px 10px 0px 0px";
            if (_type == "radio") {
                let label = document.createElement("label");
                label.innerText = _name;
                radioIndex++;
                option.id = "radio" + radioIndex;
                label.setAttribute("for", option.id);
                cap.appendChild(label);
            } else {
                if (_type == "input") {
                    option.style.flexGrow = "1";
                }
                cap.innerText = _name;
            }
            con.style.margin = "10px 0";
            con.style.display = "flex";
            con.style.alignItems = "center";
            con.appendChild(cap);
            con.appendChild(option);
            insertPos.parentNode.insertBefore(con, insertPos);
            return option;
        }
        function formatShortcut(e) {
            let result = [];
            if (e.ctrlKey) {
                result.push("Ctrl");
            }
            if (e.shiftKey) {
                result.push("Shift");
            }
            if (e.altKey) {
                result.push("Alt");
            }
            if (e.metaKey) {
                result.push("Meta");
            }
            result.push(e.key);
            return result.join(" + ");
        }
        function geneShortcutData(str) {
            if (!str) return "";
            let result = {ctrlKey: false, shiftKey: false, altKey: false, metaKey: false, key: ''};
            str.split(" + ").forEach(item => {
                switch(item) {
                    case "Ctrl":
                        result.ctrlKey = true;
                        break;
                    case "Shift":
                        result.shiftKey = true;
                        break;
                    case "Alt":
                        result.altKey = true;
                        break;
                    case "Meta":
                        result.metaKey = true;
                        break;
                    default:
                        result.key = item;
                        break;
                }
            });
            return result;
        }
        let showFilterList = createOption(i18n.showFilterList, !!GM_getValue("showFilterList"), "checkbox");
        let downloadShortcutInput = createOption(i18n.downloadShortcut, formatShortcut(downloadShortcut) || "");
        let downloadSingleShortcutInput = createOption(i18n.downloadSingleShortcut, formatShortcut(downloadSingleShortcut) || "");
        let downloadCustomShortcutInput = createOption(i18n.downloadCustomShortcut, formatShortcut(downloadCustomShortcut) || "");
        downloadShortcutInput.setAttribute("readonly", "true");
        downloadSingleShortcutInput.setAttribute("readonly", "true");
        downloadCustomShortcutInput.setAttribute("readonly", "true");
        downloadShortcutInput.style.cursor = "cell";
        downloadSingleShortcutInput.style.cursor = "cell";
        downloadCustomShortcutInput.style.cursor = "cell";
        let keydonwHandler = e => {
            if (e.key) {
                if (e.key == "Backspace") {
                    e.target.value = "";
                } else if (e.key != "Control" && e.key != "Shift" && e.key != "Alt" && e.key != "Meta") {
                    e.target.value = formatShortcut(e);
                }
            }
            e.preventDefault();
            e.stopPropagation();
        };
        downloadShortcutInput.addEventListener("keydown", keydonwHandler);
        downloadSingleShortcutInput.addEventListener("keydown", keydonwHandler);
        downloadCustomShortcutInput.addEventListener("keydown", keydonwHandler);

        let delSelector = createOption(i18n.del, GM_getValue("selectors") || "");
        delSelector.setAttribute("placeHolder", ".mask,.ksam");
        let downThreadNum = createOption(i18n.downThreadNum, GM_getValue("downThreadNum") || "20", "number");
        let maxDlPerMin = createOption(i18n.maxDlPerMin, GM_getValue("maxDlPerMin") || "0", "number");
        let customTitle = createOption(i18n.customTitle, GM_getValue("customTitle") || "");
        customTitle.setAttribute("placeHolder", "title");
        let minTxtLength = createOption(i18n.minTxtLength, GM_getValue("minTxtLength") || "100", "number");
        let contentSortUrlValue = GM_getValue("contentSortUrl") || false;
        let contentSortValue = GM_getValue("contentSort") || false;
        let reSortDefault = createOption(i18n.reSortDefault, !contentSortUrlValue && !contentSortValue, "radio");
        let reSortUrl = createOption(i18n.reSortUrl, contentSortUrlValue || false, "radio");
        let contentSort = createOption(i18n.reSort, contentSortValue || false, "radio");
        reSortDefault.name = "sort";
        reSortUrl.name = "sort";
        contentSort.name = "sort";
        let reverse = createOption(i18n.reverseOrder, !!GM_getValue("reverse"), "checkbox");
        let disableNextPage = !!GM_getValue("disableNextPage");
        let nextPage = createOption(i18n.nextPage, !disableNextPage, "checkbox");
        let nextPageReg = createOption(i18n.nextPageReg, GM_getValue("nextPageReg") || "");
        let retainImage = createOption(i18n.retainImage, !!GM_getValue("retainImage"), "checkbox");
        nextPageReg.setAttribute("placeHolder", "^\\s*(下一[页頁张張]|next\\s*page|次のページ)");
        if (disableNextPage) {
            nextPageReg.parentNode.style.display = "none";
        }
        nextPage.onclick = e => {
            nextPageReg.parentNode.style.display = nextPage.checked ? "flex" : "none";
        }
        let saveBtn = document.createElement("button");
        saveBtn.innerText = i18n.saveBtn;
        saveBtn.style.margin = "0 0 20px 0";
        insertPos.parentNode.insertBefore(saveBtn, insertPos);
        saveBtn.onclick = e => {
            GM_setValue("selectors", delSelector.value || "");
            GM_setValue("downThreadNum", parseInt(downThreadNum.value || 20));
            GM_setValue("maxDlPerMin", parseInt(maxDlPerMin.value || 20));
            GM_setValue("minTxtLength", parseInt(minTxtLength.value || 100));
            GM_setValue("customTitle", customTitle.value || "");
            if (reSortUrl.checked) {
                GM_setValue("contentSortUrl", true);
                GM_setValue("contentSort", false);
            } else if (contentSort.checked) {
                GM_setValue("contentSortUrl", false);
                GM_setValue("contentSort", true);
                
                
                
            } else {
                GM_setValue("contentSortUrl", false);
                GM_setValue("contentSort", false);
            }
            GM_setValue("reverse", reverse.checked);
            GM_setValue("retainImage", retainImage.checked);
            GM_setValue("showFilterList", showFilterList.checked);
            GM_setValue("disableNextPage", !nextPage.checked);
            GM_setValue("nextPageReg", nextPageReg.value || "");
            GM_setValue("downloadShortcut", geneShortcutData(downloadShortcutInput.value) || "");
            GM_setValue("downloadSingleShortcut", geneShortcutData(downloadSingleShortcutInput.value) || "");
            GM_setValue("downloadCustomShortcut", geneShortcutData(downloadCustomShortcutInput.value) || "");
            alert(i18n.saveOk);
        };
        return;
    }

    function setDel(){
        GM_openInTab(configPage + "#操作說明", {active: true});
    }

    function checkKey(shortcut1, shortcut2) {
        return shortcut1.ctrlKey == shortcut2.ctrlKey && shortcut1.shiftKey == shortcut2.shiftKey && shortcut1.altKey == shortcut2.altKey && shortcut1.metaKey == shortcut2.metaKey && shortcut1.key == shortcut2.key;
    }

    function startCustom() {
        var customRules = GM_getValue("DACrules_" + document.domain);
        var urls = window.prompt(i18n.customInfo, customRules ? customRules : "https://xxx.xxx/book-[20-99].html,     https://xxx.xxx/book-[01-10].html&#34;);    
        if (urls) {
            customDown(urls);
        }
    }

    document.addEventListener("keydown", function(e) {
        if (checkKey(downloadCustomShortcut, e)) {
            startCustom();
        } else if (checkKey(downloadSingleShortcut, e)) {
            fetch(true);
        } else if (checkKey(downloadShortcut, e)) {
            fetch(false);
        }
    });
    GM_registerMenuCommand(i18n.custom, () => {
        startCustom();
    });
    GM_registerMenuCommand(i18n.fetch, fetch);
    GM_registerMenuCommand(i18n.setting, setDel);
    GM_registerMenuCommand(i18n.searchRule, searchRule);
})();
"""
CODE_ST = 58344
CODE_ED = 58715
charset=[
"D",
"在",
"主",
"特",
"家",
"军",
"然",
"表",
"场",
"4",
"要",
"只",
"v",
"和",
"?",
"6",
"别",
"还",
"g",
"现",
"儿",
"岁",
"?",
"?",
"此",
"象",
"月",
"3",
"出",
"战",
"工",
"相",
"o",
"男",
"直",
"失",
"世",
"F",
"都",
"平",
"文",
"什",
"V",
"O",
"将",
"真",
"T",
"那",
"当",
"?",
"会",
"立",
"些",
"u",
"是",
"十",
"张",
"学",
"气",
"大",
"爱",
"两",
"命",
"全",
"后",
"东",
"性",
"通",
"被",
"1",
"它",
"乐",
"接",
"而",
"感",
"车",
"山",
"公",
"了",
"常",
"以",
"何",
"可",
"话",
"先",
"p",
"i",
"叫",
"轻",
"M",
"士",
"w",
"着",
"变",
"尔",
"快",
"l",
"个",
"说",
"少",
"色",
"里",
"安",
"花",
"远",
"7",
"难",
"师",
"放",
"t",
"报",
"认",
"面",
"道",
"S",
"?",
"克",
"地",
"度",
"I",
"好",
"机",
"U",
"民",
"写",
"把",
"万",
"同",
"水",
"新",
"没",
"书",
"电",
"吃",
"像",
"斯",
"5",
"为",
"y",
"白",
"几",
"日",
"教",
"看",
"但",
"第",
"加",
"候",
"作",
"上",
"拉",
"住",
"有",
"法",
"r",
"事",
"应",
"位",
"利",
"你",
"声",
"身",
"国",
"问",
"马",
"女",
"他",
"Y",
"比",
"父",
"x",
"A",
"H",
"N",
"s",
"X",
"边",
"美",
"对",
"所",
"金",
"活",
"回",
"意",
"到",
"z",
"从",
"j",
"知",
"又",
"内",
"因",
"点",
"Q",
"三",
"定",
"8",
"R",
"b",
"正",
"或",
"夫",
"向",
"德",
"听",
"更",
"?",
"得",
"告",
"并",
"本",
"q",
"过",
"记",
"L",
"让",
"打",
"f",
"人",
"就",
"者",
"去",
"原",
"满",
"体",
"做",
"经",
"K",
"走",
"如",
"孩",
"c",
"G",
"给",
"使",
"物",
"?",
"最",
"笑",
"部",
"?",
"员",
"等",
"受",
"k",
"行",
"一",
"条",
"果",
"动",
"光",
"门",
"头",
"见",
"往",
"自",
"解",
"成",
"处",
"天",
"能",
"于",
"名",
"其",
"发",
"总",
"母",
"的",
"死",
"手",
"入",
"路",
"进",
"心",
"来",
"h",
"时",
"力",
"多",
"开",
"已",
"许",
"d",
"至",
"由",
"很",
"界",
"n",
"小",
"与",
"Z",
"想",
"代",
"么",
"分",
"生",
"口",
"再",
"妈",
"望",
"次",
"西",
"风",
"种",
"带",
"J",
"?",
"实",
"情",
"才",
"这",
"?",
"E",
"我",
"神",
"格",
"长",
"觉",
"间",
"年",
"眼",
"无",
"不",
"亲",
"关",
"结",
"0",
"友",
"信",
"下",
"却",
"重",
"己",
"老",
"2",
"音",
"字",
"m",
"呢",
"明",
"之",
"前",
"高",
"P",
"B",
"目",
"太",
"e",
"9",
"起",
"稜",
"她",
"也",
"W",
"用",
"方",
"子",
"英",
"每",
"理",
"便",
"四",
"数",
"期",
"中",
"C",
"外",
"样",
"a",
"海",
"们",
"任"
]

headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'
        }



# 设置data文件夹的路径
data_dir = os.path.join(script_dir, 'data')

# 检查data文件夹是否存在，如果不存在则创建
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# 设置bookstore文件夹的路径
bookstore_dir = os.path.join(data_dir,'bookstore')

# 检查bookstore文件夹是否存在，如果不存在则创建
if not os.path.exists(bookstore_dir):
    os.makedirs(bookstore_dir)

# 更新record.json和config.json的文件路径
record_path = os.path.join(data_dir, 'record.json')
config_path = os.path.join(data_dir, 'config.json')

config_path = os.path.join(data_dir, 'config.json')
if not os.path.exists(config_path):
    if os.path.exists('config.json'):
        os.replace('config.json',config_path)
    else:
        with open(config_path, 'w', encoding='UTF-8') as f:
            json.dump({'kg': 0}, f)
else:
    with open(config_path, 'r', encoding='UTF-8') as f:
        config = json.load(f)

# 检查并创建记录文件record.json
record_path = os.path.join(data_dir, 'record.json')
if not os.path.exists(record_path):
    if os.path.exists('record.json'):
        os.replace('record.json',record_path)
    else:
        with open(record_path, 'w', encoding='UTF-8') as f:
            json.dump([], f)


def print_text(text, delay=0.001):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)

def safe_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)


def main(re=None):
    print("正在检查更新...")
    Version_updates()


    welcome_message = """
    欢迎使用小说下载器！


    本程序由YQY开发，是一个功能强大的工具，专为小说爱好者设计，让您能够轻松下载您喜爱的小说。无论是想要一次性保存整部小说，还是逐章阅读，我们都能提供相应的解决方案

    特点：
    - 支持多种下载模式，包括合并下载和分章下载
    - 智能解析小说目录，自动获取所有章节链接
    - 用户友好的命令行界面，简单易用

    在使用本程序之前，请确保您已经阅读并理解了相关的版权法律和网站使用条款，我们强烈建议您只下载那些允许下载的内容
    请注意，本程序仅供学习交流使用，不得用于商业用途，否则后果自负
    本程序在使用中selenium会输出一些乱码，请放心忽略
    本程序每一步过程都有提醒和注释，请仔细阅读
    现在，深呼吸，放松心情，让我们开始您的小说下载之旅
    按Enter键继续...
        """
    print_text(welcome_message.strip())
    input()

    print("请选择下载脚本：")
    print("1. 使用下载脚本1（下载速度飘忽不定，支持番茄小说下载）")
    time.sleep(0.1)
    print("2. 使用下载脚本2（速度快，推荐，不支持番茄小说下载）")
    time.sleep(0.1)
    print("3. 使用uncle小说下载器（下载速度最快，最好用，不支持番茄小说下载）")
    time.sleep(0.1)
    print("4. 番茄小说下载器（支持番茄小说下载）")
    time.sleep(0.1)
    print("5. 小说阅读器")
    time.sleep(0.1)
    print("6. 下载脚本子程序：小说分割器")
    time.sleep(0.1)
    print("7. 下载脚本子程序：文本编码转换器")
    time.sleep(0.1)
    print("8.epub、azw3、mobi格式转换器")
    time.sleep(0.1)
    print("9. 下载作者库中现有小说")
    time.sleep(0.1)
    print("10. 退出程序")
    time.sleep(0.1)
    choice = input("请输入您的选择（1~9）: ").strip()

    if choice == '1':
        script_dir = os.path.dirname(os.path.realpath(__file__))
        driver_path = os.path.abspath(os.path.join(script_dir, 'msedgedriver.exe'))

        if not os.path.isfile(driver_path):
            print(f"找不到WebDriver: {driver_path}")
            sys.exit(1)
        # 使用下载脚本1
        download_script1()
    elif choice == '2':
        script_dir = os.path.dirname(os.path.realpath(__file__))
        driver_path = os.path.abspath(os.path.join(script_dir, 'msedgedriver.exe'))

        if not os.path.isfile(driver_path):
            print(f"找不到WebDriver: {driver_path}")
            sys.exit(1)
        # 使用下载脚本2
        download_script2()

    elif choice == '3':
        browser.quit()
        Download_instructions = """
Uncle小说PC版为主要开发版本，提供了较为完善的功能，经历5次大版本迭代升级。主要包含功能有:
Uncle Novel PC version is the main development version, offering a more complete set of features, having undergone five major version iterations and upgrades. The main features include:
搜书文本小说
Search for text novels
搜书有声小说
Search for audio novels
全网搜书
Search across the web
文本小说书架
Text novel bookshelf
文本小说阅读器
Text novel reader
有声小说书架
Audio novel bookshelf
解析下载
Parsing and downloading
下载管理
Download management
书源管理
Book source management
软件设置
Software settings
全局热键
Global hotkeys
主题定制
Theme customization
国际化支持
Internationalization support
备份与恢复（WebDav）
Backup and recovery (WebDav)
#搜索小说
Searching for Novels
有声与文本小说的搜索都是基于书源进行，如果没有书源则无法进行搜索。但在没有规则的情况下可以进行文本小说的全网搜索，通过搜索引擎进行搜索小说，然后进行目录解析。
Both audio and text novel searches are based on book sources. Without sources, searches cannot be conducted. However, without rules, you can perform a web-wide search for text novels, search through search engines, and then parse the novel catalog.

#小说书架
Novel Bookshelf
分组管理（分组更新最新章节）
Group management (updates the latest chapters in groups)
导入本地小说（TXT）
Import local novels (TXT) Text novels can be added to the bookshelf for reading
文本小说可以加入书架进行阅读，书架能够进行书籍分组管理及分组更新，一键更新分组内的所有小说。也可以导入本地TXT格式的小说到书架然后进行阅读。
The bookshelf supports group management and updating, allowing you to update all novels in a group with one click. You can also import local TXT format novels to the bookshelf for reading.

#小说阅读器
Novel Reader
主题定制
Theme customization
页宽、行间距、字体大小、自定义字体、字体排版
Page width, line spacing, font size, custom fonts, font layout
TTS朗读
TTS reading
沉浸式阅读,阅读器采用分页与横切动画的方式，翻页阅读。
Immersive reading The reader uses page-turning and horizontal cutting animations for flipping pages



#有声书架
Audio Bookshelf
与音乐播放器相差无几，能够在线收听有声小说，支持收听进度记录。
Similar to a music player, it can play audio novels online and supports recording listening progress.

#解析下载
Parsing and Downloading
解析下载为软件的核心功能，能够对全网小说网站的小说目录进行解析，然后提取正文，最终可以选择加入书架或者直接下载。
Parsing and downloading is a core feature of the software. It can parse the novel catalog of novel websites across the web, extract the text, and finally choose to add it to the bookshelf or download it directly.

#下载管理
Download Management
下载管理可以对下载进度进行实时查看，也可以查看下载历史。
Download management allows real-time viewing of download progress and viewing of download history.

任务进行时如果下载失败可以手动重试，直到全部都下载成功为止。
During the task, if a download fails, you can manually retry it until all downloads are successful.

多线程
Multi-threading
多任务
Multi-tasking
失败重试
Retry on failure
断点续传
Resume interrupted downloads
多种格式（EPUB、TXT、MOBI）
Various formats (EPUB, TXT, MOBI)

#书源管理
Book Source Management
规则解析模块，用户通过自己设定一些爬虫规则，进行小说的精确抓取，同时支持对书源的实时调试。
A rule parsing module where users can set some crawler rules for precise capture of novels, and also support real-time debugging of book sources.

具体可以查看书源规则编写教程。
You can refer to the book source rule writing tutorial for details.

#备份与恢复
Backup and Recovery
采用WebDav进行数据同步，也可以直接导出备份数据文件。
Data synchronization is done using WebDav, and you can also directly export backup data files.

在多台电脑间阅读同一本小说时，可以利用此功能同步阅读进度。
When reading the same novel on multiple computers, you can use this feature to synchronize reading progress.
        
        
        """
        # 检查Uncle小说下载器的可执行文件是否存在
        base_path = "C:\\Program Files (x86)\\Fanqie Novel Downloader 2.1.9\\Download Model 3"

        # 使用os.path.join来构建正确的路径
        uncle_exe_path = os.path.join(base_path, "Uncle小说.exe")

        # 构建Uncle.exe的正确路径
        if not os.path.isfile(uncle_exe_path):
            print(f"未找到Uncle小说下载器的可执行文件：{uncle_exe_path}")
            return

        # 启动Uncle小说下载器
        try:
            print("正在启动Uncle小说下载器...\nLaunching Uncle Novel Downloader...")
            print_text(Download_instructions.strip())
            subprocess.run(uncle_exe_path, check=True)
        except subprocess.CalledProcessError as e:
            print(f"启动Uncle小说下载器时出错：{e}")
        except FileNotFoundError:
            print(f"找不到Uncle小说下载器的可执行文件：{uncle_exe_path}")

    elif choice == '4':
        browser.quit()
        script_dir = os.path.dirname(os.path.realpath(__file__))
        def filencl(s):
            a = ''
            for i in s:
                if i == '*':
                    a += '＊'
                elif i == '/':
                    a += '／'
                elif i == '\\':
                    a += '＼'
                elif i == '?':
                    a += '？'
                elif i == ':':
                    a += '：'
                elif i == '>':
                    a += '＞'
                elif i == '<':
                    a += '＜'
                elif i == '"':
                    a += '＂'
                elif i == '|':
                    a += '｜'
                else:
                    a += i
            return a

        def down_zj(it):
            global headers
            an = {}
            ele = etree.HTML(req.get('https://fanqienovel.com/page/' + str(it), headers=headers).text)
            a = ele.xpath('//div[@class="chapter"]/div/a')
            for i in range(len(a)):
                an[a[i].text] = a[i].xpath('@href')[0].split('/')[-1]
            if ele.xpath('//h1/text()') == []:
                return ['err', 0, 0]
            return [filencl(ele.xpath('//h1/text()')[0]), an, ele.xpath('//span[@class="info-label-yellow"]/text()')]

        def interpreter(uni):
            global CODE_ST, charset
            bias = uni - CODE_ST
            if bias < 0 or bias >= len(charset) or charset[bias] == '?':
                return chr(uni)
            return charset[bias]

        def down_text(it):
            global CODE_ST, CODE_ED, headers
            headers2 = headers
            headers2['cookie'] = 'novel_web_id=7357767624615331362'
            while True:
                res = req.get('https://fanqienovel.com/api/reader/full?itemId=' + str(it), headers=headers2)
                n = json.loads(res.text)['data']
                if 'chapterData' in n:
                    break
                time.sleep(0.5)
            n = n['chapterData']['content']
            s = ''
            for i in range(len(n)):
                uni = ord(n[i])
                if CODE_ST <= uni <= CODE_ED:
                    s += interpreter(uni)
                else:
                    s += n[i]
            return s.replace('<\/p>', '').replace('<p>', '').replace('</p>', '\n')

        def sanitize_filename(filename):
            illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
            illegal_chars_rep = ['＜', '＞', '：', '＂', '／', '＼', '｜', '？', '＊']
            for i in range(len(illegal_chars)):
                filename = filename.replace(illegal_chars[i], illegal_chars_rep[i])
            return filename

        def down_book(book_id, config_obj, mode=1):
            name, zj, zt = down_zj(book_id)
            if name == 'err':
                return 'err'
            zt = zt[0]

            safe_name = sanitize_filename(name)
            print(f'\n开始下载或更新《{safe_name}》，状态‘{zt}’')

            folder_path = os.path.join(script_dir, safe_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            book_json_path = os.path.join(bookstore_dir, f'{safe_name}.json')

            # 尝试加载现有的JSON文件，如果不存在则创建一个空字典
            if os.path.exists(book_json_path):
                with open(book_json_path, 'r', encoding='UTF-8') as json_file:
                    ozj = json.load(json_file)
            else:
                ozj = {}

            # 存储新下载或更新的章节
            updated_chapters = {}

            # 检查并下载/更新章节内容
            for chapter_title, chapter_href in zj.items():
                # 如果章节未下载或内容已更新，则下载/更新章节
                if chapter_href not in ozj or ozj[chapter_href] != down_text(chapter_href):
                    print(f'下载或更新 {chapter_title}')
                    chapter_content = down_text(chapter_href)
                    updated_chapters[chapter_href] = {
                        'title': chapter_title,
                        'content': chapter_content
                    }

            # 如果有章节更新，保存更新到JSON文件
            if updated_chapters:
                new_zj = ozj.copy()
                new_zj.update(updated_chapters)
                with open(book_json_path, 'w', encoding='UTF-8') as json_file:
                    json.dump(new_zj, json_file, ensure_ascii=False)
            else:
                print("没有章节需要更新。")

            # 根据模式写入文件
            if mode == 1:  # 正常模式 - 整本小说保存到一个文件
                # 写入所有章节到一个文件
                text_file_path = os.path.join(script_dir, f'{safe_name}.txt')
                with open(text_file_path, 'w', encoding='UTF-8') as text_file:
                    fg = '\n' + ' ' * config_obj['kg']
                    for chapter_href, chapter_data in new_zj.items():
                        text_file.write(chapter_data['title'] + fg)
                        text_file.write(chapter_data['content'].replace('\n', fg) + '\n')

            elif mode == 2:  # 分章保存模式 - 每个章节保存为单独的文件
                # 只保存更新的章节为单独的文件
                for chapter_href, chapter_data in updated_chapters.items():
                    chapter_file_name = f"{sanitize_filename(chapter_data['title'])}.txt"
                    chapter_file_path = os.path.join(folder_path, chapter_file_name)
                    with open(chapter_file_path, 'w', encoding='UTF-8') as chapter_file:
                        chapter_file.write(chapter_data['content'])

            return zt

        print('本程序完全免费。\nGithub: https://github.com/ying-ck/fanqienovel-downloader\n作者：Yck & Yqy')
        while True:
            print("\n请选择操作：")
            print("1. 下载新书")
            print("2. 更新小说")
            print("3. 设置正文段首空格数")
            print("4. 退出程序")

            operation = input()

            if operation == '2':
                # 更新小说列表的逻辑
                # 这里可以调用down_book函数，传入需要更新的书籍ID列表
                with open(record_path, 'r', encoding='UTF-8') as f:
                    records = json.load(f)
                for book_id in records:
                    status = down_book(book_id, config)
                    if status == 'err' or status == '已完结':
                        records.remove(book_id)
                with open(record_path, 'w', encoding='UTF-8') as f:
                    json.dump(records, f)
                print('更新完成')

            elif operation == '1':
                print("\n选择下载模式：")
                print("1. 正常模式 - 下载整本小说到一个文件")
                print("2. 分章保存模式 - 每个章节保存为单独的文件")

                mode = input("请输入选择的模式（1-2）：")
                if mode in ['1', '2']:
                    book_id = int(input("请输入要下载的书籍ID："))
                    with open(config_path, 'r', encoding='UTF-8') as f:
                        config = json.load(f)
                    status = down_book(book_id, config, int(mode))
                    if status == 'err':
                        print('找不到此书或下载过程中出现错误。')
                    else:
                        print('下载完成。')
                else:
                    print("无效的模式输入，请输入1或2。")

            elif operation == '3':
                # 设置正文段首空格数
                print("\n当前正文段首空格数：", config['kg'])
                new_kg = input("请输入新的正文段首空格数（0表示无空格）：")
                try:
                    new_kg = int(new_kg)
                    with open(config_path, 'r', encoding='UTF-8') as f:
                        config_data = json.load(f)
                    config_data['kg'] = new_kg
                    with open(config_path, 'w', encoding='UTF-8') as f:
                        json.dump(config_data, f)
                    print("正文段首空格数已更新。")
                except ValueError:
                    print("输入无效，请输入一个整数。")

            elif operation == '4':
                print("退出程序。")
                break

            else:
                print("无效的操作选项，请输入1、2或3。")
    elif choice == '5':
        browser.quit()
        # 使用Tkinter打开文件选择对话框
        root = Tk()
        root.withdraw()  # 隐藏主窗口
        file_path = filedialog.askopenfilename(
            title="选择TXT文件",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
            parent=root
        )
        if not file_path:
            print("未选择文件，程序将退出。")
            return

        pattern = r'第[0-9一二三四五六七八九十百千万零一二三四五六七八九十]+\s*章|番外'  # 分割模式
        temp_dir, chapters = create_temp_folder_and_split_novel(file_path, pattern)

        if not chapters:
            print("没有找到章节，程序将退出。")
            return

        # 显示章节列表
        print("\n可用章节列表：")
        for chapter_number, chapter_title in enumerate(chapters, start=1):
            title = chapter_title.split('\n')[0]  # 假设章节标题是第一行
            print(f"{chapter_number}. {title}")

        current_chapter = 1  # 初始化当前章节编号
        while True:
            display_chapter(chapters, current_chapter)
            input_action = input("\n按 Enter 跳转到下一章，或输入章节编号，或输入 'D' 删除临时文件夹并退出：\nPress Enter to jump to the next chapter, or enter the chapter number, or type 'D' to delete the temporary folder and exit.")
            if input_action.strip().lower() == 'd':
                shutil.rmtree(temp_dir)
                print("临时文件夹已删除。\nThe temporary folder has been deleted.")
                break  # 退出循环
            elif input_action == '':
                current_chapter += 1
                if current_chapter > len(chapters):
                    current_chapter = 1  # 循环回到第一章
            else:
                try:
                    new_chapter = int(input_action)
                    display_chapter(chapters, new_chapter)
                    current_chapter = new_chapter
                except ValueError:
                    print("无效输入，请输入章节编号或按 Enter 跳转到下一章，或输入 'D' 删除临时文件夹并退出。\nInvalid input. Please enter the chapter number or press Enter to go to the next chapter, or type 'D' to delete the temporary folder and exit.")

    elif choice == '6':
        browser.quit()
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        file_path = filedialog.askopenfilename(
            title="选择TXT文件",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
            parent=root
        )

        if not file_path:
            print("未选择文件，程序将退出。")
            return

        # 获取文件名（不包含扩展名）
        base_name = os.path.splitext(os.path.basename(file_path))[0]

        # 创建保存章节的文件夹
        save_dir = f"{base_name}"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # 定义分割模式，匹配文件名中的章节信息
        pattern = r'第[0-9一二三四五六七八九十百千万零一二三四五六七八九十]+\s*章|番外'

        # 读取并分割章节
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            chapters = re.split(pattern, content)

        # 移除空章节
        chapters = [chapter.strip() for chapter in chapters if chapter.strip()]

        if not chapters:
            print("没有找到章节，程序将退出。")
            return

        # 保存每个章节为单独的文件
        for i, chapter in enumerate(chapters, start=1):
            if chapter:  # 确保章节内容不为空
                chapter_title = chapter.split('\n', 1)[0]  # 假设章节标题是第一行
                chapter_content = chapter.split('\n', 1)[1] if chapter.count('\n') > 1 else chapter
                chapter_filename = f"第{i}章 - {chapter_title}.txt"
                chapter_filename = safe_filename(chapter_filename)  # 清理文件名
                chapter_filepath = os.path.join(save_dir, chapter_filename)

                # 确保文件路径正确
                print(f"正在保存文件：{chapter_filepath}")

                # 写入文件
                with open(chapter_filepath, 'w', encoding='utf-8') as chapter_file:
                    chapter_file.write(chapter_content)

                # 检查文件是否成功保存
                if os.path.exists(chapter_filepath):
                    print(f"文件已保存：{chapter_filepath}")
                    file_size = os.path.getsize(chapter_filepath)
                    print(f"文件大小：{file_size} 字节")
                else:
                    print(f"文件保存失败：{chapter_filepath}")
        print("正在检查文件...")

        # 检查所有分割后的文件，删除文件大小为0的文件
        all_files = os.listdir(save_dir)

        # 遍历所有文件
        for file_name in all_files:
            file_path = os.path.join(save_dir, file_name)

            # 检查文件是否存在
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)

                # 检查文件大小是否为0
                if file_size == 0:
                    os.remove(file_path)  # 删除文件
                    print(f"删除了大小为0的文件：{file_path}\nDeleted a file with a size of 0:{file_path}")
        input("按Enter退出程序...\nPress Enter to exit the program...")

    elif choice == '7':
        browser.quit()
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口

        # 选择文件
        file_path1 = filedialog.askopenfilename()
        if not file_path1:
            print("未选择文件")
            return

        # 检测文件编码
        print("正在检测文件编码类型...")
        encoding = chardet.detect(open(file_path1, 'rb').read())['encoding']

        # 显示文件编码
        print(f"文件编码类型为: {encoding}")

        # 用户选择转换编码
        encoding_options = {
            '1': 'utf-8',
            '2': 'utf-16',
            '3': 'CP936'
        }
        print("选择需要转换编码的类型：\nSelect the type of encoding you need to convert: ")
        for key, value in encoding_options.items():
            print(f"{key}. {value}")

        choice = input("请输入选项：")
        if choice not in encoding_options:
            print("无效的编码类型")
            return

        new_encoding = encoding_options[choice]
        new_file_path = os.path.splitext(file_path1)[0] + f"(已转换为{new_encoding}编码).txt"

        # 转换编码并保存新文件
        try:
            with open(file_path1, 'r', encoding=encoding) as f:
                content = f.read()

            # HTML实体编码
            print("正在进行HTML实体编码...")
            encoded_content = html.escape(content, quote=True)

            # 尝试使用目标编码编码内容，替换无法编码的字符
            new_encoded_content = encoded_content.encode(new_encoding, 'replace').decode(new_encoding)

            # HTML实体解码
            print("正在进行HTML实体解码...")
            decoded_content = html.unescape(new_encoded_content)

            # 写入解码后的内容到新文件
            print("正在写入新文件...")
            with open(new_file_path, 'w', encoding=new_encoding) as f:
                f.write(decoded_content)

            print(f"文件编码转换成功并完成HTML实体解码，新文件路径：{new_file_path}")
            input("按任意键退出程序...")
            return
        except Exception as e:
            print("文件编码转换或HTML实体解码失败")
            print(f"错误信息：{e}")
            input("按任意键退出程序...")
            return

    elif choice == '8':
        browser.quit()
        print("程序将txt文件转换为epub、azw3、mobi文件")
        root = Tk()
        root.withdraw()  # 隐藏主窗口
        # 弹出文件选择对话框，选择TXT文件
        txt_file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if txt_file_path:
            # 调用函数打开TXT文件
            open_txt_with_kaf_cli(txt_file_path)
        else:
            print("No file selected.")

    elif choice == '9':
        browser.quit()
        print("请选择你要下载的小说：")
        print("1.学姐别怕，我来保护你")
        print("2.我靠打爆学霸兑换黑科技")
        print("3.趁校花青涩，哄回家做老婆")
        choice = input("请输入您的选择:").strip()
        if choice == '1':
            def main1():
                while True:
                    print("请选择以下操作：")
                    print("1. 进入正常模式 - 下载整本小说到一个文件")
                    print("2. 进入分章保存模式 - 每个章节保存为单独的文件")
                    print("3. 进入Debug模式 - 打印调试信息")
                    print("4. 退出程序")
                    user_input = input("请输入您的选择（1~4）:（默认“1”）")

                    if user_input == '4':
                        print("程序已退出。")
                        break

                    try:
                        user_input = int(user_input)
                        if user_input < 1 or user_input > 4:
                            print("无效的输入，请输入1到4之间的数字。")
                            continue

                        novel_directory_url = 'http://www.xsbiquge.la/book/37389'

                        chapter_urls, chapter_names = get_novel_info(novel_directory_url)
                        if not chapter_urls or not chapter_names:
                            print("无法获取小说章节信息，请检查网址是否正确。")
                            continue

                        output_dir = get_save_directory()  # 修正为正确的函数名
                        if user_input == 1:
                            download_chapters1(chapter_urls, chapter_names, output_dir, 'complete')
                        elif user_input == 2:
                            download_chapters1(chapter_urls, chapter_names, output_dir, 'separate')
                        elif user_input == 3:
                            debug_mode(novel_directory_url)
                    except ValueError:
                        print("无效的输入，请输入数字。")

            if __name__ == "__main__":
                main1()
        elif choice == '2':
            def main2():
                while True:
                    print("请选择以下操作：")
                    print("1. 进入正常模式 - 下载整本小说到一个文件")
                    print("2. 进入分章保存模式 - 每个章节保存为单独的文件")
                    print("3. 进入Debug模式 - 打印调试信息")
                    print("4. 退出程序")
                    user_input = input("请输入您的选择（1~4）:（默认“1”）")

                    if user_input == '4':
                        print("程序已退出。")
                        break

                    try:
                        user_input = int(user_input)
                        if user_input < 1 or user_input > 4:
                            print("无效的输入，请输入1到4之间的数字。")
                            continue

                        novel_directory_url = 'https://www.bqzw789.org/620/620227/'

                        chapter_urls, chapter_names = get_novel_info2(novel_directory_url)
                        if not chapter_urls or not chapter_names:
                            print("无法获取小说章节信息，请检查网址是否正确。")
                            continue

                        output_dir = get_save_directory()  # 修正为正确的函数名
                        if user_input == 1:
                            download_chapters2(chapter_urls, chapter_names, output_dir, 'complete')
                        elif user_input == 2:
                            download_chapters2(chapter_urls, chapter_names, output_dir, 'separate')
                        elif user_input == 3:
                            debug_mode(novel_directory_url)
                    except ValueError:
                        print("无效的输入，请输入数字。")

            if __name__ == "__main__":
                main2()
        elif choice == '3':
            def main3():
                while True:
                    print("请选择以下操作：")
                    print("1. 进入正常模式 - 下载整本小说到一个文件")
                    print("2. 进入分章保存模式 - 每个章节保存为单独的文件")
                    print("3. 进入Debug模式 - 打印调试信息")
                    print("4. 退出程序")
                    user_input = input("请输入您的选择（1~4）:（默认“1”）")

                    if user_input == '4':
                        print("程序已退出。")
                        break

                    try:
                        user_input = int(user_input)
                        if user_input < 1 or user_input > 4:
                            print("无效的输入，请输入1到4之间的数字。")
                            continue

                        novel_directory_url = 'https://www.biquge.hk/book/2503200/'

                        chapter_urls, chapter_names = get_novel_info1(novel_directory_url)
                        if not chapter_urls or not chapter_names:
                            print("无法获取小说章节信息，请检查网址是否正确。")
                            continue

                        output_dir = get_save_directory()  # 修正为正确的函数名
                        if user_input == 1:
                            download_chapters3(chapter_urls, chapter_names, output_dir, 'complete')
                        elif user_input == 2:
                            download_chapters3(chapter_urls, chapter_names, output_dir, 'separate')
                        elif user_input == 3:
                            debug_mode(novel_directory_url)
                    except ValueError:
                        print("无效的输入，请输入数字。")

            if __name__ == "__main__":
                main3()

    elif choice == '10':
        return


def download_script1():
    global file_path
    folder = r'C:\Users\Administrator\Downloads'  # 设置下载文件夹路径
    file_extension = '.txt'
    pattern = r'第[0-9一二三四五六七八九十百千万零一二三四五六七八九十]+\s*章|番外'

    book_id = search()

    # 使用获取到的小说ID构造小说页面的URL
    novel_url = f"https://fanqienovel.com/page/{book_id}"
    print_text("稍后将打开您选择的小说，还有5秒\nThe novel you have selected will open shortly. You have 5 seconds remaining.".strip())
    time.sleep(5)
    print_text(f"\n正在打开您选择的小说： {novel_url}".strip())
    # 使用Selenium打开浏览器并访问小说链接
    try:
        browser.get(novel_url)
        # 等待直到页面加载完成
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
    except Exception as e:
        print(f"加载小说页面失败：{e}")
        return
    input("\n稍后将打开浏览器链接,请您确认万无一失后，按下Enter...\nPlease confirm everything is in order, and then press Enter...")

        # 打开Microsoft Edge Tampermonkey插件链接
    tampermonkey_addon_url = "https://microsoftedge.microsoft.com/addons/detail/%E7%AF%A1%E6%94%B9%E7%8C%B4/iikmkjmpaadaobahmlepeloendndfphd"
    browser.execute_script(f"window.open('{tampermonkey_addon_url}');")

    # 等待新窗口加载完成
    WebDriverWait(browser, 10).until(
        lambda driver: len(driver.window_handles) > 1
    )

    # 切换到新打开的窗口
    all_window_handles = browser.window_handles
    browser.switch_to.window(all_window_handles[-1])

    # 等待页面完全加载
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )

    # 定位到“获取”按钮并执行点击操作
    install_button_xpath = '//*[@id="getOrRemoveButton-iikmkjmpaadaobahmlepeloendndfphd"]/span/div'
    try:
        install_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, install_button_xpath))
        )
        ActionChains(browser).move_to_element(install_button).click().perform()
    except Exception as e:
        print(f"点击'获取'按钮时发生错误: {e}")

    print_text(
        "稍后将输出油猴脚本内容，请确保浏览器正常打开了网页\nEnsure that your browser is properly opened to output the Greasemonkey script content.".strip())
    print_text("脚本内容将在5秒后输出\nThe script content will be output in 5 seconds.".strip())
    time.sleep(5)
    print_text(
        "\n以下是油猴脚本内容，程序已将脚本复制到您的剪切板，若没有复制成功，您也可以将本程序输出的脚本复制并添加到Tampermonkey中:\nBelow is the Greasemonkey script content. The program has copied the script to your clipboard. If the copy was not successful, you can also copy the script output by this program and add it to Tampermonkey:".strip())
    print_text("或者在打开的网页中点击安装\nOr click to install in the opened web page.".strip())
    pyperclip.copy(user_script1)
    print(user_script1)
    user_script1_link = "https://greasyfork.org/zh-CN/scripts/490331-%E6%9B%B4%E6%8D%A2api-%E7%95%AA%E8%8C%84%E5%85%A8%E6%96%87%E5%9C%A8%E7%BA%BF%E5%85%8D%E8%B4%B9%E8%AF%BB"
    browser.execute_script(f"window.open('{user_script1_link}');")

    print_text(
        "以上就是脚本的代码,可以复制到篡改猴新建脚本的方框\nThe above is the script code, which can be copied to the Tampermonkey new script box.".strip())
    print_text(
        "请注意：程序稍后将输出一些乱码或错误(如：[Error: It's a bug for...])\nPlease note: The program will later output some garbled text or errors (such as: [Error: It's a bug for...])".strip())
    print_text(
        "这些错误可以忽略，不影响脚本运行\nThese errors can be ignored and do not affect the operation of the script.".strip())
    using_model = """
    请在打开的greasyfork网页中,点击“安装”按钮(请注意：请确保Tampermonkey插件已安装),安装完成后，请切换到番茄小说页面，按Ctrl+R刷新页面
    Please click the 'Install' button on the opened Greasy Fork web page (Note: Make sure the Tampermonkey extension is installed).After the installation is complete, switch to the Fanqie Novel page and press Ctrl+R to refresh the page.
    会发现屏幕上多了一个方框，请点击方框中的“下载全部章节”按钮，脚本将自动下载小说
    You will find a box on the screen, please click the 'Download All Chapters' button in the box, and the script will automatically download the novel.
    等待时间可能稍长，请耐心等待
    Waiting time may be a bit long, please be patient.
    若脚本下载框一直不动，请重启本程序
    If the script download box remains still, please restart this program.
    """
    print_text(using_model.strip())
    input("下载完后按Enter继续...")
    browser.quit()

    downloaded_files = [f for f in os.listdir(folder) if f.endswith(file_extension)]
    if downloaded_files:
        print("检测到下载的小说文件。")
        print("请选择目标编码（默认为utf-8）:")
        encodings = {
            '1': 'utf-8',
            '2': 'utf-16',
            '3': 'cp936'
        }
        for code, enc in encodings.items():
            print(f"{code}. {enc}")

        choice = input("请输入编码对应的编号：")
        target_encoding = encodings.get(choice, 'utf-8')  # 默认为utf-8
        print(f"您选择的编码是：{target_encoding}")

        for file in downloaded_files:
            file_path = os.path.join(folder, file)
            # 转换文件编码
            split_novel(file_path, pattern, target_encoding)  # 分割小说文件
    else:
        print("未检测到小说文件，请确保文件已下载到当前文件夹。")


def download_script2():
    global file_path
    folder = r'C:\Users\Administrator\Downloads'  # 设置下载文件夹路径
    file_extension = '.txt'
    pattern = r'第[0-9一二三四五六七八九十百千万零一二三四五六七八九十]+\s*章|番外'
    print_text(
        "在使用‘下载脚本2’前，请您悉知：本下载方式需要您自己打开需要下载小说的网站，并导航到小说的目录页面，在进行下一步操作。\nBefore using 'Download Script 2', please be aware: This download method requires you to open the website of the novel you want to download yourself and navigate to the novel's catalog page before proceeding to the next step.".strip())
    print_text(
        "在打开了您要下载的网页后，并确定安装好脚本后按下Ctrl+F9下载小说。\nAfter opening the webpage you want to download and ensuring that the script is installed, press Ctrl+F9 to download the novel.".strip())
    print_text("稍后将打开浏览器链接。\nThe browser link will open shortly.".strip())
    input("请您确认万无一失后，按下Enter...")

    # 打开Microsoft Edge Tampermonkey插件链接
    tampermonkey_addon_url = "https://microsoftedge.microsoft.com/addons/detail/%E7%AF%A1%E6%94%B9%E7%8C%B4/iikmkjmpaadaobahmlepeloendndfphd"
    browser.execute_script(f"window.open('{tampermonkey_addon_url}');")

    # 等待新窗口加载完成
    WebDriverWait(browser, 10).until(
        lambda driver: len(driver.window_handles) > 1
    )

    # 切换到新打开的窗口
    all_window_handles = browser.window_handles
    browser.switch_to.window(all_window_handles[-1])

    # 等待页面完全加载
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "h1"))
    )

    # 定位到“获取”按钮并执行点击操作
    install_button_xpath = '//*[@id="getOrRemoveButton-iikmkjmpaadaobahmlepeloendndfphd"]/span/div'
    try:
        install_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, install_button_xpath))
        )
        ActionChains(browser).move_to_element(install_button).click().perform()
    except Exception as e:
        print(f"点击'获取'按钮时发生错误: {e}")

    print_text(
        "稍后将输出油猴脚本内容，请确保浏览器正常打开了网页\nThe script content will be output shortly, please ensure your browser is properly opened.".strip())
    print_text("脚本内容将在5秒后输出\nThe script content will be output in 5 seconds.".strip())
    time.sleep(5)
    print_text(
        "\n以下是油猴脚本内容，程序已将脚本复制到您的剪切板，若没有复制成功，您也可以将本程序输出的脚本复制并添加到Tampermonkey中：\nBelow is the Greasemonkey script content. The program has copied the script to your clipboard. If the copy was not successful, you can also copy the script output by this program and add it to Tampermonkey:".strip())
    print_text("或者在打开的网页中点击安装\nOr click to install in the opened web page.".strip())

    user_script2_link = "https://greasyfork.org/zh-CN/scripts/25068-downloadallcontent"
    browser.execute_script(f"window.open('{user_script2_link}');")
    pyperclip.copy(user_script2)
    print(user_script2)
    print_text(
        "以上就是脚本的代码，可以复制到篡改猴新建脚本的方框\nThe above is the script code, which can be copied to the Tampermonkey new script box.".strip())
    print_text(
        "请注意：程序稍后将输出一些乱码或错误(如：[Error: It's a bug for...])\nPlease note: The program will later output some garbled text or errors (su"
        ""
        "ch as: [Error: It's a bug for...])".strip())
    print_text(
        "这些错误可以忽略，不影响脚本运行\nThese errors can be ignored and do not affect the operation of the script.".strip())
    browser.quit()

    downloaded_files = [f for f in os.listdir(folder) if f.endswith(file_extension)]
    if downloaded_files:
        print("检测到下载的小说文件。")
        print("请选择目标编码（默认为utf-8）:")
        encodings = {
            '1': 'utf-8',
            '2': 'utf-16',
            '3': 'cp936'
        }
        for code, enc in encodings.items():
            print(f"{code}. {enc}")

        choice = input("请输入编码对应的编号：")
        target_encoding = encodings.get(choice, 'utf-8')  # 默认为utf-8
        print(f"您选择的编码是：{target_encoding}")

        for file in downloaded_files:
            file_path = os.path.join(folder, file)
            # 转换文件编码
            convert_encoding(file_path, target_encoding)
            split_novel(file_path, pattern, target_encoding)  # 分割小说文件
    else:
        print("未检测到小说文件，请确保文件已下载到当前文件夹。")


if __name__ == "__main__":
    main()

