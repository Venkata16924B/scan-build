# -*- coding: utf-8 -*-
#                     The LLVM Compiler Infrastructure
#
# This file is distributed under the University of Illinois Open Source
# License. See LICENSE.TXT for details.
"""
This module responsible to run the Clang static analyzer against any build
and generate reports.

This work is derived from the original 'scan-build' Perl implementation and
from an independent project 'bear'. For history let me record how the Perl
implementation was working. Then explain how is it now.

=============================
Perl implementation internals
=============================

There were two major parts of the original design. The compiler wrappers
('ccc-analyzer' and 'c++-analyzer') and the driver ('scan-build').
De facto 'CC' and 'CXX' environment variables are the standard way to make
your build configurable on compilers. (A build might respect this convention
or not.) When the driver started it overrides the 'CC' and 'CXX' environment
variables with the wrapper files and start the build. The wrappers are doing
their jobs (explained later) generates the desired output files and the
reports. Then the driver goes through on the reports and generates a "cover"
for it.

As you can see the driver is the only interface for the user. The wrappers
are doing the real work. The communication between the two parts does via
environment variables. The driver not only set the 'CC' and 'CXX', but many
others as well.

As the wrappers called as compilers. These should do behave like a compiler.
So, it calls the real compiler (it choose from environment variables, depends
from the OS type). This step generates the desired output file, so the build
can carry on. The exit code of the compilation is saved to be the exit code
of the wrapper. Then it execute the analyzer if that is needed. This is a
complex logic: it parses the command line arguments, it picks the needed
arguments to run the analyzer or decide to run or not. And it executes the
analyzer and exit.

The static analyzer is inside the Clang binary, can be triggered by special
command line argument. To run the analyzer against a single file,
wrapper collect arguments from the the current command line. And also
make arguments from the driver's command line parameters (which were
passed as environment variables).

If the analyzer fails, then the wrapper generates error report. This is
optional, but when it triggered then those go into the "cover".

===========================
Current implementation idea
===========================

The current design address these tasks separably. The major split is between
to capture the compilations and record it into a compilation database, and run
the analyzer against all file in the compilation database.

To capture the compiler invocation can be done as the Perl implementation
was doing. (To override the 'CC' and 'CXX' variables.) But that depends on the
build process do respect those variables or not. For better coverage 'bear'
was using the pre-load feature of the OS dynamic linker. Details explained
later, the point here is to generate the compilation database can be done in
multiple ways, but keep the compilation database as an interface between these
two steps.

To run the analyzer against the entire project is more easier. It could be done
in a single executable (no need to pass environment variables between
processes) and parallelism can be exploited. The analyzer execution is also
implemented in splits. As earlier explained, a single analyzer run depends from
these two factors: the command line parameters of the 'scan-build' and the
command line parameter of the individual compilation. So steps like generate a
command to analyzer, execute it can be done parallel. Then to collect the
outputs and generate the "cover" also can be divided and make it parallel.

For more please check the individual modules.
"""


def duplicate_check(method):
    """ Predicate to detect duplicated entries.

    Unique hash method can be use to detect duplicates. Entries are
    represented as dictionaries, which has no default hash method.
    This implementation uses a set datatype to store the unique hash values.

    This method returns a method which can detect the duplicate values.
    """

    def predicate(entry):
        entry_hash = predicate.unique(entry)
        if entry_hash not in predicate.state:
            predicate.state.add(entry_hash)
            return False
        return True

    predicate.unique = method
    predicate.state = set()
    return predicate


def tempdir():
    """ Return the default temorary directory. """
    from os import getenv
    return getenv('TMPDIR', getenv('TEMP', getenv('TMP', '/tmp')))
