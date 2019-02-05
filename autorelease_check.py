#/usr/bin/env python
from __future__ import print_function
import setup
import annotated_trajectories
from autorelease import DefaultCheckRunner, conda_recipe_version
from packaging.version import Version

repo_path = '.'
versions = {
    'package': autorelease.version.version,
    'setup.py': setup.PACKAGE_VERSION,
    # 'conda-recipe': conda_recipe_version('ci/conda-recipe/meta.yaml'),
}

RELEASE_BRANCHES = ['stable']
RELEASE_TAG = "v" + Version(setup.PACKAGE_VERSION).base_version

if __name__ == "__main__":
    checker = DefaultCheckRunner(
        versions=versions,
        setup=setup,
        repo_path='.'
    )
    checker.release_branches = RELEASE_BRANCHES + [RELEASE_TAG]

    tests = checker.select_tests_from_sysargs()
    n_fails = checker.run_as_test(tests)
