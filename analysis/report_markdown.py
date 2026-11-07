"""Small, escaped Markdown renderer for assessment text and HTML navigation."""
import html
import re

TOKENS = re.compile(r'(\*\*.*?\*\*|`[^`]+`|\[[^\]]+\]\(https?://[^\s)]+\))')


def inline_html(text):
    pieces=[]
    for token in TOKENS.split(text):
        if token.startswith('**') and token.endswith('**'):
            pieces.append('<strong>'+inline_html(token[2:-2])+'</strong>')
        elif token.startswith('`') and token.endswith('`'):
            pieces.append('<code>'+html.escape(token[1:-1])+'</code>')
        elif (match:=re.fullmatch(r'\[([^\]]+)\]\((https?://[^\s)]+)\)',token)):
            pieces.append('<a href="'+html.escape(match[2],quote=True)+'">'+html.escape(match[1])+'</a>')
        else:
            pieces.append(html.escape(token))
    return ''.join(pieces)


def markdown_html(document):
    lines=document.splitlines(); output=[];i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:
            i+=1;continue
        if line.startswith('```'):
            block=[];i+=1
            while i<len(lines) and not lines[i].startswith('```'):
                block.append(lines[i]);i+=1
            output.append('<pre><code>'+html.escape('\n'.join(block))+'</code></pre>')
            i+=1;continue
        if match:=re.match(r'^(#{1,3}) (.*)',line):
            level=len(match[1]);output.append(f'<h{level}>'+inline_html(match[2])+f'</h{level}>')
            i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[cell.strip() for cell in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch('[-:]+',cell) for cell in cells):
                    rows.append(cells)
                i+=1
            output.append('<table border="1" cellpadding="6">')
            for j,row in enumerate(rows):
                tag='th' if j==0 else 'td'
                output.append('<tr>'+''.join(f'<{tag}>'+inline_html(cell)+f'</{tag}>' for cell in row)+'</tr>')
            output.append('</table>');continue
        paragraph=[line];i+=1
        while i<len(lines) and lines[i].strip() and not re.match(r'^(#|\||```)',lines[i].strip()):
            paragraph.append(lines[i].strip());i+=1
        output.append('<p>'+inline_html(' '.join(paragraph))+'</p>')
    return ''.join(output)


def add_contents(document):
    entries=[]
    def heading(match):
        level,body=match[1],match[2]
        anchor=f'section-{len(entries)+1:03d}'
        label=re.sub('<[^>]*>','',body)
        entries.append((int(level),anchor,label))
        return f'<h{level} id="{anchor}">{body}</h{level}>'
    document=re.sub(r'<h([1-3])>(.*?)</h\1>',heading,document,flags=re.DOTALL)
    navigation='<nav aria-label="Contents"><strong>Contents / Inhaltsverzeichnis / 目录</strong><ul>'
    navigation+=''.join(f'<li style="margin-left:{(level-1)*18}px"><a href="#{anchor}">{label}</a></li>' for level,anchor,label in entries)
    navigation+='</ul></nav>'
    return re.sub(r'(<body\b[^>]*>)',lambda m:m[1]+navigation,document,count=1)
