"""Extract native Fusion report images without dumping embedded image data."""
from html.parser import HTMLParser
from pathlib import Path
import base64
import json
import sys


class Report(HTMLParser):
    def __init__(self, output):
        super().__init__()
        self.output = output
        self.section = 'general'
        self.images = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'table' and attrs.get('id'):
            self.section = attrs['id']
        if tag == 'img' and attrs.get('src', '').startswith('data:image/'):
            source = attrs['src']
            extension = source.split(';', 1)[0].split('/')[-1]
            path = self.output / f'{len(self.images):02d}_{self.section}.{extension}'
            path.write_bytes(base64.b64decode(source.split(',', 1)[1]))
            self.images.append({'section': self.section, 'path': str(path)})


source = Path(sys.argv[1])
output = source.with_suffix('')
output.mkdir(exist_ok=True)
report = Report(output)
report.feed(source.read_text())
print(json.dumps(report.images, ensure_ascii=False, indent=2))
