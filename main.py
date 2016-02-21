import requests
import pprint
import bs4
import urllib.request
import os
import json
import sys
import codecs
import locale
from concurrent.futures.thread import ThreadPoolExecutor


def makedir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    pass


prod_url = "http://www.j-boutique.com/products/"
urlPath = prod_url + "?p={0}"#&lang=eng"
makedir('products/')
os.chdir('products/')

executor = ThreadPoolExecutor(max_workers=10)


def processImages(i, images):
    dirname = str(i)
    sdir = dirname + '/' + "small"
    mdir = dirname + '/' + "medium"
    ldir = dirname + '/' + "large"
    makedir(sdir)
    makedir(mdir)
    makedir(ldir)

    futures = []
    for img in images:
        imgname = img.rsplit('/',1)[-1]
        surl = imgname[1:]
        murl = img.rsplit('/', 1)[0] + '/m' + imgname[1:]
        lurl = img.rsplit('/', 1)[0].rsplit('/', 1)[0] + '/' + imgname[1:]

        futures.append(executor.submit(urllib.request.urlretrieve, prod_url + img, sdir + '/' + surl))
        futures.append(executor.submit(urllib.request.urlretrieve, prod_url + murl, mdir + '/' + surl))
        futures.append(executor.submit(urllib.request.urlretrieve, prod_url + lurl, ldir + '/' + surl))

    (future.result() for future in futures)


s = requests.Session()
s.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:42.0) Gecko/20100101 Firefox/42.0'
s.headers['Accept-Language'] = 'en-US,en;q=0.5'
cookie = {'PHPSESSID' : '4n58hnpfkiojgr9h1l0djtrqg5'}

#for i in range(0x3040, 0x30a0): print(chr(i), end='')

for i in range(1, 500):
    print(i)
    if(os.path.exists(str(i))):
        print("already downloaded. Skipping..")
        continue

    urlCur = urlPath.format(i)
    print(urlCur)
    img_p = False
    for cook in (cookie, {}):
        page = s.get(urlCur, cookies = cook)

        print("page-" + page.encoding)

        if page.status_code == 404:
            print("Skipping id-", str(i))
        elif page.status_code == 303:
            print("Skipping id-", str(i))
        else:

            myhash = {}

            #tree = html.fromstring(page.content)
            soup = bs4.BeautifulSoup(page.content, "lxml", from_encoding='utf8')
            print (soup.original_encoding)
            #print(soup.prettify)

            links = soup.select('div.dts_div img')
            #pprint.pprint(links)

            images = []
            for a in soup.find_all(id='dts_div'):
                images = images + [img.get('src') for img in a.find_all('img')]

            if(len(images) == 0):
                print("Skipping id-", str(i))
                continue
            #pprint.pprint(images)
            if img_p == False:
                processImages(i, images)
                img_p = True
            count = 0
            for data in soup.find_all(id='dtr_data_div'):
                for row in data.find_all('tr'):
                    cells = row.findAll("td")
                    if len(cells) == 2:
                        (col1, col2) = cells

                        name = col1.string # .encode('utf8') #, 'ignore') #col1.text.strip()
                        #print (type(name))
                        name = name.split('\xa0', 1)[0]
                        if name == 'Classification' or count == 1:
                            value = [a.string.strip() for a in col2.find_all('a')]
                        else:
                            value = col2.string.strip() if col2.string is not None else "" #.encode('utf-16')  #col2.text.strip() #.decode('iso8859-1')
                        myhash[name] = value
                    count = count + 1
            desc = soup.find(id="dtr_desc")
            val = ''.join(cont for cont in desc.contents if isinstance(cont, bs4.element.NavigableString))
            #print(codecs.decode(codecs.encode(val, 'utf8'), 'SHIFT_JIS'))
            myhash["description"] = val # if desc.string is not None else ""

            title = soup.find(id="dtpt_left")
            print("title = ", title.contents)
            myhash["title"] = title.contents[0] if title.contents else "Not present"

            pprint.pprint(myhash)
            with codecs.open(str(i) + '/data' + ('-en' if cook == cookie else '-jp') + '.json', 'w', encoding='utf8') as outfile:
                json.dump(myhash, outfile, sort_keys=True, ensure_ascii=False)
