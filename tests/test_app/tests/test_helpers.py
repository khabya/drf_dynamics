from drf_dynamics.helpers import dynamic_queryset, tagged_chain
from drf_dynamics.specs import DynamicAnnotation, DynamicPrefetch, DynamicSelect
from tests.test_app.models import Invite, Party
from tests.test_app.tests.testcases import TestCase


class TaggedChainTestCase(TestCase):
    def test_regular(self):
        gen = tagged_chain((1, 2), (3, 4), (5, 6))
        self.assertEqual((0, 1), next(gen))
        self.assertEqual((0, 2), next(gen))
        self.assertEqual((1, 3), next(gen))
        self.assertEqual((1, 4), next(gen))
        self.assertEqual((2, 5), next(gen))
        self.assertEqual((2, 6), next(gen))

    def test_tag_names(self):
        gen = tagged_chain(
            (1, 2), (3, 4), (5, 6), tag_names=("first", "second", "third")
        )
        self.assertEqual(("first", 1), next(gen))
        self.assertEqual(("first", 2), next(gen))
        self.assertEqual(("second", 3), next(gen))
        self.assertEqual(("second", 4), next(gen))
        self.assertEqual(("third", 5), next(gen))
        self.assertEqual(("third", 6), next(gen))

    def test_empty_iterables(self):
        gen = tagged_chain((1, 2), (), (), (3, 4))
        self.assertEqual((0, 1), next(gen))
        self.assertEqual((0, 2), next(gen))
        self.assertEqual((3, 3), next(gen))
        self.assertEqual((3, 4), next(gen))


class DynamicQuerySetTestCase(TestCase):
    def setUp(self):
        class ViewSet:
            queryset = Party.objects.all()

        self.viewset_class = ViewSet

    def test_simple_lookups(self):
        prefetches = "invites"
        annotations = ("invites_count", "invites.has_answer")
        selects = ("host", "invites.sender", "invites.recipient", "invites.answer")

        dynamic_queryset(
            prefetches=prefetches, annotations=annotations, selects=selects
        )(self.viewset_class)

        self.assertEqual(1, len(self.viewset_class.dynamic_prefetches))
        self.assertSpecsEqual(
            DynamicPrefetch("invites", Invite.objects.all()),
            self.viewset_class.dynamic_prefetches["invites"],
        )

        self.assertEqual(2, len(self.viewset_class.dynamic_annotations))
        self.assertSpecsEqual(
            DynamicAnnotation("with_invites_count"),
            self.viewset_class.dynamic_annotations["invites_count"],
        )
        self.assertSpecsEqual(
            DynamicAnnotation("with_has_answer", parent_prefetch_path="invites"),
            self.viewset_class.dynamic_annotations["invites.has_answer"],
        )

        self.assertEqual(4, len(self.viewset_class.dynamic_selects))
        self.assertSpecsEqual(
            DynamicSelect("host"), self.viewset_class.dynamic_selects["host"],
        )
        self.assertSpecsEqual(
            DynamicSelect("sender", parent_prefetch_path="invites"),
            self.viewset_class.dynamic_selects["invites.sender"],
        )
        self.assertSpecsEqual(
            DynamicSelect("recipient", parent_prefetch_path="invites"),
            self.viewset_class.dynamic_selects["invites.recipient"],
        )
        self.assertSpecsEqual(
            DynamicSelect("answer", parent_prefetch_path="invites"),
            self.viewset_class.dynamic_selects["invites.answer"],
        )
