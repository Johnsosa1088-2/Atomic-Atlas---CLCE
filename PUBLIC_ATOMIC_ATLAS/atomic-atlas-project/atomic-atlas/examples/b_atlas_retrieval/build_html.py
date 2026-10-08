"""Embed the actual corpus and engine into one portable offline HTML."""
import pathlib
ROOT=pathlib.Path(__file__).resolve().parent
data=(ROOT/'data.json').read_text(encoding='utf-8').replace('</','<\\/')
engine=(ROOT/'engine.js').read_text(encoding='utf-8').replace('</','<\\/')
template=(ROOT/'template.html').read_text(encoding='utf-8')
(ROOT/'index.html').write_text(template.replace('__DATA__',data).replace('__ENGINE__',engine),encoding='utf-8')
print(ROOT/'index.html')
