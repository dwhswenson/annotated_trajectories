import matplotlib.pyplot as plt
import openpathsampling as paths
from openpathsampling.netcdfplus import StorableNamedObject
from collections import namedtuple

# this hack of making a class from my namedtuple allows me to give it a
# docstring
class Annotation(namedtuple('Annotation', ['state', 'begin', 'end'])):
    """
    Annotation for the trajectory. Frame numbers refer to a specific
    trajectory in an AnnotatedTrajectory object.

    Parameters
    ----------
    state : str
        the name of the state
    begin : int
        the initial frame that is labelled as in the state
    end : int
        the final frame that is labelled as in the state (inclusive)
    """

_validation_fields = ['correct', 'false_positive', 'false_negative']
class ValidationResults(namedtuple('ValidationResults', _validation_fields)):
    """
    Object returned by validation.
    
    Simply a named tuple with the a list of the correct snapshots, the
    snapshots which ???

    Parameters
    ----------
    correct : list of ``paths.Snapshot``
        the snapshots which were correctly identified as in the state
    false_positive : list of ``paths.Snapshot``
        the snapshots which were identified as in the state by the volume
        function, but not by the annotation
    false_negative : list of ``paths.Snapshot``
        the snapshots which were not identified as in the state by the
        volume, but were in the state according to the annotation.
    """

class AnnotatedTrajectory(StorableNamedObject):
    """Trajectory with state annotations.
    
    Parameters
    ----------
    trajectory : ``paths.Trajectory``
        trajectory for the annotations
    annotations : dict {str : list of 2-tuple (int, int)}
        the strings are names for  states associated with the frames in the
        2-tuple (begin, end), inclusive
    """
    def __init__(self, trajectory, annotations=None):
        self.trajectory = trajectory
        self._frame_map = [None]*len(self.trajectory)
        self._annotation_dict = {}
        if annotations is not None:
            self.add_annotations(annotations)

    def add_annotations(self, annotations):
        if isinstance(annotations, Annotation):
            annotations = [annotations]
        for annotation in annotations:
            state = annotation.state
            begin  = annotation.begin
            end = annotation.end
            range_tuple = (begin, end)
            range_list = range(begin, end+1)
            for frame_num in range_list:
                if self._frame_map[frame_num] is not None:
                    raise ValueError("Cannot assign frame to more than one state")
                else:
                    self._frame_map[frame_num] = state
            if state in self._annotation_dict.keys():
                self._annotation_dict[state] += [range_tuple]
            else:
                self._annotation_dict[state] = [range_tuple]

    def get_all_frames(self, volume):
        return sum(self.get_segments(volume), paths.Trajectory([]))

    def get_segments(self, volume):
        try:
            all_ranges = self._annotation_dict[volume]
        except KeyError:
            all_ranges = []

        all_segments = [self.trajectory[r[0]:r[1]+1] for r in all_ranges]
        return all_segments

    def get_unassigned(self):
        unassigned = [k for k in range(len(self._frame_map))
                      if self._frame_map[k] is None]
        return unassigned

    @property
    def state_names(self):
        return self._annotation_dict.keys()

    def _validation_idxs(self, state, state_annotations):
        """
        Find indexes of snapshots labeled correctly, false positive, false
        negative.

        Used internally by the :meth:`.validate_states` method. This section
        factored out to facilitate testing.
        """
        expected = set(sum([range(a[0], a[1]+1) 
                            for a in state_annotations], []))
        in_state = set([i for i in range(len(self.trajectory))
                        if state(self.trajectory[i])])
        correct_idxs = expected & in_state
        false_pos_idxs = in_state - expected
        false_neg_idxs = expected - in_state
        return (correct_idxs, false_pos_idxs, false_neg_idxs)

    def validate_states(self, names_to_volumes):
        n_states = len(self._annotation_dict)
        n_defined = len(names_to_volumes)
        if n_defined < n_states:
            pass # log a warning?
        elif n_defined > n_states:
            raise RuntimeError("More states defined than annotated! "
                               + "n_states=" + str(n_states) + "; "
                               + "n_defined=" + str(n_defined))
        results = {}
        for state_name in self._annotation_dict:
            state = names_to_volumes[state_name]
            state_annotations = self._annotation_dict[state_name]
            idxs = self._validation_idxs(state, state_annotations)
            correct = [self.trajectory[i] for i in sorted(idxs[0])]
            false_pos = [self.trajectory[i] for i in sorted(idxs[1])]
            false_neg = [self.trajectory[i] for i in sorted(idxs[2])]
            results.update({
                state_name: ValidationResults(correct=correct,
                                              false_positive=false_pos,
                                              false_negative=false_neg)
            })
        return results


def plot_annotated(trajectory, cv, names_to_volumes, plot_styles=None):
    pass
