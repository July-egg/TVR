
from collections import defaultdict
from pathlib import Path
import shutil
from typing import Callable, Container, Dict, Iterator, List, Optional, Set, Tuple, Union, overload
import os
import json
from os import path
from datetime import date
from PIL import Image
import tqdm


class DObject:
    def __init__(self, left, top, right, bottom, category, owner) -> None:
        self.own = owner

        self.left = max(left, 0)
        self.top = max(top, 0)
        self.right = min(right, self.own.width())
        self.bottom = min(bottom, self.own.height())

        self.cat = category

        self.id = -1

    def box(self) -> Tuple[float, float, float, float]:
        return self.left, self.top, self.right, self.bottom

    def category(self) -> str:
        return self.cat

    def owner(self):
        return self.own

    def width(self) -> float:
        return self.right - self.left

    def height(self) -> float:
        return self.bottom - self.top

    def x(self) -> float:
        return (self.left + self.right) / 2

    def y(self) -> float:
        return (self.top + self.bottom) / 2

    def set_id(self, id) -> None:
        self.id = id

    def copy(self):
        obj = DObject(self.left, self.top, self.right, self.bottom, self.cat, self.own)
        obj.set_id(self.id)

        return obj

    def to_coco(self, categories: Dict[str, int]) -> dict:
        assert self.category() in categories
        assert self.id > 0

        return {
            'segmentation': [],
            'area': self.width() * self.height(),
            'iscrowd': 0,
            'image_id': self.owner().id,
            'bbox': [
                self.left, self.top, self.right - self.left, self.bottom - self.top
            ],
            'category_id': categories[self.category()],
            'id': self.id
        }


class DObjectIterator:
    def __init__(self, image, filter: Optional[Callable[[DObject], bool]]) -> None:
        self.image = image
        self.idx = 0
        self.filter = filter

    def __len__(self) -> int:
        if self.filter is None:
            return len(self.image)
        else:
            count = 0
            for obj in self.image.objects:
                if self.filter(obj):
                    count += 1
            return count

    def __next__(self) -> DObject:
        while self.idx < len(self.image):
            obj = self.image.objects[self.idx]

            self.idx += 1

            if self.filter is None or self.filter(obj):
                return obj

        raise StopIteration

    def __iter__(self) -> Iterator:
        return self


class DImage:
    def __init__(self, filepath: str, width, height) -> None:
        self.objects: List[DObject] = []
        self.path = filepath

        self.w = width
        self.h = height

        self.license_id = -1
        self.coco_url = None
        self.data_captured = None
        self.flickr_url = None
        self.id = -1

    def __len__(self) -> int:
        return len(self.objects)

    def width(self) -> int:
        return self.w

    def height(self) -> int:
        return self.h

    def filepath(self) -> str:
        return self.path

    def categories(self) -> Set[str]:
        cats = set()
        for obj in self.objects:
            cats.add(obj.category())
        return cats

    def change_size(self, height: int, width: int, dest_path: Optional[str]) -> None:
        height_scale = self.height() / height
        width_scale = self.width() / width

        scale = max(height_scale, width_scale)

        dest_height, dest_width = round(self.height() / scale), round(self.width() / scale)

        image = Image.open(self.filepath())
        temp = image.resize((dest_width, dest_height), Image.BICUBIC).convert('RGB')
        dest_image = temp.crop((0, 0, width, height))

        dest_path = dest_path if dest_path else self.filepath()

        dest_image.save(dest_path)
        self.set_filepath(dest_path)

        self.h = height
        self.w = width

        for obj in self:
            obj.left /= scale
            obj.right /= scale
            obj.top /= scale
            obj.bottom /= scale

    def __iter__(self):
        return self.iterator()

    def iterator(self, filter: Optional[Callable[[DObject], bool]]=None) -> DObjectIterator:
        return DObjectIterator(self, filter)

    def __add_object(self, obj: DObject) -> DObject:
        obj.own = self

        self.objects.append(obj)

        return obj

    def __add_object_params(self, left, top, right, bottom, category) -> DObject:
        obj = DObject(left, top, right, bottom, category, self)
        self.objects.append(obj)

        return obj

    @overload
    def add_object(self, left, top, right, bottom, category) -> None:
        ...

    @overload
    def add_object(self, obj: DObject) -> None:
        ...

    def add_object(self, p0, p1=None, p2=None, p3=None, p4=None) -> None:
        if p1 is None:
            return self.__add_object(p0)
        else:
            return self.__add_object_params(p0, p1, p2, p3, p4)

    def set_filepath(self, filepath) -> None:
        self.path = filepath

    def set_license_id(self, id) -> None:
        self.license_id = id

    def set_coco_url(self, url) -> None:
        self.coco_url = url

    def set_data_captured(self, date) -> None:
        self.data_captured = date

    def set_flickr_url(self, url) -> None:
        self.flickr_url = url

    def set_id(self, id) -> None:
        self.id = id

    def copy(self, filter: Optional[Callable[[DObject], bool]]=None):
        image = DImage(self.path, self.w, self.h)
        image.set_license_id(self.license_id)
        image.set_coco_url(self.coco_url)
        image.set_data_captured(self.data_captured)
        image.set_flickr_url(self.flickr_url)
        image.set_id(self.id)

        for obj in self.iterator(filter):
            image.add_object(obj.copy())

        return image

    def to_coco(self) -> dict:
        assert self.id > 0

        assert self.license_id > 0
        assert self.coco_url is not None
        assert self.data_captured is not None
        assert self.flickr_url is not None

        return {
            'license': self.license_id,
            'file_name': path.split(self.filepath())[1],
            'coco_url': self.coco_url,
            'height': self.height(),
            'width': self.width(),
            'data_captured': self.data_captured,
            'flickr_url': self.flickr_url,
            'id': self.id
        }


