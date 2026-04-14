import pytest
from src.automation.ariadne.labyrinth.skeleton import Skeleton, AbstractElement, ElementType


def el(type_: ElementType, role: str, selector: str = "div", slots=()) -> AbstractElement:
    return AbstractElement(type=type_, role=role, selector=selector, slots=slots)


@pytest.fixture
def base_skeleton():
    return Skeleton(elements=(
        el(ElementType.navbar,  "main_nav"),
        el(ElementType.form,    "search_form"),
        el(ElementType.button,  "submit_button"),
    ))


class TestTransitionJudge:
    def test_identical_skeletons_not_a_transition(self, base_skeleton):
        clone = Skeleton(elements=base_skeleton.elements)
        assert not base_skeleton.is_transition_from(clone)

    def test_added_element_is_transition(self, base_skeleton):
        extended = Skeleton(elements=base_skeleton.elements + (el(ElementType.modal, "cookie_modal"),))
        assert extended.is_transition_from(base_skeleton)

    def test_removed_element_is_transition(self, base_skeleton):
        reduced = Skeleton(elements=base_skeleton.elements[:-1])
        assert reduced.is_transition_from(base_skeleton)

    def test_reclassified_element_is_transition(self, base_skeleton):
        # same role, different type → structural change
        reclassified = Skeleton(elements=(
            el(ElementType.navbar,   "main_nav"),
            el(ElementType.form,     "search_form"),
            el(ElementType.dropdown, "submit_button"),  # was button, now dropdown
        ))
        assert reclassified.is_transition_from(base_skeleton)

    def test_selector_change_not_a_transition(self, base_skeleton):
        # same type+role, different selector → NOT structural (PortalDictionary concern)
        same_structure = Skeleton(elements=(
            el(ElementType.navbar,  "main_nav",     selector="#new-nav"),
            el(ElementType.form,    "search_form",  selector=".form-v2"),
            el(ElementType.button,  "submit_button"),
        ))
        assert not same_structure.is_transition_from(base_skeleton)

    def test_slot_content_change_not_a_transition(self):
        s1 = Skeleton(elements=(el(ElementType.card, "job_card", slots=("Software Engineer",)),))
        s2 = Skeleton(elements=(el(ElementType.card, "job_card", slots=("Data Scientist",)),))
        assert not s2.is_transition_from(s1)

    def test_empty_skeletons_equal(self):
        assert not Skeleton().is_transition_from(Skeleton())


class TestSerialization:
    def test_roundtrip(self, base_skeleton):
        restored = Skeleton.from_dict(base_skeleton.to_dict())
        assert not restored.is_transition_from(base_skeleton)
        assert len(restored.elements) == len(base_skeleton.elements)

    def test_element_fields_preserved(self, base_skeleton):
        restored = Skeleton.from_dict(base_skeleton.to_dict())
        for orig, rest in zip(base_skeleton.elements, restored.elements):
            assert orig.type == rest.type
            assert orig.role == rest.role
            assert orig.selector == rest.selector
