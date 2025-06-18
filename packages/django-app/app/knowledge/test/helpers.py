import factory
from factory.django import DjangoModelFactory
from factory import Faker, SubFactory

from core.test.helpers import UserFactory
from knowledge.models import Page, Block


class PageFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    title = Faker("sentence", nb_words=3)
    slug = factory.LazyAttribute(
        lambda obj: obj.title.lower().replace(" ", "-").replace(".", "")
    )
    content = Faker("text", max_nb_chars=200)
    is_published = True
    page_type = "page"

    class Meta:
        model = Page


class BlockFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    page = SubFactory(PageFactory)
    content = Faker("text", max_nb_chars=100)
    content_type = "text"
    block_type = "bullet"
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = Block
