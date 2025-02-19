from datetime import datetime
from datetime import timedelta
import os

import pendulum

from weread2notionpro.weread_api import WeReadApi
from weread2notionpro.notion_helper import NotionHelper
from weread2notionpro.utils import (
    format_date,
    get_date,
    get_icon,
    get_number,
    get_relation,
    get_title,
)

def insert_to_notion(page_id, timestamp, duration):
    parent = {"database_id": notion_helper.day_database_id, "type": "database_id"}
    properties = {
        "Title": get_title(
            format_date(
                datetime.utcfromtimestamp(timestamp) + timedelta(hours=8),
                "%Y-%m-%d",
            )
        ),
        "Date": get_date(
            start=format_date(datetime.utcfromtimestamp(timestamp) + timedelta(hours=8))
        ),
        "Duration": get_number(duration),
        "Timestamp": get_number(timestamp),
        "Year": get_relation(
            [
                notion_helper.get_year_relation_id(
                    datetime.utcfromtimestamp(timestamp) + timedelta(hours=8)
                ),
            ]
        ),
        "Month": get_relation(
            [
                notion_helper.get_month_relation_id(
                    datetime.utcfromtimestamp(timestamp) + timedelta(hours=8)
                ),
            ]
        ),
        "Week": get_relation(
            [
                notion_helper.get_week_relation_id(
                    datetime.utcfromtimestamp(timestamp) + timedelta(hours=8)
                ),
            ]
        ),
    }
    if page_id != None:
        notion_helper.client.pages.update(page_id=page_id, properties=properties)
    else:
        notion_helper.client.pages.create(
            parent=parent,
            icon=get_icon("https://www.notion.so/icons/target_red.svg"),
            properties=properties,
        )

def get_file():
    # Set folder path
    folder_path = "./OUT_FOLDER"

    # Check if folder exists
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        entries = os.listdir(folder_path)

        file_name = entries[0] if entries else None
        return file_name
    else:
        print("OUT_FOLDER does not exist.")
        return None

def get_fresh_url(original_url):
    timestamp = int(datetime.datetime.now().timestamp())  
    return f"{original_url}?t={timestamp}"  # 避免 GitHub 和 Notion 缓存

HEATMAP_GUIDE = "https://mp.weixin.qq.com/s?__biz=MzI1OTcxOTI4NA==&mid=2247484145&idx=1&sn=81752852420b9153fc292b7873217651&chksm=ea75ebeadd0262fc65df100370d3f983ba2e52e2fcde2deb1ed49343fbb10645a77570656728&token=157143379&lang=en_US#rd"

notion_helper = NotionHelper()
weread_api = WeReadApi()
def main():
    image_file = get_file()
    if image_file:
        image_url = f"https://raw.githubusercontent.com/{os.getenv('REPOSITORY')}/{os.getenv('REF').split('/')[-1]}/OUT_FOLDER/{image_file}"
        heatmap_url = get_fresh_url(f"https://heatmap.malinkang.com/?image={image_url}")
        if notion_helper.heatmap_block_id:
            response = notion_helper.update_heatmap(
                block_id=notion_helper.heatmap_block_id, url=heatmap_url
            )
        else:
            print(f"Failed to update heatmap, placeholder missing. Refer to: {HEATMAP_GUIDE}")
    else:
        print(f"Failed to update heatmap, no heatmap generated. Refer to: {HEATMAP_GUIDE}")
    api_data = weread_api.get_api_data()
    readTimes = {int(key): value for key, value in api_data.get("readTimes").items()}
    now = pendulum.now("Asia/Shanghai").start_of("day")
    today_timestamp = now.int_timestamp
    if today_timestamp not in readTimes:
        readTimes[today_timestamp] = 0
    readTimes = dict(sorted(readTimes.items()))
    results = notion_helper.query_all(database_id=notion_helper.day_database_id)
    for result in results:
        timestamp = result.get("properties").get("Timestamp").get("number")
        duration = result.get("properties").get("Duration").get("number")
        id = result.get("id")
        if timestamp in readTimes:
            value = readTimes.pop(timestamp)
            if value != duration:
                insert_to_notion(page_id=id, timestamp=timestamp, duration=value)
    for key, value in readTimes.items():
        insert_to_notion(None, int(key), value)
if __name__ == "__main__":
    main()
