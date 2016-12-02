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
    
    Results from comparing frames identified by a proposed state definition
    to the frames identified by the user. Checks for correct results, false
    positives (proposed definition finds frames the user didn't) and false
    negatives (user finds frames the proposed definition didn't).

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
        self.annotations = set([])
        self._frame_map = [None]*len(self.trajectory)
        self._annotation_dict = {}
        if annotations is not None:
            self.add_annotations(annotations)

    @classmethod
    def from_dict(cls, dct):
        # we need a custom from_dict because storage just treats our
        # annotations as a list, and doesn't know how to make them back into
        # the namedtuple
        trajectory = dct['trajectory']
        annotations_list = dct['annotations']
        annotations = [Annotation(a[0], a[1], a[2]) 
                       for a in annotations_list]
        return cls(trajectory, annotations)

    def add_annotations(self, annotations):
        """
        Add annotations to the internal list. Do not do this after saving!

        Parameters
        ----------
        annotations : :class:`.Annotation` or list of :class:`.Annotation`
            the annotations to add to the list
        """
        if isinstance(annotations, Annotation):
            annotations = [annotations]
        self.annotations |= set(annotations)
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

    def get_all_frames(self, label):
        """Return all frames for a given label as a flattened trajectory.

        Parameters
        ----------
        label : str
            the label used for this state

        Returns
        -------
        ``paths.Trajectory``
            all frames in this trajectory with the given label
        """
        return sum(self.get_segments(label), paths.Trajectory([]))

    def get_segment_idxs(self, label):
        try:
            all_ranges = self._annotation_dict[label]
        except KeyError:
            all_ranges = []

        all_segment_idxs = [range(r[0], r[1]+1) for r in all_ranges]
        return all_segment_idxs


    def get_segments(self, label):
        try:
            all_ranges = self._annotation_dict[label]
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
        conflicts = {}
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
            conflicts[state_name] = [i for i in idxs[1]  # false pos idxs
                                     if self._frame_map[i] is not None]
        
        return (results, conflicts)


def plot_annotated(trajectory, cv, names_to_volumes, names_to_colors, dt=1):
    import matplotlib.pyplot as plt
    plt.plot([i*dt for i in range(len(trajectory.trajectory))],
             cv(trajectory.trajectory), '-k')
    for state_name in trajectory.state_names:
	ann_segment_idxs = trajectory.get_segment_idxs(state_name)
	ann_segments = trajectory.get_segments(state_name)
	for idxs, segs in zip(ann_segment_idxs, ann_segments):
	    if len(idxs) > 1:
                plt.plot([i*dt for i in idxs], cv(segs), linestyle='-',
                         color=names_to_colors[state_name])
	    else:
                plt.plot(idxs, cv(segs), marker='+', markersize=10,
                         color=names_to_colors[state_name])
	state = names_to_volumes[state_name]
	in_state_idxs = [i for i in range(len(trajectory.trajectory))
			 if state(trajectory.trajectory[i])]
        plt.plot([i*dt for i in in_state_idxs], 
                 [cv(trajectory.trajectory[i]) for i in in_state_idxs],
                 color=names_to_colors[state_name], marker='o',
                 linestyle='None')
