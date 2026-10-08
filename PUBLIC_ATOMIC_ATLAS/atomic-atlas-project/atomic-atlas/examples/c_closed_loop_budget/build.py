from pathlib import Path
import json
root=Path(__file__).resolve().parent
model=(root/'model.js').read_text()
app=(root/'app.js').read_text()
template=(root/'index.template.html').read_text()
html=template.replace('/* MODEL_INLINE */',model+'\nconst MODEL_SOURCE='+json.dumps(model)+';').replace('/* APP_INLINE */',app)
(root/'index.html').write_text(html)
print('Built standalone HTML')

