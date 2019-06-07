# -*- coding: utf-8 -*-

from flask import render_template, flash
from flask_login import login_required
from . import main


@main.route('/')
@login_required
def index():
    return render_template('index.html')