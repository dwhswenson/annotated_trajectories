import openpathsampling as paths
from annotated_trajectories import *

import pytest

import os
from pkg_resources import resource_filename

# TODO: when OPS no longer imports nose
from openpathsampling.tests.test_helpers import make_1d_traj
def make_1d_traj(coordinates, velocities=None, engine=None):
    if velocities is None:
        velocities = [1.0]*len(coordinates)
    try:
        _ = len(velocities)
    except TypeError:
        velocities = [velocities] * len(coordinates)

    if engine is None:
        engine = toys.Engine(
            {},
            toys.Topology(
                n_spatial=3,
                masses=[1.0, 1.0, 1.0], pes=None
            )
        )
    traj = []
    for (pos, vel) in zip(coordinates, velocities):
        snap = toys.Snapshot(
            coordinates=np.array([[pos, 0, 0]]),
            velocities=np.array([[vel, 0, 0]]),
            engine=engine
        )
        traj.append(snap)
    return paths.Trajectory(traj)

def data_filename(fname):
    return resource_filename('annotated_trajectories',
                             os.path.join('tests', fname))


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

        self.states = {
            "1-digit": self.state_1,
            "2-digit": self.state_2,
            "3-digit": self.state_3
        }

        self.annotated = AnnotatedTrajectory(self.traj)
        self.annotations = [self.annotation_1, self.annotation_2,
                            self.annotation_3, self.annotation_4]

    def test_add_single_annotation(self):
        self.annotated.add_annotations(self.annotation_1)
        assert self.annotated.state_names == ["1-digit"]
        assert self.annotated._annotation_dict["1-digit"] == [(1, 4)]
        # check that the labels are correct
        for (i, label) in enumerate(self.annotated._frame_map):
            if i in range(1, 5):
                assert label == "1-digit"
            else:
                assert label is None

    @staticmethod
    def _check_standard_annotated_trajectory(trajectory):
        # this factors out some reused test code; we usually test the same
        # set of annotations on the same trajectory, and this code verifies
        # that, no matter how we made it, the result is the same
        assert len(trajectory.state_names) == 3
        assert set(["1-digit", "2-digit", "3-digit"]) == \
                set(trajectory.state_names)
        assert trajectory._annotation_dict["1-digit"] == [(1, 4)]
        assert trajectory._annotation_dict["3-digit"] == [(10, 10)]
        assert set(trajectory._annotation_dict["2-digit"]) == \
                set([(6, 8), (11, 12)])
        for (i, label) in enumerate(trajectory._frame_map):
            if i in range(1, 5):
                assert label == "1-digit"
            elif i in range(6, 9):
                assert label == "2-digit"
            elif i == 10:
                assert label == "3-digit"
            elif i in range(11, 13):
                assert label == "2-digit"
            else:
                assert label is None

    def test_add_many_annotations(self):
        self.annotated.add_annotations([self.annotation_1,
                                        self.annotation_2,
                                        self.annotation_3,
                                        self.annotation_4])
        self._check_standard_annotated_trajectory(self.annotated)

    def test_init_with_annotations(self):
        annotated = AnnotatedTrajectory(self.traj, self.annotations)
        self._check_standard_annotated_trajectory(annotated)

    def test_relabel_error(self):
        bad_annotations = self.annotations + [Annotation("2-digit", 2, 3)]
        with pytest.raises(ValueError):
            annotated = AnnotatedTrajectory(self.traj, bad_annotations)

    def test_get_segment_idxs(self):
        annotated = AnnotatedTrajectory(self.traj, self.annotations)
        idxs_1 = annotated.get_segment_idxs("1-digit")
        idxs_2 = annotated.get_segment_idxs("2-digit")
        idxs_3 = annotated.get_segment_idxs("3-digit")
        assert idxs_1 == [[1, 2, 3, 4]]
        assert idxs_2 == [[6, 7, 8], [11, 12]]
        assert idxs_3 == [[10]]
        assert annotated.get_segment_idxs('no-such') == []

    def test_get_label_for_frame(self):
        annotated = AnnotatedTrajectory(self.traj, self.annotations)
        assert annotated.get_label_for_frame(5) is None
        assert annotated.get_label_for_frame(3) == '1-digit'
        assert annotated.get_label_for_frame(8) == '2-digit'
        assert annotated.get_label_for_frame(10) == '3-digit'
        assert annotated.get_label_for_frame(11) == '2-digit'

    def test_get_segments(self):
        annotated = AnnotatedTrajectory(self.traj, self.annotations)
        segments_1 = annotated.get_segments("1-digit")
        segments_2 = annotated.get_segments("2-digit")
        segments_3 = annotated.get_segments("3-digit")
        assert annotated.get_segments("no-such") == []
        assert len(segments_1) == 1
        assert len(segments_2) == 2
        assert len(segments_3) == 1
        assert segments_1[0] == self.traj[1:5]
        assert segments_3[0] == self.traj[10:11]
        if len(segments_2[0]) == 2:
            assert segments_2[0] == self.traj[11:13]
            assert segments_2[1] == self.traj[6:9]
        else:
            assert segments_2[1] == self.traj[11:13]
            assert segments_2[0] == self.traj[6:9]

    def test_get_all_frames(self):
        annotated = AnnotatedTrajectory(self.traj, self.annotations)
        all_2 = annotated.get_all_frames("2-digit")
        assert len(all_2) == 5

    def test_get_unassigned(self):
        annotated = AnnotatedTrajectory(self.traj, self.annotations)
        unassigned = annotated.get_unassigned()
        assert len(unassigned) == 3
        assert set(unassigned) == set([0, 5, 9])

    def test_validation_idxs(self):
        annotated = AnnotatedTrajectory(self.traj, self.annotations)
        annotated.add_annotations(Annotation(state="1-digit", begin=5,
                                             end=5))
        results_1 = annotated._validation_idxs(
            state=self.state_1,
            state_annotations=annotated._annotation_dict["1-digit"]
        )
        results_2 = annotated._validation_idxs(
            state=self.state_2,
            state_annotations=annotated._annotation_dict["2-digit"]
        )
        # correct, false_positive, false_negative
        assert results_1[0] == set([1, 2, 3, 4])
        assert results_1[1] == set([])
        assert results_1[2] == set([5])

        assert results_2[0] == set([6, 7, 8, 11, 12])
        assert results_2[1] == set([5])
        assert results_2[2] == set([])

    def test_validate_states(self):
        annotated = AnnotatedTrajectory(self.traj, self.annotations)
        annotated.add_annotations(Annotation(state="1-digit", begin=5,
                                             end=5))

        (results, conflicts) = annotated.validate_states(self.states)

        assert results["1-digit"].correct == [s for s in self.traj[1:5]]
        assert results["1-digit"].false_positive == []
        assert results["1-digit"].false_negative == [self.traj[5]]
        assert results["2-digit"].correct == ([s for s in self.traj[6:9]]
                                              + [self.traj[11],
                                                 self.traj[12]])
        assert results["2-digit"].false_positive == [self.traj[5]]
        assert results["2-digit"].false_negative == []
        assert results["3-digit"].correct == [self.traj[10]]
        assert results["3-digit"].false_positive == [self.traj[9]]
        assert results["3-digit"].false_negative == []
        assert conflicts["1-digit"] == []
        assert conflicts["2-digit"] == [5]  # annotate != state def
        assert conflicts["3-digit"] == []

    def test_validate_states_extra_labels(self):
        annotated = AnnotatedTrajectory(self.traj, self.annotations)
        annotated.add_annotations(Annotation(state="magic", begin=5,
                                             end=5))
        with pytest.raises(RuntimeError):
            (results, conflicts) = annotated.validate_states(self.states)

    def test_validate_states_extra_volumes(self):
        annotated = AnnotatedTrajectory(self.traj, self.annotations)
        states = self.states
        states['magic'] = paths.EmptyVolume()
        with pytest.raises(RuntimeError):
            (results, conflicts) = annotated.validate_states(states)

    def test_store_and_reload(self):
        if os.path.isfile(data_filename("output.nc")):
            os.remove(data_filename("output.nc"))
        storage = paths.Storage(data_filename("output.nc"), 'w')
        annotated = AnnotatedTrajectory(self.traj, self.annotations)
        storage.tag['traj1'] = annotated
        storage.close()

        analysis = paths.Storage(data_filename("output.nc"), 'r')
        reloaded = analysis.tag['traj1']

        assert len(reloaded.trajectory) == 13
        assert len(reloaded.annotations) == 4
        self._check_standard_annotated_trajectory(reloaded)

        if os.path.isfile(data_filename("output.nc")):
            os.remove(data_filename("output.nc"))


    def test_plot_annotated(self):
        # just a smoke test
        names_to_colors = {
            '1-digit': 'b',
            '2-digit': 'c',
            '3-digit': 'r'
        }
        annotated = AnnotatedTrajectory(self.traj, self.annotations)
        plot_annotated(annotated, self.cv, self.states, names_to_colors, 0.1)
