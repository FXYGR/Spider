import os
import requests
import re
import execjs
from pyquery import PyQuery as pq


class Model():
    """
    基类, 用来显示类的信息
    """

    def __repr__(self):
        name = self.__class__.__name__
        properties = ('{}=({})'.format(k, v) for k, v in self.__dict__.items())
        s = '\n<{} \n  {}>'.format(name, '\n  '.join(properties))
        return s


class Movie(Model):
    """
    存储电影信息
    """

    def __init__(self):
        self.name = ''
        self.score = 0
        self.brief = ''
        self.cover_url = ''
        self.ranking = 0


def get_js(url, headers):
    js = requests.get(url=url, headers=headers).content.decode('utf-8')
    return js


def execute_js(first_html):
    # 提取其中的JS加密函数
    js_string = ''.join(re.findall(r'(function .*?)</script>', first_html))

    # 提取其中执行JS函数的参数
    js_arg = ''.join(re.findall(r'setTimeout\(\"\D+\((\d+)\)\"', first_html))
    js_name = re.findall(r'function (\w+)',js_string)[0]

    # 修改JS函数，使其返回Cookie内容
    js_string = js_string.replace('eval("qo=eval;qo(po);")', 'return po')

    func = execjs.compile(js_string)
    return func.call(js_name, js_arg)


def parse_cookie(string):
    string = string.replace("document.cookie='", "")
    clearance = string.split(';')[0]
    return clearance


def set_cookie(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/70.0.3538.110 '
                      'Safari/537.36',
    }
    js_code = get_js(url, headers)
    # 执行JS获取Cookie
    cookie_str = execute_js(js_code)

    # 将Cookie转换为字典格式
    cookie = parse_cookie(cookie_str)
    print('cookies = ', cookie)
    headers["Cookie"] = cookie
    return headers


def get(url, filename):
    """
    缓存, 避免重复下载网页浪费时间
    """
    folder = 'shiguangCached'
    # 建立 cached 文件夹
    if not os.path.exists(folder):
        os.makedirs(folder)

    path = os.path.join(folder, filename)
    suffix = filename.split('.')[1]

    if os.path.exists(path):
        with open(path, 'rb') as f:
            s = f.read()
            return s
    else:
        # 发送网络请求, 把结果写入到文件夹中
        if suffix == 'html':
            headers = set_cookie(url)
            r = requests.get(url, headers=headers)
        else:
            r = requests.get(url)

        with open(path, 'wb') as f:
            f.write(r.content)
        return r.content


def movie_from_div(div):
    """
    从一个 div 里面获取到一个电影信息
    """
    e = pq(div)

    # 小作用域变量用单字符
    m = Movie()
    m.name = e('.mov_pic').find('a').attr('title')
    m.score = e('.total').text() + e('.total2').text()
    m.brief = e('.mt3').text()
    m.cover_url = e('img').attr('src')
    m.ranking = e('.number').find('em').text()
    return m


def save_cover(movies):
    for m in movies:
        filename = '{}.jpg'.format(m.ranking)
        get(m.cover_url, filename)


def cached_page(url):
    filename = '{}'.format(url.split('top100/', 1)[-1])
    page = get(url, filename)
    return page


def movies_from_url(url):
    """
    从 url 中下载网页并解析出页面内所有的电影
    """
    page = cached_page(url)
    e = pq(page)
    items = e('.top_list').find('li')
    # 调用 movie_from_div
    movies = [movie_from_div(i) for i in items]
    save_cover(movies)
    return movies


def main():
    url = 'http://www.mtime.com/top/movie/top100/index.html'
    movies = movies_from_url(url)
    print('top10 movies', movies)
    for i in range(2, 11):
        url = 'http://www.mtime.com/top/movie/top100/index-{}.html'.format(i)
        movies = movies_from_url(url)
        print('top{} movies'.format(i * 10), movies)


if __name__ == '__main__':
    main()