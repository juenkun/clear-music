#!/usr/bin/env python3
"""Clear-music AI DJ - 本地服务器（含音乐搜索代理）"""
import json
import os
import re
import urllib.request
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler


class DJHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

    def do_GET(self):
        if self.path.startswith('/api/search'):
            self.handle_search()
        else:
            super().do_GET()

    def handle_search(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        platform = params.get('platform', ['netease'])[0]
        song = params.get('song', [''])[0]
        artist = params.get('artist', [''])[0]

        if not song:
            self.send_json({'error': 'missing song'}, 400)
            return

        try:
            if platform == 'qq':
                result = self.search_qq(song, artist)
            elif platform == 'netease':
                result = self.search_netease(song, artist)
            else:
                result = {'error': f'unsupported platform: {platform}'}
        except Exception as e:
            result = {'error': str(e), 'song': song, 'artist': artist}

        self.send_json(result)

    def search_qq(self, song, artist):
        """搜索 QQ 音乐，返回第一首匹配歌曲的 songmid"""
        keywords = f'{song} {artist}'.strip()
        url = f'https://c.y.qq.com/splcloud/fcgi-bin/smartbox_new.fcg?key={urllib.parse.quote(keywords)}&format=json&inCharset=utf-8&outCharset=utf-8'
        data = self.fetch_json(url)

        # smartbox 返回结构: data.song.itemlist
        items = data.get('data', {}).get('song', {}).get('itemlist', [])
        if not items:
            return {'error': 'no match', 'song': song, 'artist': artist}

        best = items[0]
        songmid = best.get('mid', '')
        songname = best.get('name', song)
        singer = best.get('singer', artist)

        # Universal Link: 手机有 QQ 音乐时会自动唤起 App
        return {
            'found': True,
            'song': songname,
            'artist': singer,
            'songmid': songmid,
            'url': f'https://y.qq.com/n/ryqq/songDetail/{songmid}'
        }

    def search_netease(self, song, artist):
        """搜索网易云音乐，返回第一首匹配歌曲的 id"""
        keywords = f'{song} {artist}'.strip()
        url = f'https://music.163.com/api/search/get?s={urllib.parse.quote(keywords)}&type=1&limit=1'
        data = self.fetch_json(url, referer='https://music.163.com/')

        songs = data.get('result', {}).get('songs', [])
        if not songs:
            return {'error': 'no match', 'song': song, 'artist': artist}

        best = songs[0]
        song_id = best.get('id', 0)
        songname = best.get('name', song)
        singer_name = best.get('artists', [{}])[0].get('name', artist)

        return {
            'found': True,
            'song': songname,
            'artist': singer_name,
            'id': song_id,
            'url': f'https://music.163.com/song?id={song_id}'
        }

    def fetch_json(self, url, referer=None):
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        if referer:
            req.add_header('Referer', referer)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        if '/api/' in str(args[0]):
            print(f'  [{self.log_date_time_string()}] {args[0]}')
        else:
            pass  # 静默静态文件日志


if __name__ == '__main__':
    port = 8080
    print(f'=== Clear-music AI DJ 服务器 ===')
    print(f'本地: http://localhost:{port}')
    print(f'API:  http://localhost:{port}/api/search?platform=qq&song=xxx&artist=xxx')
    HTTPServer(('0.0.0.0', port), DJHandler).serve_forever()
