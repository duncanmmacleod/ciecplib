# Releasing `ciecplib`

The instructions below detail how to finalise a new release
for version `{X.Y.Z}`.

In all commands below that placeholder should be replaced
with an actual release version.

## 1. Update the packaging files

-   Create a new branch on which to update the OS packaging files:

    ```shell
    git checkout -b finalise-{X.Y.Z}
    ```

-   Bump the version in the Python package `ciecplib/__init__.py` file

-   Bump versions and add changelog entries in OS packaging files:

    - `debian/changelog`
    - `ciecplib.spec`

    and then commit the changes to the branch.

-   Push this branch to your fork:

    ```shell
    git push -u origin finalise-{X.Y.Z}
    ```

-   Open a merge request on GitHub to finalise the packaging update.

## 2. Tag the release

-   Draft release notes by looking through the merge requests associated
    with the relevant
    [milestone on GitHub](https://github.com/duncanmmacleod/ciecplib/milestones).

-   Create an annotated, signed tag in `git` using the release notes
    as the tag message:

    ```shell
    git tag --sign {X.Y.Z}
    ```

-   Push the tag to the project on GitLab:

    ```shell
    git push -u upstream {X.Y.Z}
    ```

## 3. Create a Release on GitHub

-   Create a
    [Release on GitLab](https://github.com/duncanmmacleod/ciecplib/releases/new),
    copying the same release notes from the tag message.

    Make sure and correctly associated the correct Tag to the Release.

## 4. Publish the new release on PyPI:

-   Generate a new source distribution and binary wheel for this release:

    ```shell
    git clean -dfX
    python -m build --sdist --wheel
    ```

-   Upload these distributions to PyPI:

    ```shell
    python -m twine upload --sign dist/ciecplib-{X.Y.Z}*
    ```
