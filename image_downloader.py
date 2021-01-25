import os
import urllib.request


def download_image(url, image_id, path_to_picture, path_to_archive_file):
    opener = urllib.request.build_opener()
    opener.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/81.0')]
    urllib.request.install_opener(opener)
    file_extension = ""
    file_name = str(url).split("/")[-1]
    file_extension = file_name.split(".")[-1]
    succeeded = False
    try:
        urllib.request.urlretrieve(url, path_to_picture + "." + file_extension)
        succeeded = True
        with open(path_to_archive_file, "a", encoding="utf-8") as write_file:
            write_file.writelines(str(image_id) + "\n")
    except:
        print("Couldn't find: " + url)
        succeeded = False
    return succeeded
