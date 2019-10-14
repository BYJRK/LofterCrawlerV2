import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from multiprocessing import pool
from pathlib import Path
import json
import re
import time
from tqdm import tqdm


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/73.0.3683.103 '
                  'Safari/537.36'
}
TIMEOUT = 16
PROCESSES = 8
MAX_RETRY = 2
MAX_SIZE = None
REPLACE = True
DATE_DELTA = timedelta(days=40732)
ILLEGAL_PATH_CHARS = r'\/:*?"<>|'
CHUNK_SIZE = 1024


def get_html(url: str) -> str:
    """
    访问给定的 url，获取并返回 html 文档
    """
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code == 200:
        html = r.text
        return html
    else:
        print(f'无法访问 {url}')
        return None


def get_filename(url: str) -> str:
    """
    从图片的链接中获取图片的真实名称
    """
    # 图片的名称形如：
    # zJtTDg2RGdJREZ3PT0.jpg
    # 5982469947077.jpg
    # http://imglf2.ph.126.net/As9QcYbKzXKCnJdVWMe7FA==/6630839067281310791.jpg
    # http://xxx/xxx.jpg?imageView&amp;thumbnail=1680x0&amp;quality=96&amp;stripmeta=0&amp;type=jpg
    return re.search(r'(?<!/)/(\w+\.\w+)', url).group(1)


def download_image(url, file, replace=True):
    """
    从给定的链接下载图片到指定的位置

    Args:
        url: 图片链接
        file: 存放路径
        replace: 是否覆盖已有同名文件（默认为 False）

    Returns:
        下载的状态：
            成功：(True, 文件路径)
            失败：(False, 图片链接)
    """
    if not isinstance(file, Path):
        file = Path(file)
    # 如果不替换，而且已有同名文件，则直接跳过
    if not replace and file.exists():
        return None
    if MAX_SIZE:
        assert isinstance(MAX_SIZE, int) and MAX_SIZE > 0, 'maxsize 参数有误'
        url = re.sub(r'(?<=thumbnail=)\d+(?=x)', str(MAX_SIZE), url)
    img = requests.get(url, stream=True, timeout=TIMEOUT)
    if img.status_code == 200:
        with file.open('wb') as f:
            for chunk in img.iter_content(CHUNK_SIZE):
                f.write(chunk)
        return None
    else:
        print(f'下载超时：{url}')
        if file.exists():
            file.unlink()
        return url, file


def download_images_mt(image_links, retry=0):
    print(f"开始下载图片")

    pbar = tqdm(total=len(image_links), ascii=True)
    mypool = pool.Pool(processes=PROCESSES)
    result = []

    def update(res):
        if res:
            result.append(res)
        pbar.update()

    start_time = time.time()
    for link, path in image_links:
        mypool.apply_async(download_image, args=(
            link, path, REPLACE), callback=update)
    mypool.close()
    mypool.join()
    pbar.close()
    stop_time = time.time()
    print(f'下载完毕，耗时 {stop_time-start_time:.4f} 秒')
    if len(result):
        print(f'其中 {len(result)} 张图片下载失败', end='')
        if retry < MAX_RETRY:
            print('，尝试重新下载')
            download_images_mt(result, retry + 1)
        else:
            print('，链接如下：')
            for link, _ in result:
                print(link)


def get_image_links_in_post(soup) -> List[str]:
    """
    获取指定贴子下的所有图片的原图链接
    """
    links = []
    for link in soup.find_all(lambda tag: tag.has_attr('bigimgsrc')):
        links.append(link.get('bigimgsrc'))
    return links


def get_domain_title(domain: str) -> str:
    """
    获取域名的标题
    """
    try:
        html = get_html(get_page_url(domain, 1))
        soup = BeautifulSoup(html, 'lxml')
        title = re.split(r'\s+', soup.head.title.string)[0].strip()
        return title
    except:
        # 如果无法获取标题，则返回域名
        return domain


def get_post_info(url: str) -> Dict[str, str]:
    """
    从贴子链接获取贴子的所有信息，包含图片列表，返回一个字典
    """
    html = get_html(url)
    if not html:
        return None
    soup = BeautifulSoup(html, 'lxml')
    # 贴子的标题
    title = re.sub(r'\s+', ' ', soup.head.title.text).strip()
    # 贴子中的文字内容（可能包含模特信息等）
    content = soup.find('div', class_='content')
    if content:
        text = content.find('div', class_='text')
    else:
        text = soup.find('div', class_='text')
    text = text.text if text else None
    # 贴子发布的日期（不准，可能会差几天）
    # date = re.search(r'\d{4}-\d{2}-\d{2}', html)
    # if date:
    #     date = datetime.strptime(date.group(), '%Y-%m-%d')
    # else:
    date = datetime.fromtimestamp(
        int(url.split('_')[-1], base=16)) - DATE_DELTA
    date = date.strftime('%Y-%m-%d')

    return {
        'title': title,
        'url': url,
        'date': date,
        'text': text,
        'images': [link for link in get_image_links_in_post(soup)]
    }


def get_post_links_in_page(url: str) -> List[str]:
    """
    获取博客某一页的所有推文的链接
    """
    # 推文链接形如 xxx.lofter.com/post/123abcd_12496ef13
    # 前面必须加博客的域名，因为推主可能会转发别人的
    pattern = url[:url.index('.com/') + 5] + r'post/[0-9a-f]+_[0-9a-f]+'
    links = []
    html = get_html(url)
    if not html:
        return []
    soup = BeautifulSoup(html, 'lxml')
    posts = soup.find_all('a', href=re.compile(pattern))
    for post in posts:
        href = post.get('href')
        # 忽略已有的推文链接
        # 这可能是由于一些奇怪的网页模板导致的
        if href in links:
            continue
        links.append(href)
    return links


