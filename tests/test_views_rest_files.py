# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Module tests."""

from __future__ import absolute_import, print_function

import hashlib
import json

from flask import url_for
from flask_security import url_for_security
from six import BytesIO

from invenio_deposit.api import Deposit


def test_files_get(app, db, deposit, files, users):
    """Test rest files get."""
    with app.test_request_context():
        # the user is the owner
        with app.test_client() as client:
            # get resources without login
            res = client.get(
                url_for('invenio_deposit_rest.dep_files',
                        pid_value=deposit['_deposit']['id']))
            assert res.status_code == 401
            # login
            res = client.post(url_for_security('login'), data=dict(
                email=users[0].email,
                password="tester"
            ))
            # get resources
            res = client.get(
                url_for('invenio_deposit_rest.dep_files',
                        pid_value=deposit['_deposit']['id']))
            assert res.status_code == 200
            data = json.loads(res.data.decode('utf-8'))
            assert data[0]['checksum'] == files[0].file.checksum
            assert data[0]['filename'] == files[0].key
            assert data[0]['filesize'] == files[0].file.size

        # the user is NOT the owner
        with app.test_client() as client:
            # login
            res = client.post(url_for_security('login'), data=dict(
                email=users[1].email,
                password="tester2"
            ))
            # get resources
            res = client.get(
                url_for('invenio_deposit_rest.dep_files',
                        pid_value=deposit['_deposit']['id']))
            assert res.status_code == 403


def test_files_get_without_files(app, db, deposit, users):
    """Test rest files get a deposit without files."""
    with app.test_request_context():
        with app.test_client() as client:
            # login
            res = client.post(url_for_security('login'), data=dict(
                email=users[0].email,
                password="tester"
            ))
            # get resources
            res = client.get(
                url_for('invenio_deposit_rest.dep_files',
                        pid_value=deposit['_deposit']['id']))
            assert res.status_code == 200
            data = json.loads(res.data.decode('utf-8'))
            assert data == []


def test_files_post_oauth2(app, db, deposit, files, users, write_token):
    """Test rest files get + oauth2."""
    real_filename = 'real_test.json'
    content = b'### Testing textfile ###'
    #  digest = 'md5:{0}'.format(hashlib.md5(content).hexdigest())
    filename = 'test.json'
    with app.test_request_context():
        with app.test_client() as client:
            # get resources
            file_to_upload = (BytesIO(content), filename)
            res = client.post(
                url_for('invenio_deposit_rest.dep_files',
                        pid_value=deposit['_deposit']['id']),
                data={'file': file_to_upload, 'name': real_filename},
                content_type='multipart/form-data',
                headers=[
                    ('Authorization',
                     'Bearer {0}'.format(write_token.access_token))
                ]
            )
            assert res.status_code == 201
            data = json.loads(res.data.decode('utf-8'))
            assert data['filename'] == real_filename


