import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple
from datetime import datetime
from multiprocessing import pool
from pathlib import Path
import json
import re
import time
from tqdm import tqdm


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/68.0.3440.106 Safari/537.36 '
}
TIMEOUT = 16
PROCESSES = 8


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
    # http://xxx/xxx.jpg?imageView&amp;thumbnail=1680x0&amp;quality=96&amp;stripmeta=0&amp;type=jpg
    return re.search(r'(?<=img/)\w+\.\w+', url).group()


def download_image(url, file, maxsize=None, replace=False):
    """
    从给定的链接下载图片到指定的位置

    Args:
        url: 图片链接
        file: 存放路径
        replace: 是否覆盖已有同名文件（默认为 False）
        maxsize: 是否限制图片最大尺寸

    Returns:
        下载的状态：
            成功：(True, 文件路径)
            失败：(False, 图片链接)
    """
    if not isinstance(file, Path):
        file = Path(file)
    # 如果不替换，而且已有同名文件，则直接跳过
    if not replace and file.exists():
        return (True, file)
    if maxsize:
        assert isinstance(maxsize, int) and maxsize > 0, 'maxsize 参数有误'
        url = re.sub(r'(?<=thumbnail=)\d+(?=x)', str(maxsize), url)
    img = requests.get(url, stream=True, timeout=TIMEOUT)
    if img.status_code == 200:
        with file.open('wb') as f:
            for chunk in img:
                f.write(chunk)
        return (True, file)
    else:
        print(f'下载超时：{url}')
        if file.exists():
            file.unlink()
        return (False, url)


def download_post_mt(post, processes=8, pbar=False, maxsize=None):
    print(f"开始下载贴子 {post['url']} 中的图片")
    myPool = pool.Pool(processes=processes)
    folder = Path(post['title'])
    folder.mkdir(exist_ok=True)
    pbar = tqdm(total=len(post['images']), ascii=True)

    def update(*p):
        # TODO: 考虑下载失败的情况
        pbar.update()

    for link in post['images']:
        filename = folder / get_filename(link)
        myPool.apply_async(download_image, args=(
            link, filename, maxsize), callback=update)

    myPool.close()
    myPool.join()
    pbar.close()


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

    Args:
        domain: 域名，形如 yurisa123

    Returns:
        str: 域名的标题
    """
    try:
        html = get_html(get_page_url(domain, 1))
        soup = BeautifulSoup(html, 'lxml')
        title = re.split(r'\s+', soup.head.title.string)[0].strip()
        return soup.head.title.string
    except:
        # 如果无法获取标题，则返回域名
        return domain


def get_post_info(url: str) -> Dict[str, str]:
    html = get_html(url)
    if not html:
        return None
    soup = BeautifulSoup(html, 'lxml')
    title = soup.head.title.text
    content = soup.find('div', class_='content')
    if content:
        text = content.find('div', class_='text')
    else:
        text = soup.find('div', class_='text')
    text = text.text if text else None
    # date = re.search(r'\d{4}-\d{2}-\d{2}', html)
    # date = datetime.strptime(date.group(), '%Y-%m-%d') if date else None
    info = soup.find('div', class_='info')
    return {
        'title': re.sub(r'\s', ' ', soup.head.title.text),
        'url': url,
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


def gather_image_links(domain, start_page=1, end_page=0):
    username = get_domain_title(domain)
    end_page = get_end_page_number(domain, start_page, end_page)
    print(f'开始爬取博客「{username}」 {start_page} 至 {end_page} 页的所有贴子')

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
        'page_range': [start_page, end_page],
        'posts': post_infos
    }

    json_file = Path(f'{username}_{start_page}_{end_page}.json')
    with json_file.open('w', encoding='utf-8') as f:
        json.dump(domain_info, f)
        print('.json 文件保存完毕。')


if __name__ == "__main__":
    gather_image_links('hiroron')
