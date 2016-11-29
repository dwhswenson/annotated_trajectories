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
        self.names_to_volumes = {}

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
        assigned = sum([
            sum([self._annotation_dict[k] for k in self._annotation_dict], [])
        ], [])
        unassigned = set(range(len(self.trajectory) + 1)) - set(assigned)
        return unassigned

    @property
    def state_names(self):
        return self._annotation_dict.keys()

    def validate_states(self):
        n_states = len(self._annotation_dict)
        n_defined = len(self.names_to_volumes)
        if n_defined < n_states:
            pass # log a warning?
        elif n_defined > n_states:
            raise RuntimeError("More states defined than annotated! "
                               + "n_states=" + str(n_states) + "; "
                               + "n_defined=" + str(n_defined))
        for state_name in self._annotation_dict:
            state = self.names_to_volumes[state_name]
            ranges = [range(a[0], a[1]+1) 
                      for a in self._annotation_dict[state_name]]
            in_state = [i for i in range(len(self.trajectory))
                        if state(self.trajectory[i])]




def plot_annotated(trajectory, cv, plot_styles=None):
    if len(trajectory.names_to_volumes) == 0:
        raise RuntimeError("No volumes associated with this annotated trajectory")

    pass
