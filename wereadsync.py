import os
import time
import requests
from notion_client import Client
from requests.exceptions import HTTPError

# --- 配置 ---
WEREAD_COOKIE = os.getenv("WEREAD_COOKIE")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

PAGE_SIZE = 20
MAX_RETRY = 3
RETRY_DELAY = 3  # 秒

HEADERS = {
    "Cookie": WEREAD_COOKIE,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Referer": "https://weread.qq.com/",
    "Origin": "https://weread.qq.com"
}

def get_weread_notes(start=0, limit=PAGE_SIZE):
    url = f"https://i.weread.qq.com/book/bookmarklist?start={start}&limit={limit}&orderby=1&selectType=0"

    for attempt in range(1, MAX_RETRY + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("errcode") != 0:
                raise Exception(f"Weread API error: {data.get('errmsg')}")
            return data.get("data", {}).get("bookmarkList", [])
        except HTTPError as e:
            print(f"HTTP error on attempt {attempt}: {e}")
        except Exception as e:
            print(f"Error on attempt {attempt}: {e}")

        if attempt < MAX_RETRY:
            print(f"Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
    raise Exception("Max retries reached, failed to get Weread notes.")

def convert_to_notion_page(note):
    title = note.get("content", "")[:100] or "无内容"
    book_name = note.get("bookName", "未知书籍")
    ctime = note.get("createTime", "")

    return {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": title}}]},
            "Book": {"rich_text": [{"text": {"content": book_name}}]},
            "Created Time": {"date": {"start": ctime}}
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"text": [{"type": "text", "text": {"content": note.get("content", "")}}]}
            }
        ]
    }

def add_note_to_notion(notion_client, page_data):
    notion_client.pages.create(**page_data)

def main():
    if not (WEREAD_COOKIE and NOTION_TOKEN and NOTION_DATABASE_ID):
        print("请先设置 WEREAD_COOKIE, NOTION_TOKEN, NOTION_DATABASE_ID 环境变量")
        return

    notion = Client(auth=NOTION_TOKEN)
    start = 0

    while True:
        print(f"Fetching notes from {start} ...")
        notes = get_weread_notes(start=start)
        if not notes:
            print("所有笔记同步完成")
            break

        for note in notes:
            try:
                page = convert_to_notion_page(note)
                add_note_to_notion(notion, page)
                print(f"同步笔记：{note.get('content', '')[:30]}...")
            except Exception as e:
                print(f"写入 Notion 失败: {e}")

        start += PAGE_SIZE

if __name__ == "__main__":
    main()