def is_valid_page(url: str) -> bool:
    """
    检查博客的指定页面是否存在。
    除了常规检查，还可以用来查看博客页数的上限
    """
    posts = get_post_links_in_page(url)
    if posts:
        return True
    else:
        return False


def get_page_url(domain: str, page_number: int) -> str:
    """
    获取指定博客某一页的网址
    """
    assert type(page_number) is int and page_number >= 1, '输入的页数有误'
    # 虽然 ?page=1 也是可以正确获取首页内容的，但最好还是不这样写
    if page_number == 1:
        return f'http://{domain}.lofter.com/'
    return f'http://{domain}.lofter.com/?page={page_number}'


def get_post_title(url: str) -> str:
    """
    获取推文的标题（一般是拿去做文件或文件夹的名称）
    """
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    # 有时候莫名其妙地，推文标题中会包含换行符
    s = ''
    return re.sub(r'\s', ' ', soup.head.title.string)


def get_end_page_number(domain, start_page=1, end_page=0):
    """
    查找需要爬取的博客的结束页码

    Args:
        domain: 博客的域名
        start_page: 起始页（默认为 1）
        end_page: 最大总页数（默认为 0，表示直到最后一页）

    Returns:
        int: 结束页码
    """
    assert type(start_page) is int and start_page > 0
    # 如果给定的起始页数已经是无效的
    if not is_valid_page(get_page_url(domain, start_page)):
        raise Exception('the given start page is invalid')

    assert type(end_page) is int and end_page >= start_page or not end_page
    # 如果最大页数给定
    if end_page:
        if is_valid_page(get_page_url(domain, end_page)):
            return end_page
        right = end_page - 1
    else:
        # 如果没有给定最大页数
        right = 32
    # 寻找最小的无效页码
    left = 1
    while is_valid_page(get_page_url(domain, right)):
        left = right
        right *= 2
    # 二分法
    while right - left > 1:
        middle = (right - left) // 2 + left
        result = is_valid_page(get_page_url(domain, int(middle)))
        if result:
            left = middle
        else:
            right = middle
        if right - left == 1:
            if result:
                return middle
            else:
                return left


def gather_post_infos(domain, start_page=1, end_page=0):
    """
    爬取博客指定页数范围内的所有贴子信息（包含图片链接）
    """
    username = get_domain_title(domain)
    end_page = get_end_page_number(domain, start_page, end_page)
    json_file = Path(f'{username}_{start_page}_{end_page}.json')
    if json_file.exists():
        print(f'找到已有文件：{json_file.name}')
        with json_file.open('r', encoding='utf-8') as f:
            domain_info = json.load(f)
            return domain_info
    print(f'开始爬取博客「{username}」{start_page} 至 {end_page} 页的所有贴子')

    mypool = pool.Pool(processes=PROCESSES)
    # 获取每一页的网址
    start_time = time.time()
    page_links = [get_page_url(domain, i)
                  for i in range(start_page, end_page + 1)]
    post_links_in_pages = mypool.map(get_post_links_in_page, page_links)
    post_links = []
    for links in post_links_in_pages:
        post_links.extend(links)
    stop_time = time.time()
    print(f'共找到 {len(post_links)} 个贴子，耗时 {stop_time - start_time:.4f} 秒')

    start_time = time.time()
    post_infos = mypool.map(get_post_info, post_links)
    mypool.close()
    mypool.join()
    stop_time = time.time()
    # 这里先大致总结一下图片的数量
    image_links = []
    for post in post_infos:
        image_links.extend(post['images'])
    print(f'共找到 {len(image_links)} 张图片，耗时 {stop_time - start_time:.4f} 秒')

    domain_info = {
        'domain': f'http://{domain}.lofter.com/',
        'username': username,
        'page_range': [start_page, end_page],
        'posts': post_infos
    }

    with json_file.open('w', encoding='utf-8') as f:
        json.dump(domain_info, f)
        print(f'{json_file.name} 文件保存完毕。')
    return domain_info


def gather_image_links(info, separate_folders=True):
    """
    汇总所有图片的链接以及对应的存放位置，并提前创建需要的文件夹
    """
    if isinstance(info, str):
        with open(info, 'r', encoding='utf-8') as f:
            info = json.load(f)

    image_links = []
    # 表明这是一个 domain info
    if 'posts' in info:
        # 创建域名文件夹
        domain_dir = Path(info['username'])
        domain_dir.mkdir(exist_ok=True)
        for post in info['posts']:
            # 说明这个贴子下没有图片，直接跳过
            if not post['images']:
                continue
            # 贴子下有图片
            if separate_folders:
                title = post['title']
                for c in ILLEGAL_PATH_CHARS:
                    title = title.replace(c, '')
                post_dir = domain_dir / Path(title)
                post_dir.mkdir(exist_ok=True)
                for image in post['images']:
                    image_links.append((image, post_dir / get_filename(image)))
            else:
                for image in post['images']:
                    image_links.append(
                        (image, domain_dir / get_filename(image)))
    # 否则表明这是一个 post info
    else:
        if not info['images']:
            return []
        title = info['title']
        for c in ILLEGAL_PATH_CHARS:
            title = title.replace(c, '')
        post_dir = Path(title)
        post_dir.mkdir(exist_ok=True)
        for image in info['images']:
            image_links.append((image, post_dir / get_filename(image)))

    return image_links
