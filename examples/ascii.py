from PIL import Image
import requests
from io import BytesIO



image = 'https://avatars3.githubusercontent.com/u/33701864?s=460&u=91f0c9f0ee2c4df114f5eed98fe31d8ef6a69fbc&v=4'
if image.startswith("http"):
    response = requests.get(image)
    im = Image.open(BytesIO(response.content))
else:
    im = Image.open(image)
im.save('converted.gif', 'gif')