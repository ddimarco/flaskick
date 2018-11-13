#!/usr/bin/env python

import os
import requests
import pagan
import shutil

from flaskick.app import app

AVATAR_DIR = os.path.join(app.root_path, 'static/avatars/')


def avatar_filename(player_name):
    return os.path.join(AVATAR_DIR, player_name)


def fetch_player_avatar(player, avatar_fname):
    # if player.avatar_url:
    #     # download avatar
    #     r = requests.get(player.avatar_url, stream=True)
    #     if r.status_code == 200:
    #         with open(avatar_fname, 'wb') as f:
    #             r.raw.decode_content = True
    #             shutil.copyfileobj(r.raw, f)
    #         return
    # generate a pagan avatar
    avatar = pagan.Avatar(player.name.encode('utf-8'), pagan.SHA512)
    scaled = avatar.img
    scaled.thumbnail((80, 80))
    scaled.save(avatar_fname, 'PNG')


def generate_or_load_avatar(player):
    """Returns the path to an avatar image file for the given player."""
    # make sure avatar dir exists
    if not os.path.isdir(AVATAR_DIR):
        os.mkdir(AVATAR_DIR)

    avatar_fname = avatar_filename(player.name)
    if not os.path.isfile(avatar_fname):
        fetch_player_avatar(player, avatar_fname)
    return avatar_fname
