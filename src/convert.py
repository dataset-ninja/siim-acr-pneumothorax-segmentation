import csv
import supervisely as sly
import os
from dataset_tools.convert import unpack_if_archive
import src.settings as s
from urllib.parse import unquote, urlparse
from supervisely.io.fs import get_file_name, get_file_name_with_ext

from tqdm import tqdm

def download_dataset(teamfiles_dir: str) -> str:
    """Use it for large datasets to convert them on the instance"""
    api = sly.Api.from_env()
    team_id = sly.env.team_id()
    storage_dir = sly.app.get_data_dir()

    if isinstance(s.DOWNLOAD_ORIGINAL_URL, str):
        parsed_url = urlparse(s.DOWNLOAD_ORIGINAL_URL)
        file_name_with_ext = os.path.basename(parsed_url.path)
        file_name_with_ext = unquote(file_name_with_ext)

        sly.logger.info(f"Start unpacking archive '{file_name_with_ext}'...")
        local_path = os.path.join(storage_dir, file_name_with_ext)
        teamfiles_path = os.path.join(teamfiles_dir, file_name_with_ext)

        fsize = api.file.get_directory_size(team_id, teamfiles_dir)
        with tqdm(
            desc=f"Downloading '{file_name_with_ext}' to buffer...",
            total=fsize,
            unit="B",
            unit_scale=True,
        ) as pbar:        
            api.file.download(team_id, teamfiles_path, local_path, progress_cb=pbar)
        dataset_path = unpack_if_archive(local_path)

    if isinstance(s.DOWNLOAD_ORIGINAL_URL, dict):
        for file_name_with_ext, url in s.DOWNLOAD_ORIGINAL_URL.items():
            local_path = os.path.join(storage_dir, file_name_with_ext)
            teamfiles_path = os.path.join(teamfiles_dir, file_name_with_ext)

            if not os.path.exists(get_file_name(local_path)):
                fsize = api.file.get_directory_size(team_id, teamfiles_dir)
                with tqdm(
                    desc=f"Downloading '{file_name_with_ext}' to buffer...",
                    total=fsize,
                    unit="B",
                    unit_scale=True,
                ) as pbar:
                    api.file.download(team_id, teamfiles_path, local_path, progress_cb=pbar)

                sly.logger.info(f"Start unpacking archive '{file_name_with_ext}'...")
                unpack_if_archive(local_path)
            else:
                sly.logger.info(
                    f"Archive '{file_name_with_ext}' was already unpacked to '{os.path.join(storage_dir, get_file_name(file_name_with_ext))}'. Skipping..."
                )

        dataset_path = storage_dir
    return dataset_path
    
def count_files(path, extension):
    count = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(extension):
                count += 1
    return count
    
def convert_and_upload_supervisely_project(
    api: sly.Api, workspace_id: int, project_name: str
) -> sly.ProjectInfo:
    ### Function should read local dataset and upload it to Supervisely project, then return project info.###
    images_path = os.path.join("siim-acr-pneumothorax","png_images")
    masks_path = os.path.join("siim-acr-pneumothorax","png_masks")
    train_csv_path = os.path.join("siim-acr-pneumothorax","stage_1_train_images.csv")
    test_csv_path = os.path.join("siim-acr-pneumothorax","stage_1_test_images.csv")
    batch_size = 30

    img_height = 1024
    img_wight = 1024


    def create_ann(image_path):
        labels = []

        image_name = get_file_name_with_ext(image_path)

        image_data = images_data[image_name]
        image_id = sly.Tag(tag_image_id, value=image_data[0])
        pneumo_value = value_to_pneumo[image_data[1]]
        pneumo = sly.Tag(tag_image_id, value=pneumo_value)

        mask_path = os.path.join(masks_path, image_name)
        mask_np = sly.imaging.image.read(mask_path)[:, :, 0]

        mask = mask_np == 255
        curr_bitmap = sly.Bitmap(mask)
        curr_label = sly.Label(curr_bitmap, obj_class)
        labels.append(curr_label)

        return sly.Annotation(
            img_size=(img_height, img_wight), labels=labels, img_tags=[image_id, pneumo]
        )


    obj_class = sly.ObjClass("pneumothorax", sly.Bitmap)

    tag_image_id = sly.TagMeta("image id", sly.TagValueType.ANY_STRING)
    tag_pneumo = sly.TagMeta("has pneumo", sly.TagValueType.ANY_STRING)

    value_to_pneumo = {"0": "False", "1": "True"}


    project = api.project.create(workspace_id, project_name, change_name_if_conflict=True)
    meta = sly.ProjectMeta(obj_classes=[obj_class], tag_metas=[tag_image_id, tag_pneumo])
    api.project.update_meta(project.id, meta.to_json())

    train_split = {}
    with open(train_csv_path, "r") as file:
        csvreader = csv.reader(file)
        for idx, row in enumerate(csvreader):
            if idx != 0:
                train_split[row[0]] = (row[1], row[2])

    test_split = {}
    with open(test_csv_path, "r") as file:
        csvreader = csv.reader(file)
        for idx, row in enumerate(csvreader):
            if idx != 0:
                test_split[row[0]] = (row[1], row[2])

    ds_name_to_data = {"train": train_split, "test": test_split}

    for ds_name, images_data in ds_name_to_data.items():
        images_names = list(images_data.keys())

        dataset = api.dataset.create(project.id, ds_name, change_name_if_conflict=True)

        progress = sly.Progress("Create dataset {}".format(ds_name), len(images_names))

        for img_names_batch in sly.batched(images_names, batch_size=batch_size):
            images_pathes_batch = [
                os.path.join(images_path, image_name) for image_name in img_names_batch
            ]

            img_infos = api.image.upload_paths(dataset.id, img_names_batch, images_pathes_batch)
            img_ids = [im_info.id for im_info in img_infos]

            anns_batch = [create_ann(image_path) for image_path in images_pathes_batch]
            api.annotation.upload_anns(img_ids, anns_batch)

            progress.iters_done_report(len(img_names_batch))


