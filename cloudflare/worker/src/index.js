/**
 * GitBlog TTS Worker
 * 手动触发 TTS 生成，结果存入 R2
 *
 * 路由:
 *   POST /tts/:issueNumber  - 为指定 issue 生成 TTS 音频
 *   GET  /status             - 查看服务状态
 */

const TTS_VOICE = 'zh-CN-XiaoxiaoNeural';
const MAX_CHARS = 5000;

// Microsoft Edge TTS WebSocket 端点
const TTS_URL = 'wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1';

// Trusted clients for API authentication
const API_TOKEN = typeof TTS_API_TOKEN !== 'undefined' ? TTS_API_TOKEN : '';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Status endpoint
    if (url.pathname === '/status') {
      return Response.json({
        service: 'gitblog-tts',
        status: 'ok',
        voice: TTS_VOICE,
      }, { headers: corsHeaders });
    }

    // TTS generation endpoint
    const ttsMatch = url.pathname.match(/^\/tts\/(\d+)$/);
    if (ttsMatch && request.method === 'POST') {
      // Optional token check
      if (API_TOKEN) {
        const auth = request.headers.get('Authorization');
        if (auth !== `Bearer ${API_TOKEN}`) {
          return Response.json({ error: 'Unauthorized' }, { status: 401, headers: corsHeaders });
        }
      }

      const issueNumber = ttsMatch[1];
      try {
        const result = await handleTTSRequest(issueNumber, env);
        return Response.json(result, { headers: corsHeaders });
      } catch (err) {
        return Response.json(
          { error: err.message || 'TTS generation failed' },
          { status: 500, headers: corsHeaders }
        );
      }
    }

    return Response.json({ error: 'Not found' }, { status: 404, headers: corsHeaders });
  },
};

async function handleTTSRequest(issueNumber, env) {
  const r2Key = `articles/${issueNumber}.mp3`;

  // Check if already exists in R2
  try {
    const existing = await env.TTS_BUCKET.head(r2Key);
    if (existing) {
      return {
        status: 'exists',
        issueNumber,
        message: 'Audio already exists in R2',
        key: r2Key,
      };
    }
  } catch (e) {
    // Ignore check errors, proceed with generation
  }

  // Fetch issue content from GitHub
  const issueBody = await fetchIssueContent(issueNumber, env);
  const cleanText = cleanTextForTTS(issueBody);

  if (!cleanText || cleanText.length < 10) {
    return { status: 'skipped', issueNumber, message: 'Content too short' };
  }

  // Generate audio via Microsoft TTS WebSocket
  const audioBuffer = await synthesizeSpeech(cleanText);

  // Upload to R2
  await env.TTS_BUCKET.put(r2Key, audioBuffer, {
    httpMetadata: { contentType: 'audio/mpeg' },
  });

  return {
    status: 'generated',
    issueNumber,
    key: r2Key,
    textLength: cleanText.length,
  };
}

async function fetchIssueContent(issueNumber, env) {
  const repo = env.GITHUB_REPO || 'myogg/gitblog';
  const token = env.GITHUB_TOKEN || '';

  const resp = await fetch(`https://api.github.com/repos/${repo}/issues/${issueNumber}`, {
    headers: {
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'gitblog-tts-worker',
      ...(token ? { Authorization: `token ${token}` } : {}),
    },
  });

  if (!resp.ok) {
    throw new Error(`GitHub API error: ${resp.status}`);
  }

  const data = await resp.json();
  return data.body || '';
}

