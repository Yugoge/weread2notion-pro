import calendar
from datetime import datetime
from datetime import timedelta
import hashlib
import os
import re
import requests
import base64
from weread2notionpro.config import (
    RICH_TEXT,
    URL,
    RELATION,
    NUMBER,
    DATE,
    FILES,
    STATUS,
    TITLE,
    SELECT,
)
import pendulum

MAX_LENGTH = (
    1024  # NOTION 2000-character limit https://developers.notion.com/reference/request-limits
)

def get_heading(level, content):
    if level == 1:
        heading = "heading_1"
    elif level == 2:
        heading = "heading_2"
    else:
        heading = "heading_3"
    return {
        "type": heading,
        heading: {
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": content[:MAX_LENGTH],
                    },
                }
            ],
            "color": "default",
            "is_toggleable": False,
        },
    }

def get_table_of_contents():
    """Get Table of Contents"""
    return {"type": "table_of_contents", "table_of_contents": {"color": "default"}}

def get_title(content):
    return {"title": [{"type": "text", "text": {"content": content[:MAX_LENGTH]}}]}

def get_rich_text(content):
    return {"rich_text": [{"type": "text", "text": {"content": content[:MAX_LENGTH]}}]}

def get_url(url):
    return {"url": url}

def get_file(url):
    return {"files": [{"type": "external", "name": "Cover", "external": {"url": url}}]}

def get_multi_select(names):
    return {"multi_select": [{"name": name} for name in names]}

def get_relation(ids):
    return {"relation": [{"id": id} for id in ids]}

def get_date(start, end=None):
    return {
        "date": {
            "start": start,
            "end": end,
            "time_zone": "Asia/Shanghai",
        }
    }

def get_icon(url):
    return {"type": "external", "external": {"url": url}}

def get_select(name):
    return {"select": {"name": name}}

def get_number(number):
    return {"number": number}

def get_quote(content):
    return {
        "type": "quote",
        "quote": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": content[:MAX_LENGTH]},
                }
            ],
            "color": "default",
        },
    }

def get_block(content, block_type, show_color, style, colorStyle, reviewId):
    color = "default"
    if show_color:
        if colorStyle == 1:
            color = "red"
        elif colorStyle == 2:
            color = "purple"
        elif colorStyle == 3:
            color = "blue"
        elif colorStyle == 4:
            color = "green"
        elif colorStyle == 5:
            color = "yellow"
    block = {
        "type": block_type,
        block_type: {
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": content[:MAX_LENGTH],
                    },
                }
            ],
            "color": color,
        },
    }
    if block_type == "callout":
        emoji = "〰️"
        if style == 0:
            emoji = "💡"
        elif style == 1:
            emoji = "⭐"
        if reviewId is not None:
            emoji = "✍️"
        block[block_type]["icon"] = {"emoji": emoji}
    return block

def get_rich_text_from_result(result, name):
    return result.get("properties").get(name).get("rich_text")[0].get("plain_text")

def get_number_from_result(result, name):
    return result.get("properties").get(name).get("number")

def format_time(time):
    """Format seconds into hours and minutes"""
    result = ""
    hour = time // 3600
    if hour > 0:
        result += f"{hour}h"
    minutes = time % 3600 // 60
    if minutes > 0:
        result += f"{minutes}m"
    return result

def format_date(date, format="%Y-%m-%d %H:%M:%S"):
    return date.strftime(format)

def timestamp_to_date(timestamp):
    """Convert timestamp to date"""
    return datetime.utcfromtimestamp(timestamp) + timedelta(hours=8)

def get_first_and_last_day_of_month(date):
    first_day = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    _, last_day_of_month = calendar.monthrange(date.year, date.month)
    last_day = date.replace(
        day=last_day_of_month, hour=0, minute=0, second=0, microsecond=0
    )
    return first_day, last_day

def get_first_and_last_day_of_year(date):
    first_day = date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day = date.replace(month=12, day=31, hour=0, minute=0, second=0, microsecond=0)
    return first_day, last_day

def get_first_and_last_day_of_week(date):
    first_day_of_week = (date - timedelta(days=date.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    last_day_of_week = first_day_of_week + timedelta(days=6)
    return first_day_of_week, last_day_of_week

def get_properties(dict1, dict2):
    properties = {}
    for key, value in dict1.items():
        type = dict2.get(key)
        if value is None:
            continue
        property = None
        if type == TITLE:
            property = {
                "title": [{"type": "text", "text": {"content": value[:MAX_LENGTH]}}]
            }
        elif type == RICH_TEXT:
            property = {
                "rich_text": [{"type": "text", "text": {"content": value[:MAX_LENGTH]}}]
            }
        elif type == NUMBER:
            property = {"number": value}
        elif type == STATUS:
            property = {"status": {"name": value}}
        elif type == FILES:
            property = {
                "files": [
                    {"type": "external", "name": "Cover", "external": {"url": value}}
                ]
            }
        elif type == DATE:
            property = {
                "date": {
                    "start": pendulum.from_timestamp(
                        value, tz="Asia/Shanghai"
                    ).to_datetime_string(),
                    "time_zone": "Asia/Shanghai",
                }
            }
        elif type == URL:
            property = {"url": value}
        elif type == SELECT:
            property = {"select": {"name": value}}
        elif type == RELATION:
            property = {"relation": [{"id": id} for id in value]}
        if property:
            properties[key] = property
    return properties

def get_property_value(property):
    """Retrieve value from Property"""
    type = property.get("type")
    content = property.get(type)
    if content is None:
        return None
    if type == "title" or type == "rich_text":
        if len(content) > 0:
            return content[0].get("plain_text")
        else:
            return None
    elif type == "status" or type == "select":
        return content.get("name")
    elif type == "files":
        if len(content) > 0 and content[0].get("type") == "external":
            return content[0].get("external").get("url")
        else:
            return None
    elif type == "date":
        return str_to_timestamp(content.get("start"))
    else:
        return content

def str_to_timestamp(date):
    if date is None:
        return 0
    dt = pendulum.parse(date)
    return int(dt.timestamp())

upload_url = "https://wereadassets.malinkang.com/"

def upload_image(folder_path, filename, file_path):
    with open(file_path, "rb") as file:
        content_base64 = base64.b64encode(file.read()).decode("utf-8")
    data = {"file": content_base64, "filename": filename, "folder": folder_path}
    response = requests.post(upload_url, json=data)
    if response.status_code == 200:
        print("File uploaded successfully.")
        return response.text
    else:
        return None

def url_to_md5(url):
    md5_hash = hashlib.md5()
    encoded_url = url.encode("utf-8")
    md5_hash.update(encoded_url)
    return md5_hash.hexdigest()

def download_image(url, save_dir="cover"):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    file_name = url_to_md5(url) + ".jpg"
    save_path = os.path.join(save_dir, file_name)
    if os.path.exists(save_path):
        print(f"File {file_name} already exists. Skipping download.")
        return save_path
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=128):
                file.write(chunk)
        print(f"Image downloaded successfully to {save_path}")
    else:
        print(f"Failed to download image. Status code: {response.status_code}")
    return save_path

def get_embed(url):
    return {"type": "embed", "embed": {"url": url}}
