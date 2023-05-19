import base64
import random
import os
import json
from io import BytesIO
import gzip

def get_response(data):
    if image_was_selected(data):
        record_selection(data.id, data.ip)

    png_filenames = get_png_filenames()
    three_random_filenames = random.sample(png_filenames, 3)
    base64_imgs = list(map(png_to_base64, three_random_filenames))
    json = generate_json(base64_imgs, three_random_filenames)
    resp = gzipencode(json.encode('utf-8'))
    return resp

def record_selection(selected_id, ip):
    response_directory = get_sub_directory('response')
    filename = ip + '.txt'
    full_path = os.path.join(response_directory, filename)
    with open(full_path, 'a+') as file:
        file.write(selected_id + ' ')

def image_was_selected(data):
    return isinstance(data.id, str)

def get_sub_directory(dir):
    script_directory = os.path.dirname(os.path.realpath(__file__))
    sub_directory = os.path.join(script_directory, '..', dir)
    return sub_directory
    
def png_to_base64(filename):
    image_directory = get_sub_directory('imgs')
    complete_filepath = os.path.join(image_directory, filename)
    with open(complete_filepath, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_png_filenames():
    image_directory = get_sub_directory('imgs')    
    return [f for f in os.listdir(image_directory) if f.endswith('.png')]

def generate_json(base64_imgs, filenames):
    data = {}
    for i in range(3):
        id = os.path.splitext(filenames[i])[0]
        data['img' + str(i + 1)] = {'base64': base64_imgs[i], 'id': id}
    return json.dumps(data)    

def gzipencode(content):
    out = BytesIO()
    f = gzip.GzipFile(fileobj=out, mode='w', compresslevel=5)
    f.write(content)
    f.close()
    return out.getvalue()