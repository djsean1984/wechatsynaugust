import os
import requests
from notion_client import Client
from typing import List

# --- 配置 ---

WEREAD_COOKIE = os.getenv("WEREAD_COOKIE")  # 微信读书Cookie，完整复制
NOTION_TOKEN = os.getenv("NOTION_TOKEN")    # Notion集成token
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")  # Notion数据库ID

# 微信读书笔记分页大小
PAGE_SIZE = 20

# --- 请求微信读书接口获取笔记 ---

def get_weread_notes(start: int = 0, limit: int = PAGE_SIZE) -> List[dict]:
    url = f"https://i.weread.qq.com/book/bookmarklist?start={start}&limit={limit}&orderby=1&selectType=0"
    headers = {
        "Cookie": WEREAD_COOKIE,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    if data.get("errcode") != 0:
        raise Exception(f"Weread API Error: {data.get('errmsg')}")
    return data.get("data", {}).get("bookmarkList", [])

# --- 处理笔记转换为Notion格式 ---

def convert_to_notion_page(note: dict) -> dict:
    # 简单转换示例，根据 Notion API 要求构造页面属性
    title = note.get("content", "")[:100]  # 取笔记内容前100字符作为标题
    book_name = note.get("bookName", "未知书籍")
    ctime = note.get("createTime", "")

    notion_page = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Name": {
                "title": [{"text": {"content": title}}]
            },
            "Book": {
                "rich_text": [{"text": {"content": book_name}}]
            },
            "Created Time": {
                "date": {"start": ctime}
            }
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "text": [{"type": "text", "text": {"content": note.get("content", "")}}]
                }
            }
        ]
    }
    return notion_page

# --- 写入Notion ---

def add_note_to_notion(notion: Client, page_data: dict):
    notion.pages.create(**page_data)

# --- 主函数 ---

def main():
    notion = Client(auth=NOTION_TOKEN)

    start = 0
    while True:
        notes = get_weread_notes(start=start, limit=PAGE_SIZE)
        if not notes:
            print("笔记获取完毕")
            break

        for note in notes:
            page = convert_to_notion_page(note)
            add_note_to_notion(notion, page)
            print(f"已同步笔记：{note.get('content', '')[:30]}...")

        start += PAGE_SIZE

if __name__ == "__main__":
    main()
