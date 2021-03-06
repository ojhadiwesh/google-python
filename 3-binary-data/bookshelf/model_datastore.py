# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import current_app
from google.cloud import datastore
from google.cloud import vision
from google.cloud.vision import types
import io

builtin_list = list


def init_app(app):
    pass

def get_vision_client():
    return vision.ImageAnnotatorClient()

def get_client():
    return datastore.Client(current_app.config['PROJECT_ID'])


def from_datastore(entity):
    """Translates Datastore results into the format expected by the
    application.

    Datastore typically returns:
        [Entity{key: (kind, id), prop: val, ...}]

    This returns:
        {id: id, prop: val, ...}
    """
    if not entity:
        return None
    if isinstance(entity, builtin_list):
        entity = entity.pop()

    entity['id'] = entity.key.id
    return entity


def list(limit=10, cursor=None):
    ds = get_client()

    query = ds.query(kind='image', order=['title'])
    query_iterator = query.fetch(limit=limit, start_cursor=cursor)
    page = next(query_iterator.pages)

    entities = builtin_list(map(from_datastore, page))
    next_cursor = (
        query_iterator.next_page_token.decode('utf-8')
        if query_iterator.next_page_token else None)

    return entities, next_cursor


def read(id):
    ds = get_client()
    key = ds.key('image', int(id))
    results = ds.get(key)
    return from_datastore(results)
def scan(id):
    vision = get_vision_client()
    datastore_image= read(id)
    content = io.read(datastore_image)
    image = types.Image(content=content)
    response = vision.text_detection(image= image)
    texts  = response.text_annotations
    for text in texts:
         return ('\n"{}"'.format(text.description))


def update(data, id=None):
    ds = get_client()
    if id:
        key = ds.key('image', int(id))
    else:
        key = ds.key('image')

    entity = datastore.Entity(
        key=key,
        exclude_from_indexes=['description'])

    entity.update(data)
    ds.put(entity)
    return from_datastore(entity)


create = update


def delete(id):
    ds = get_client()
    key = ds.key('image', int(id))
    ds.delete(key)
