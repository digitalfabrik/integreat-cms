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