class DImageIterator:
    def __init__(self, dataset, filter: Optional[Callable[[DImage], bool]]) -> None:
        self.dataset = dataset
        self.idx = 0
        self.filter = filter

    def __len__(self) -> int:
        if self.filter is None:
            return len(self.dataset)
        else:
            count = 0
            for image in self.dataset.images:
                if self.filter(image):
                    count += 1
            return count

    def __next__(self) -> DImage:
        while self.idx < len(self.dataset):
            image = self.dataset.images[self.idx]

            self.idx += 1

            if self.filter is None or self.filter(image):
                return image

        raise StopIteration

    def __iter__(self) -> Iterator:
        return self


default_info = {
    'description': 'private vehicle dataset',
    'url': '',
    'version': '1.0',
    'year': '2021',
    'contributor': 'Wuhan University',
    'date_created': '2021/09/15',
}

default_licenses = [
    {
        'url': '',
        'id': 1,
        'name': 'Empty now'
    }
]

def union_info(info1, info2):
    sep = ' | '
    description = f"union from: {info1['description']}{sep}{info2['description']}"
    url = ''
    version = '1.0'
    contributor = sep.join([info1['contributor'], info2['contributor']])
    today = date.today()
    date_created = '/'.join(map(str,[today.year, today.month, today.day]))

    return {
        'description': description,
        'url': url,
        'version': version,
        'year': today.year,
        'contributor': contributor,
        'date_created': date_created
    }

def union_licenses(main_licenses, attached_licenses):
    if main_licenses is attached_licenses:
        return main_licenses, None

    max_id = max(l['id'] for l in attached_licenses)

    ids = set(l['id'] for l in main_licenses)

    licenses = main_licenses.copy()
    licenses_map = {}
    for lic in attached_licenses:
        lic_copy = lic.copy()
        if lic_copy['id'] in ids:
            max_id = max_id + 1
            licenses_map[lic_copy['id']] = max_id
            lic_copy['id'] = max_id
        licenses.append(lic_copy)

    if not licenses_map:
        licenses_map = None

    return licenses, licenses_map


