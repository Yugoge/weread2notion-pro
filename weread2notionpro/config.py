RICH_TEXT = "rich_text"
URL = "url"
RELATION = "relation"
NUMBER = "number"
DATE = "date"
FILES = "files"
STATUS = "status"
TITLE = "title"
SELECT = "select"

book_properties_type_dict = {
    "Title": TITLE,
    "BookId": RICH_TEXT,
    "ISBN": RICH_TEXT,
    "Link": URL,
    "Author": RELATION,
    "Sort": NUMBER,
    "Rating": NUMBER,
    "Cover": FILES,
    "Categories": RELATION,
    "Reading Status": STATUS,
    "Reading Time": NUMBER,
    "Reading Progress": NUMBER,
    "Reading Days": NUMBER,
    "Date": DATE,
    "Start Reading Date": DATE,
    "Last Reading Date": DATE,
    "Introduction": RICH_TEXT,
    "Bookshelf Category": SELECT,
    "My Rating": SELECT,
    "Douban Link": URL,
}
tz = 'Asia/Shanghai'
