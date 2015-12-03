---
layout: page
title: "Contributing"
category: dev
date: 2013-07-20 11:49:22
order: 0
---

The first step in contributing to the code base is [forking the repo](https://help.github.com/articles/fork-a-repo).

If you have an existing fork, make the repo is up-to-date. Always create the branch off the actively developed branch (typically `develop` or `master`)

**Before submitting code:**
First off, thank you for considering a contribution! Before you submit any code, please read the following Developer's Certificate of Origin (DCO):

```
By making a contribution to the Varify project ("Project"),
I represent and warrant that:

a. The contribution was created in whole or in part by me and I have the right
to submit the contribution on my own behalf or on behalf of a third party who
has authorized me to submit this contribution to the Project; or

b. The contribution is based upon previous work that, to the best of my
knowledge, is covered under an appropriate open source license and I have the
right and authorization to submit that work with modifications, whether
created in whole or in part by me, under the same open source license (unless
I am permitted to submit under a different license) that I have identified in
the contribution; or

c. The contribution was provided directly to me by some other person who
represented and warranted (a) or (b) and I have not modified it.

d. I understand and agree that this Project and the contribution are publicly
known and that a record of the contribution (including all personal
information I submit with it, including my sign-off record) is maintained
indefinitely and may be redistributed consistent with this Project or the open
source license(s) involved.
```

This DCO simply certifies that the code you are submitting abides by the clauses stated above. To comply with this agreement, all commits must be signed off with your legal name and email address.

**For bug fixes:**

- Create a branch
- Once the bug has been fixed with sufficient testing submit a [pull request](https://help.github.com/articles/using-pull-requests)
- If there is an existing open issue, reference the issue number in the pull request description.

**For new features:**

Open a ticket thoroughly describing the feature. The more detail you provide, the better. After at least one of core developers responds or triages the ticket and says it's a go, follow the steps:

- Create a branch
- Once implemented with tests and documentation, submit a pull request referencing the open ticket.

**For documentation:**

- Create a branch or [edit the file](https://help.github.com/articles/creating-and-editing-files-in-your-repository#changing-files-you-dont-own)
- Submit a pull request
