# -*- coding: utf-8 -*-

from flask import render_template
from flask_login import login_required
from . import main


@main.route('/')
@login_required
def index():
    return render_template('index.html')


@main.route('/write')
@login_required
def write():
    return render_template('write.html')