def test_files_post(app, db, deposit, users):
    """Post a deposit file."""
    real_filename = 'real_test.json'
    content = b'### Testing textfile ###'
    digest = 'md5:{0}'.format(hashlib.md5(content).hexdigest())
    filename = 'test.json'
    with app.test_request_context():
        # the user is the owner
        with app.test_client() as client:
            # test post without login
            file_to_upload = (BytesIO(content), filename)
            res = client.post(
                url_for('invenio_deposit_rest.dep_files',
                        pid_value=deposit['_deposit']['id']),
                data={'file': file_to_upload, 'name': real_filename},
                content_type='multipart/form-data'
            )
            assert res.status_code == 401
            # login
            res = client.post(url_for_security('login'), data=dict(
                email=users[0].email,
                password="tester"
            ))
            # test empty post
            res = client.post(
                url_for('invenio_deposit_rest.dep_files',
                        pid_value=deposit['_deposit']['id']),
                data={'name': real_filename},
                content_type='multipart/form-data'
            )
            assert res.status_code == 400
            # test post
            file_to_upload = (BytesIO(content), filename)
            res = client.post(
                url_for('invenio_deposit_rest.dep_files',
                        pid_value=deposit['_deposit']['id']),
                data={'file': file_to_upload, 'name': real_filename},
                content_type='multipart/form-data'
            )
            deposit_id = deposit.id
            db.session.expunge(deposit.model)
            deposit = Deposit.get_record(deposit_id)
            files = list(deposit.files)
            assert res.status_code == 201
            assert real_filename == files[0].key
            assert digest == files[0].file.checksum
            data = json.loads(res.data.decode('utf-8'))
            obj = files[0]
            assert data['filename'] == obj.key
            assert data['checksum'] == obj.file.checksum
            assert data['id'] == str(obj.file.id)

        # the user is NOT the owner
        with app.test_client() as client:
            # login
            res = client.post(url_for_security('login'), data=dict(
                email=users[1].email,
                password="tester2"
            ))
            # test post
            file_to_upload = (BytesIO(content), filename)
            res = client.post(
                url_for('invenio_deposit_rest.dep_files',
                        pid_value=deposit['_deposit']['id']),
                data={'file': file_to_upload, 'name': real_filename},
                content_type='multipart/form-data'
            )
            assert res.status_code == 403


def test_files_put_oauth2(app, db, deposit, files, users, write_token):
    """Test put deposito files with oauth2."""
    with app.test_request_context():
        with app.test_client() as client:
            # fixture
            content = b'### Testing textfile 2 ###'
            stream = BytesIO(content)
            key = 'world.txt'
            deposit.files[key] = stream
            deposit.commit()
            db.session.commit()
            deposit_id = deposit.id
            db.session.expunge(deposit.model)
            deposit = Deposit.get_record(deposit_id)
            key0 = files[0].key
            files = list(deposit.files)
            assert files[0]['key'] == str(key0)
            assert files[1]['key'] == str(key)
            # order files
            res = client.put(
                url_for('invenio_deposit_rest.dep_files',
                        pid_value=deposit['_deposit']['id']),
                data=json.dumps([
                    {'id': key},
                    {'id': key0}
                ]),
                headers=[
                    ('Authorization',
                     'Bearer {0}'.format(write_token.access_token))
                ]
            )
            assert res.status_code == 200
            data = json.loads(res.data.decode('utf-8'))
            assert data[0]['filename'] == str(key)
            assert data[1]['filename'] == str(key0)


def test_files_put(app, db, deposit, files, users):
    """Test put deposit files."""
    with app.test_request_context():
        # the user is the owner
        with app.test_client() as client:
            # fixture
            content = b'### Testing textfile 2 ###'
            stream = BytesIO(content)
            key = 'world.txt'
            deposit.files[key] = stream
            deposit.commit()
            db.session.commit()
            deposit_id = deposit.id
            db.session.expunge(deposit.model)
            deposit = Deposit.get_record(deposit_id)
            key0 = files[0].key
            files = list(deposit.files)
            assert files[0]['key'] == str(key0)
            assert files[1]['key'] == str(key)
            # add new file (without login)
            res = client.put(
                url_for('invenio_deposit_rest.dep_files',
                        pid_value=deposit['_deposit']['id']),
                data=json.dumps([
                    {'id': key},
                    {'id': key0}
                ])
            )
            assert res.status_code == 401
            # login
            res = client.post(url_for_security('login'), data=dict(
                email=users[0].email,
                password="tester"
            ))
            # order files
            res = client.put(
                url_for('invenio_deposit_rest.dep_files',
                        pid_value=deposit['_deposit']['id']),
                data=json.dumps([
                    {'id': key},
                    {'id': key0}
                ])
            )
            db.session.expunge(deposit.model)
            deposit = Deposit.get_record(deposit_id)
            files = list(deposit.files)
            assert len(deposit.files) == 2
            assert files[0]['key'] == str(key)
            assert files[1]['key'] == str(key0)
            data = json.loads(res.data.decode('utf-8'))
            assert data[0]['filename'] == str(key)
            assert data[1]['filename'] == str(key0)

        # the user is NOT the owner
        with app.test_client() as client:
            # login
            res = client.post(url_for_security('login'), data=dict(
                email=users[1].email,
                password="tester2"
            ))
            # test files post
            res = client.put(
                url_for('invenio_deposit_rest.dep_files',
                        pid_value=deposit['_deposit']['id']),
                data=json.dumps([
                    {'id': key},
                    {'id': key0}
                ])
            )
            assert res.status_code == 403