class RawDataset:
    def __init__(self, raw_data, categories: Optional[List[dict]], default_image_params: Optional[dict], info=default_info, licenses=default_licenses) -> None:
        self.images = []
        self.raw_data = raw_data

        self.cats = categories
        self.cats_order = None
        self.info = info
        self.licenses = licenses

        self.default_image_params = default_image_params

    def __len__(self) -> int:
        return len(self.images)

    def data(self):
        return self.raw_data

    def category_details(self):
        return self.cats

    def designate_categories_order(self, cats: List[str]) -> None:
        if self.cats:
            cat_map = {c['name']: c['supercategory'] for c in self.category_details()}
            reorder = []
            ordered = set()
            iid = 1
            for cat in cats:
                if cat in cat_map:
                    reorder.append((iid, cat, cat_map[cat]))
                    ordered.add(cat)
                    iid += 1

            for cat in cat_map:
                if cat not in ordered:
                    reorder.append((iid, cat, cat_map[cat]))
                    iid += 1

            self.cats.clear()
            for iid, cat, super_cat in reorder:
                self.cats.append({
                    'supercategory': super_cat,
                    'id': iid,
                    'name': cat
                })
        else:
            self.cats_order = cats

    def arange_categories(self, categories: Union[str, List[Tuple[str, ...]]]) -> None:
        cats = set()
        for image in self.iterator():
            cats.update(image.categories())

        cat_to_supercat = {}
        if isinstance(categories, str):
            for cat in cats:
                cat_to_supercat[cat] = categories
        else:
            for supercat, *cats_param in categories:
                for cat in cats_param:
                    if cat in cats:
                        cat_to_supercat[cat] = supercat

        self.cats = []
        for i, (cat, supercat) in enumerate(cat_to_supercat.items()):
            self.cats.append({
                'supercategory': supercat,
                'id': i + 1,
                'name': cat
            })

        if self.cats_order:
            self.designate_categories_order(self.cats_order)

    def rearange_id(self):
        image_id, annotation_id = 1, 1
        for image in self.iterator():
            image.set_id(image_id)

            for obj in image.iterator():
                obj.set_id(annotation_id)

                annotation_id += 1

            image_id += 1

    def __iter__(self) -> DImageIterator:
        return self.iterator()

    def iterator(self, filter: Callable[[DImage], bool]=None) -> DImageIterator:
        return DImageIterator(self, filter)

    def add_image(self, image: DImage) -> None:
        if self.default_image_params is not None:
            if image.license_id <= 0 and 'license_id' in self.default_image_params:
                image.set_license_id(self.default_image_params['license_id'])

            if image.coco_url is None and 'coco_url' in self.default_image_params:
                image.set_coco_url(self.default_image_params['coco_url'])

            if image.data_captured is None and 'data_captured' in self.default_image_params:
                image.set_data_captured(self.default_image_params['data_captured'])

            if image.flickr_url is None and 'flickr_url' in self.default_image_params:
                image.set_flickr_url(self.default_image_params['flickr_url'])

        self.images.append(image)

    def subset(self, image_filter: Optional[Callable[[DImage], bool]]=None, object_filter: Optional[Callable[[DObject], bool]] = None):
        dt = RawDataset(self, categories=None, default_image_params=None,
                        info=self.info, licenses=self.licenses)

        for image in self.iterator(image_filter):
            image_copy = image.copy(object_filter)
            dt.add_image(image_copy)

        cats_param = [(cat['supercategory'], cat['name']) for cat in self.category_details()]

        dt.arange_categories(cats_param)
        dt.rearange_id()

        return dt

    def union(self, dt: 'RawDataset', info=None, licenses=None) -> 'RawDataset':
        if info is None:
            info = union_info(self.info, dt.info)
        if licenses is None:
            licenses, licenses_map = union_licenses(self.licenses, dt.licenses)

        res = RawDataset([self, dt], info=info, licenses=licenses, categories=None, default_image_params=None)
        for img in self:
            res.add_image(img.copy())
        for img in dt:
            cp = img.copy()
            if licenses_map and cp.license_id in licenses_map:
                cp.set_license_id(licenses_map[cp.license_id])
            res.add_image(cp)

        res.rearange_id()

        categories = []
        for cat in self.category_details():
            categories.append((cat['supercategory'], cat['name']))
        for cat in dt.category_details():
            categories.append((cat['supercategory'], cat['name']))

        res.arange_categories(categories)

        return res

    def split(self, *predicates: Callable[[DImage], bool]) -> List['RawDataset']:
        dts = [RawDataset(None, self.cats, None, info=self.info, licenses=self.licenses) for _ in predicates]

        for image in self:
            for dt, p in zip(dts, predicates):
                if p(image):
                    image_copy = image.copy()
                    dt.add_image(image_copy)
                    break

        for dt in dts:
            dt.rearange_id()

        return dts

    def migrate_to(self, dest_dir, filetrans: Callable[[str], str]=None, mkdir_if_not_exists=False) -> None:
        if mkdir_if_not_exists and not path.exists(dest_dir):
            os.makedirs(dest_dir)

        for image in self:
            filename = path.split(image.filepath())[1]
            destname = filename if not filetrans else filetrans(filename)
            destpath = path.join(dest_dir, destname)

            shutil.copy(image.filepath(), destpath)
            image.set_filepath(destpath)

    def change_image_size(self, height: int, width: int, dest_dir: Optional[str]=None, mkdir_if_not_exists=False) -> None:
        if dest_dir and mkdir_if_not_exists and not path.exists(dest_dir):
            os.makedirs(dest_dir)

        for image in self:
            filename = path.split(image.filepath())[1]
            destpath = path.join(dest_dir, filename) if dest_dir else None
            image.change_size(height, width, destpath)

    def to_coco(self, rearange_id: bool=False) -> dict:
        if rearange_id:
            self.rearange_id()

        categories_map = {cat['name']: cat['id'] for cat in self.cats}

        images = []
        annotations = []
        for image in self:
            images.append(image.to_coco())

            for obj in image:
                annotation = obj.to_coco(categories_map)

                annotations.append(annotation)

        return {
            'info': self.info,
            'licenses': self.licenses,
            'images': images,
            'annotations': annotations,
            'categories': self.cats
        }


