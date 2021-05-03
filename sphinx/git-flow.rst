***************
GitHub Workflow
***************


Git
===

There are many great tutorials on git out there, so this one won't cover the basics.
Check out e.g.:

* `git - the simple guide <https://rogerdudler.github.io/git-guide/>`_
* `How to Write a Git Commit Message <https://chris.beams.io/posts/git-commit/>`_


GitHub Flow
===========

In general, we use the `GitHub flow <https://guides.github.com/introduction/flow/>`_:

.. image:: images/github-flow.png
   :alt: GitHub flow diagram

.. Note::

    If you want to build your commits on CircleCI or start a discussion before your branch is ready for review, you can also create a `draft pull request <https://github.blog/2019-02-14-introducing-draft-pull-requests/>`_.


Rebasing
========

In extension to the GitHub flow, we use `rebasing <https://git-scm.com/book/en/v2/Git-Branching-Rebasing>`_ in two situations:


1. Update feature branch
------------------------

.. highlight:: bash

You want to merge recent changes of the develop branch into your current feature branch, e.g. because there are conflicts that prevent your branch from being merged::

    # fetch upstream changes of origin/develop
    git fetch --all
    # rebase your feature branch onto the current upstream develop branch
    git rebase origin/develop
    # if the rebase cannot be performed automatically, resolve the conflicts and continue
    git rebase --continue
    # if more conflicts pop up, repeat the previous step until the rebase is finished
    # force-push your changes
    git push --force-with-lease


2. Clean up git history
-----------------------

You have many small commits which clutter the git history, or want to combine rearrange commits on your current feature branch::

    # interactive rebase starting at the commit where your current branch was forked from develop
    git rebase --interactive $(git merge-base --fork-point develop $(git rev-parse --abbrev-ref HEAD))
    # sort and modify your commits as you want
    # exit the editor and save
    # if the rebase cannot be performed automatically, resolve the conflicts and continue
    git rebase --continue
    # if more conflicts pop up, repeat the previous step until the rebase is finished
    # force-push your changes
    git push --force-with-lease


.. Warning::

    * Don't do ``git pull`` between rebasing and pushing.
      This will result in duplicate commits.
      You have to overwrite the upstream branch with your rebased commits by using the option ``--force-with-lease``.
    * Only force-push to your own feature branches!

.. Note::

    If you want to pull your rebased branch ``feature`` from another machine, use the following::

        git fetch --all
        git reset --hard origin/feature


.. _pre-commit-hooks:

Pre-commit Hooks
================

`Pre-commit <https://pre-commit.com/>`_ hooks are commands which are run every time a commit is created to check whether the committed changes comply
with the repository's standards.
All hooks for this repository are defined in :github-source:`.pre-commit-config.yaml`.
At the moment, the following hooks are configured:

* ``shellcheck``: a static analysis tool for shell scripts  (see: :ref:`shellcheck` and `ShellCheck wiki <https://github.com/koalaman/shellcheck/wiki>`_)
* ``black``: A formatter which applies automatic code formatting to Python files (see :ref:`black-code-style`)
* ``translations`` A script which checks whether the translation file is up-to-date (see: :doc:`internationalization` and :ref:`translations`)


Activation
----------

To activate the pre-commit hooks, either install the CMS with the command::

    ./dev-tools/install.sh --pre-commit

or execute::

    pipenv run pre-commit install

manually after installing.


Deactivation
------------

To deactivate a specific hook (in this example the ``translations``-hook), use::

    SKIP=translations git commit

To deactivate all pre-commit hooks for a specific commit, use::

    git commit --no-verify

If you want to deactivate pre-commit hooks for this repository entirely, use::

    pipenv run pre-commit uninstall
