import base64
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

spec = importlib.util.spec_from_file_location('image_api', Path(__file__).parents[1] / 'scripts/image_api.py')
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


class Response(io.BytesIO):
    pass


class ImageClientTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.output = Path(self.temp.name) / 'output.png'
        self.config = {'base_url': 'https://api.example.com/v1', 'model': 'test-model'}
        image = io.BytesIO()
        Image.new('RGB', (32, 18), 'green').save(image, 'PNG')
        self.image = image.getvalue()

    def tearDown(self):
        self.temp.cleanup()

    def fake_opener(self, item):
        class Opener:
            def open(inner, request, timeout):
                self.request = request
                return Response(json.dumps({'data': [item]}).encode())
        return Opener()

    def test_success_validates_image_and_writes_png(self):
        item = {'b64_json': base64.b64encode(self.image).decode()}
        with patch.object(api.urllib.request, 'build_opener', return_value=self.fake_opener(item)):
            result = api.run_generate(self.config, '测试', self.output, '32x18', 'test-only')
        self.assertEqual((result['width'], result['height']), (32, 18))
        self.assertEqual(json.loads(self.request.data)['model'], 'test-model')
        self.assertEqual(self.output.read_bytes(), self.image)

    def test_invalid_image_is_not_saved(self):
        item = {'b64_json': base64.b64encode(b'invalid').decode()}
        with patch.object(api.urllib.request, 'build_opener', return_value=self.fake_opener(item)):
            with self.assertRaises(Exception):
                api.run_generate(self.config, '测试', self.output, '32x18', 'test-only')
        self.assertFalse(self.output.exists())

    def test_url_download_does_not_forward_api_key(self):
        requests = []
        class Opener:
            def open(inner, request, timeout):
                requests.append(request)
                if len(requests) == 1:
                    return Response(json.dumps({'data': [{'url': 'https://cdn.example.com/a.png?token=example'}]}).encode())
                return Response(self.image)
        with patch.object(api.urllib.request, 'build_opener', return_value=Opener()):
            api.run_generate(self.config, '测试', self.output, '32x18', 'test-only')
        self.assertIsNone(requests[1].get_header('Authorization'))

    def test_rejects_unsafe_base_urls(self):
        for url in ['http://example.com/v1', 'https://user:pass@example.com/v1', 'https://example.com/v1?key=example']:
            with self.assertRaises(ValueError):
                api.https_url(url)


if __name__ == '__main__':
    unittest.main()
