"""Small synchronous OpenAI-compatible image client; never persists API keys."""
import argparse
import base64
import getpass
import io
import json
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def https_url(value):
    p = urllib.parse.urlsplit(value)
    if p.scheme != 'https' or not p.hostname or p.username or p.password or p.query or p.fragment:
        raise ValueError('API地址必须为不带账号、查询参数或片段的HTTPS地址')
    return value.rstrip('/')


def run_generate(config, prompt, output, size, key):
    from PIL import Image
    endpoint = https_url(config['base_url']) + '/images/generations'
    payload = json.dumps({'model': config['model'], 'prompt': prompt, 'n': 1, 'size': size}).encode('utf-8')
    request = urllib.request.Request(endpoint, data=payload, headers={
        'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'
    })
    # Prevent credentials being forwarded by automatic POST redirects.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = urllib.request.build_opener(NoRedirect)
    with opener.open(request, timeout=900) as response:
        raw = response.read(100 * 1024 * 1024 + 1)
    if len(raw) > 100 * 1024 * 1024:
        raise ValueError('响应过大，请检查供应商返回格式')
    data = json.loads(raw)
    if not data.get('data') or not isinstance(data['data'][0], dict):
        raise ValueError('响应不符合同步data[0]结构；没有自动重试')
    item = data['data'][0]
    if item.get('b64_json'):
        content = base64.b64decode(item['b64_json'], validate=True)
    elif item.get('url'):
        url = item['url']
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('图片下载地址必须为HTTPS')
        # No API Authorization header on a separate download request.
        with opener.open(urllib.request.Request(url), timeout=120) as response:
            content = response.read(50 * 1024 * 1024 + 1)
        if len(content) > 50 * 1024 * 1024:
            raise ValueError('下载图片过大')
    else:
        raise ValueError('未返回图片；异步任务需要专用适配器')
    with Image.open(io.BytesIO(content)) as image:
        image.verify()
    with Image.open(io.BytesIO(content)) as image:
        image.load()
        image = image.copy()
    destination = Path(output)
    if destination.exists():
        raise FileExistsError('输出文件已存在，请换新文件名')
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.image-', suffix='.png', dir=destination.parent)
    os.close(fd)
    try:
        image.save(temporary, format='PNG')
        # Exclusive creation avoids overwriting an existing output.
        with destination.open('xb') as stream:
            stream.write(Path(temporary).read_bytes())
    finally:
        Path(temporary).unlink(missing_ok=True)
    return {'file': str(destination.resolve()), 'width': image.width, 'height': image.height}


def main():
    parser = argparse.ArgumentParser(description='用户自配生图API：不保存密钥、不自动重试')
    commands = parser.add_subparsers(dest='command', required=True)
    configure = commands.add_parser('configure')
    configure.add_argument('--config', required=True)
    generate = commands.add_parser('generate')
    generate.add_argument('--config', required=True)
    generate.add_argument('--prompt-file', required=True)
    generate.add_argument('--output', required=True)
    generate.add_argument('--size', default='1536x1024')
    args = parser.parse_args()
    try:
        if args.command == 'configure':
            base = https_url(input('API基础地址（含/v1，按文档填写）: ').strip())
            model = input('准确模型名称: ').strip()
            if not model:
                raise ValueError('模型不能为空')
            path = Path(args.config)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('x', encoding='utf-8') as stream:
                json.dump({'base_url': base, 'model': model}, stream, ensure_ascii=False, indent=2)
            print('已保存地址和模型；密钥将在生成时隐藏输入。')
            return 0
        config = json.loads(Path(args.config).read_text(encoding='utf-8'))
        if set(config) != {'base_url', 'model'}:
            raise ValueError('配置只允许base_url和model，禁止保存密钥')
        prompt = Path(args.prompt_file).read_text(encoding='utf-8-sig').strip()
        if not prompt or not isinstance(config['model'], str) or not config['model'].strip():
            raise ValueError('提示词和模型不能为空')
        if Path(args.output).exists():
            raise FileExistsError('输出文件已存在；未调用API')
        key = os.environ.get('PPT_IMAGE_API_KEY') or getpass.getpass('API密钥（隐藏，不保存）: ')
        if not key.strip():
            raise ValueError('密钥不能为空')
        print(json.dumps(run_generate(config, prompt, args.output, args.size, key), ensure_ascii=False))
        return 0
    except urllib.error.HTTPError as error:
        print(json.dumps({'error': 'HTTP请求失败，未打印响应正文；请在服务商后台核对', 'status': error.code, 'retried': False}, ensure_ascii=False))
    except (ValueError, FileExistsError) as error:
        print(str(error))
    except Exception as error:
        # Exception text may contain URLs or other service data: show type only.
        print('操作失败：' + type(error).__name__ + '；没有自动重试，请核对已有任务。')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
