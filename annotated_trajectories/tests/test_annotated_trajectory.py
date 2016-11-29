import openpathsampling as paths
from openpathsampling.tests.test_helpers import make_1d_traj
from annotated_trajectories import AnnotatedTrajectory, Annotation
from nose.tools import assert_equal, assert_in
from nose.plugins.skip import SkipTest

class TestAnnotatedTrajectory(object):
    def setup(self):
        # set up the trajectory that we'll annotate in the tests
	self.traj = make_1d_traj([-1, 1, 4, 3, 6, 11, 22, 33, 23, 101, 205, 
                                  35, 45])
        # set up some states to test later
        # this system is designed under the assumption that the "states" are
        # defined by how many digits are in the x-coordinate (and I'll
        # intentionally fail to identify some of them)
	self.cv = paths.CoordinateFunctionCV("x", lambda s: s.xyz[0][0])
	self.state_1 = paths.CVDefinedVolume(self.cv, 0, 9)
	self.state_2 = paths.CVDefinedVolume(self.cv, 10, 99)
	self.state_3 = paths.CVDefinedVolume(self.cv, 100, 999)
        # create the annotations
        self.annotation_1 = Annotation(state="1-digit", begin=1, end=4)
        self.annotation_2 = Annotation(state="2-digit", begin=6, end=8)
        self.annotation_3 = Annotation(state="3-digit", begin=10, end=10)
        self.annotation_4 = Annotation(state="2-digit", begin=11, end=12)

        self.annotated = AnnotatedTrajectory(self.traj)
        self.annotations = [self.annotation_1, self.annotation_2,
                            self.annotation_3, self.annotation_4]

    def test_add_single_annotation(self):
        self.annotated.add_annotations(self.annotation_1)
        assert_equal(self.annotated.state_names, ["1-digit"])
        assert_equal(self.annotated._annotation_dict["1-digit"],
                     [(1, 4)])
        # check that the labels are correct
        for (i, label) in enumerate(self.annotated._frame_map):
            if i in range(1, 5):
                assert_equal(label, "1-digit")
            else:
                assert_equal(label, None)


    def test_add_many_annotations(self):
        self.annotated.add_annotations([self.annotation_1,
                                        self.annotation_2,
                                        self.annotation_3,
                                        self.annotation_4])
        assert_equal(len(self.annotated.state_names), 3)
        assert_equal(set(["1-digit", "2-digit", "3-digit"]),
                     set(self.annotated.state_names))
        assert_equal(self.annotated._annotation_dict["1-digit"], [(1,4)])
        assert_equal(self.annotated._annotation_dict["3-digit"], [(10,10)])
        assert_equal(set(self.annotated._annotation_dict["2-digit"]),
                     set([(6, 8), (11, 12)]))
        for (i, label) in enumerate(self.annotated._frame_map):
            if i in range(1, 5):
                assert_equal(label, "1-digit")
            elif i in range(6, 9):
                assert_equal(label, "2-digit")
            elif i == 10:
                assert_equal(label, "3-digit")
            elif i in range (11, 13):
                assert_equal(label, "2-digit")
            else:
                assert_equal(label, None)


    def test_init_with_annotations(self):
        annotated = AnnotatedTrajectory(self.traj, self.annotations)
        assert_equal(len(annotated.state_names), 3)
        assert_equal(set(["1-digit", "2-digit", "3-digit"]),
                     set(annotated.state_names))
        assert_equal(annotated._annotation_dict["1-digit"], [(1,4)])
        assert_equal(annotated._annotation_dict["3-digit"], [(10,10)])
        assert_equal(set(annotated._annotation_dict["2-digit"]),
                     set([(6, 8), (11, 12)]))
        for (i, label) in enumerate(annotated._frame_map):
            if i in range(1, 5):
                assert_equal(label, "1-digit")
            elif i in range(6, 9):
                assert_equal(label, "2-digit")
            elif i == 10:
                assert_equal(label, "3-digit")
            elif i in range (11, 13):
                assert_equal(label, "2-digit")
            else:
                assert_equal(label, None)


    def test_relabel_error(self):
        raise SkipTest

    def test_get_all_frames(self):
        raise SkipTest

    def test_get_segments(self):
        annotated = AnnotatedTrajectory(self.traj, self.annotations)
        segments_1 = annotated.get_segments("1-digit")
        segments_2 = annotated.get_segments("2-digit")
        segments_3 = annotated.get_segments("3-digit")
        assert_equal(annotated.get_segments("no-such"), [])
        assert_equal(len(segments_1), 1)
        assert_equal(len(segments_2), 2)
        assert_equal(len(segments_3), 1)
        assert_equal(segments_1[0], self.traj[1:5])
        assert_equal(segments_3[0], self.traj[10:11])
        if len(segments_2[0]) == 2:
            assert_equal(segments_2[0], self.traj[11:13])
            assert_equal(segments_2[1], self.traj[6:9])
        else:
            assert_equal(segments_2[1], self.traj[11:13])
            assert_equal(segments_2[0], self.traj[6:9])


    def test_get_unassigned(self):
        annotated = AnnotatedTrajectory(self.traj, self.annotations)
        unassigned = annotated.get_unassigned()
        assert_equal(len(unassigned), 3)
        assert_equal(set(unassigned), set([0, 5, 9]))

    def test_validate_states(self):
        raise SkipTest


def test_plot_annotated():
    # just a smoke test
    raise SkipTest