def load_coco_dataset(json_file: str, image_dir: Optional[str]=None) -> RawDataset:
    if image_dir is None:
        p = Path(json_file)
        image_dir = str(p.parent / 'images')
        assert path.isdir(image_dir), f"can not find {image_dir}"

    with open(json_file, 'r') as f:
        coco = json.load(f)

    dt = RawDataset(
        raw_data=None,
        categories=coco['categories'],
        default_image_params=None,
        info=coco['info'],
        licenses=coco['licenses']
    )

    image_map: Dict[int, DImage] = {}
    for image_info in coco['images']:
        image_path = path.join(image_dir, image_info['file_name'])

        license_id = image_info['license']
        coco_url = image_info['coco_url']
        height = image_info['height']
        width = image_info['width']
        data_captured = image_info['data_captured']
        flickr_url = image_info['flickr_url']

        image_id = image_info['id']

        image = DImage(image_path, width, height)

        image.set_id(image_id)

        image.set_license_id(license_id)
        image.set_coco_url(coco_url)
        image.set_data_captured(data_captured)
        image.set_flickr_url(flickr_url)

        image_map[image_info['id']] = image

        dt.add_image(image)

    categories = {cat['id']: cat['name'] for cat in coco['categories']}

    for annotation in coco['annotations']:
        image_id = annotation['image_id']
        left, top, width, height = annotation['bbox']
        category_id = annotation['category_id']
        obj_id = annotation['id']

        obj = DObject(left, top, left + width, top + height, categories[category_id], image_map[image_id])

        obj.set_id(obj_id)

        image_map[image_id].add_object(obj)

    return dt


def dataset_statistics(dt: RawDataset) -> dict:
    d = {}
    counter = defaultdict(int)
    for image in dt:
        for obj in image:
            counter[obj.category()] += 1
    d['number per category'] = counter
    d['number of images'] = len(dt)
    return d


def adjust_screen_dataset(dt: RawDataset) -> None:
    import numpy as np
    import cv2
    from utility import dip

    difficult_images = []

    for image in tqdm.tqdm(dt):
        objects = image.objects

        assert len(objects) <= 1, f"more than 1 tags"

        if len(objects) == 0:
            continue

        obj = objects[0]

        img = cv2.imread(image.filepath())
        assert img is not None

        res = dip.detect_screen(img)

        if res is None:
            difficult_images.append(image)
            continue

        x1, y1, x2, y2, _, cls = res
        assert round(cls) == 0, f"unknown category in {image.filepath()}"

        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)

        obj.left = x1
        obj.right = x2
        obj.top = y1
        obj.bottom = y2

    for image in difficult_images:
        print(image.filepath())


def save_coco_dataset(dt: RawDataset, dest_dir: str, json_name: str) -> None:
    dt.migrate_to(path.join(dest_dir, 'images'), mkdir_if_not_exists=True)

    with open(path.join(dest_dir, json_name), 'x', encoding='utf-8') as f:
        json.dump(dt.to_coco(), f, ensure_ascii=False, indent=4)


def auto_adjust_coco_dataset(coco_file: str) -> None:
    dt = load_coco_dataset(coco_file)

    adjust_screen_dataset(dt)

    coco_dir = Path(coco_file).parent

    save_coco_dataset(dt, f'{str(coco_dir)}-new', Path(coco_file).name)

    shutil.move(str(coco_dir), f'{str(coco_dir)}-old')
    shutil.move(f'{str(coco_dir)}-new', str(coco_dir))


def get_detection_dataset(image_dir, cat) -> RawDataset:
    import numpy as np
    import cv2
    from utility import dip

    default_params = {
        'license_id': 1,
        'coco_url': '',
        'data_captured': '2022-01-05 00:00:00',
        'flickr_url': ''
    }
    dt = RawDataset(None, None, default_params)

    for item in tqdm.tqdm(list(os.listdir(image_dir))):
        filepath = path.join(image_dir, item)

        image = cv2.imread(filepath)
        h, w = dip.image_size(image)

        dimage = DImage(filepath, w, h)

        res = dip.detect_screen(image)

        if res is not None:
            l, t, r, b, *_ = res
            dimage.add_object(l, t, r, b, cat)

        dt.add_image(dimage)

    dt.rearange_id()
    dt.arange_categories('')

    return dt
