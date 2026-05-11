// Clear-music 音乐搜索代理 — Cloudflare Worker
// 部署到 Workers 后，将 URL 填入网页的 Worker URL 设置即可
// 免费额度 10 万次/天

export default {
  async fetch(request) {
    const url = new URL(request.url);

    // CORS 预检
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        }
      });
    }

    if (url.pathname === '/api/search') {
      return handleSearch(url);
    }

    return new Response('Clear-music proxy OK', { headers: cors() });
  }
};

async function handleSearch(url) {
  const platform = url.searchParams.get('platform') || 'netease';
  const song = url.searchParams.get('song') || '';
  const artist = url.searchParams.get('artist') || '';

  if (!song) {
    return json({ error: 'missing song' }, 400);
  }

  try {
    if (platform === 'qq') {
      return await searchQQ(song, artist);
    }
    return await searchNetease(song, artist);
  } catch (e) {
    return json({ error: e.message, song, artist });
  }
}

async function searchQQ(song, artist) {
  const keywords = encodeURIComponent(`${song} ${artist}`);
  const apiUrl = `https://c.y.qq.com/splcloud/fcgi-bin/smartbox_new.fcg?key=${keywords}&format=json&inCharset=utf-8&outCharset=utf-8`;

  const resp = await fetch(apiUrl);
  const data = await resp.json();
  const items = data?.data?.song?.itemlist || [];

  if (!items.length) {
    return json({ found: false, song, artist });
  }

  const best = items[0];
  return json({
    found: true,
    song: best.name || song,
    artist: best.singer || artist,
    songmid: best.mid || '',
    url: `https://y.qq.com/n/ryqq/songDetail/${best.mid}`
  });
}

async function searchNetease(song, artist) {
  const keywords = encodeURIComponent(`${song} ${artist}`);
  const apiUrl = `https://music.163.com/api/search/get?s=${keywords}&type=1&limit=1`;

  const resp = await fetch(apiUrl, {
    headers: { 'Referer': 'https://music.163.com/' }
  });
  const data = await resp.json();
  const songs = data?.result?.songs || [];

  if (!songs.length) {
    return json({ found: false, song, artist });
  }

  const best = songs[0];
  return json({
    found: true,
    song: best.name || song,
    artist: best.artists?.[0]?.name || artist,
    id: best.id || 0,
    url: `https://music.163.com/song?id=${best.id}`
  });
}

function json(data, status) {
  return new Response(JSON.stringify(data), {
    status: status || 200,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      ...cors()
    }
  });
}

function cors() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400'
  };
}
