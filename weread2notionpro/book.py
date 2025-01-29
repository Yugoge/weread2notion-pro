import pendulum
from weread2notionpro.notion_helper import NotionHelper
from weread2notionpro.weread_api import WeReadApi
from weread2notionpro import utils
from weread2notionpro.config import book_properties_type_dict, tz

TAG_ICON_URL = "https://www.notion.so/icons/tag_gray.svg"
USER_ICON_URL = "https://www.notion.so/icons/user-circle-filled_gray.svg"
BOOK_ICON_URL = "https://www.notion.so/icons/book_gray.svg"
rating = {"poor": "⭐️", "fair": "⭐️⭐️⭐️", "good": "⭐️⭐️⭐️⭐️⭐️"}

def insert_book_to_notion(books, index, book_id):
    """Insert Book to Notion"""
    book = {}
    if book_id in archive_dict:
        book["Bookshelf Category"] = archive_dict.get(book_id)
    if book_id in notion_books:
        book.update(notion_books.get(book_id))
    book_info = weread_api.get_bookinfo(book_id)
    if book_info != None:
        book.update(book_info)
    read_info = weread_api.get_read_info(book_id)
    # Researched that this status is unknown in some cases, even when read, the status is still 1 markedStatus = 1 To-do 4 Complete Others are In Progress
    read_info.update(read_info.get("readDetail", {}))
    read_info.update(read_info.get("bookInfo", {}))
    book.update(read_info)
    book["Reading Progress"] = (
        100 if (book.get("markedStatus") == 4) else book.get("readingProgress", 0)
    ) / 100
    marked_status = book.get("markedStatus")
    status = "To-do"
    if marked_status == 4:
        status = "Complete"
    elif book.get("readingTime", 0) >= 60:
        status = "In Progress"
    book["Reading Status"] = status
    book["Reading Time"] = book.get("readingTime")
    book["Reading Days"] = book.get("totalReadDay")
    book["Rating"] = book.get("newRating")
    if book.get("newRatingDetail") and book.get("newRatingDetail").get("myRating"):
        book["My Rating"] = rating.get(book.get("newRatingDetail").get("myRating"))
    elif status == "Complete":
        book["My Rating"] = "Not Rated"
    book["Date"] = (
        book.get("finishedDate")
        or book.get("lastReadingDate")
        or book.get("readingBookDate")
    )
    book["Start Reading Date"] = book.get("beginReadingDate")
    book["Last Reading Date"] = book.get("lastReadingDate")
    cover = book.get("cover").replace("/s_", "/t7_")
    if not cover or not cover.strip() or not cover.startswith("http"):
        cover = BOOK_ICON_URL
    if book_id not in notion_books:
        book["Title"] = book.get("title")
        book["BookId"] = book.get("bookId")
        book["ISBN"] = book.get("isbn")
        book["Link"] = weread_api.get_url(book_id)
        book["Introduction"] = book.get("intro")
        book["Author"] = [
            notion_helper.get_relation_id(
                x, notion_helper.author_database_id, USER_ICON_URL
            )
            for x in book.get("author").split(" ")
        ]
        if book.get("categories"):
            book["Categories"] = [
                notion_helper.get_relation_id(
                    x.get("title"), notion_helper.category_database_id, TAG_ICON_URL
                )
                for x in book.get("categories")
            ]
    properties = utils.get_properties(book, book_properties_type_dict)
    if book.get("Date"):
        notion_helper.get_date_relation(
            properties,
            pendulum.from_timestamp(book.get("Date"), tz="Asia/Shanghai"),
        )

    print(
        f"Inserting \u300a{book.get('title')}\u300b, Total {len(books)} books, Current {index+1}."
    )
    parent = {"database_id": notion_helper.book_database_id, "type": "database_id"}
    result = None
    if book_id in notion_books:
        result = notion_helper.update_page(
            page_id=notion_books.get(book_id).get("pageId"),
            properties=properties,
            cover=utils.get_icon(cover),
        )
    else:
        result = notion_helper.create_book_page(
            parent=parent,
            properties=properties,
            icon=utils.get_icon(cover),
        )
    page_id = result.get("id")
    if book.get("readDetail") and book.get("readDetail").get("data"):
        data = book.get("readDetail").get("data")
        data = {item.get("readDate"): item.get("readTime") for item in data}
        insert_read_data(page_id, data)

def insert_read_data(page_id, read_times):
    read_times = dict(sorted(read_times.items()))
    filter = {"property": "Bookshelf", "relation": {"contains": page_id}}
    results = notion_helper.query_all_by_book(notion_helper.read_database_id, filter)
    for result in results:
        timestamp = result.get("properties").get("Timestamp").get("number")
        duration = result.get("properties").get("Duration").get("number")
        id = result.get("id")
        if timestamp in read_times:
            value = read_times.pop(timestamp)
            if value != duration:
                insert_to_notion(
                    page_id=id,
                    timestamp=timestamp,
                    duration=value,
                    book_database_id=page_id,
                )
    for key, value in read_times.items():
        insert_to_notion(None, int(key), value, page_id)

def insert_to_notion(page_id, timestamp, duration, book_database_id):
    parent = {"database_id": notion_helper.read_database_id, "type": "database_id"}
    properties = {
        "Title": utils.get_title(
            pendulum.from_timestamp(timestamp, tz=tz).to_date_string()
        ),
        "Date": utils.get_date(
            start=pendulum.from_timestamp(timestamp, tz=tz).format(
                "YYYY-MM-DD HH:mm:ss"
            )
        ),
        "Duration": utils.get_number(duration),
        "Timestamp": utils.get_number(timestamp),
        "Bookshelf": utils.get_relation([book_database_id]),
    }
    if page_id != None:
        notion_helper.client.pages.update(page_id=page_id, properties=properties)
    else:
        notion_helper.client.pages.create(
            parent=parent,
            icon=utils.get_icon("https://www.notion.so/icons/target_red.svg"),
            properties=properties,
        )

weread_api = WeReadApi()
notion_helper = NotionHelper()
archive_dict = {}
notion_books = {}

def main():
    global notion_books
    global archive_dict
    bookshelf_books = weread_api.get_bookshelf()
    notion_books = notion_helper.get_all_book()
    book_progress = bookshelf_books.get("bookProgress")
    book_progress = {book.get("bookId"): book for book in book_progress}
    for archive in bookshelf_books.get("archive"):
        name = archive.get("name")
        book_ids = archive.get("bookIds")
        archive_dict.update({book_id: name for book_id in book_ids})
    not_need_sync = []
    for key, value in notion_books.items():
        if (
            (
                key not in book_progress
                or value.get("readingTime") == book_progress.get(key).get("readingTime")
            )
            and (archive_dict.get(key) == value.get("category"))
            and (value.get("cover") is not None)
            and (
                value.get("status") != "Complete"
                or (value.get("status") == "Complete" and value.get("myRating"))
            )
        ):
            not_need_sync.append(key)
    notebooks = weread_api.get_notebooklist()
    notebooks = [d["bookId"] for d in notebooks if "bookId" in d]
    books = bookshelf_books.get("books")
    books = [d["bookId"] for d in books if "bookId" in d]
    books = list((set(notebooks) | set(books)) - set(not_need_sync))
    for index, book_id in enumerate(books):
        insert_book_to_notion(books, index, book_id)

if __name__ == "__main__":
    main()
