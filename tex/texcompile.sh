cd tex
pdflatex $1.tex >> texout.log 2>&1
if [ $? != 0 ];
then
    grep -A 10 -m 1 "^!" $1.log;
else
    echo "";
fi
convert -background white -flatten -border 80 -density 500 -quality 100 $1.pdf $1.png
#cd tex
#latex -no-shell-escape -halt-on-error $1.tex >> $1.texout.log 2>&1
#dvipng -bg White -T tight -D 620 -o $1.png $1