def test_file_get(app, db, deposit, files, users):
    """Test get file."""
    with app.test_request_context():
        # the user is the owner
        with app.test_client() as client:
            # get resource without login
            res = client.get(url_for(
                'invenio_deposit_rest.dep_file',
                pid_value=deposit['_deposit']['id'],
                key=files[0].key
            ))
            assert res.status_code == 401
            # login
            res = client.post(url_for_security('login'), data=dict(
                email=users[0].email,
                password="tester"
            ))
            # get resource
            res = client.get(url_for(
                'invenio_deposit_rest.dep_file',
                pid_value=deposit['_deposit']['id'],
                key=files[0].key
            ))
            assert res.status_code == 200
            data = json.loads(res.data.decode('utf-8'))
            obj = files[0]
            assert data['filename'] == obj.key
            assert data['checksum'] == obj.file.checksum
            assert data['id'] == str(obj.file.id)

        # the user is NOT the owner
        with app.test_client() as client:
            # login
            res = client.post(url_for_security('login'), data=dict(
                email=users[1].email,
                password="tester2"
            ))
            # get resource
            res = client.get(url_for(
                'invenio_deposit_rest.dep_file',
                pid_value=deposit['_deposit']['id'],
                key=files[0].key
            ))
            assert res.status_code == 403


def test_file_get_not_found(app, db, deposit, users):
    """Test get file."""
    with app.test_request_context():
        with app.test_client() as client:
            # login
            res = client.post(url_for_security('login'), data=dict(
                email=users[0].email,
                password="tester"
            ))
            # get resource
            res = client.get(url_for(
                'invenio_deposit_rest.dep_file',
                pid_value=deposit['_deposit']['id'],
                key='not_found'
            ))
            assert res.status_code == 404


def test_file_delete_oauth2(app, db, deposit, files, users, write_token):
    """Test delete file with oauth2."""
    with app.test_request_context():
        with app.test_client() as client:
            deposit_id = deposit.id
            # delete resource
            res = client.delete(
                url_for(
                    'invenio_deposit_rest.dep_file',
                    pid_value=deposit['_deposit']['id'],
                    key=files[0].key
                ),
                headers=[
                    ('Authorization',
                     'Bearer {0}'.format(write_token.access_token))
                ]
            )
            assert res.status_code == 204
            db.session.expunge(deposit.model)
            deposit = Deposit.get_record(deposit_id)
            assert files[0].key not in deposit.files


def test_file_delete(app, db, deposit, files, users):
    """Test delete file."""
    with app.test_request_context():
        # the user is the owner
        with app.test_client() as client:
            deposit_id = deposit.id
            res = client.delete(url_for(
                'invenio_deposit_rest.dep_file',
                pid_value=deposit['_deposit']['id'],
                key=files[0].key
            ))
            assert res.status_code == 401
            db.session.expunge(deposit.model)
            deposit = Deposit.get_record(deposit_id)
            assert files[0].key in deposit.files
            assert deposit.files[files[0].key] is not None
            # login
            res = client.post(url_for_security('login'), data=dict(
                email=users[0].email,
                password="tester"
            ))
            # delete resource
            res = client.delete(url_for(
                'invenio_deposit_rest.dep_file',
                pid_value=deposit['_deposit']['id'],
                key=files[0].key
            ))
            assert res.status_code == 204
            assert res.data == b''
            db.session.expunge(deposit.model)
            deposit = Deposit.get_record(deposit_id)
            assert files[0].key not in deposit.files

        # the user is NOT the owner
        with app.test_client() as client:
            # login
            res = client.post(url_for_security('login'), data=dict(
                email=users[1].email,
                password="tester2"
            ))
            # delete resource
            res = client.delete(url_for(
                'invenio_deposit_rest.dep_file',
                pid_value=deposit['_deposit']['id'],
                key=files[0].key
            ))
            assert res.status_code == 403


