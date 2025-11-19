import os
import re
import zipfile
from xml.sax.saxutils import escape
from PIL import Image

BASE = os.path.dirname(os.path.dirname(__file__))
MD_PATH = os.path.join(BASE, 'docs', 'reporte_final.md')
OUT_PATH = os.path.join(BASE, 'docs', 'reporte_final.docx')
IMAGES = [
    ('Figura 1. Promedio C1 por método.', os.path.join(BASE, 'results', 'plots', 'avg_C1.png')),
    ('Figura 2. Promedio C2 por método.', os.path.join(BASE, 'results', 'plots', 'avg_C2.png')),
    ('Figura 3. Promedio de C3 (balance) por método.', os.path.join(BASE, 'results', 'plots', 'avg_C3.png')),
    ('Figura 4. Tiempo promedio por método.', os.path.join(BASE, 'results', 'plots', 'avg_time.png')),
]

HEADING1 = re.compile(r'^#\s+(.*)')
HEADING2 = re.compile(r'^##\s+(.*)')
BULLET = re.compile(r'^-\s+(.*)')
NUMBERED = re.compile(r'^[0-9]+\.\s+(.*)')


def parse_markdown(path):
    paragraphs = []
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    in_code = False
    code_lines = []
    for line in lines:
        if line.strip().startswith('```'):
            if in_code:
                paragraphs.append({'type': 'code', 'text': '\n'.join(code_lines).rstrip()})
                code_lines = []
            in_code = not in_code
            continue
        if in_code:
            code_lines.append(line)
            continue
        if HEADING1.match(line):
            paragraphs.append({'type': 'heading1', 'text': HEADING1.match(line).group(1).strip()})
            continue
        if HEADING2.match(line):
            paragraphs.append({'type': 'heading2', 'text': HEADING2.match(line).group(1).strip()})
            continue
        if BULLET.match(line):
            paragraphs.append({'type': 'bullet', 'text': BULLET.match(line).group(1).strip()})
            continue
        if NUMBERED.match(line):
            paragraphs.append({'type': 'text', 'text': line.strip()})
            continue
        if line.strip() == '':
            paragraphs.append({'type': 'blank'})
        else:
            paragraphs.append({'type': 'text', 'text': line.strip()})
    return paragraphs


def paragraph_xml(text, style=None, bullet=False):
    text = escape(text).replace('\n', '</w:t><w:br/><w:t>')
    props = ''
    if style:
        props += f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
    elif bullet:
        text = '• ' + text
    return f'<w:p>{props}<w:r><w:t>{text}</w:t></w:r></w:p>'


def code_paragraph(text):
    text = escape(text).replace('\n', '</w:t><w:br/><w:t>')
    return (
        '<w:p>'
        '<w:r>'
        '<w:rPr>'
        '<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New"/>'
        '</w:rPr>'
        f'<w:t>{text}</w:t>'
        '</w:r>'
        '</w:p>'
    )


def image_paragraph(rel_id, descr, width_px, height_px, dpi=96):
    cx = int(width_px / dpi * 914400)
    cy = int(height_px / dpi * 914400)
    docpr_id = abs(hash(rel_id)) % (10**6)
    return f"""
<w:p>
  <w:r>
    <w:drawing>
      <wp:inline distT=\"0\" distB=\"0\" distL=\"0\" distR=\"0\" xmlns:wp=\"http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing\">
        <wp:extent cx=\"{cx}\" cy=\"{cy}\"/>
        <wp:docPr id=\"{docpr_id}\" name=\"{escape(descr)}\"/>
        <a:graphic xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\">
          <a:graphicData uri=\"http://schemas.openxmlformats.org/drawingml/2006/picture\">
            <pic:pic xmlns:pic=\"http://schemas.openxmlformats.org/drawingml/2006/picture\">
              <pic:nvPicPr>
                <pic:cNvPr id=\"{docpr_id}\" name=\"{escape(descr)}\"/>
                <pic:cNvPicPr/>
              </pic:nvPicPr>
              <pic:blipFill>
                <a:blip r:embed=\"{rel_id}\"/>
                <a:stretch><a:fillRect/></a:stretch>
              </pic:blipFill>
              <pic:spPr>
                <a:xfrm>
                  <a:off x=\"0\" y=\"0\"/>
                  <a:ext cx=\"{cx}\" cy=\"{cy}\"/>
                </a:xfrm>
                <a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom>
              </pic:spPr>
            </pic:pic>
          </a:graphicData>
        </a:graphic>
      </wp:inline>
    </w:drawing>
  </w:r>
</w:p>
"""


def build_docx(paragraphs, images):
    # Append figures
    for caption, path in images:
        paragraphs.append({'type': 'text', 'text': caption})
        paragraphs.append({'type': 'image', 'path': path, 'descr': caption})

    blocks = []
    image_entries = []
    for para in paragraphs:
        t = para.get('type')
        if t == 'heading1':
            blocks.append(paragraph_xml(para['text'], style='Heading1'))
        elif t == 'heading2':
            blocks.append(paragraph_xml(para['text'], style='Heading2'))
        elif t == 'bullet':
            blocks.append(paragraph_xml(para['text'], bullet=True))
        elif t == 'code':
            blocks.append(code_paragraph(para['text']))
        elif t == 'image':
            path = para['path']
            descr = para['descr']
            image_entries.append((path, descr))
            # placeholder, actual drawing added after relationships assigned
            blocks.append({'image_placeholder': len(image_entries)-1})
        elif t == 'blank':
            blocks.append('<w:p/>')
        else:
            blocks.append(paragraph_xml(para.get('text', '')))

    # relationships
    rels = [('<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>')]
    media_files = []
    for idx, (img_path, descr) in enumerate(image_entries, start=1):
        rel_id = f'rIdIMG{idx}'
        rels.append(f'<Relationship Id="{rel_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/img{idx}.png"/>')
        media_files.append((img_path, f'word/media/img{idx}.png', rel_id, descr))

    # replace placeholders with drawings
    new_blocks = []
    placeholder_index = 0
    for block in blocks:
        if isinstance(block, str):
            new_blocks.append(block)
        else:
            rel_id = media_files[placeholder_index][2]
            descr = media_files[placeholder_index][3]
            width, height = Image.open(media_files[placeholder_index][0]).size
            new_blocks.append(image_paragraph(rel_id, descr, width, height))
            placeholder_index += 1
    blocks = new_blocks

    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" mc:Ignorable="w14 wp14">
  <w:body>
    {''.join(blocks)}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
      <w:cols w:space="720"/>
      <w:docGrid w:linePitch="360"/>
    </w:sectPr>
  </w:body>
</w:document>
"""

    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:qFormat/>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:spacing w:after="200"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="32"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr><w:spacing w:after="120"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="28"/></w:rPr>
  </w:style>
</w:styles>
"""

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>
"""

    package_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="R1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

    doc_rels = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
  {rels}
</Relationships>
""".format(rels=''.join(rels))

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with zipfile.ZipFile(OUT_PATH, 'w') as zf:
        zf.writestr('[Content_Types].xml', content_types)
        zf.writestr('_rels/.rels', package_rels)
        zf.writestr('word/document.xml', document_xml)
        zf.writestr('word/styles.xml', styles_xml)
        zf.writestr('word/_rels/document.xml.rels', doc_rels)
        for src, dst, _, _ in media_files:
            with open(src, 'rb') as img_f:
                zf.writestr(dst, img_f.read())


if __name__ == '__main__':
    paragraphs = parse_markdown(MD_PATH)
    build_docx(paragraphs, IMAGES)
    print('Documento generado en', OUT_PATH)