function cleanTextForTts(body) {
  if (!body) return '';

  let text = body;

  // Remove YAML frontmatter
  text = text.replace(/^---\s*\n.*?\n---\s*\n/s, '');
  // Remove tags line
  text = text.replace(/^tags:.*$/gm, '');
  // Remove code blocks
  text = text.replace(/```[\s\S]*?```/g, '');
  // Remove inline code
  text = text.replace(/`[^`]+`/g, '');
  // Remove images
  text = text.replace(/!\[.*?\]\(.*?\)/g, '');
  // Remove links, keep text
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
  // Remove HTML tags
  text = text.replace(/<[^>]+>/g, '');
  // Remove HTML entities
  text = text.replace(/&[a-zA-Z]+;/g, ' ');
  // Remove comments
  text = text.replace(/<!--.*?-->/g, '');
  // Remove Markdown heading markers
  text = text.replace(/^#{1,6}\s+/gm, '');
  // Remove bold/italic markers
  text = text.replace(/\*{1,3}([^*]+)\*{1,3}/g, '$1');
  text = text.replace(/_{1,3}([^_]+)_{1,3}/g, '$1');
  // Remove quote markers
  text = text.replace(/^>\s+/gm, '');
  // Remove list markers
  text = text.replace(/^\s*[-*+]\s+/gm, '');
  text = text.replace(/^\s*\d+\.\s+/gm, '');
  // Remove horizontal rules
  text = text.replace(/^[-*_]{3,}$/gm, '');
  // Clean up whitespace
  text = text.replace(/\n{3,}/g, '\n\n').trim();

  // Truncate
  if (text.length > MAX_CHARS) {
    text = text.substring(0, MAX_CHARS) + '...';
  }

  return text;
}

async function synthesizeSpeech(text) {
  // Connect to Microsoft Edge TTS WebSocket
  const reqId = generateRequestId();
  const ws = new WebSocket(
    `${TTS_URL}?TrustedClientToken=6A5AA1D4EAFF4E9FB37E23D68491D6F4&ConnectionId=${reqId}`
  );

  return new Promise((resolve, reject) => {
    const audioChunks = [];
    let audioStarted = false;

    ws.addEventListener('open', () => {
      // Configuration message
      const configMsg = [
        'X-Timestamp:' + new Date().toISOString(),
        'Content-Type:application/json; charset=utf-8',
        'Path:speech.config',
        '',
        JSON.stringify({
          context: {
            synthesis: {
              audio: {
                metadataoptions: { sentenceBoundaryEnabled: 'false', wordBoundaryEnabled: 'true' },
                outputFormat: 'audio-24khz-48kbitrate-mono-mp3',
              },
            },
          },
        }),
      ].join('\r\n');
      ws.send(configMsg);

      // SSML message
      const ssml = [
        'X-RequestId:' + reqId,
        'Content-Type:application/ssml+xml',
        'Path:ssml',
        '',
        `<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'>` +
          `<voice name='${TTS_VOICE}'>${escapeXml(text)}</voice>` +
          `</speak>`,
      ].join('\r\n');
      ws.send(ssml);
    });

    ws.addEventListener('message', (event) => {
      const data = typeof event.data === 'string' ? event.data : '';

      if (data.includes('Path:turn.start')) {
        audioStarted = true;
      } else if (data.includes('Path:audio') && audioStarted) {
        // Extract binary audio data from the message
        const binaryHeader = 'Path:audio\r\n';
        const headerEnd = data.indexOf('\r\n\r\n');
        if (headerEnd !== -1) {
          // The binary data follows after the header separator
          // In Cloudflare Workers, we need to handle this differently
        }
      } else if (data.includes('Path:turn.end')) {
        ws.close();
      }
    });

    ws.addEventListener('error', (event) => {
      reject(new Error('WebSocket error during TTS synthesis'));
    });

    ws.addEventListener('close', () => {
      if (audioChunks.length > 0) {
        resolve(concatBuffers(audioChunks));
      } else {
        reject(new Error('No audio data received from TTS service'));
      }
    });

    // Timeout after 30 seconds
    setTimeout(() => {
      ws.close();
      reject(new Error('TTS synthesis timed out'));
    }, 30000);
  });
}

function generateRequestId() {
  return 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'.replace(/x/g, () =>
    Math.floor(Math.random() * 16).toString(16)
  );
}

function escapeXml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function concatBuffers(buffers) {
  let totalLen = 0;
  for (const b of buffers) totalLen += b.byteLength;
  const result = new Uint8Array(totalLen);
  let offset = 0;
  for (const b of buffers) {
    result.set(new Uint8Array(b), offset);
    offset += b.byteLength;
  }
  return result.buffer;
}
