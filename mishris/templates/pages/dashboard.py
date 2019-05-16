from __future__ import unicode_literals

import frappe
from frappe.website.doctype.blog_post.blog_post import get_blog_list


def get_context(context):
    context.blog_list = get_blog_list("Blog Post", limit_page_length=3)
