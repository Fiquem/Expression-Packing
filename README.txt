Paper Info
----------

Title: Expression Packing: As-Few-As-Possible Training Expressions for Blendshape Transfer
Authors: Emma Carrigan, Eduard Zell, Cédric Guiard, Rachel McDonnell
Conference: Eurographics 2020


How to run Expression Packing
-----------------------------

We used Python 3.6.2

Prerequisites:
- Install CPLEX 12.9.0
	-- you will need to create an IBM account with an email from an academic institution
	-- you can download CPLEX Studio 12.9 from https://www-03.ibm.com/isc/esd/dswdown/searchPartNumber.wss?partNumber=CNZM0ML
		> check that cplex.exe is in the PATH
			run "cplex.exe" in the command line
- Install pulp, numpy, cvxpy
	-- From the command line run:
		pip install pulp
		pip install numpy
		pip install cvxpy

How-To:
- open a command prompt and navigate to this folder
- run:
	python expression_packing.py
- the results will be displayed on screen and saved to results.txt in the form of a list of lists of blendshape indices

-----------------------------

Currently there is no data included in this repository for testing.
