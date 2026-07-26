# scrape.py
# -*- coding: utf-8 -*-
from pathlib import Path
from urllib.parse import urljoin
from io import BytesIO
import re

import requests
import pandas as pd
from bs4 import BeautifulSoup
from PIL import Image

BASE_URL = "https://minecraftjapan.miraheze.org"
PAGE_URL = BASE_URL + "/wiki/%E9%80%B2%E6%8D%97"
SPRITE_URL = "https://static.wikitide.net/minecraftjapanwiki/4/44/InvSprite.png"
CELL_SIZE = 32

session = requests.Session()
session.headers["User-Agent"]="Mozilla/5.0"

Path("csv").mkdir(exist_ok=True)
Path("images").mkdir(exist_ok=True)

sprite_path=Path("images/InvSprite.png")
if not sprite_path.exists():
    sprite_path.write_bytes(session.get(SPRITE_URL).content)
sprite=Image.open(sprite_path)

html=session.get(PAGE_URL)
html.raise_for_status()
soup=BeautifulSoup(html.text,"lxml")
tables=soup.find_all("table",class_="wikitable")

for t_index,table in enumerate(tables[:6],1):
    rows=[]
    for tr in table.find_all("tr"):
        row=[]
        for cell in tr.find_all(["th","td"]):
            text=cell.get_text(" ",strip=True)
            value=text

            img=cell.find("img")
            if img and img.get("src"):
                url=urljoin(BASE_URL,img["src"])
                fname=re.sub(r'[\\/:*?"<>|]','_',text or f"img_{t_index}")
                ext=".png"
                Path("images",fname+ext).write_bytes(session.get(url).content)
                value=f"{fname+ext}\n{text}"

            sprite_span=cell.find("span",class_="inv-sprite")
            if sprite_span:
                m=re.search(r'background-position:\s*(-?\d+)px\s*(-?\d+)px',sprite_span.get("style",""))
                if m:
                    x=abs(int(m.group(1)))
                    y=abs(int(m.group(2)))
                    icon=sprite.crop((x,y,x+CELL_SIZE,y+CELL_SIZE))
                    fname=re.sub(r'[\\/:*?"<>|]','_',text or f"sprite_{x}_{y}")
                    out=Path("images",fname+".png")
                    icon.save(out)
                    value=f"{out.name}\n{text}"
            row.append(value)
        if row:
            rows.append(row)
    if rows:
        w=max(map(len,rows))
        for r in rows:
            r.extend([""]*(w-len(r)))
        pd.DataFrame(rows).to_csv(Path("csv",f"table_{t_index}.csv"),index=False,header=False,encoding="utf-8-sig")
print("Done")
