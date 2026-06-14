import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import urljoin
import re
import time

BASE_URL = "https://www.wevity.com/"
headers = {
    "User-Agent": "Mozilla/5.0"
}

rows = []

# 1페이지당 약 20개 → 3페이지 수집 = 약 60개
for page in range(1, 4):
    list_url = f"https://www.wevity.com/?c=find&s=1&gbn=list&gp={page}"

    response = requests.get(list_url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for tit in soup.select("div.tit"):
        parent = tit.find_parent()

        a_tag = tit.select_one("a")
        sub_tit = tit.select_one("div.sub-tit")

        if a_tag is None:
            continue

        title = a_tag.get_text(" ", strip=True)
        title = title.replace("SPECIAL", "").replace("IDEA", "").strip()

        category = ""
        if sub_tit:
            category = sub_tit.get_text(" ", strip=True)
            category = category.replace("분류 :", "").strip()

        day_tag = parent.select_one("div.day") if parent else None
        organ_tag = parent.select_one("div.organ") if parent else None

        d_day = None
        deadline = ""
        status = ""

        if day_tag:
            day_text = day_tag.get_text(" ", strip=True)

            d_match = re.search(r"D-(\d+)", day_text)
            if d_match:
                d_day = int(d_match.group(1))
                deadline = (datetime.today() + timedelta(days=d_day)).strftime("%Y-%m-%d")

            status_tag = day_tag.select_one("span")
            if status_tag:
                status = status_tag.get_text(strip=True)

        organization = organ_tag.get_text(strip=True) if organ_tag else ""
        link = urljoin(BASE_URL, a_tag.get("href"))

        rows.append({
            "title": title,
            "category": category,
            "organization": organization,
            "d_day": d_day,
            "deadline": deadline,
            "status": status,
            "url": link,
            "source": "위비티",
            "collected_at": datetime.today().strftime("%Y-%m-%d")
        })

    print(f"{page}페이지 수집 완료")
    time.sleep(1)

df = pd.DataFrame(rows)

df = df.drop_duplicates(subset=["title"])
df = df.sort_values("d_day", na_position="last")

df.to_csv("data/external_deadlines.csv", index=False, encoding="utf-8-sig")

print("위비티 데이터 수집 완료")
print(f"총 {len(df)}개 수집")
print(df.head(10))