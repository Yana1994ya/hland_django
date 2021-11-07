import dataclasses

from django.core.paginator import Page
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe


@dataclasses.dataclass
class SinglePage:
    number: int
    current: bool
    link: str


class Pager:
    def __init__(self, page: Page, view):
        self.page = page
        self.view = view

    def render(self):
        previous_link = None
        if self.page.has_previous():
            previous_link = reverse(self.view, kwargs={
                "page_number": self.page.previous_page_number()
            })

        next_link = None
        if self.page.has_next():
            next_link = reverse(self.view, kwargs={
                "page_number": self.page.next_page_number()
            })

        pages = []

        for page_num in self.page.paginator.page_range:
            pages.append(SinglePage(
                number=page_num,
                current=self.page.number == page_num,
                link=reverse(self.view, kwargs={
                    "page_number": page_num
                })
            ))

        return mark_safe(render_to_string(
            "attractions/pager.html",
            {
                "previous_link": previous_link,
                "pages": pages,
                "next_link": next_link
            }
        ))
