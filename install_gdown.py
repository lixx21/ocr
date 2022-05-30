import gdown

url ="https://drive.google.com/file/d/1iD0f0hn461fur_8byxSFp2DiX9n8GCCD/view?usp=sharing"
output = "ocr-model-Felix-5.h5"
gdown.download(url, output, quiet=False, fuzzy=True)
