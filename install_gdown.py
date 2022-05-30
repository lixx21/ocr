import gdown

url ="https://drive.google.com/file/d/1wLaE2mVfVsoM5ym9iRCU4VAfuYrKVBlq/view?usp=sharing"
output = "bounding_box_segmentation_5.h5"
gdown.download(url, output, quiet=False, fuzzy=True)
