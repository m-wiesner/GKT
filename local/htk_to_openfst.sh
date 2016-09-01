

lattices=$1
output=$2
syms=$3
lattice_files=( `find $lattices -name "*.latt"` )

for lat in ${lattice_files[@]}; do
  latname=`basename $lat`
  latname=${latname%.*}
  gunzip -c $lat | htk_to_openfst.py | fstcompile --isymbols=$syms --osymbols=$syms > ${output}/${latname}.fst
done

