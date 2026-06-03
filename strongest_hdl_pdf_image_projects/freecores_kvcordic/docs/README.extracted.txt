cordic user manual
Title cordic (Multi-function, universal, ﬁxed-point CORDIC)
Author Nikolaos Kavvadias (C) 2010, 2011, 2012, 2013, 2014
Contact nikos@nkavvadias.com
Website http://www.nkavvadias.com
Release Date 22 February 2014
V ersion 1.0.0
Rev. history
v1.0.0 2013-02-22
Updated architecture. A single cycle is now needed per iter-
ation. Documentation updated to RestructuredText. Logic
synthesis scripts updated for Xilinx ISE/XST 14.6.
v0.0.2 2010-11-08
A universal CORDIC algorithm is now speciﬁed. The new
version uses the full CORDIC interface (X,Y ,Z) for input
and output. Q2.14 (16-bit) signed ﬁxed-point arithmetic is
emulated through the use of integers.
v0.0.1 2010-11-04
The CORDIC-EULA.txt has been added.
v0.0.0 2010-11-01
Initial release.
1. Introduction
cordic is a collection of ﬁles comprising an implementation of a universal CORDIC
algorithm (rotation/vectoring direction, circular/linear/hyperbolic mode) high-level syn-
thesis benchmark by Nikolaos Kavvadias. All design ﬁles exceptcordic.c, cordic.nac,
and cordic_test_data.txt have been automatically generated. The original
cordic.vhd has been optimized via (manual) operation chaining.operpack.vhd,
std_logic_textio.vhd are simulation/synthesis library ﬁles, copyrighted by their
respective authors.
IMPORTANT: Please go through the license agreement (CORDIC-EULA.txt) to
ensure proper use of the CORDIC IP CORE.
2. File listing
The CORDIC IP core distribution includes the following ﬁles:
1
/cordic Top-level directory
/bench/vhdl Benchmarks VHDL directory
cordic_tb.vhd Automatically-generated VHDL testbench ﬁle.
/doc Documentation directory
AUTHORS List of authors.
CORDIC-EULA.txt End-user license agreement for using cordic.
README This ﬁle.
README.html HTML version of README.
README.pdf PDF version of README.
rst2docs.sh Bash script for generating the HTML and PDF versions.
VERSION Current version of the CORDIC IP cores.
/rtl/vhdl RTL source code directory for the IP core
cordic.vhd Automatically-generated VHDL design ﬁle (hand-
optimized for operation chaining).
cordic_cdt_pkg.vhd Package containing declarations.
/sim/rtl_sim RTL simulation ﬁles directory
/sim/rtl_sim/bin RTL simulation scripts directory
cordic.mk Unix/Cygwin makeﬁle for running a GHDL simulation.
/sim/rtl_sim/out Dumps and other useful output from RTL simulation
cordic_alg_test_res-
ults.txt
Check this ﬁle for output.
/sim/rtl_sim/run Files for running RTL simulations
cordic.sh Unix/Cygwin bash shell script for running a GHDL sim-
ulation.
cordic_test_data.txt Reference vectors.
/sim/rtl_sim/vhdl VHDL source ﬁles used for running RTL simulations
operpack.vhd Reduced version of Nikolaos Kavvadias’ operator li-
brary.
std_logic_textio.vhd Modiﬁed version of a testbench-related package.
/sw Software utilities
cordic.c Reference C implementation for test vector generation.
cordic.dot CDFG of the cordic procedure as a Graphviz ﬁle.
cordic.dot.png PNG image for the above.
cordic.nac The NAC description of the CORDIC application.
cordic-ﬂp.txt Comparison of ﬁxed-point to ﬂoating-point CORDIC
(using calls to the math C library) results.
/syn/xise Synthesis ﬁles for use with Xilinx ISE
/syn/xise/bin Synthesis scripts directory
xst.mk Standard Makeﬁle for command-line usage of ISE.
/syn/xise/log Generated log ﬁles from the synthesis process
cordic-xst14.6.txt Synthesis report from Xilinx ISE (XST) 14.6.
2
/syn/xise/run Files for running synthesis
syn.sh Bash shell script for synthesizingcordic architectures
with ISE.
3. Usage
1. Run the shell script from a Unix/Linux/Cygwin command line.
$ ./cordic.sh
After this process, the cordic_alg_test_results.txt ﬁle is generated
containing simulation results. The GHDL simulation will also generate a VCD (wave-
form) ﬁle that can be opened with GTKwave:
$gtkwave cordic_fsmd.vcd
2. Create, build and run a Modelsim project with the following ﬁles (in this order):
operpack.vhd
std_logic_textio.vhd
cordic_cdt_pkg.vhd
ram.vhd
cordic.vhd
cordic_tb.vhd
4. Synthesis
The CORDI