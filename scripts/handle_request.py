import base64
import random
import os
import json
from io import BytesIO
import gzip

tests_per_cluster = 10

def get_response(data):
    user_id = data.userId
    current_cluster, current_test = get_current_progress(user_id)
    done=False
    total_clusters = get_total_clusters()

    if image_was_selected(data):
        record_selection(data.selectedImgId, data.choiceIds, user_id, current_cluster)
        next_test = current_test + 1
        next_cluster = current_cluster
        if next_test > tests_per_cluster:
            next_test = 1
            next_cluster += 1
            total_clusters = get_total_clusters()
            done = next_cluster >= total_clusters
    else:
        next_test = current_test
        next_cluster = current_cluster
        total_clusters = get_total_clusters()
        done = next_cluster >= total_clusters

    if not done:
        in_cluster_filenames = get_png_filenames([next_cluster])
        print(in_cluster_filenames)
        out_of_cluster_filenames = get_png_filenames([i for i in range(total_clusters) if i != next_cluster])
        # Calculate the start index based on the test number
        start_index = (next_test - 1) * 2 
        # Select 2 files per test following the order from 0 to 20
        random_in_cluster_filenames = in_cluster_filenames[start_index : start_index + 2]
        random_out_of_cluster_filename = random.sample(out_of_cluster_filenames, 1)
        in_cluster_base64_imgs = list(map(png_to_base64, random_in_cluster_filenames))
        out_of_cluster_base64_imgs = list(map(png_to_base64, random_out_of_cluster_filename))
        json_data = generate_json(in_cluster_base64_imgs + out_of_cluster_base64_imgs, 
                             random_in_cluster_filenames + random_out_of_cluster_filename,
                             next_test, tests_per_cluster, next_cluster, total_clusters)
    else:
        json_data = json.dumps({ 'done': True })
    
    resp = gzipencode(json_data.encode('utf-8'))
    return resp


def image_was_selected(data):
    return isinstance(data.selectedImgId, str)

def record_selection(selected_img_id, choice_ids, user_id, current_cluster):
    user_directory = get_directory(['response', user_id])

    filename = str(current_cluster) + '.txt'
    full_path = os.path.join(user_directory, filename)
    with open(full_path, 'a+') as file:
        for choice_id in choice_ids:
            file.write(choice_id + ' ')

        file.write(selected_img_id + ',')
        

def get_current_progress(user_id):
    user_directory = get_directory(['response', user_id])
    if not os.path.exists(user_directory):
        os.makedirs(user_directory)

    current_cluster = get_current_cluster(user_directory)
    current_test = get_current_test(user_directory, current_cluster)

    if current_test > tests_per_cluster:
        current_test = 1
        current_cluster += 1

    return current_cluster, current_test

def get_current_test(user_directory, current_cluster):
    full_path = os.path.join(user_directory, str(current_cluster) + '.txt')
    num_responses = count_values_in_file(full_path)
    return num_responses + 1

def count_values_in_file(file_path):
    with open(file_path, 'r') as f:
        data = f.read().strip(',')
    if data:
        values = data.split(',')
        return len(values)
    else:
        return 0

def create_file(file_path):
    with open(file_path, 'w') as f:
        pass

def get_current_cluster(user_directory):
    cluster_files = list_txt_files_without_extension(user_directory)
    cluster_files.sort()
    if len(cluster_files) == 0:
        create_file(os.path.join(user_directory, '0.txt'))
        current_cluster = 0
    else:
        current_cluster = int(cluster_files[-1])
    
    return current_cluster

def get_total_clusters():
    image_directory = get_directory(['imgs'])
    return len(list_subdirectories(image_directory))

def get_directory(dir_list):
    script_directory = os.path.dirname(os.path.realpath(__file__))
    sub_directory = os.path.join(script_directory, '..', *dir_list)
    return sub_directory

def list_txt_files_without_extension(directory):
    return [os.path.splitext(name)[0] for name in os.listdir(directory) if name.endswith('.txt')]

def list_subdirectories(directory):
    return [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]

def get_png_filenames(clusters):
    res = []
    for cluster in clusters:
        filenames = [(cluster, f) for f in os.listdir(get_directory(['imgs', str(cluster)])) if f.endswith('.png')]
        res.extend(filenames)

    return res

def png_to_base64(cluster_and_filename):
    cluster = cluster_and_filename[0]
    filename = cluster_and_filename[1]
    image_directory = get_directory(['imgs', str(cluster)])
    complete_filepath = os.path.join(image_directory, filename)
    with open(complete_filepath, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def generate_json(base64_imgs, filenames, next_test, tests_per_cluster, next_cluster, total_clusters):
    zipped = list(zip(base64_imgs, filenames))
    random.shuffle(zipped)
    base64_imgs, filenames = zip(*zipped)
    data = { 'testIdx': next_test, 'totalTests': tests_per_cluster, 'clusterIdx': next_cluster, 'totalClusters': total_clusters }
    for i in range(3):
        id = os.path.splitext(filenames[i][1])[0]
        data['img' + str(i + 1)] = {'base64': base64_imgs[i], 'id': id}
    
    data['done'] = False
    return json.dumps(data)

def gzipencode(content):
    out = BytesIO()
    f = gzip.GzipFile(fileobj=out, mode='w', compresslevel=5)
    f.write(content)
    f.close()
    return out.getvalue()
