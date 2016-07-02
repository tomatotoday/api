# -*- coding: utf-8 -*-

from flask_wtf import Form
from wtforms.fields import StringField
from wtforms.validators import Length

class DiscussionCommentForm(Form):

    title = StringField('Title', [Length(min=1, max=150)])
    content = StringField('Content', [Length(min=1, max=5000)])
