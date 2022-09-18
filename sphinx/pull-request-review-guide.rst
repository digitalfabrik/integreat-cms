******************************
Pull Request Review Guidelines
******************************


To maintain high code quality standards while ensuring efficiency and meeting deadlines
when reviewing our :github:`pull requests <pulls>`, we compiled this list of guidelines.


.. admonition:: First and foremost

    *No blaming, but constructive advice and suggestions. No one is perfect.*


Goals and purpose
=================

* Checking whether the PR actually does what it's supposed to do
* Avoiding the introduction of new bugs
* Keeping the team up to date about changes in the code base
* Knowledge transfer between developers


.. tip::

    Have a personal goal of a minimum of reviews. You should aim to make a review for every own PR that you open.


Checklist
=========

1. General overview
-------------------

  * Read issue and PR description carefully (including background and context) and get an overview of the changed files.
  * Does the PR match the issue description? Are there any unrelated changes or additional resolved issues?

  .. Note::

    When the changes are out of the issue's scope, suggest to open another separate PR


2. Functional tests
-------------------

  * Checkout the branch, open the CMS and test the main functionality, that the PR implements
  * Test for edge cases in user inputs etc.
  * Have a look at the dev server log and keep an eye on any errors or warnings
  * Test the GUI:

    * Test potential breaks in the GUI
    * Is the design responsive?
    * Are all hard coded strings translated?
    * Are UI elements spelled correctly?
    * Is the wording consistent?
    * Is gender-sensitive language used in the German translations?
    * Does the GUI make sense from a user perspective?


3. Code review
--------------

Now read the code in detail and check whether the PR fulfills the requirements:

  * Try to find potential problems in edge cases by following along the code and think about breaks in conditions
  * Check tests, that already exist. Do they miss edge cases or can they be extended for the current PR?
  * Are exceptions handled gracefully?
  * Does it have any negative side effects (e.g. slower execution)?
  * Is the logic correct (endless loop, deadlock, etc...)?
  * Is the code understandable/retraceable?
  * Are the files & functions reasonably large or would it be better so split them?
  * Is the code nesting sensible or does it have too many levels?
  * Do the variables have unambiguous naming?
  * Has redundant code been avoided?
  * Is the change covered by the test?
  * Is the styling consistent?
  * Are there enough inline comments on code?
  * Can complicated loops be replaced by syntactic sugar?


4. Feedback
-----------

  * Be kind.
  * Explain your reasoning.
  * Balance giving explicit directions with just pointing out problems and letting the developer decide.
  * Encourage developers to simplify code or add code comments instead of just explaining the complexity to you.
  * When you feel a comment is purely subjective, mark it as "nit picky" and leave it up to the PR author whether they want to implement your feedback.
  * If you are unsure about the quality of your review, give a short review report - describe how and what you have tested.


More information: `How to do a code review - Google's Engineering Practices documentation <https://google.github.io/eng-practices/review/reviewer/>`__