def test_file_put_not_found_bucket_not_exist(app, db, deposit, users):
    """Test put file and bucket doesn't exist."""
    with app.test_request_context():
        with app.test_client() as client:
            # login
            res = client.post(url_for_security('login'), data=dict(
                email=users[0].email,
                password="tester"
            ))
            res = client.put(url_for(
                'invenio_deposit_rest.dep_file',
                pid_value=deposit['_deposit']['id'],
                key='not_found'),
                data=json.dumps({'filename': 'foobar'})
            )
            assert res.status_code == 404


def test_file_put_not_found_file_not_exist(app, db, deposit, files, users):
    """Test put file and file doesn't exist."""
    with app.test_request_context():
        with app.test_client() as client:
            # login
            res = client.post(url_for_security('login'), data=dict(
                email=users[0].email,
                password="tester"
            ))
            res = client.put(url_for(
                'invenio_deposit_rest.dep_file',
                pid_value=deposit['_deposit']['id'],
                key='not_found'),
                data=json.dumps({'filename': 'foobar'})
            )
            assert res.status_code == 404


def test_file_put_oauth2(app, db, deposit, files, users, write_token):
    """PUT a deposit file with oauth2."""
    with app.test_request_context():
        with app.test_client() as client:
            old_file_id = files[0].file_id
            old_filename = files[0].key
            new_filename = '{0}-new-name'.format(old_filename)
            # test rename file
            res = client.put(
                url_for('invenio_deposit_rest.dep_file',
                        pid_value=deposit['_deposit']['id'],
                        key=old_filename),
                data=json.dumps({'filename': new_filename}),
                headers=[
                    ('Authorization',
                     'Bearer {0}'.format(write_token.access_token))
                ]
            )
            deposit_id = deposit.id
            db.session.expunge(deposit.model)
            deposit = Deposit.get_record(deposit_id)
            files = list(deposit.files)
            assert res.status_code == 200
            assert new_filename == files[0].key
            assert old_file_id == files[0].file_id
            data = json.loads(res.data.decode('utf-8'))
            obj = files[0]
            assert data['filename'] == obj.key
            assert data['checksum'] == obj.file.checksum
            assert data['id'] == str(obj.file.id)


def test_file_put(app, db, deposit, files, users):
    """PUT a deposit file."""
    with app.test_request_context():
        with app.test_client() as client:
            old_file_id = files[0].file_id
            old_filename = files[0].key
            new_filename = '{0}-new-name'.format(old_filename)
            # test rename file (without login)
            res = client.put(
                url_for('invenio_deposit_rest.dep_file',
                        pid_value=deposit['_deposit']['id'],
                        key=old_filename),
                data=json.dumps({'filename': new_filename}))
            assert res.status_code == 401
            # login
            res = client.post(url_for_security('login'), data=dict(
                email=users[0].email,
                password="tester"
            ))
            # test rename file
            res = client.put(
                url_for('invenio_deposit_rest.dep_file',
                        pid_value=deposit['_deposit']['id'],
                        key=old_filename),
                data=json.dumps({'filename': new_filename}))
            deposit_id = deposit.id
            db.session.expunge(deposit.model)
            deposit = Deposit.get_record(deposit_id)
            files = list(deposit.files)
            assert res.status_code == 200
            assert new_filename == files[0].key
            assert old_file_id == files[0].file_id
            data = json.loads(res.data.decode('utf-8'))
            obj = files[0]
            assert data['filename'] == obj.key
            assert data['checksum'] == obj.file.checksum
            assert data['id'] == str(obj.file.id)