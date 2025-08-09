import os
import requests
from notion_client import Client

WEREAD_COOKIE = os.getenv("WEREAD_COOKIE")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

if not (WEREAD_COOKIE and NOTION_TOKEN and NOTION_DATABASE_ID):
    print("请设置 WEREAD_COOKIE, NOTION_TOKEN, NOTION_DATABASE_ID 环境变量")
    exit(1)

notion = Client(auth=NOTION_TOKEN)

def get_weread_notes(start=0, limit=20):
    url = "https://i.weread.qq.com/book/bookmarklist"
    headers = {
        "Cookie": WEREAD_COOKIE,
        "User-Agent": "Mozilla/5.0"
    }
    params = {
        "start": start,
        "limit": limit,
        "orderby": 1,
        "selectType": 0
    }
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"微信读书接口错误: {data}")
    return data.get("data", {})

def query_notion_page_by_id(bookmark_id):
    filter_params = {
        "filter": {
            "property": "笔记ID",
            "rich_text": {
                "equals": bookmark_id
            }
        }
    }
    response = notion.databases.query(database_id=NOTION_DATABASE_ID, **filter_params)
    return response["results"]

def add_notion_page(book_name, author, content, bookmark_id):
    notion.pages.create(
        parent={"database_id": NOTION_DATABASE_ID},
        properties={
            "书名": {
                "title": [{"text": {"content": book_name}}]
            },
            "作者": {
                "rich_text": [{"text": {"content": author}}]
            },
            "笔记": {
                "rich_text": [{"text": {"content": content}}]
            },
            "笔记ID": {
                "rich_text": [{"text": {"content": bookmark_id}}]
            }
        }
    )

def main():
    start = 0
    limit = 20
    total_added = 0
    while True:
        notes_data = get_weread_notes(start, limit)
        bookmarks = notes_data.get("bookmarkList", [])
        if not bookmarks:
            break
        for bm in bookmarks:
            book_name = bm.get("bookName", "未知书名")
            author = bm.get("author", "未知作者")
            content = bm.get("content", "").strip()
            bookmark_id = str(bm.get("id", ""))
            if not content:
                continue
            exists = query_notion_page_by_id(bookmark_id)
            if exists:
                print(f"跳过已存在笔记: {content[:20]}...")
                continue
            add_notion_page(book_name, author, content, bookmark_id)
            print(f"添加笔记: 《{book_name}》 - {content[:20]}...")
            total_added += 1
        start += limit
    print(f"同步完成，共添加 {total_added} 条笔记。")

if __name__ == "__main__":
    main()
